from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
from augmentation_dialog import GridDialog
import cv2

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        ######
        # change this for main programm
        self.test_picture = cv2.imread("lena_copy.png")
        self.preprocessing_list = []
        self.augmentation_list = []
        self.preprocessing_deleted_list = []
        self.augmentation_deleted_list = []
        ######
        self.setMinimumSize(900, 600)
        self.main_widget_layout = QVBoxLayout()
        self.setLayout(self.main_widget_layout)

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

        # bottom frame
        self.bottom_widget = QWidget()
        self.bottom_widget.setFixedHeight(50)
        self.bottom_widget.setStyleSheet(
            ""
        )
        self.bottom_widget_layout = QHBoxLayout()
        self.bottom_widget.setLayout(self.bottom_widget_layout)
        # adding buttons to bottom_widget
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_pressed)
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.back_pressed)
        self.bottom_widget_layout.addWidget(self.back_button)
        self.bottom_widget_layout.addWidget(self.next_button)
        self.bottom_widget_layout.insertStretch(1)

        # add widgets to main_widget
        self.container_widget_layout = QHBoxLayout()
        self.container_widget = QWidget()
        self.container_widget.setLayout(self.container_widget_layout)
        self.container_widget_layout.addWidget(self.left_frame)
        self.container_widget_layout.addWidget(self.right_frame)
        self.main_widget_layout.addWidget(self.container_widget)
        self.main_widget_layout.addWidget(self.bottom_widget)

    def add_preprocessing(self):
        self.select_dialog = GridDialog(self.test_picture, 0, deleted_processes=self.preprocessing_deleted_list)
        self.select_dialog.accept.connect(self.add_preprocessing_widget)
        self.select_dialog.closed.connect(lambda: self.setEnabled(True))
        self.setEnabled(False)
        self.select_dialog.show()

    def add_preprocessing_widget(self, details_list):
        self.setEnabled(True)
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

    def add_augmentation_widget(self, details_list):
        self.setEnabled(True)
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

    def next_pressed(self):
        print("next")

    def back_pressed(self):
        print("back")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main = MainWindow()
    main.show()

    sys.exit(app.exec())
