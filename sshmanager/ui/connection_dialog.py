from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QFormLayout,
)
from PyQt5.QtGui import QIntValidator

from ..models import Connection


class ConnectionDialog(QDialog):
    """Dialog to create or edit an SSH connection."""

    def __init__(self, parent=None, connection: Connection | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Connection")
        self._connection = connection

        self.label_edit = QLineEdit(self)
        self.host_edit = QLineEdit(self)
        self.user_edit = QLineEdit(self)
        self.port_edit = QLineEdit(self)
        self.port_edit.setValidator(QIntValidator(1, 65535, self))
        self.folder_edit = QLineEdit(self)
        self.key_edit = QLineEdit(self)
        self.initial_cmd_edit = QLineEdit(self)

        if connection:
            self.label_edit.setText(connection.label)
            self.host_edit.setText(connection.host)
            self.user_edit.setText(connection.username)
            self.port_edit.setText(str(connection.port))
            self.folder_edit.setText(connection.folder)
            if connection.key_path:
                self.key_edit.setText(connection.key_path)
            if connection.initial_cmd:
                self.initial_cmd_edit.setText(connection.initial_cmd)

        layout = QFormLayout(self)
        layout.addRow("Label:", self.label_edit)
        layout.addRow("Host:", self.host_edit)
        layout.addRow("Username:", self.user_edit)
        layout.addRow("Port:", self.port_edit)
        layout.addRow("Folder:", self.folder_edit)
        layout.addRow("SSH Key Path:", self.key_edit)
        layout.addRow("Initial Command:", self.initial_cmd_edit)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def connection(self) -> Connection:
        label = self.label_edit.text().strip()
        host = self.host_edit.text().strip()
        user = self.user_edit.text().strip()
        port_text = self.port_edit.text().strip() or "22"
        port = int(port_text)
        folder = self.folder_edit.text().strip() or "Default"
        key_path = self.key_edit.text().strip() or None
        initial_cmd = self.initial_cmd_edit.text().strip() or None
        return Connection(
            label=label,
            host=host,
            username=user,
            port=port,
            folder=folder,
            key_path=key_path,
            initial_cmd=initial_cmd,
        )
