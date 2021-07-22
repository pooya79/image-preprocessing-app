from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import threading
import cv2
import sys
from libs.utils import *
from libs.zoomWidget import ZoomWidget
from libs.canvas import Canvas
from libs.toolBar import ToolBar
from libs.resources import *
from libs.colorDialog import ColorDialog
from libs.shape import Shape
from functools import partial

class WindowMixin(object):

    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            add_actions(menu, actions)
        return menu

    def toolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setObjectName(u'%sToolBar' % title)
        # toolbar.setOrientation(Qt.Vertical)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        if actions:
            add_actions(toolbar, actions)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        return toolbar

class LabelingApp(QMainWindow, WindowMixin):
    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = list(range(3))
    pageClosedWithYes = pyqtSignal(bool, list, list)

    def __init__(self, image_list, label_list=[]):
        super(LabelingApp, self).__init__()

        labels_layout = QVBoxLayout()
        labels_layout.setContentsMargins(0, 0, 0, 0)

        # adding picture label edit line
        picture_label_text = QLabel("<h4>Image Label:</h4>")
        self.picture_label_edit = QLineEdit()
        self.model_list = QStringListModel()
        self.completer = QCompleter()
        self.completer.setModel(self.model_list)
        self.picture_label_edit.setCompleter(self.completer)
        self.picture_label_edit.setValidator(label_validator())
        self.picture_label_edit.editingFinished.connect(self.label_edit_finished)
        labels_layout.addWidget(picture_label_text)
        labels_layout.addWidget(self.picture_label_edit)

        # Create and add a widget for showing current label items
        current_pictures_label = QLabel("<h4>All Labels:</h4>")
        self.label_list = QListWidget()
        label_list_container = QWidget()
        label_list_container.setLayout(labels_layout)
        self.label_list.itemActivated.connect(self.label_selection_changed)
        self.label_list.itemSelectionChanged.connect(self.label_selection_changed)
        self.label_list.itemDoubleClicked.connect(self.edit_label)
        labels_layout.addWidget(current_pictures_label)
        labels_layout.addWidget(self.label_list)

        self.label_dock = QDockWidget('Box Labels', self)
        self.label_dock.setObjectName('labels')
        self.label_dock.setWidget(label_list_container)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.label_dock)
        self.dock_features = QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable
        self.label_dock.setFeatures(self.label_dock.features() ^ self.dock_features)

        # Create and add a widget for showing current images
        self.image_list_widget = QListWidget()
        self.image_list_widget.itemDoubleClicked.connect(self.image_item_double_clicked)
        image_list_layout = QVBoxLayout()
        image_list_layout.setContentsMargins(0, 0, 0, 0)
        image_list_layout.addWidget(self.image_list_widget)
        image_list_container = QWidget()
        image_list_container.setLayout(image_list_layout)
        self.image_dock = QDockWidget("Image List", self)
        self.image_dock.setObjectName("images")
        self.image_dock.setWidget(image_list_container)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.image_dock)
        self.image_dock.setFeatures(QDockWidget.DockWidgetFloatable)

        # adding canvas and its actions
        self.zoom_widget = ZoomWidget()
        self.color_dialog = ColorDialog(parent=self)

        self.canvas = Canvas(parent=self)
        self.canvas.zoomRequest.connect(self.zoom_request)

        scroll = QScrollArea()
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True)
        self.scroll_bars = {
            Qt.Vertical: scroll.verticalScrollBar(),
            Qt.Horizontal: scroll.horizontalScrollBar()
        }
        self.scroll_area = scroll
        self.canvas.scrollRequest.connect(self.scroll_request)

        self.setCentralWidget(scroll)

        # Actions
        action = partial(new_action, self)
        quit = action('Quit', self.exit,
                      'Ctrl+Q', 'quit', 'Quit App')

        open_next_image = action('Next Image', self.open_next_image,
                                 'd', 'next', "Open the next image (d)")

        open_prev_image = action('Prev Image', self.open_prev_image,
                                 'a', 'prev', "Open the previous image (a)")

        delete_label = action("Delete Label", self.delete_label,
                              'Delete', 'delete', "Remove the label", enabled=False)

        reset_all = action("Reset All", self.reset_all, None, 'resetall', 'Reset All')

        zoom = QWidgetAction(self)
        zoom.setDefaultWidget(self.zoom_widget)
        self.zoom_widget.setWhatsThis(
            u"Zoom in or out of the image. Also accessible with"
            " %s and %s from the canvas." % (format_shortcut("Ctrl+[-+]"),
                                             format_shortcut("Ctrl+Wheel")))

        zoom_in = action("Zoom In", partial(self.add_zoom, 10),
                         'Ctrl++', 'zoom-in', "Increase zoom level")

        zoom_out = action("Zoom Out", partial(self.add_zoom, -10),
                          'Ctrl+-', 'zoom-out', "Decrease zoom level")

        zoom_org = action("Original Size", partial(self.set_zoom, 100),
                          'Ctrl+=', 'zoom', "Zoom to original size")

        fit_window = action("Fit Window", self.set_fit_window,
                            'Ctrl+F', 'fit-window', "Zoom follows window size")

        fit_width = action("Fit Width", self.set_fit_width,
                           'Ctrl+Shift+F', 'fit-width', "Zoom follows window width")

        # Group zoom controls into a list for easier toggling.
        zoom_actions = (self.zoom_widget, zoom_in, zoom_out,
                        zoom_org, fit_window, fit_width)
        self.zoom_mode = self.MANUAL_ZOOM
        self.scalers = {
            self.FIT_WINDOW: self.scale_fit_window,
            self.FIT_WIDTH: self.scale_fit_width,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }

        shape_line_color = action("Box Line Color", self.choose_color1,
                                  icon='color_line', tip="Choose Box line color")

        labels = self.label_dock.toggleViewAction()
        labels.setText("Show/Hide Label Panel")
        labels.setShortcut("Ctrl+Shift+L")

        # Store actions for further handling
        self.actions = Struct(deleteLabel=delete_label, lineColor=shape_line_color,
                              zoom=zoom, zoomIn=zoom_in, zoomOut=zoom_out, zoomOrg=zoom_org, resetAll=reset_all,
                              fitWindow=fit_window, fitWidth=fit_width, zoomActions=zoom_actions)

        self.menus = Struct(
            file=self.menu("file"),
            edit=self.menu("edit"),
            view=self.menu("view")
        )

        add_actions(self.menus.file,
                    (reset_all, None, quit))
        add_actions(self.menus.edit,
                    (delete_label, None, shape_line_color))
        add_actions(self.menus.view, (
            zoom_in, zoom_out,
            zoom_org, None, fit_window, fit_width
        ))

        self.tools = self.toolbar('Tools')
        self.actions.beginner = (
            open_next_image, open_prev_image, None, delete_label, None,
            zoom_in, zoom, zoom_out, zoom_org, fit_window, fit_width
        )
        add_actions(self.tools, self.actions.beginner)

        # Application state.
        self.cv_image = None
        self.line_color = QColor(0, 255, 0, 128)
        self.image_list_labels_first = [l[2] for l in image_list]
        self.image_list_shapes_first = []
        for l in image_list:
            if len(l) == 4:
                self.image_list_shapes_first.append(l[-1])
            else:
                self.image_list_shapes_first.append([])
        self.image_list = image_list[:]
        self.all_labels_first = label_list
        self.all_labels = []
        self.shape = Shape("Boundaries")
        self.image = None
        self.image_index = 0
        self.image_count = len(self.image_list)
        self.shape.line_color = QColor(255, 255, 255, 200)
        self.shape.fill_color = QColor(255, 255, 255, 70)

        self.statusBar().showMessage("labeling app started.")
        self.statusBar().show()

        self.resize(600, 500)
        self.canvas.set_drawing_color(self.line_color)


        # Callbacks:
        self.zoom_widget.valueChanged.connect(self.paint_canvas)

        # Display cursor coordinates at the right of status bar
        self.label_coordinates = QLabel('')
        self.statusBar().addPermanentWidget(self.label_coordinates)

        # start function
        self.start()

    def start(self):
        if len(self.image_list[0]) != 4:
            self.cv_image = cv2.imread(self.image_list[0][1])
            self.image_list[0].append([0, 0, self.cv_image.shape[1], self.cv_image.shape[0]])
        self.image_index = 0
        self.load_image(0)
        self.set_app_title()

        for label in self.all_labels_first:
            self.add_label(label)

        t = threading.Thread(target=self.load_other_images)
        t.start()

    def load_image(self, image_index=0):
        self.image = self.get_pixmap(cv2.imread(self.image_list[image_index][1]))
        x_min = self.image_list[image_index][-1][0]
        y_min = self.image_list[image_index][-1][1]
        x_max = self.image_list[image_index][-1][2]
        y_max = self.image_list[image_index][-1][3]

        self.shape.points = [QPointF(x_min, y_min), QPointF(x_max, y_min), QPointF(x_max, y_max), QPointF(x_min, y_max)]
        self.shape.close()

        self.canvas.load_pixmap(self.image)
        self.canvas.load_shapes((self.shape,))

        self.picture_label_edit.setText(self.image_list[image_index][2])

    def set_app_title(self):
        current_index = self.image_index % self.image_count + 1
        self.setWindowTitle("labeling app: ({})".format(self.image_list[self.image_index][1]) + " [{}/{}]".format(current_index, self.image_count))

    def load_other_images(self):
        for image in self.image_list:
            self.image_list_widget.addItem(image[0])
        for i in range(1, len(self.image_list)):
            if len(self.image_list[i]) == 3:
                self.cv_image = cv2.imread(self.image_list[i][1])
                self.image_list[i].append([0, 0, self.cv_image.shape[1], self.cv_image.shape[0]])

    def label_edit_finished(self):
        new_label = self.picture_label_edit.text().strip()
        if new_label:
            if new_label not in [self.label_list.item(x).text() for x in range(self.label_list.count())]:
                self.add_label(new_label)
            self.image_list[self.image_index][2] = new_label
        self.picture_label_edit.setText(new_label)

    def edit_label(self, item=None):
        self.picture_label_edit.setText(item.text())
        self.image_list[self.image_index][2] = item.text()

    def add_label(self, label):
        item = QListWidgetItem(label)
        item.setBackground(generate_color_by_text(label))
        self.label_list.addItem(item)
        if label not in self.all_labels:
            self.all_labels.append(label)

    def image_item_double_clicked(self, item=None):
        self.save_current_image_changes()
        for i, image_properties in enumerate(self.image_list):
            if image_properties[0] == item.text():
                self.image_index = i
                self.load_image(self.image_index)
                self.set_app_title()
                break

    def save_current_image_changes(self):
        list_x = [point.x() for point in self.shape.points]
        list_y = [point.y() for point in self.shape.points]
        min_x = min(list_x)
        min_y = min(list_y)
        max_x = max(list_x)
        max_y = max(list_y)

        self.image_list[self.image_index][-1] = [min_x, min_y, max_x, max_y]

    def label_selection_changed(self, item=None):
        self.actions.deleteLabel.setEnabled(True)

    # Canvas Functions
    def zoom_request(self, delta):
        # get the current scrollbar positions
        # calculate the percentages ~ coordinates
        h_bar = self.scroll_bars[Qt.Horizontal]
        v_bar = self.scroll_bars[Qt.Vertical]

        # get the current maximum, to know the difference after zooming
        h_bar_max = h_bar.maximum()
        v_bar_max = v_bar.maximum()

        # get the cursor position and canvas size
        # calculate the desired movement from 0 to 1
        # where 0 = move left
        #       1 = move right
        # up and down analogous
        cursor = QCursor()
        pos = cursor.pos()
        relative_pos = QWidget.mapFromGlobal(self, pos)

        cursor_x = relative_pos.x()
        cursor_y = relative_pos.y()

        w = self.scroll_area.width()
        h = self.scroll_area.height()

        # the scaling from 0 to 1 has some padding
        # you don't have to hit the very leftmost pixel for a maximum-left movement
        margin = 0.1
        move_x = (cursor_x - margin * w) / (w - 2 * margin * w)
        move_y = (cursor_y - margin * h) / (h - 2 * margin * h)

        # clamp the values from 0 to 1
        move_x = min(max(move_x, 0), 1)
        move_y = min(max(move_y, 0), 1)

        # zoom in
        units = delta / (8 * 15)
        scale = 10
        self.add_zoom(scale * units)

        # get the difference in scrollbar values
        # this is how far we can move
        d_h_bar_max = h_bar.maximum() - h_bar_max
        d_v_bar_max = v_bar.maximum() - v_bar_max

        # get the new scrollbar values
        new_h_bar_value = h_bar.value() + move_x * d_h_bar_max
        new_v_bar_value = v_bar.value() + move_y * d_v_bar_max

        h_bar.setValue(new_h_bar_value)
        v_bar.setValue(new_v_bar_value)

    def scroll_request(self, delta, orientation):
        units = - delta / (8 * 15)
        bar = self.scroll_bars[orientation]
        bar.setValue(int(bar.value() + bar.singleStep() * units))

    # action functions
    def open_prev_image(self):
        self.save_current_image_changes()
        self.image_index -= 1
        self.image_index = self.image_index % self.image_count
        self.load_image(self.image_index)
        self.set_app_title()

    def open_next_image(self):
        self.save_current_image_changes()
        self.image_index += 1
        self.image_index = self.image_index % self.image_count
        self.load_image(self.image_index)
        self.set_app_title()

    def delete_label(self):
        current_label = self.label_list.currentItem()
        self.all_labels.remove(current_label.text())
        self.label_list.takeItem(self.label_list.currentIndex().row())
        if not self.all_labels:
            self.actions.deleteLabel.setEnabled(False)

    def add_zoom(self, increment=10):
        self.set_zoom(self.zoom_widget.value() + increment)

    def set_zoom(self, value):
        self.actions.fitWidth.setChecked(False)
        self.actions.fitWindow.setChecked(False)
        self.zoom_mode = self.MANUAL_ZOOM
        self.zoom_widget.setValue(value)

    def set_fit_window(self, x, value=True):
        if value:
            self.actions.fitWidth.setChecked(False)
        self.zoom_mode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjust_scale()

    def set_fit_width(self, x, value=True):
        if value:
            self.actions.fitWindow.setChecked(False)
        self.zoom_mode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjust_scale()

    def adjust_scale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoom_mode]()
        self.zoom_widget.setValue(int(100 * value))

    def choose_color1(self):
        color = self.color_dialog.getColor(self.line_color, u'Choose Line Color',
                                           default=QColor(0, 255, 0, 128))
        if color:
            self.line_color = color
            self.shape.line_color = color
            self.shape.fill_color = color

    def reset_all(self):
        for i, imagel in enumerate(self.image_list):
            if self.image_list_shapes_first[i]:
                imagel[-1] = self.image_list_shapes_first[i]
            else:
                imagel.pop()
            imagel[2] = self.image_list_labels_first[i]
        self.label_list.clear()
        self.image_list_widget.clear()
        self.start()

    def exit(self):
        self.close()

    # canvas signal
    def shape_moved(self):
        pass

    # helper functions
    def scale_fit_window(self):
        """Figure out the size of the pixmap in order to fit the main widget."""
        e = 2.0 # So that no scrollbars are generated.
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1
        # Calculate a new scale value based on the pixmap's aspect ration
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    def scale_fit_width(self):
        # The epsilon does not seem to work too wll here.
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()

    def paint_canvas(self):
        # assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoom_widget.value()
        self.canvas.label_font_size = int(0.02 * max(self.image.width(), self.image.height()))
        self.canvas.adjustSize()
        self.canvas.update()

    def get_pixmap(self, cv_image):
        frame = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
        return QPixmap.fromImage(image)

    def discard_changes_dialog(self):
        yes, no, cancel = QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel
        msg = u'Would you like to save changes and proceed?'
        return QMessageBox.warning(self, u'Attention', msg, yes | no | cancel)

    def closeEvent(self, ev):
        message = self.discard_changes_dialog()
        self.save_current_image_changes()
        if message == QMessageBox.Cancel:
            ev.ignore()
        elif message == QMessageBox.Yes:
            self.pageClosedWithYes.emit(True, self.image_list, self.all_labels)
        elif message == QMessageBox.No:
            self.pageClosedWithYes.emit(False, self.image_list, self.all_labels)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    lena = cv2.imread("lena_copy.png")
    test = cv2.imread("test.jpg")
    main = LabelingApp([["lena", "lena_copy.png", "person"], ["test", "test.jpg", "lamp"]], ["person", "lamp"])
    main.show()

    sys.exit(app.exec())