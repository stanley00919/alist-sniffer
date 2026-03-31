from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PyQt6.QtCore import pyqtSignal


class URLInputWidget(QWidget):
    sniff_requested = pyqtSignal(str)
    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.input = QLineEdit()
        self.input.setPlaceholderText('Paste a webpage URL to sniff media links...')
        self.input.returnPressed.connect(self._on_sniff)

        self.btn_sniff = QPushButton('Sniff')
        self.btn_sniff.setFixedWidth(90)
        self.btn_sniff.clicked.connect(self._on_sniff)

        self.btn_cancel = QPushButton('Cancel')
        self.btn_cancel.setFixedWidth(70)
        self.btn_cancel.setObjectName('btn_danger')
        self.btn_cancel.clicked.connect(self.cancel_requested)
        self.btn_cancel.setVisible(False)

        self.btn_clear = QPushButton('Clear')
        self.btn_clear.setFixedWidth(70)
        self.btn_clear.setObjectName('btn_secondary')
        self.btn_clear.clicked.connect(self.input.clear)

        layout.addWidget(self.input)
        layout.addWidget(self.btn_sniff)
        layout.addWidget(self.btn_cancel)
        layout.addWidget(self.btn_clear)

    def _on_sniff(self):
        url = self.input.text().strip()
        if url:
            self.sniff_requested.emit(url)

    def set_url(self, url: str):
        self.input.setText(url)

    def set_busy(self, busy: bool):
        self.btn_sniff.setEnabled(not busy)
        self.btn_sniff.setText('Sniffing...' if busy else 'Sniff')
        self.btn_cancel.setVisible(busy)
