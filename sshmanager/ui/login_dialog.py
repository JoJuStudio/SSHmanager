from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QFormLayout,
)


class LoginDialog(QDialog):
    """Prompt for Bitwarden login information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bitwarden Login")
        self.email_edit = QLineEdit(self)
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.server_edit = QLineEdit(self)
        self.server_edit.setPlaceholderText("https://vault.bitwarden.com")

        layout = QFormLayout(self)
        layout.addRow("Server:", self.server_edit)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Master Password:", self.password_edit)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self,
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def values(self):
        server = self.server_edit.text().strip() or None
        return (
            self.email_edit.text().strip(),
            self.password_edit.text(),
            server,
        )
