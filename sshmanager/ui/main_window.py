from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow,
    QTreeWidget,
    QTreeWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QSplitter,
    QPlainTextEdit,
    QPushButton,
    QToolBar,
    QDialog,
    QLabel,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QMenu,
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QAction

from ..models import Connection, Config
from ..config import load_config, save_config


class ConnectionDialog(QDialog):
    def __init__(self, parent=None, connection: Connection | None = None):
        super().__init__(parent)
        self.conn = None
        self._orig = connection

        if connection is None:
            self.setWindowTitle("Add SSH Connection")
        else:
            self.setWindowTitle("Edit SSH Connection")


        layout = QFormLayout(self)
        self.label_edit = QLineEdit(self)
        self.host_edit = QLineEdit(self)
        self.user_edit = QLineEdit(self)
        self.port_edit = QLineEdit(self)
        self.port_edit.setText("22")

        if connection is not None:
            self.label_edit.setText(connection.label)
            self.host_edit.setText(connection.host)
            self.user_edit.setText(connection.username)
            self.port_edit.setText(str(connection.port))

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
            folder=self._orig.folder if self._orig else "Default",
            key_path=self._orig.key_path if self._orig else None,
            initial_cmd=self._orig.initial_cmd if self._orig else None,
        )
        super().accept()


class TerminalTab(QWidget):
    """Embeds KDE Konsole for an SSH connection using KParts."""

    def __init__(self, connection: Connection, parent=None) -> None:
        super().__init__(parent)
        self._conn = connection

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        from ..util.konsole_embed import create_konsole_widget

        self.container = create_konsole_widget(
            user=connection.username,
            host=connection.host,
            port=connection.port,
            key=connection.key_path,
            initial_cmd=connection.initial_cmd,
            parent=self,
        )

        if self.container is None:
            self.container = QLabel("Failed to load Konsole", self)

        layout.addWidget(self.container)

    def closeEvent(self, event) -> None:
        super().closeEvent(event)


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
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

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

    def show_context_menu(self, pos: QPoint) -> None:
        item = self.tree.itemAt(pos)
        if item is None:
            return
        conn = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        if isinstance(conn, Connection):
            open_act = QAction("Open", self)
            open_act.triggered.connect(lambda: self.open_connection(item))
            menu.addAction(open_act)

            edit_act = QAction("Edit", self)
            edit_act.triggered.connect(lambda: self.edit_connection(item, conn))
            menu.addAction(edit_act)

            del_act = QAction("Delete", self)
            del_act.triggered.connect(lambda: self.delete_connection(item, conn))
            menu.addAction(del_act)
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def edit_connection(self, item: QTreeWidgetItem, conn: Connection) -> None:
        dlg = ConnectionDialog(self, conn)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.conn:
            index = self.config.connections.index(conn)
            self.config.connections[index] = dlg.conn
            save_config(self.config)
            self.load_connections()

    def delete_connection(self, item: QTreeWidgetItem, conn: Connection) -> None:
        if conn in self.config.connections:
            self.config.connections.remove(conn)
            save_config(self.config)
            self.load_connections()
