from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import sys
import signal
import os
import logging
from pathlib import Path

from .ui.main_window import MainWindow


def main() -> None:
    log_path = Path.home() / ".sshmanager" / "sshmanager.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    print("Name (email)")

    # Ensure any Bitwarden CLI environment from the launching shell does not
    # leak into the application or embedded terminals.
    os.environ.pop("BW_SESSION", None)
    os.environ.pop("BITWARDENCLI_APPDATA_DIR", None)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception
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
