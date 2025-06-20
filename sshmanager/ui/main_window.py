from __future__ import annotations

import logging
from PyQt5.QtWidgets import (
    QMainWindow,
    QTreeWidget,
    QTreeWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QSplitter,
    QPushButton,
    QToolBar,
    QDialog,
    QLabel,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QMenu,
    QShortcut,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction

from ..models import Connection, Config
from ..config import load_config, save_config
from ..bitwarden import fetch_credentials, is_available as bw_available


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
        self.folder_edit = QLineEdit(self)
        self.key_edit = QLineEdit(self)
        self.cmd_edit = QLineEdit(self)
        self.bw_item_edit = QLineEdit(self)
        self.fetch_btn = QPushButton("Fetch", self)
        self.fetch_btn.clicked.connect(self.fetch_from_bitwarden)
        if not bw_available():
            self.fetch_btn.setEnabled(False)

        if connection is not None:
            self.label_edit.setText(connection.label)
            self.host_edit.setText(connection.host)
            self.user_edit.setText(connection.username)
            self.port_edit.setText(str(connection.port))
            self.folder_edit.setText(connection.folder)
            if connection.key_path:
                self.key_edit.setText(connection.key_path)
            if connection.initial_cmd:
                self.cmd_edit.setText(connection.initial_cmd)

        layout.addRow("Label", self.label_edit)
        layout.addRow("Host", self.host_edit)
        layout.addRow("Username", self.user_edit)
        layout.addRow("Port", self.port_edit)
        layout.addRow("Folder", self.folder_edit)
        layout.addRow("SSH Key", self.key_edit)
        layout.addRow("Initial Cmd", self.cmd_edit)
        bw_layout = QHBoxLayout()
        bw_layout.addWidget(self.bw_item_edit)
        bw_layout.addWidget(self.fetch_btn)
        layout.addRow("Bitwarden Item", bw_layout)

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
            folder=self.folder_edit.text() or "Default",
            key_path=self.key_edit.text() or None,
            initial_cmd=self.cmd_edit.text() or None,
        )
        super().accept()

    def fetch_from_bitwarden(self) -> None:
        """Populate fields using a connection stored in Bitwarden."""
        item = self.bw_item_edit.text().strip()
        if not item:
            return
        cfg = fetch_credentials(item)
        if not cfg:
            return
        if cfg.get("label"):
            self.label_edit.setText(cfg["label"])
        if cfg.get("host"):
            self.host_edit.setText(cfg["host"])
        if cfg.get("username"):
            self.user_edit.setText(cfg["username"])
        if cfg.get("port"):
            self.port_edit.setText(str(cfg["port"]))
        if cfg.get("folder"):
            self.folder_edit.setText(cfg["folder"])
        if cfg.get("key_path"):
            self.key_edit.setText(cfg["key_path"])
        if cfg.get("initial_cmd"):
            self.cmd_edit.setText(cfg["initial_cmd"])


class TerminalTab(QWidget):
    """Embeds KDE Konsole for an SSH connection or local shell."""

    def __init__(self, connection: Connection | None = None, parent=None) -> None:
        super().__init__(parent)
        self._conn = connection

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        from ..util.konsole_embed import (
            create_shell_widget,
            get_last_error,
            send_input,
        )

        # Use a dedicated container so the helper library can set up its own
        # layout without touching this widget's layout. This avoids duplicate
        # layout warnings when opening terminal tabs.
        embed_container = QWidget(self)
        if connection is None:
            widget = create_shell_widget(parent=embed_container)
        else:
            widget = create_shell_widget(parent=embed_container)

        if widget is None:
            error_msg = get_last_error() or "Failed to load Konsole"
            logging.error(
                "Failed to create Konsole widget for %s@%s: %s",
                connection.username,
                connection.host,
                error_msg,
            )
            self.container = QLabel(error_msg, self)
            layout.addWidget(self.container)
        else:
            self.container = embed_container
            layout.addWidget(embed_container)
            self._term_widget = widget
            if connection is not None:
                cmd_parts = ["ssh"]
                if connection.key_path:
                    cmd_parts.extend(["-i", connection.key_path])
                cmd_parts.extend([f"{connection.username}@{connection.host}", "-p", str(connection.port)])
                ssh_cmd = " ".join(cmd_parts)
                send_input(widget, f"clear && {ssh_cmd}")
                if connection.initial_cmd:
                    QTimer.singleShot(1000, lambda: send_input(widget, connection.initial_cmd))
            self._check_timer = QTimer(self)
            self._check_timer.timeout.connect(self._check_widget)
            self._check_timer.start(2000)

    def _check_widget(self):
        from PyQt5 import sip
        if sip.isdeleted(self._term_widget):
            logging.error(
                "Konsole widget closed unexpectedly%s",
                f" for {self._conn.username}@{self._conn.host}" if self._conn else "",
            )
            self._check_timer.stop()
            layout = self.layout()
            layout.removeWidget(self.container)
            self.container.deleteLater()
            self.container = QLabel("Konsole closed unexpectedly", self)
            layout.addWidget(self.container)

    def closeEvent(self, event) -> None:
        if hasattr(self, "_check_timer"):
            self._check_timer.stop()
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
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

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

        # Shortcuts for switching tabs
        next_tab_shortcut = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_tab_shortcut.activated.connect(self.next_tab)
        prev_tab_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_tab_shortcut.activated.connect(self.prev_tab)

        # Shortcut for opening a new local terminal tab
        new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        new_tab_shortcut.activated.connect(self.open_shell_tab)

        self.load_connections()
        self.tree.itemDoubleClicked.connect(self.open_connection)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.open_shell_tab()

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

    def open_shell_tab(self) -> None:
        """Open a new tab running a local shell."""
        tab = TerminalTab(None, self)
        self.tab_widget.addTab(tab, "Terminal")
        self.tab_widget.setCurrentWidget(tab)

    def open_connection(self, item: QTreeWidgetItem):
        conn = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(conn, Connection):
            tab = TerminalTab(conn, self)
            self.tab_widget.addTab(tab, conn.label)
            self.tab_widget.setCurrentWidget(tab)

    def close_tab(self, index: int) -> None:
        """Close and delete the tab at the given index."""
        widget = self.tab_widget.widget(index)
        if widget is not None:
            widget.close()
            widget.deleteLater()
        self.tab_widget.removeTab(index)

    def next_tab(self) -> None:
        """Switch to the next tab."""
        count = self.tab_widget.count()
        if count:
            new_index = (self.tab_widget.currentIndex() + 1) % count
            self.tab_widget.setCurrentIndex(new_index)

    def prev_tab(self) -> None:
        """Switch to the previous tab."""
        count = self.tab_widget.count()
        if count:
            new_index = (self.tab_widget.currentIndex() - 1) % count
            self.tab_widget.setCurrentIndex(new_index)

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
