from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import sys
import signal
import os

from .ui.main_window import MainWindow


def main() -> None:
    args = sys.argv[:]
    if "--debug" in args:
        os.environ.setdefault("QT_DEBUG_PLUGINS", "1")
        args.remove("--debug")
        print("Debugging enabled (QT_DEBUG_PLUGINS=1)")

    if not os.environ.get("DISPLAY"):
        print("Warning: DISPLAY environment variable is not set. Qt may fail to start.")

    app = QApplication(args)
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
