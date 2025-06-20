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
        self.email_edit.setFocus()

        layout = QFormLayout(self)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Master Password:", self.password_edit)
        layout.addRow("Server:", self.server_edit)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self,
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

        self.setTabOrder(self.email_edit, self.password_edit)
        self.setTabOrder(self.password_edit, self.server_edit)
        self.setTabOrder(self.server_edit, self.buttons)

    def values(self):
        server = self.server_edit.text().strip() or None
        return (
            self.email_edit.text().strip(),
            self.password_edit.text(),
            server,
        )
