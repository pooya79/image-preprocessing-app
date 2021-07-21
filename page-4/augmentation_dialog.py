import cv2
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import imutils
import sys

def random_crop(cv_image, ratio):
    if ratio == 0:
        return cv_image
    if ratio == 1:
        return np.ones(cv_image.shape, np.uint8) * 255
    index_h = int(cv_image.shape[0] * ratio/2)
    index_w = int(cv_image.shape[1] * ratio/2)
    return cv_image[index_h:-index_h - 1, index_w:-index_w - 1]

class GridDialog(QDialog):
    PREPROCESSING, AUGMENTATION = range(2)
    PREPROCESSING_CASES = ["grayscale", "resize"]
    AUGMENTATION_CASES = ["flip", "90 degree rotate", "random crop", "random rotation",
                          "blur", "brightness"]
    accept = pyqtSignal(list)
    closed = pyqtSignal()
    def __init__(self, test_picture, type=1, draw_case="menu", deleted_processes=[]):
        super(GridDialog, self).__init__()
        # main widget layout
        self.setFixedSize(650, 650)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.setWindowFlags(Qt.WindowType.WindowSystemMenuHint |
                            Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
        self.test_picture = test_picture
        self.deleted_processes = deleted_processes
        self.draw_case = draw_case
        self.type = type
        if draw_case == "menu":
            self.draw_menu()
        elif draw_case in self.PREPROCESSING_CASES or draw_case in self.AUGMENTATION_CASES:
            self.show_submenu(draw_case)

    def draw_menu(self):
        for i in reversed(range(self.main_layout.count())):
            self.main_layout.itemAt(i).widget().setParent(None)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        # upper frame
        self.upper_frame = QFrame()
        self.upper_frame.setFrameShape(QFrame.Shape.Box)
        self.upper_frame.setFrameShadow(QFrame.Shadow.Plain)
        self.upper_frame_layout = GridLayout(4, 4)
        self.upper_frame.setLayout(self.upper_frame_layout)

        # adding custom labels to upper frame for preprocessing
        cv_image = cv2.imread(r"test.jpg")
        if self.type == 0:
            for process in self.PREPROCESSING_CASES:
                if process not in self.deleted_processes:
                    process_widget = CustomLabel(cv_image, process)
                    process_widget.clicked.connect(self.show_submenu)
                    self.upper_frame_layout.add_widget(process_widget)
        elif self.type == 1:
            for process in self.AUGMENTATION_CASES:
                if process not in self.deleted_processes:
                    process_widget = CustomLabel(cv_image, process)
                    process_widget.clicked.connect(self.show_submenu)
                    self.upper_frame_layout.add_widget(process_widget)

        # bottom widget
        self.bottom_widget = QWidget()
        self.bottom_widget.setFixedHeight(50)
        self.bottom_widget_layout = QHBoxLayout()
        self.bottom_widget.setLayout(self.bottom_widget_layout)
        # add button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.exit_cancel_pressed)
        self.bottom_widget_layout.addStretch()
        self.bottom_widget_layout.addWidget(self.cancel_button)
        self.bottom_widget_layout.addStretch()

        # add widgets to main widget
        self.main_layout.addWidget(self.upper_frame)
        self.main_layout.addWidget(self.bottom_widget)

    def show_submenu(self, process_type):
        for i in reversed(range(self.main_layout.count())):
            self.main_layout.itemAt(i).widget().setParent(None)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        self.process_type = process_type

        # designing template
        self.submenu_main_widget = QWidget()
        self.submenu_main_layout = QHBoxLayout()
        self.submenu_main_widget.setLayout(self.submenu_main_layout)
        # control box widget
        self.control_widget_container = QWidget()
        self.control_widget_container.setFixedWidth(250)
        self.control_widget_container_layout = QVBoxLayout(self.control_widget_container)

        # pictures widget container + original test picture
        self.image_width, self.image_height = 300, 190
        self.pictures_widget_container = QFrame()
        self.pictures_widget_container.setFrameShape(QFrame.Shape.Box)
        self.pictures_widget_container.setFrameShadow(QFrame.Shadow.Plain)
        self.pictures_widget_container.setStyleSheet(
            "background: #ffffff;"
        )
        self.pictures_widget_container_layout = QVBoxLayout(self.pictures_widget_container)
        # original picture
        original_picture_label_image = QLabel()
        original_picture_label_image.setFixedSize(self.image_width, self.image_height)
        original_picture_label_image.setAlignment(Qt.AlignCenter)
        original_picture_pixmap = self.get_pixmap(self.test_picture)
        original_picture_pixmap = original_picture_pixmap.scaled(self.image_width, self.image_height, Qt.KeepAspectRatio)
        original_picture_label_image.setPixmap(original_picture_pixmap)
        original_picture_label_text = QLabel("Original Picture")
        original_picture_label_text.setAlignment(Qt.AlignCenter)
        self.pictures_widget_container_layout.addWidget(original_picture_label_image, alignment=Qt.AlignCenter)
        self.pictures_widget_container_layout.addWidget(original_picture_label_text)
        self.pictures_widget_container_layout.addStretch()

        # apply and cancel buttons widget
        buttons_widget = QWidget()
        buttons_widget_layout = QHBoxLayout()
        buttons_widget.setLayout(buttons_widget_layout)
        apply_button = QPushButton("apply")
        cancel_button = QPushButton("cancel")
        buttons_widget_layout.addWidget(cancel_button)
        buttons_widget_layout.addStretch()
        buttons_widget_layout.addWidget(apply_button)
        if self.draw_case != "menu":
            cancel_button.clicked.connect(self.exit_cancel_pressed)
        else:
            cancel_button.clicked.connect(self.back_cancel_pressed)

        apply_button.clicked.connect(self.apply_pressed)

        # adding all widgets to main layout
        self.submenu_main_layout.addWidget(self.pictures_widget_container)
        self.submenu_main_layout.addWidget(self.control_widget_container)
        self.main_layout.addWidget(self.submenu_main_widget)
        self.main_layout.addWidget(buttons_widget)

        if self.type == 0:
            if process_type == "grayscale":
                self.draw_grayscale_menu()
            elif process_type == "resize":
                self.draw_resize_menu()
        elif self.type == 1:
            if process_type == "flip":
                self.draw_flip_menu()
            elif process_type == "90 degree rotate":
                self.draw_90rotate_menu()
            elif process_type == "random crop":
                self.draw_crop_menu()
            elif process_type == "random rotation":
                self.draw_rotate_menu()
            elif process_type == "blur":
                self.draw_blur_menu()
            elif process_type == "brightness":
                self.draw_brightness_menu()

    def draw_grayscale_menu(self):
        # adding control widget's buttons
        self.title_label = QLabel("<h2>Grayscale:</h2>")
        self.check_box_grayscale = QCheckBox("GrayScale")
        self.control_widget_container_layout.addWidget(self.title_label)
        self.control_widget_container_layout.addWidget(self.check_box_grayscale)
        self.control_widget_container_layout.addStretch()

        self.check_box_grayscale.stateChanged.connect(self.check_grayscale_changed)

        # show case pictures
        self.widget_case1 = QWidget()
        self.widget_case2 = QWidget()
        self.layout_show_case1 = QHBoxLayout(self.widget_case1)
        self.layout_show_case2 = QHBoxLayout(self.widget_case2)
        self.pictures_widget_container_layout.addWidget(self.widget_case1)
        self.pictures_widget_container_layout.addWidget(self.widget_case2)

        self.picture_grayscale_label = QLabel()
        self.picture_grayscale_label.setPixmap(self.get_pixmap(
            cv2.cvtColor(self.test_picture, cv2.COLOR_BGR2GRAY)).scaled(self.image_width, self.image_height, Qt.KeepAspectRatio))
        self.text_label_grayscale = QLabel("GrayScale")
        self.picture_grayscale_label.setAlignment(Qt.AlignCenter)
        self.text_label_grayscale.setAlignment(Qt.AlignCenter)

        self.layout_show_case1.addWidget(self.picture_grayscale_label)
        self.layout_show_case2.addWidget(self.text_label_grayscale)

    def check_grayscale_changed(self, state):
        pass

    def draw_resize_menu(self):
        # adding control widget's buttons
        self.title_label = QLabel("<h2>Resize:</h2>")
        self.resize_combobox = QComboBox()
        self.resize_combobox.addItem("Stretch")
        self.resize_combobox.addItem("Resize & Crop")
        self.size_label = QLabel("Size: ")
        self.cross_label = QLabel(" \u00D7 ")
        self.width_edit = QLineEdit("0")
        self.height_edit = QLineEdit("0")
        self.size_layout = QHBoxLayout()
        self.size_layout.addWidget(self.size_label)
        self.size_layout.addWidget(self.width_edit)
        self.size_layout.addWidget(self.cross_label)
        self.size_layout.addWidget(self.height_edit)
        self.size_layout.addStretch()
        self.control_widget_container_layout.addWidget(self.title_label)
        self.control_widget_container_layout.addWidget(self.resize_combobox)
        self.control_widget_container_layout.addLayout(self.size_layout)
        self.control_widget_container_layout.addStretch()

        self.resize_combobox.currentTextChanged.connect(self.resize_type_changed)
        self.width_edit.editingFinished.connect(self.size_changed)
        self.height_edit.editingFinished.connect(self.size_changed)
        self.valid_number = QIntValidator(1, 20000)
        self.resize_width = 0
        self.resize_height = 0

        # show case pictures
        self.widget_case1 = QWidget()
        self.widget_case2 = QWidget()
        self.layout_show_case1 = QHBoxLayout(self.widget_case1)
        self.layout_show_case2 = QHBoxLayout(self.widget_case2)
        self.pictures_widget_container_layout.addWidget(self.widget_case1)
        self.pictures_widget_container_layout.addWidget(self.widget_case2)

        self.picture_resize_label = QLabel()
        self.picture_resize_label.setPixmap(self.get_pixmap(self.test_picture).scaled(self.image_width, self.image_height, Qt.KeepAspectRatio))
        self.text_label_resize = QLabel("Resized")
        self.picture_resize_label.setAlignment(Qt.AlignCenter)
        self.text_label_resize.setAlignment(Qt.AlignCenter)

        self.layout_show_case1.addWidget(self.picture_resize_label)
        self.layout_show_case2.addWidget(self.text_label_resize)

    def resize_type_changed(self, type):
        if self.resize_width and self.resize_height:
            resize_type = self.resize_combobox.currentText()
            if type == "Stretch":
                cv_image = self.resize_image(self.test_picture, self.resize_width, self.resize_height, 0)
                self.picture_resize_label.setPixmap(
                    self.get_pixmap(cv_image).scaled(self.image_width, self.image_height, Qt.KeepAspectRatio))
            elif type == "Resize & Crop":
                cv_image = self.resize_image(self.test_picture, self.resize_width, self.resize_height, 1)
                self.picture_resize_label.setPixmap(
                    self.get_pixmap(cv_image).scaled(self.image_width, self.image_height, Qt.KeepAspectRatio))

    def size_changed(self):
        width = self.width_edit.text()
        height = self.height_edit.text()
        if self.valid_number.validate(width, 0)[0] == 2:
            self.resize_width = int(width)
        if self.valid_number.validate(height, 0)[0] == 2:
            self.resize_height = int(height)
        if self.resize_width and self.resize_height:
            resize_type = self.resize_combobox.currentText()
            if resize_type == "Stretch":
                cv_image = self.resize_image(self.test_picture, self.resize_width, self.resize_height, 0)
                self.picture_resize_label.setPixmap(self.get_pixmap(cv_image).scaled(self.image_width, self.image_height, Qt.KeepAspectRatio))
            elif resize_type == "Resize & Crop":
                cv_image = self.resize_image(self.test_picture, self.resize_width, self.resize_height, 1)
                self.picture_resize_label.setPixmap(self.get_pixmap(cv_image).scaled(self.image_width, self.image_height, Qt.KeepAspectRatio))
        self.width_edit.setText(str(self.resize_width))
        self.height_edit.setText(str(self.resize_height))

    @staticmethod
    def resize_image(cv_image, width, height, type=0):
        if type == 1:
            ratio = width / height
            image_ratio = cv_image.shape[1] / cv_image.shape[0]
            if ratio >= image_ratio:
                resize_image = cv2.resize(cv_image, (width, int(cv_image.shape[0]*width/cv_image.shape[1])))
                y = (resize_image.shape[0] - height) // 2
                return resize_image[y:y+height, :]
            else:
                resize_image = cv2.resize(cv_image, (int(cv_image.shape[1]*height/cv_image.shape[0]), height))
                x = (resize_image.shape[1] - width) // 2
                return resize_image[:, x:x+width]
        else:
            return cv2.resize(cv_image, (width, height))

    def draw_flip_menu(self):
        # adding control widget's buttons
        self.title_label = QLabel("<h2>Flip:</h2>")
        self.check_box_fliph = QCheckBox("Horizontal")
        self.check_box_flipv = QCheckBox("Vertical")
        self.control_widget_container_layout.addWidget(self.title_label)
        self.control_widget_container_layout.addWidget(self.check_box_fliph)
        self.control_widget_container_layout.addWidget(self.check_box_flipv)
        self.control_widget_container_layout.addStretch()

        self.check_box_fliph.clicked.connect(self.update_flip)
        self.check_box_flipv.clicked.connect(self.update_flip)

        # show case pictures
        self.widget_case1 = QWidget()
        self.widget_case2 = QWidget()
        self.layout_show_case1 = QHBoxLayout(self.widget_case1)
        self.layout_show_case2 = QHBoxLayout(self.widget_case2)
        self.pictures_widget_container_layout.addWidget(self.widget_case1)
        self.pictures_widget_container_layout.addWidget(self.widget_case2)
        # horizontal flip
        self.picture_fliph_label = QLabel()
        self.fliph_pixmap = self.get_pixmap(cv2.flip(self.test_picture, 1))
        self.text_label_fliph = QLabel("Horizontal Flip")
        self.picture_fliph_label.setAlignment(Qt.AlignCenter)
        self.text_label_fliph.setAlignment(Qt.AlignCenter)
        # vertical flip
        self.picture_flipv_label = QLabel()
        self.flipv_pixmap = self.get_pixmap(cv2.flip(self.test_picture, 0))
        self.text_label_flipv = QLabel("Vertical Flip")
        self.picture_flipv_label.setAlignment(Qt.AlignCenter)
        self.text_label_flipv.setAlignment(Qt.AlignCenter)

    def update_flip(self):
        stateh = self.check_box_fliph.checkState()
        statev = self.check_box_flipv.checkState()

        if stateh and statev:
            self.picture_fliph_label.setFixedSize(self.image_width//2, self.image_height)
            self.picture_fliph_label.setPixmap(self.fliph_pixmap.scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))
            self.picture_flipv_label.setFixedSize(self.image_width//2, self.image_height)
            self.picture_flipv_label.setPixmap(self.flipv_pixmap.scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))
            self.layout_show_case1.addWidget(self.picture_fliph_label)
            self.layout_show_case1.addWidget(self.picture_flipv_label)
            self.layout_show_case2.addWidget(self.text_label_fliph)
            self.layout_show_case2.addWidget(self.text_label_flipv)
        elif stateh and not statev:
            self.picture_fliph_label.setFixedSize(self.image_width, self.image_height)
            self.picture_fliph_label.setPixmap(self.fliph_pixmap.scaled(self.image_width, self.image_height, Qt.KeepAspectRatio))
            self.picture_fliph_label.setParent(None)
            self.text_label_fliph.setParent(None)
            self.picture_flipv_label.setParent(None)
            self.text_label_flipv.setParent(None)
            self.layout_show_case1.addWidget(self.picture_fliph_label)
            self.layout_show_case2.addWidget(self.text_label_fliph)
        elif statev and not stateh:
            self.picture_flipv_label.setFixedSize(self.image_width, self.image_height)
            self.picture_flipv_label.setPixmap(self.flipv_pixmap.scaled(self.image_width, self.image_height, Qt.KeepAspectRatio))
            self.picture_fliph_label.setParent(None)
            self.text_label_fliph.setParent(None)
            self.picture_flipv_label.setParent(None)
            self.text_label_flipv.setParent(None)
            self.layout_show_case1.addWidget(self.picture_flipv_label, alignment=Qt.AlignCenter)
            self.layout_show_case2.addWidget(self.text_label_flipv)
        else:
            self.picture_fliph_label.setParent(None)
            self.text_label_fliph.setParent(None)
            self.picture_flipv_label.setParent(None)
            self.text_label_flipv.setParent(None)

    def draw_90rotate_menu(self):
        # adding control widget's buttons
        self.title_label = QLabel("<h3>90 Degree Rotation:</h3>")
        self.check_box_c = QCheckBox("Clockwise")
        self.check_box_cc = QCheckBox("Counter Clockwise")
        self.check_box_ud = QCheckBox("Upside-Down")
        self.control_widget_container_layout.addWidget(self.title_label)
        self.control_widget_container_layout.addWidget(self.check_box_c)
        self.control_widget_container_layout.addWidget(self.check_box_cc)
        self.control_widget_container_layout.addWidget(self.check_box_ud)
        self.control_widget_container_layout.addStretch()

        self.check_box_c.clicked.connect(self.update_rotate90)
        self.check_box_cc.clicked.connect(self.update_rotate90)
        self.check_box_ud.clicked.connect(self.update_rotate90)

        # show case pictures
        self.widget_case1 = QWidget()
        self.widget_case2 = QWidget()
        self.layout_show_case1 = QHBoxLayout(self.widget_case1)
        self.layout_show_case2 = QHBoxLayout(self.widget_case2)
        self.pictures_widget_container_layout.addWidget(self.widget_case1)
        self.pictures_widget_container_layout.addWidget(self.widget_case2)
        # clockwise rotation
        self.picture_clockwise_label = QLabel()
        self.clockwise_pixmap = self.get_pixmap(cv2.rotate(self.test_picture, cv2.ROTATE_90_CLOCKWISE))
        self.text_label_clockwise = QLabel("Clockwise")
        self.picture_clockwise_label.setAlignment(Qt.AlignCenter)
        self.text_label_clockwise.setAlignment(Qt.AlignCenter)
        # counter clockwise rotation
        self.picture_cclockwise_label = QLabel()
        self.cclockwise_pixmap = self.get_pixmap(cv2.rotate(self.test_picture, cv2.ROTATE_90_COUNTERCLOCKWISE))
        self.text_label_cclockwise = QLabel("Counter Clockwise")
        self.picture_cclockwise_label.setAlignment(Qt.AlignCenter)
        self.text_label_cclockwise.setAlignment(Qt.AlignCenter)
        # upside down rotation
        self.picture_ud_label = QLabel()
        self.ud_pixmap = self.get_pixmap(cv2.flip(cv2.flip(self.test_picture, 0), 1))
        self.text_label_ud = QLabel("upside-down")
        self.picture_ud_label.setAlignment(Qt.AlignCenter)
        self.text_label_ud.setAlignment(Qt.AlignCenter)

        self.rotate90_image_pixmap = [self.clockwise_pixmap, self.cclockwise_pixmap, self.ud_pixmap]
        self.rotate90_image_label = [self.picture_clockwise_label, self.picture_cclockwise_label, self.picture_ud_label]
        self.rotate90_text_label = [self.text_label_clockwise, self.text_label_cclockwise, self.text_label_ud]

    def update_rotate90(self):
        count = int(bool(self.check_box_c.checkState()) + bool(self.check_box_cc.checkState()) + bool(self.check_box_ud.checkState()))
        checklist = [bool(self.check_box_c.checkState()), bool(self.check_box_cc.checkState()), bool(self.check_box_ud.checkState())]
        for label_img, label_text in zip(self.rotate90_image_label, self.rotate90_text_label):
            label_img.setParent(None)
            label_text.setParent(None)
        c = 0
        if count == 3:
            for label_img, label_text, pixmap in zip(self.rotate90_image_label, self.rotate90_text_label, self.rotate90_image_pixmap):
                label_img.setFixedSize(self.image_width//2, self.image_height//2)
                label_img.setPixmap(pixmap.scaled(self.image_width//2, self.image_height//2, Qt.KeepAspectRatio))
                if c != 2:
                    self.layout_show_case1.addWidget(label_img)
                    self.layout_show_case2.addWidget(label_text)
                else:
                    self.pictures_widget_container_layout.addWidget(label_img, alignment=Qt.AlignHCenter)
                    self.pictures_widget_container_layout.addWidget(label_text)
                c += 1
        elif count == 2:
            for label_img, label_text, pixmap in zip(self.rotate90_image_label, self.rotate90_text_label, self.rotate90_image_pixmap):
                if not checklist[c]:
                    c += 1
                    continue
                label_img.setFixedSize(self.image_width//2, self.image_height)
                label_img.setPixmap(pixmap.scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))
                self.layout_show_case1.addWidget(label_img)
                self.layout_show_case2.addWidget(label_text)
                c += 1
        elif count == 1:
            for label_img, label_text, pixmap in zip(self.rotate90_image_label, self.rotate90_text_label, self.rotate90_image_pixmap):
                if checklist[c]:
                    label_img.setFixedSize(self.image_width, self.image_height)
                    label_img.setPixmap(pixmap.scaled(self.image_width, self.image_height, Qt.KeepAspectRatio))
                    self.layout_show_case1.addWidget(label_img)
                    self.layout_show_case2.addWidget(label_text)
                c += 1


    def draw_crop_menu(self):
        # adding control widget's buttons
        self.title_label = QLabel("<h2>Random Crop:</h2>")
        self.value_label = QLabel("upper limit: {}% | lower limit: {}%".format(0, 0))
        self.upper_limit_slider = QSlider()
        self.lower_limit_slider = QSlider()
        self.upper_limit_slider.setMaximum(100)
        self.upper_limit_slider.setMinimum(0)
        self.lower_limit_slider.setMaximum(100)
        self.lower_limit_slider.setMinimum(0)
        self.upper_limit_slider.setValue(0)
        self.lower_limit_slider.setValue(0)
        self.sliders_layout = QHBoxLayout()
        self.sliders_layout.addWidget(self.upper_limit_slider)
        self.sliders_layout.addWidget(self.lower_limit_slider)
        self.control_widget_container_layout.addWidget(self.title_label)
        self.control_widget_container_layout.addWidget(self.value_label)
        self.control_widget_container_layout.addLayout(self.sliders_layout)

        self.upper_limit_slider.valueChanged.connect(self.uslider_crop_changed)
        self.lower_limit_slider.valueChanged.connect(self.lslider_crop_changed)

        # show case pictures
        self.widget_case1 = QWidget()
        self.widget_case2 = QWidget()
        self.layout_show_case1 = QHBoxLayout(self.widget_case1)
        self.layout_show_case2 = QHBoxLayout(self.widget_case2)
        self.pictures_widget_container_layout.addWidget(self.widget_case1)
        self.pictures_widget_container_layout.addWidget(self.widget_case2)

        self.upper_limit_image_label = QLabel()
        self.upper_limit_image_label.setAlignment(Qt.AlignCenter)
        self.upper_limit_image_label.setPixmap(self.get_pixmap(self.test_picture).scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))
        self.upper_limit_text_label = QLabel("Upper Limit")
        self.upper_limit_text_label.setAlignment(Qt.AlignCenter)
        self.lower_limit_image_label = QLabel()
        self.lower_limit_image_label.setAlignment(Qt.AlignCenter)
        self.lower_limit_image_label.setPixmap(self.get_pixmap(self.test_picture).scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))
        self.lower_limit_text_label = QLabel("Lower Limit")
        self.lower_limit_text_label.setAlignment(Qt.AlignCenter)

        self.layout_show_case1.addWidget(self.upper_limit_image_label)
        self.layout_show_case1.addWidget(self.lower_limit_image_label)
        self.layout_show_case2.addWidget(self.upper_limit_text_label)
        self.layout_show_case2.addWidget(self.lower_limit_text_label)

    def uslider_crop_changed(self, value):
        self.lslider_crop_changed(self.lower_limit_slider.value())
        cv_image = random_crop(self.test_picture, value/100)
        self.upper_limit_image_label.setPixmap(self.get_pixmap(cv_image).scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))

    def lslider_crop_changed(self, value):
        value = np.round(value * self.upper_limit_slider.value()/100, 1)
        self.value_label.setText("upper limit: {}% / lower limit: {}%".format(self.upper_limit_slider.value(), value))
        cv_image = random_crop(self.test_picture, value/100)
        self.lower_limit_image_label.setPixmap(self.get_pixmap(cv_image).scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))

    def draw_rotate_menu(self):
        # adding control widget's buttons
        self.title_label = QLabel("<h2>Random Rotation:</h2>")
        self.value_label = QLabel(u"clockwise: {}\N{DEGREE SIGN} | counter clockwise: {}\N{DEGREE SIGN}".format(0, 0))
        self.clockwise_limit_slider = QSlider()
        self.cclockwise_limit_slider = QSlider()
        self.clockwise_limit_slider.setMaximum(45)
        self.clockwise_limit_slider.setMinimum(0)
        self.cclockwise_limit_slider.setMaximum(45)
        self.cclockwise_limit_slider.setMinimum(0)
        self.clockwise_limit_slider.setValue(0)
        self.cclockwise_limit_slider.setValue(0)
        self.sliders_layout = QHBoxLayout()
        self.sliders_layout.addWidget(self.clockwise_limit_slider)
        self.sliders_layout.addWidget(self.cclockwise_limit_slider)
        self.control_widget_container_layout.addWidget(self.title_label)
        self.control_widget_container_layout.addWidget(self.value_label)
        self.control_widget_container_layout.addLayout(self.sliders_layout)

        self.clockwise_limit_slider.valueChanged.connect(self.clockwise_slider_changed)
        self.cclockwise_limit_slider.valueChanged.connect(self.cclockwise_slider_changed)

        # show case pictures
        self.widget_case1 = QWidget()
        self.widget_case2 = QWidget()
        self.layout_show_case1 = QHBoxLayout(self.widget_case1)
        self.layout_show_case2 = QHBoxLayout(self.widget_case2)
        self.pictures_widget_container_layout.addWidget(self.widget_case1)
        self.pictures_widget_container_layout.addWidget(self.widget_case2)

        self.clockwise_image_label = QLabel()
        self.clockwise_image_label.setAlignment(Qt.AlignCenter)
        self.clockwise_image_label.setPixmap(self.get_pixmap(self.test_picture).scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))
        self.clockwise_text_label = QLabel("Clockwise")
        self.clockwise_text_label.setAlignment(Qt.AlignCenter)
        self.cclockwise_image_label = QLabel()
        self.cclockwise_image_label.setAlignment(Qt.AlignCenter)
        self.cclockwise_image_label.setPixmap(self.get_pixmap(self.test_picture).scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))
        self.cclockwise_text_label = QLabel("Counter Clockwise")
        self.cclockwise_text_label.setAlignment(Qt.AlignCenter)

        self.layout_show_case1.addWidget(self.clockwise_image_label)
        self.layout_show_case1.addWidget(self.cclockwise_image_label)
        self.layout_show_case2.addWidget(self.clockwise_text_label)
        self.layout_show_case2.addWidget(self.cclockwise_text_label)

    def clockwise_slider_changed(self, value):
        cv_image = imutils.rotate(self.test_picture, -value)
        self.clockwise_image_label.setPixmap(self.get_pixmap(cv_image).scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))
        self.value_label.setText(u"clockwise: {}\N{DEGREE SIGN} | counter clockwise: {}\N{DEGREE SIGN}".format(value, self.cclockwise_limit_slider.value()))

    def cclockwise_slider_changed(self, value):
        cv_image = imutils.rotate(self.test_picture, value)
        self.cclockwise_image_label.setPixmap(self.get_pixmap(cv_image).scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))
        self.value_label.setText(u"clockwise: {}\N{DEGREE SIGN} | counter clockwise: {}\N{DEGREE SIGN}".format(self.clockwise_limit_slider.value(), value))

    def draw_blur_menu(self):
        # adding control widget's buttons
        self.title_label = QLabel("<h2>Blur:</h2>")
        self.value_label = QLabel("kernel size: {}px \u00D7 {}px".format(0, 0))
        self.value_label.setAlignment(Qt.AlignCenter)
        self.blur_limit_slider = QSlider()
        self.blur_limit_slider.setMaximum(35)
        self.blur_limit_slider.setMinimum(0)
        self.blur_limit_slider.setValue(0)
        self.sliders_layout = QHBoxLayout()
        self.sliders_layout.addWidget(self.blur_limit_slider)
        self.control_widget_container_layout.addWidget(self.title_label)
        self.control_widget_container_layout.addWidget(self.value_label, alignment=Qt.AlignCenter)
        self.control_widget_container_layout.addLayout(self.sliders_layout)

        self.blur_limit_slider.valueChanged.connect(self.blur_slider_changed)

        # show case pictures
        self.widget_case1 = QWidget()
        self.widget_case2 = QWidget()
        self.layout_show_case1 = QHBoxLayout(self.widget_case1)
        self.layout_show_case2 = QHBoxLayout(self.widget_case2)
        self.pictures_widget_container_layout.addWidget(self.widget_case1)
        self.pictures_widget_container_layout.addWidget(self.widget_case2)

        self.blur_image_label = QLabel()
        self.blur_image_label.setAlignment(Qt.AlignCenter)
        self.blur_image_label.setPixmap(self.get_pixmap(self.test_picture).scaled(self.image_width, self.image_height, Qt.KeepAspectRatio))
        self.blur_text_label = QLabel("Blurred Picture")
        self.blur_text_label.setAlignment(Qt.AlignCenter)

        self.layout_show_case1.addWidget(self.blur_image_label)
        self.layout_show_case2.addWidget(self.blur_text_label)

    def blur_slider_changed(self, value):
        self.value_label.setText("kernel size: {}px \u00D7 {}px".format(value, value))
        if value == 0:
            self.blur_image_label.setPixmap(
                self.get_pixmap(self.test_picture).scaled(self.image_width, self.image_height, Qt.KeepAspectRatio))
            return
        kernel = (value, value)
        cv_image = cv2.blur(self.test_picture, kernel)
        self.blur_image_label.setPixmap(self.get_pixmap(cv_image).scaled(self.image_width, self.image_height, Qt.KeepAspectRatio))

    def draw_brightness_menu(self):
        # adding control widget's buttons
        self.title_label = QLabel("<h2>Brightness:</h2>")
        self.value_label = QLabel("brightness: {}% | darkness: {}%".format(0, 0))
        self.brightness_limit_slider = QSlider()
        self.brightness_limit_slider.setMaximum(99)
        self.brightness_limit_slider.setMinimum(0)
        self.brightness_limit_slider.setValue(0)
        self.darkness_limit_slider = QSlider()
        self.darkness_limit_slider.setMaximum(99)
        self.darkness_limit_slider.setMinimum(0)
        self.darkness_limit_slider.setValue(0)
        self.sliders_layout = QHBoxLayout()
        self.sliders_layout.addWidget(self.brightness_limit_slider)
        self.sliders_layout.addWidget(self.darkness_limit_slider)
        self.control_widget_container_layout.addWidget(self.title_label)
        self.control_widget_container_layout.addWidget(self.value_label)
        self.control_widget_container_layout.addLayout(self.sliders_layout)

        self.brightness_limit_slider.valueChanged.connect(self.brightness_slider_changed)
        self.darkness_limit_slider.valueChanged.connect(self.darkness_slider_changed)

        # show case pictures
        self.widget_case1 = QWidget()
        self.widget_case2 = QWidget()
        self.layout_show_case1 = QHBoxLayout(self.widget_case1)
        self.layout_show_case2 = QHBoxLayout(self.widget_case2)
        self.pictures_widget_container_layout.addWidget(self.widget_case1)
        self.pictures_widget_container_layout.addWidget(self.widget_case2)

        self.brightness_image_label = QLabel()
        self.brightness_image_label.setAlignment(Qt.AlignCenter)
        self.brightness_image_label.setPixmap(self.get_pixmap(self.test_picture).scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))
        self.brightness_text_label = QLabel("Bright Picture")
        self.brightness_text_label.setAlignment(Qt.AlignCenter)
        self.darkness_image_label = QLabel()
        self.darkness_image_label.setAlignment(Qt.AlignCenter)
        self.darkness_image_label.setPixmap(self.get_pixmap(self.test_picture).scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))
        self.darkness_text_label = QLabel("Dark Picture")
        self.darkness_text_label.setAlignment(Qt.AlignCenter)

        self.layout_show_case1.addWidget(self.brightness_image_label)
        self.layout_show_case2.addWidget(self.brightness_text_label)
        self.layout_show_case1.addWidget(self.darkness_image_label)
        self.layout_show_case2.addWidget(self.darkness_text_label)

    def brightness_slider_changed(self, value):
        self.value_label.setText("brightness: {}% | darkness: {}%".format(value, self.darkness_limit_slider.value()))
        hsv = cv2.cvtColor(self.test_picture, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        value = int(128 * value / 100)
        v = np.where((255 - v) < value, 255, v + value)
        cv_image = cv2.merge((h,s,v))
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_HSV2BGR)
        self.brightness_image_label.setPixmap(self.get_pixmap(cv_image).scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))

    def darkness_slider_changed(self, value):
        self.value_label.setText("brightness: {}% | darkness: {}%".format(self.brightness_limit_slider.value(), value))
        hsv = cv2.cvtColor(self.test_picture, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        value = int(128 * value / 100)
        v = np.where(v < value, 0, v - value)
        cv_image = cv2.merge((h,s,v))
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_HSV2BGR)
        self.darkness_image_label.setPixmap(self.get_pixmap(cv_image).scaled(self.image_width//2, self.image_height, Qt.KeepAspectRatio))

    def exit_cancel_pressed(self):
        self.close()

    def back_cancel_pressed(self):
        self.draw_menu()

    def apply_pressed(self):
        if self.process_type == "grayscale":
            if not self.check_box_grayscale.checkState():
                self.show_error()
                return
            return_list = ["grayscale", "Grayscale"]
            self.accept.emit(return_list)
            self.close()
            return
        elif self.process_type == "resize":
            if not self.resize_width or not self.resize_height:
                self.show_error()
                return
            if self.resize_combobox.currentText() == "Stretch":
                return_list = ["resize", self.resize_width, self.resize_height,
                               0, "Stretch Resize: {}px \u00D7 {}px".format(self.resize_width, self.resize_height)]
            else:
                return_list = ["resize", self.resize_width, self.resize_height,
                               1, "Resize & Crop: {}px \u00D7 {}px".format(self.resize_width, self.resize_height)]
            self.accept.emit(return_list)
            self.close()
            return
        elif self.process_type == "flip":
            if not self.check_box_fliph.checkState() and not self.check_box_flipv.checkState():
                self.show_error()
                return
            if self.check_box_flipv.checkState() and self.check_box_fliph.checkState():
                message = "Flip: Horizontal & Vertical"
            elif self.check_box_flipv.checkState():
                message = "Flip: Vertical"
            elif self.check_box_fliph.checkState():
                message = "Flip: Horizontal"
            return_list = ["flip", bool(self.check_box_fliph.checkState()),
                           bool(self.check_box_flipv.checkState()), message]
            self.accept.emit(return_list)
            self.close()
            return
        elif self.process_type == "90 degree rotate":
            checkbox_list = [self.check_box_c, self.check_box_cc, self.check_box_ud]
            if not any([b.checkState() for b in checkbox_list]):
                self.show_error()
                return
            message = ", ".join([s.text() for s in checkbox_list if s.checkState()])
            bool_list = [bool(b.checkState()) for b in checkbox_list]
            return_list = ["90 degree rotate"] + bool_list + [u"90\N{DEGREE SIGN} rotate: " + message]
            self.accept.emit(return_list)
            self.close()
            return
        elif self.process_type == "random crop":
            if not self.upper_limit_slider.value():
                self.show_error()
                return
            upper_limit = self.upper_limit_slider.value()
            lower_limit = np.round(self.lower_limit_slider.value()*upper_limit/100, 1)
            return_list = ["random crop", upper_limit, lower_limit,
                           "Random Crop: {}% upper & {}% lower".format(upper_limit, lower_limit)]
            self.accept.emit(return_list)
            self.close()
            return
        elif self.process_type == "random rotation":
            if not self.clockwise_limit_slider.value() and not self.cclockwise_limit_slider.value():
                self.show_error()
                return
            clockwise = self.clockwise_limit_slider.value()
            cclockwise = self.cclockwise_limit_slider.value()
            if clockwise and cclockwise:
                message = u"Random Rotation: {}\N{DEGREE SIGN} clock & {}\N{DEGREE SIGN} counter".format(clockwise,
                                                                                                    cclockwise)
            elif clockwise:
                message = u"Random Rotation: {}\N{DEGREE SIGN} clockwise".format(clockwise)
            elif cclockwise:
                message = u"Random Rotation: {}\N{DEGREE SIGN} counter clockwise".format(cclockwise)
            return_list = ["random rotation", clockwise, cclockwise, message]
            self.accept.emit(return_list)
            self.close()
            return
        elif self.process_type == "blur":
            if not self.blur_limit_slider.value():
                self.show_error()
                return
            return_list = ["blur", self.blur_limit_slider.value(), "Blur: {}px".format(self.blur_limit_slider.value())]
            self.accept.emit(return_list)
            self.close()
            return
        elif self.process_type == "brightness":
            bright_val = self.brightness_limit_slider.value()
            dark_val = self.darkness_limit_slider.value()
            if not bright_val and not dark_val:
                self.show_error()
                return
            return_list = ["brightness", bright_val, dark_val,
                           "Brightness: {}%, Darkness: {}%".format(bright_val, dark_val)]
            self.accept.emit(return_list)
            self.close()
            return

    def show_error(self):
        error_box = QMessageBox()
        error_box.critical(None, "Error", "Invalid Inputs!")

    def get_pixmap(self, cv_image):
        frame = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
        return QPixmap.fromImage(image)

    def closeEvent(self, ev):
        self.closed.emit()


class CustomLabel(QWidget):
    clicked = pyqtSignal(str)
    def __init__(self, cv_image, process_type):
        super(CustomLabel, self).__init__()
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.setFixedSize(120,130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.process_type = process_type

        # picture label
        self.get_pix_map(cv_image, process_type)
        self.image_label = QLabel()
        self.image_label.setPixmap(self.pix_map)
        self.image_label.setAlignment(Qt.AlignCenter)

        # text label
        self.text_label = QLabel(process_type.title())
        self.text_label.setAlignment(Qt.AlignCenter)

        # adding text label and picture label to main widget
        self.main_layout.addWidget(self.image_label)
        self.main_layout.addWidget(self.text_label)

    def get_pix_map(self, cv_image, process_type):
        if process_type == "flip":
            cv_image = cv2.flip(cv_image, 0)
        elif process_type == "90 degree rotate":
            cv_image = cv2.rotate(cv_image, cv2.ROTATE_90_CLOCKWISE)
        elif process_type == "random crop":
            cv_image = random_crop(cv_image, 0.3)
        elif process_type == "random rotation":
            cv_image = imutils.rotate(cv_image, 45)
        elif process_type == "blur":
            cv_image = cv2.blur(cv_image, (30, 30))
        elif process_type == "brightness":
            hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
            h,s,v = cv2.split(hsv)
            lim = 255 - 130
            v[v > lim] = 255
            v[v <= lim] += 50
            final_hsv = cv2.merge((h,s,v))
            cv_image = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
        frame = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        self.image = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
        if process_type == "grayscale":
            self.image = self.image.convertToFormat(QImage.Format.Format_Grayscale8)
        self.pix_map = QPixmap.fromImage(self.image).scaled(100, 110, Qt.AspectRatioMode.KeepAspectRatio)

    def enterEvent(self, ev):
        self.pix_map = self.pix_map.scaled(130, 140, Qt.AspectRatioMode.KeepAspectRatio)
        self.image_label.setPixmap(self.pix_map)

    def leaveEvent(self, ev):
        self.pix_map = self.pix_map.scaled(100, 110, Qt.AspectRatioMode.KeepAspectRatio)
        self.image_label.setPixmap(self.pix_map)

    def mousePressEvent(self, ev):
        self.clicked.emit(self.process_type)

    def keyPressEvent(self, ev):
        pass


class GridLayout(QVBoxLayout):
    def __init__(self, n_rows, n_columns, *args, **kwargs):
        super(GridLayout, self).__init__(*args, **kwargs)
        self.n_rows = n_rows
        self.n_columns = n_columns
        self.horizontal_layouts = {}
        for i in range(n_rows):
            horizontal_layout = QHBoxLayout()
            horizontal_layout.addStretch()
            horizontal_layout.addStretch()
            self.horizontal_layouts[horizontal_layout] = 0
            self.addLayout(horizontal_layout)
        self.addStretch()

    def add_widget(self, widget):
        for horizontal_layout, index in self.horizontal_layouts.items():
            if index < self.n_columns:
                horizontal_layout.insertWidget(index+1, widget)
                self.horizontal_layouts[horizontal_layout] += 1
                return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_picture = cv2.imread("lena_copy.png")
    main = GridDialog(test_picture, 1)
    main.show()

    sys.exit(app.exec())