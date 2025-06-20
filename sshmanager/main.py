from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import sys
import signal

from .ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, lambda *args: app.quit())
    # Periodic no-op timer keeps the Qt event loop responsive to SIGINT
    timer = QTimer()
    timer.start(100)
    timer.timeout.connect(lambda: None)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
