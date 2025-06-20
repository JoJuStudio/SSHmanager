from PyQt5.QtWidgets import QApplication
import sys
import signal

from .ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, lambda *args: app.quit())
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
