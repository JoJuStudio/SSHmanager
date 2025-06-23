from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt


class LoadingDialog(QDialog):
    """Simple modal dialog showing a spinner while a task runs."""

    def __init__(self, text: str = "Please wait...", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(text)
        self.setModal(True)
        layout = QVBoxLayout(self)
        self.spinner_label = QLabel(self)
        self.spinner_label.setAlignment(Qt.AlignCenter)
        movie = QMovie(":/qt-project.org/styles/commonstyle/images/working-32.gif")
        self.spinner_label.setMovie(movie)
        movie.start()
        layout.addWidget(self.spinner_label)
        text_label = QLabel(text, self)
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)
        self.setFixedSize(150, 100)

