from __future__ import annotations

import logging
import subprocess
from PyQt5.QtWidgets import (
    QMainWindow,
    QTreeWidget,
    QTreeWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QSplitter,
    QToolBar,
    QLabel,
    QMenu,
    QShortcut,
    QMessageBox,
    QToolButton,
    QAction,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QKeySequence, QIcon, QPixmap
import keyring

from ..models import Connection, Config
from ..config import load_config
from .. import bitwarden
from .login_dialog import LoginDialog


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

        self.profile_btn = QToolButton(self)
        self.profile_btn.setIcon(QIcon.fromTheme("user-identity"))
        self.profile_menu = QMenu(self.profile_btn)
        self.profile_btn.setMenu(self.profile_menu)
        self.profile_btn.setPopupMode(QToolButton.InstantPopup)

        spacer = QWidget(toolbar)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        toolbar.addWidget(self.profile_btn)

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
        self.update_ui_state()

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

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def login_bitwarden(self) -> None:
        """Prompt for credentials and reload connections."""
        dlg = LoginDialog(self)
        if dlg.exec() != dlg.Accepted:
            return
        email, password, server = dlg.values()
        if not bitwarden.login(email, password, server):
            err = bitwarden.get_last_error() or "Invalid Bitwarden credentials"
            QMessageBox.critical(
                self,
                "Login Failed",
                err,
            )
            return
        # Store the email and server in the system keyring for convenience
        keyring.set_password("sshmanager", "email", email)
        keyring.set_password("sshmanager", "server", server or "")
        self.statusBar().showMessage("Bitwarden login successful", 3000)
        self.config = load_config()
        self.load_connections()
        self.update_ui_state()

    def logout_bitwarden(self) -> None:
        """Log out of Bitwarden and disable the UI."""
        bitwarden.logout()
        self.config = load_config()
        self.load_connections()
        self.statusBar().showMessage("Logged out", 3000)
        self.update_ui_state()

    def update_ui_state(self) -> None:
        """Enable or disable widgets based on login status."""
        logged_in = bitwarden.is_unlocked()
        self.splitter.setEnabled(logged_in)
        self.profile_menu.clear()
        if logged_in:
            act = QAction("Logout", self)
            act.triggered.connect(self.logout_bitwarden)
            self.profile_menu.addAction(act)
            avatar_data = bitwarden.fetch_avatar()
            if avatar_data:
                pix = QPixmap()
                if pix.loadFromData(avatar_data):
                    self.profile_btn.setIcon(QIcon(pix))
                else:
                    self.profile_btn.setIcon(QIcon.fromTheme("user-identity"))
            else:
                self.profile_btn.setIcon(QIcon.fromTheme("user-identity"))
        else:
            act = QAction("Login", self)
            act.triggered.connect(self.login_bitwarden)
            self.profile_menu.addAction(act)
            self.profile_btn.setIcon(QIcon.fromTheme("user-identity"))
