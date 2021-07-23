from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np
import sys
import os
import cv2
import imutils
from libs.drag_and_drop_frame import DrageAndDropFrame, image_file_formats
from simple_labeling_GUI import LabelingApp
from libs.augmentation_dialog import GridDialog, random_crop


class MainMenu(QWidget):
    def __init__(self, *args, **kwargs):
        super(MainMenu, self).__init__(*args, **kwargs)
        self.main_layout = QGridLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(900, 600)
        self.image_list = []
        self.images_dictionary = {}
        self.preprocessing_list = []
        self.augmentation_list = []
        self.preprocessing_deleted_list = []
        self.augmentation_deleted_list = []
        self.save_location = ""
        self.test_picture = cv2.imread("lena_copy.png") # cv2 image

        self.project_labels = []
        self.first_page()

    # first page function
    def first_page(self):
        # clear window
        for i in reversed(range(self.main_layout.count())):
            self.main_layout.itemAt(i).widget().setParent(None)

        # upper widgets
        upper_frame = QFrame()
        upper_frame.setFrameShape(QFrame.Shape.Box)
        upper_frame.setFrameShadow(QFrame.Shadow.Plain)
        upper_frame_layout = QVBoxLayout(upper_frame)
        self.project_name_label = QLabel("<h3>Project Name:</h3>")
        self.project_name_edit_line = QLineEdit()
        self.project_name_edit_line.editingFinished.connect(self.update_next_button)
        self.project_type_label = QLabel("<h3>Project Type:</h3>")
        self.project_type_combobox = QComboBox()
        self.project_type_combobox.addItem("Classification")
        self.project_type_combobox.addItem("Object Detection (under development)")
        self.project_type_combobox.currentTextChanged.connect(self.update_next_button)
        self.labels_label = QLabel("<h3>Labels: (cat, dog, ...)</h3>")
        self.labels_edit = QLineEdit("")
        self.labels_edit.editingFinished.connect(self.update_next_button)

        upper_frame_layout.addStretch()
        upper_frame_layout.addStretch()
        upper_frame_layout.addWidget(self.project_name_label)
        upper_frame_layout.addWidget(self.project_name_edit_line)
        upper_frame_layout.addStretch()
        upper_frame_layout.addWidget(self.project_type_label)
        upper_frame_layout.addWidget(self.project_type_combobox)
        upper_frame_layout.addStretch()
        upper_frame_layout.addWidget(self.labels_label)
        upper_frame_layout.addWidget(self.labels_edit)
        upper_frame_layout.addStretch()
        upper_frame_layout.addStretch()

        upper_frame.setStyleSheet(
            "QFrame {background: #ffffff;}"
        )

        # buttons widget
        self.get_buttons_widget(next_callback=self.second_page)
        self.next_button.setEnabled(False)

        self.main_layout.addWidget(upper_frame,0,1,1,3)
        self.main_layout.addWidget(self.buttons_widget,1,0,1,5)

    # first page helper functions
    def update_next_button(self):
        self.project_name = self.project_name_edit_line.text().strip()
        self.project_type = self.project_type_combobox.currentText()
        self.project_labels = [label.strip().lower() for label in self.labels_edit.text().split(",") if label.strip()]
        if bool(self.project_name) and self.project_type[:6] == "Classi" and bool(self.project_labels):
            self.next_button.setEnabled(True)
        else:
            self.next_button.setEnabled(False)

    # second page function
    def second_page(self):
        # clear window
        for i in reversed(range(self.main_layout.count())):
            self.main_layout.itemAt(i).widget().setParent(None)

        # upper widgets
        upper_widgets_container = QWidget()
        upper_widgets_layout = QVBoxLayout(upper_widgets_container)

        # load file widgets
        self.drag_drop_frame = DrageAndDropFrame()
        self.drag_drop_frame.setFrameShape(QFrame.Shape.Box)
        self.drag_drop_frame.setFrameShadow(QFrame.Shadow.Plain)
        self.drag_drop_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.drag_drop_frame.setStyleSheet(
            "QFrame {background: #BBBBBB;}"
        )
        self.drag_and_drop_label = QLabel("<h1>Drag And Drop Files Here</h1>")
        self.drag_and_drop_label.setAlignment(Qt.AlignCenter)
        self.add_file_button = QPushButton("Add Files")
        self.add_file_button.setMinimumHeight(50)
        self.add_folder_button = QPushButton("Add Folder")
        self.add_folder_button.setMinimumHeight(50)
        self.drag_drop_frame_layout = QVBoxLayout(self.drag_drop_frame)
        self.drag_drop_buttons_layout = QHBoxLayout()
        self.drag_drop_frame_layout.addWidget(self.drag_and_drop_label)
        self.drag_drop_buttons_layout.addWidget(self.add_file_button)
        self.drag_drop_buttons_layout.addWidget(self.add_folder_button)
        self.drag_drop_frame_layout.addLayout(self.drag_drop_buttons_layout)

        self.drag_drop_frame.files_drag.connect(self.add_file_list)
        self.add_file_button.clicked.connect(self.add_file_clicked)
        self.add_folder_button.clicked.connect(self.add_folder_clicked)

        # show file widget
        self.file_list_label = QLabel("<h3>Images:</h3>")
        self.files_list = QListWidget()
        self.files_list.setCursor(Qt.PointingHandCursor)

        self.files_list.itemDoubleClicked.connect(self.show_image)

        upper_widgets_layout.addWidget(self.drag_drop_frame)
        upper_widgets_layout.addWidget(self.file_list_label)
        upper_widgets_layout.addWidget(self.files_list)

        # buttons widget
        self.get_buttons_widget(True, True, self.third_page, self.first_page)

        self.main_layout.addWidget(upper_widgets_container, 0, 0)
        self.main_layout.addWidget(self.buttons_widget, 1, 0)

        if self.image_list:
            for image in self.image_list:
                self.files_list.addItem(image[1])

    # second page helper functions
    def add_file_clicked(self):
        formats = ['*.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        filters = "Image files (%s)" % ' '.join(formats)
        files_address = QFileDialog.getOpenFileNames(self, "Add Image Files", QDir.homePath(), filters)

        file_list = []
        for file_address in files_address[0]:
            file_list.append([file_address.split("/")[-1], file_address])
        self.add_file_list(file_list)

    def add_folder_clicked(self):
        folder = QFileDialog.getExistingDirectory(self,
                                                    'Add Directory', QDir.homePath(),
                                                     QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if folder:
            file_list = []
            for file in os.listdir(folder):
                if file.endswith(image_file_formats):
                    file_list.append([file, folder + "/" + file])

            self.add_file_list(file_list)

    def add_file_list(self, file_list):
        for image in file_list:
            if image[1] not in [x[1] for x in self.image_list]:
                self.files_list.addItem(image[1])
                if os.path.dirname(image[1]).split("/")[-1].strip().lower() in self.project_labels:
                    image.append(os.path.dirname(image[1]).split("/")[-1].strip().lower())
                else:
                    image.append("")
                self.image_list.append(image)

    def show_image(self, item):
        img = cv2.imread(item.text())
        cv2.imshow(item.text(), img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # third page function
    def third_page(self):
        # clear window
        for i in reversed(range(self.main_layout.count())):
            self.main_layout.itemAt(i).widget().setParent(None)

        # upper frame
        upper_frame_container = QWidget()
        upper_frame_layout = QVBoxLayout(upper_frame_container)
        self.label_selection_combobox = QComboBox()
        self.label_selection_combobox.setFixedHeight(50)
        self.label_selection_combobox.addItem("All Images")
        for label in self.project_labels:
            self.label_selection_combobox.addItem(label)
        self.label_selection_combobox.addItem("No Label")
        self.label_selection_combobox.currentTextChanged.connect(self.label_selection_changed)

        self.files_list = QListWidget()
        self.files_list.setCursor(Qt.PointingHandCursor)

        for image in self.image_list:
            self.files_list.addItem(image[1])

        self.files_list.itemDoubleClicked.connect(self.show_image)

        labeling_button = QPushButton("Label Images")
        labeling_button.setFixedSize(200, 100)
        labeling_button.clicked.connect(self.label_images_app)

        upper_frame_layout.addWidget(self.label_selection_combobox)
        upper_frame_layout.addWidget(self.files_list)
        upper_frame_layout.addWidget(labeling_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.get_buttons_widget(True, False, self.fourth_page, self.second_page)

        self.main_layout.addWidget(upper_frame_container, 0, 0)
        self.main_layout.addWidget(self.buttons_widget, 1, 0)

        self.update_images_labels()

    def label_selection_changed(self):
        self.current_label = self.label_selection_combobox.currentText()
        self.files_list.clear()
        if self.current_label == "All Images":
            for key in self.images_dictionary:
                for image in self.images_dictionary[key]:
                    self.files_list.addItem(image[1])
        elif self.current_label == "No Label":
            for image in self.images_dictionary["No Label"]:
                self.files_list.addItem(image[1])
        elif self.current_label:
            print(self.current_label)
            for image in self.images_dictionary[self.current_label]:
                self.files_list.addItem(image[1])

    def update_images_labels(self):
        for label in self.project_labels:
            self.images_dictionary[label] = []
        self.images_dictionary["No Label"] = []
        for image in self.image_list:
            if image[2] in self.images_dictionary.keys():
                self.images_dictionary[image[2]].append(image)
            else:
                self.images_dictionary["No Label"].append(image)

    def label_images_app(self):
        label = self.label_selection_combobox.currentText()
        if label == "No Label" and not bool(self.images_dictionary["No Label"]):
            return
        elif label != "All Images" and not bool(self.images_dictionary[label]):
            return
        if label == "All Images":
            all_images = []
            for key in self.images_dictionary.keys():
                all_images += self.images_dictionary[key]
            self.image_labeling_GUI = LabelingApp(all_images, self.project_labels)
        elif label == "No Label":
            self.image_labeling_GUI = LabelingApp(self.images_dictionary["No Label"], self.project_labels)
        else:
            self.image_labeling_GUI = LabelingApp(self.images_dictionary[label], self.project_labels)
        self.setEnabled(False)
        self.image_labeling_GUI.show()
        self.image_labeling_GUI.pageClosedWithYes.connect(self.update_widgets_after_labeling)

    def update_widgets_after_labeling(self, make_changes=False, image_list=[], project_labels=[]):
        self.setEnabled(True)
        print(project_labels)
        if make_changes:
            current_combobox_label = self.label_selection_combobox.currentText()
            self.label_selection_combobox.clear()
            self.label_selection_combobox.addItem("All Images")
            temp_dictionary = {}
            for label in project_labels:
                temp_dictionary[label] = []
                self.label_selection_combobox.addItem(label)
            self.label_selection_combobox.addItem("No Label")
            temp_dictionary["No Label"] = []
            if current_combobox_label == "All Images":
                for image in image_list:
                    if image[2] not in project_labels:
                        image[2] = ""
                        temp_dictionary["No Label"].append(image)
                    else:
                        temp_dictionary[image[2]].append(image)
            elif current_combobox_label == "No Label":
                self.images_dictionary["No Label"] = image_list
                for key in self.images_dictionary:
                    for image in self.images_dictionary[key]:
                        if image[2] not in project_labels:
                            image[2] = ""
                            temp_dictionary["No Label"].append(image)
                        else:
                            temp_dictionary[image[2]].append(image)
            else:
                self.images_dictionary[current_combobox_label] = image_list
                for key in self.images_dictionary:
                    for image in self.images_dictionary[key]:
                        if image[2] not in project_labels:
                            image[2] = ""
                            temp_dictionary["No Label"].append(image)
                        else:
                            temp_dictionary[image[2]].append(image)

            self.project_labels = project_labels
            self.images_dictionary = temp_dictionary
            self.label_selection_combobox.setCurrentText("No Label")

    # fourth page function
    def fourth_page(self):
        # clear window
        for i in reversed(range(self.main_layout.count())):
            self.main_layout.itemAt(i).widget().setParent(None)

        if self.image_list:
            self.test_picture = cv2.imread(self.image_list[0][1])

        # left frame
        self.left_frame = QFrame()
        self.left_frame.setFrameShape(QFrame.Shape.Box)
        self.left_frame.setFrameShadow(QFrame.Shadow.Sunken)
        self.left_frame.setStyleSheet(
            ""
        )
        self.left_frame_layout = QVBoxLayout()
        self.left_frame.setLayout(self.left_frame_layout)
        # adding buttons
        self.preprocess_add_button = QPushButton("Add Preprocessing")
        self.preprocess_add_button.setFixedHeight(50)
        self.preprocess_add_button.clicked.connect(self.add_preprocessing)
        self.preprocessing_container_scroll = QScrollArea()
        self.preprocessing_container = QWidget()
        self.preprocessing_container_scroll.setWidget(self.preprocessing_container)
        self.preprocessing_container_scroll.setWidgetResizable(True)
        self.preprocessing_container_layout = QVBoxLayout()
        self.preprocessing_container_layout.addStretch()
        self.preprocessing_container.setLayout(self.preprocessing_container_layout)
        self.left_frame_layout.addWidget(self.preprocess_add_button)
        self.left_frame_layout.addWidget(self.preprocessing_container_scroll)

        # right frame
        self.right_frame = QFrame()
        self.right_frame.setMinimumWidth(200)
        self.right_frame.setFrameShape(QFrame.Shape.Box)
        self.right_frame.setFrameShadow(QFrame.Shadow.Sunken)
        self.right_frame.setStyleSheet(
            ""
        )
        self.right_frame_layout = QVBoxLayout()
        self.right_frame.setLayout(self.right_frame_layout)
        # adding buttons
        self.augmentation_add_button = QPushButton("Add Augmentation")
        self.augmentation_add_button.setFixedHeight(50)
        self.augmentation_add_button.clicked.connect(self.add_augmentation)
        self.augmentation_container_scroll = QScrollArea()
        self.augmentation_container = QWidget()
        self.augmentation_container_scroll.setWidget(self.augmentation_container)
        self.augmentation_container_scroll.setWidgetResizable(True)
        self.augmentation_container_layout = QVBoxLayout()
        self.augmentation_container_layout.addStretch()
        self.augmentation_container.setLayout(self.augmentation_container_layout)
        self.right_frame_layout.addWidget(self.augmentation_add_button)
        self.right_frame_layout.addWidget(self.augmentation_container_scroll)

        # buttons widget
        self.get_buttons_widget(True, True, self.sample_number_dialog, self.third_page)

        # add widgets to main_widget
        container_widget = QWidget()
        container_widget_layout = QHBoxLayout(container_widget)
        container_widget_layout.addWidget(self.left_frame)
        container_widget_layout.addWidget(self.right_frame)
        self.main_layout.addWidget(container_widget, 0, 0)
        self.main_layout.addWidget(self.buttons_widget, 1, 0)

        for preprocess in self.preprocessing_list:
            self.add_preprocessing_widget(preprocess, from_list=True)
        for augment in self.augmentation_list:
            self.add_augmentation_widget(augment, from_list=True)

    # fourth page helper functions
    def add_preprocessing(self):
        self.select_dialog = GridDialog(self.test_picture, 0, deleted_processes=self.preprocessing_deleted_list)
        self.select_dialog.accept.connect(self.add_preprocessing_widget)
        self.select_dialog.closed.connect(lambda: self.setEnabled(True))
        self.setEnabled(False)
        self.select_dialog.show()

    def add_preprocessing_widget(self, details_list, from_list=False):
        self.setEnabled(True)
        if not from_list:
            self.preprocessing_list.append(details_list)
            self.preprocessing_deleted_list.append(details_list[0])

        process_widget = QFrame()
        process_widget.setFixedHeight(50)
        process_widget.setFrameShape(QFrame.Shape.Box)
        process_widget.setFrameShadow(QFrame.Shadow.Plain)
        process_layout = QHBoxLayout(process_widget)
        process_description = QLabel(details_list[-1])
        process_edit_button = QPushButton("edit")
        process_delete_button = QPushButton("delete")
        process_layout.addWidget(process_description)
        process_layout.addWidget(process_edit_button)
        process_layout.addWidget(process_delete_button)
        self.preprocessing_container_layout.insertWidget(0, process_widget)

        process_edit_button.setFixedWidth(80)
        process_delete_button.setFixedWidth(80)

        process_delete_button.clicked.connect(lambda: self.delete_preprocessing(process_description))
        process_edit_button.clicked.connect(lambda: self.edit_preprocessing(process_description))

    def delete_preprocessing(self, process_description):
        description = process_description.text()
        for process in self.preprocessing_list:
            if description == process[-1]:
                self.preprocessing_list.remove(process)
                self.preprocessing_deleted_list.remove(process[0])
                break
        process_description.parent().setParent(None)

    def edit_preprocessing(self, process_description):
        description = process_description.text()
        for detail in self.preprocessing_list:
            if description == detail[-1]:
                process_type = detail[0]
                break
        self.edit_dialog = GridDialog(self.test_picture, 0, draw_case=process_type)
        self.edit_dialog.show()
        self.edit_dialog.accept.connect(
            lambda return_list: self.edit_preprocessing_helper(process_description, return_list))
        self.edit_dialog.closed.connect(lambda: self.setEnabled(True))
        self.setEnabled(False)

    def edit_preprocessing_helper(self, process_description, return_list):
        for i, detail in enumerate(self.preprocessing_list):
            if return_list[0] == detail[0]:
                self.preprocessing_list[i] = return_list
        process_description.setText(return_list[-1])

    def add_augmentation(self):
        self.select_dialog = GridDialog(self.test_picture, 1, deleted_processes=self.augmentation_deleted_list)
        self.select_dialog.accept.connect(self.add_augmentation_widget)
        self.select_dialog.closed.connect(lambda: self.setEnabled(True))
        self.setEnabled(False)
        self.select_dialog.show()

    def add_augmentation_widget(self, details_list, from_list=False):
        self.setEnabled(True)
        if not from_list:
            self.augmentation_list.append(details_list)
            self.augmentation_deleted_list.append(details_list[0])

        process_widget = QFrame()
        process_widget.setFixedHeight(50)
        process_widget.setFrameShape(QFrame.Shape.Box)
        process_widget.setFrameShadow(QFrame.Shadow.Plain)
        process_layout = QHBoxLayout(process_widget)
        process_description = QLabel(details_list[-1])
        process_edit_button = QPushButton("edit")
        process_delete_button = QPushButton("delete")
        process_layout.addWidget(process_description)
        process_layout.addWidget(process_edit_button)
        process_layout.addWidget(process_delete_button)
        self.augmentation_container_layout.insertWidget(0, process_widget)

        process_edit_button.setFixedWidth(80)
        process_delete_button.setFixedWidth(80)

        process_delete_button.clicked.connect(lambda: self.delete_augmentation(process_description))
        process_edit_button.clicked.connect(lambda: self.edit_augmentation(process_description))

    def delete_augmentation(self, process_description):
        description = process_description.text()
        for process in self.augmentation_list:
            if description == process[-1]:
                self.augmentation_list.remove(process)
                self.augmentation_deleted_list.remove(process[0])
                break
        process_description.parent().setParent(None)

    def edit_augmentation(self, process_description):
        description = process_description.text()
        for detail in self.augmentation_list:
            if description == detail[-1]:
                process_type = detail[0]
                break
        self.edit_dialog = GridDialog(self.test_picture, 1, draw_case=process_type)
        self.edit_dialog.show()
        self.edit_dialog.accept.connect(lambda return_list: self.edit_augmentation_helper(process_description, return_list))
        self.edit_dialog.closed.connect(lambda: self.setEnabled(True))
        self.setEnabled(False)

    def edit_augmentation_helper(self, process_description, return_list):
        for i, detail in enumerate(self.augmentation_list):
            if return_list[0] == detail[0]:
                self.augmentation_list[i] = return_list
        process_description.setText(return_list[-1])

    def sample_number_dialog(self):
        self.sampler_dialog = QDialog()
        self.sampler_dialog.setFixedSize(300,150)
        sampler_dialog_layout = QVBoxLayout(self.sampler_dialog)
        title = QLabel("<h2>      Number of Samples:</h2>")
        samples_combo = QComboBox()
        number_of_images = len(self.image_list)
        samples_combo.addItem("       \u00D7" + str(1) + " (" + str(0) + " augmented & "
                                + str(number_of_images) + " originals)")
        if self.augmentation_list:
            for i in range(1,9):
                samples_combo.addItem("       \u00D7" + str(i) + " (" + str(number_of_images*i) + " augmented & "
                                      + str(number_of_images) + " originals)")

        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("Ok")
        ok_button.clicked.connect(lambda: self.process_page(int(samples_combo.currentText().strip()[1])))
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.sampler_dialog.close)
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)

        sampler_dialog_layout.addWidget(title)
        sampler_dialog_layout.addWidget(samples_combo)
        sampler_dialog_layout.addLayout(buttons_layout)

        self.sampler_dialog.show()

    # process page
    def process_page(self, samples_multiplier=1):
        # clear window
        for i in reversed(range(self.main_layout.count())):
            self.main_layout.itemAt(i).widget().setParent(None)

        self.samples_number = samples_multiplier - 1
        self.sampler_dialog.close()

        save_address = QLabel("<h3>Save Directory:</h3>")
        save_address.setFixedHeight(30)
        self.save_directoery_container = QWidget()
        self.save_directoery_layout = QVBoxLayout(self.save_directoery_container)
        self.directory_selection_container = QWidget()
        directory_selection_layout = QHBoxLayout(self.directory_selection_container)
        self.save_directory_edit = QLineEdit()
        select_directory_button = QPushButton("Select dir")
        select_directory_button.setFixedSize(150, 40)
        self.save_directory_edit.setFixedHeight(30)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, len(self.image_list)+1)
        directory_selection_layout.addWidget(self.save_directory_edit)
        directory_selection_layout.addWidget(select_directory_button)
        self.save_directoery_layout.addWidget(save_address)
        self.save_directoery_layout.addWidget(self.directory_selection_container)
        self.save_directoery_layout.addStretch()
        self.save_directoery_layout.addWidget(self.progress_bar)
        self.save_directoery_layout.addStretch()

        select_directory_button.clicked.connect(self.select_save_location)
        self.save_directory_edit.editingFinished.connect(self.save_directory_edit_finished)

        self.get_buttons_widget(True, True, self.generate_images, self.close)
        self.next_button.setText("Generate Images")
        self.back_button.setText("Cancel")

        self.main_layout.addWidget(self.save_directoery_container, 0,0)
        self.main_layout.addWidget(self.buttons_widget, 1, 0)

    # process page helper functions
    def select_save_location(self):
        folder = QFileDialog.getExistingDirectory(self,
                                                    'Add Directory', QDir.homePath(),
                                                     QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)

        self.save_location = folder
        self.save_directory_edit.setText(folder)

    def save_directory_edit_finished(self):
        path = self.save_directory_edit.text()
        pathDir = QDir(path)
        if pathDir.exists():
            self.save_location = path
        else:
            self.save_directory_edit.setText(self.save_location)

    def generate_images(self):
        if not self.save_location or not os.path.exists(self.save_location):
            return
        if self.save_location[-1] != "/" or self.save_location != "\\":
            self.save_location += "/"
        self.save_location += self.project_name + "/"
        if not os.path.exists(self.save_location):
            os.mkdir(self.save_location)
        for label in self.project_labels + ["No Label"]:
            if not os.path.exists(self.save_location + label):
                os.mkdir(self.save_location + label)
        c = 1
        brihtness = True
        for key in self.images_dictionary.keys():
            for image in self.images_dictionary[key]:
                c += 1
                self.progress_bar.setValue(c)
                cv_original_image = cv2.imread(image[1])
                if cv_original_image is None:
                    continue
                if len(image) == 4:
                    cv_original_image = cv_original_image[int(image[-1][1]):int(image[-1][3])+1, int(image[-1][0]):int(image[-1][2]+1)]
                for preprocess in self.preprocessing_list:
                    if preprocess[0] == "grayscale":
                        cv_original_image = self.grayscale(cv_original_image)
                        brihtness = False
                    elif preprocess[0] == "resize":
                        cv_original_image = self.resize(cv_original_image, preprocess[1], preprocess[2], preprocess[3])
                name, fmt = tuple(image[0].split("."))
                if image[2]:
                    address = self.save_location + image[2] + "/" + name + "." +fmt
                    cv2.imwrite(address, cv_original_image)
                else:
                    address = self.save_location + "No Label" + "/" + name + "." +fmt
                    cv2.imwrite(address, cv_original_image)

                for i in range(self.samples_number):
                    img = np.copy(cv_original_image)
                    for process in self.augmentation_list:
                        if process[0] == "flip":
                            img = self.flip(img, process[1], process[2])
                        elif process[0] == "90 degree rotate":
                            img = self.degree90(img, process[1], process[2], process[3])
                        elif process[0] == "random crop":
                            img = self.random_crop(img, process[1], process[2])
                        elif process[0] == "random rotation":
                            img = self.random_rotation(img, process[1], process[2])
                        elif process[0] == "blur":
                            img = self.blur(img, process[1])
                        elif process[0] == "brightness" and brihtness:
                            img = self.brightness(img, process[1], process[2])
                    if image[2]:
                        address = self.save_location + image[2] + "/" + name + "({})".format(i+1) + "." +fmt
                        cv2.imwrite(address, img)
                    else:
                        address = self.save_location + "No Label" + "/" + name + "({})".format(i+1) + "." +fmt
                        cv2.imwrite(address, img)

        self.next_button.clicked.disconnect(self.generate_images)
        self.next_button.clicked.connect(self.fourth_page)
        self.next_button.setText("Again")

    # image preprocessing functions
    def grayscale(self, cv_image):
        return cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

    def resize(self, cv_image, width, height, type):
        return GridDialog.resize_image(cv_image, width, height, type)

    # image augmentation functinos
    def flip(self, cv_image, Horizontal=False, Vertical=True):
        if Horizontal and Vertical:
            random_number = np.random.randint(0, 2)
            return cv2.flip(cv_image, random_number)
        elif Horizontal:
            return cv2.flip(cv_image, 1)
        elif Vertical:
            return cv2.flip(cv_image, 0)

    def degree90(self, cv_image, clockwise=False, cclockwise=False, ud=False):
        clockwise_rotate = cv2.rotate(cv_image, cv2.ROTATE_90_CLOCKWISE)
        cclockwise_rotate = cv2.rotate(cv_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        ud_rotate = cv2.flip(cv2.flip(cv_image, 0), 1)

        sum = int(clockwise) + int(cclockwise) + int(ud)
        random_number = np.random.randint(0, sum)
        if sum == 1:
            if clockwise:
                return clockwise_rotate
            elif cclockwise:
                return cclockwise_rotate
            elif ud:
                return ud_rotate
        elif sum == 2:
            if clockwise and cclockwise:
                if random_number:
                    return clockwise_rotate
                else:
                    return cclockwise_rotate
            elif clockwise and ud:
                if random_number:
                    return clockwise_rotate
                else:
                    return ud_rotate
            elif cclockwise and ud:
                if random_number:
                    return cclockwise_rotate
                else:
                    return ud_rotate
        elif sum == 3:
            if random_number==0:
                return clockwise_rotate
            elif random_number==1:
                return cclockwise_rotate
            elif random_number==2:
                return ud_rotate

    def random_crop(self, cv_image, high_limit, low_limit):
        random_number = np.random.randint(int(low_limit), int(high_limit)+1)
        return cv2.resize(random_crop(cv_image, random_number/100), (cv_image.shape[1], cv_image.shape[0]))

    def random_rotation(self, cv_image, clockwise, cclockwise):
        random_number = np.random.randint(0,2)
        clockwise = -np.random.randint(0, clockwise+1)
        cclockwise = np.random.randint(0, cclockwise+1)

        if random_number:
            if clockwise:
                return imutils.rotate(cv_image, clockwise)
            else:
                return imutils.rotate(cv_image, cclockwise)
        else:
            if cclockwise:
                return imutils.rotate(cv_image, cclockwise)
            else:
                return imutils.rotate(cv_image, clockwise)

    def blur(self, cv_image, kernel_size):
        random_number = np.random.randint(0, kernel_size+1)
        if random_number:
            return cv2.blur(cv_image, (random_number, random_number))
        else:
            return cv_image

    def brightness(self, cv_image, brightness, darkness):
        random_number = np.random.randint(0, 2)
        brightness = np.random.randint(0, brightness + 1)
        darkness = np.random.randint(0, darkness + 1)
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        darkness = int(128 * darkness / 100)
        brightness = int(128 * brightness / 100)
        if random_number:
            if brightness:
                v = np.where((255 - v) < brightness, 255, v + brightness)
                return cv2.cvtColor(cv2.merge((h,s,v)), cv2.COLOR_HSV2BGR)
            else:
                v = np.where(v < darkness, 0, v - darkness)
                return cv2.cvtColor(cv2.merge((h,s,v)), cv2.COLOR_HSV2BGR)
        else:
            if darkness:
                v = np.where(v < darkness, 0, v - darkness)
                return cv2.cvtColor(cv2.merge((h,s,v)), cv2.COLOR_HSV2BGR)
            else:
                v = np.where((255 - v) < brightness, 255, v + brightness)
                return cv2.cvtColor(cv2.merge((h,s,v)), cv2.COLOR_HSV2BGR)

    # helper functions
    def get_buttons_widget(self, next=True, back=False, next_callback=None, back_callback=None):
        self.buttons_widget = QWidget()
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setLineWidth(1)
        self.buttons_widget.setFixedHeight(80)
        buttons_layout = QVBoxLayout(self.buttons_widget)
        buttons_layout_h = QHBoxLayout()
        buttons_layout.addWidget(line)
        buttons_layout.addLayout(buttons_layout_h)

        if back and back_callback:
            self.back_button = QPushButton("Back")
            self.back_button.clicked.connect(back_callback)
            buttons_layout_h.addWidget(self.back_button)
        buttons_layout_h.addStretch()
        if next and next_callback:
            self.next_button = QPushButton("Next")
            self.next_button.clicked.connect(next_callback)
            buttons_layout_h.addWidget(self.next_button)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main = MainMenu()
    main.show()

    sys.exit(app.exec_())