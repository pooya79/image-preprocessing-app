from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

image_file_formats = tuple('.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats())

class DrageAndDropFrame(QFrame):
    files_drag = pyqtSignal(list)
    def __init__(self, *args, **kwargs):
        super(DrageAndDropFrame, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, ev: QDragEnterEvent) -> None:
        if ev.mimeData().hasUrls():
            ev.acceptProposedAction()

    def dropEvent(self, ev: QDropEvent) -> None:
        file_list = []
        for url in ev.mimeData().urls():
            filename = url.fileName()
            if filename.endswith(image_file_formats):
                file_address = url.toLocalFile()
                file_list.append([filename, file_address])
        self.files_drag.emit(file_list)


