from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow, QTreeWidget, QTreeWidgetItem, QTabWidget,
    QVBoxLayout, QWidget, QSplitter, QPlainTextEdit, QPushButton, QToolBar,
    QDialog, QLabel, QFormLayout, QLineEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QProcess

from ..models import Connection, Config
from ..config import load_config, save_config


class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add SSH Connection")
        self.conn = None

        layout = QFormLayout(self)
        self.label_edit = QLineEdit(self)
        self.host_edit = QLineEdit(self)
        self.user_edit = QLineEdit(self)
        self.port_edit = QLineEdit(self)
        self.port_edit.setText("22")

        layout.addRow("Label", self.label_edit)
        layout.addRow("Host", self.host_edit)
        layout.addRow("Username", self.user_edit)
        layout.addRow("Port", self.port_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def accept(self):
        try:
            port = int(self.port_edit.text())
        except ValueError:
            port = 22
        self.conn = Connection(
            label=self.label_edit.text(),
            host=self.host_edit.text(),
            username=self.user_edit.text(),
            port=port,
        )
        super().accept()


class TerminalTab(QWidget):
    """Simple SSH terminal using ``QProcess``."""

    def __init__(self, connection: Connection, parent=None) -> None:
        super().__init__(parent)
        self._conn = connection

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        self.output = QPlainTextEdit(self)
        self.output.setReadOnly(True)
        self.input = QLineEdit(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.output)
        layout.addWidget(self.input)

        self.process.readyReadStandardOutput.connect(self._handle_output)
        self.process.readyReadStandardError.connect(self._handle_output)
        self.input.returnPressed.connect(self._send_input)

        cmd = [
            "ssh",
            f"{connection.username}@{connection.host}",
            "-p",
            str(connection.port),
        ]
        if connection.key_path:
            cmd.extend(["-i", connection.key_path])
        self.process.start(cmd[0], cmd[1:])

    def _handle_output(self) -> None:
        data = bytes(self.process.readAll()).decode(errors="ignore")
        self.output.moveCursor(self.output.textCursor().MoveOperation.End)
        self.output.insertPlainText(data)
        self.output.moveCursor(self.output.textCursor().MoveOperation.End)

    def _send_input(self) -> None:
        text = self.input.text() + "\n"
        self.process.write(text.encode())
        self.input.clear()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SSH Manager")
        self.config: Config = load_config()

        self.splitter = QSplitter(self)
        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tab_widget = QTabWidget(self)

        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.tab_widget)
        self.splitter.setStretchFactor(1, 1)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.splitter)
        self.setCentralWidget(container)

        toolbar = QToolBar("Main", self)
        self.addToolBar(toolbar)
        add_btn = QPushButton("Add SSH", self)
        toolbar.addWidget(add_btn)
        add_btn.clicked.connect(self.add_connection)

        self.load_connections()
        self.tree.itemDoubleClicked.connect(self.open_connection)

    def load_connections(self):
        self.tree.clear()
        folders = {}
        for conn in self.config.connections:
            folder_item = folders.get(conn.folder)
            if folder_item is None:
                folder_item = QTreeWidgetItem(self.tree, [conn.folder])
                folders[conn.folder] = folder_item
            item = QTreeWidgetItem(folder_item, [conn.label])
            item.setData(0, Qt.ItemDataRole.UserRole, conn)
        self.tree.expandAll()

    def add_connection(self):
        dlg = ConnectionDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.conn:
            self.config.connections.append(dlg.conn)
            save_config(self.config)
            self.load_connections()

    def open_connection(self, item: QTreeWidgetItem):
        conn = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(conn, Connection):
            tab = TerminalTab(conn, self)
            self.tab_widget.addTab(tab, conn.label)
            self.tab_widget.setCurrentWidget(tab)
