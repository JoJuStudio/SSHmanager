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
        self.setWindowTitle("Bitwarden API Login")
        self.token_edit = QLineEdit(self)
        self.token_edit.setEchoMode(QLineEdit.Password)
        self.server_edit = QLineEdit(self)
        self.server_edit.setPlaceholderText("https://vault.bitwarden.com")

        layout = QFormLayout(self)
        layout.addRow("Server:", self.server_edit)
        layout.addRow("API Token:", self.token_edit)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self,
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def values(self):
        server = self.server_edit.text().strip() or None
        return self.token_edit.text().strip(), server
