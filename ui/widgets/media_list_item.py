from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from core.media_file import MediaFile


ICONS = {
    'mp3': '♪', 'wav': '♪', 'flac': '♪', 'ogg': '♪',
    'm4a': '♪', 'aac': '♪', 'opus': '♪',
    'mp4': '▶', 'avi': '▶', 'mkv': '▶', 'webm': '▶',
    'm3u8': '▶',
}


class MediaListItem(QWidget):
    download_requested = pyqtSignal(object)  # MediaFile

    def __init__(self, media: MediaFile, parent=None):
        super().__init__(parent)
        self.media = media
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        icon = ICONS.get(media.media_type, '?')
        lbl_icon = QLabel(icon)
        lbl_icon.setFixedWidth(20)
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_name = QLabel(media.filename)
        lbl_name.setToolTip(media.url)
        lbl_name.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        lbl_name.setFont(QFont('Segoe UI', 13))

        lbl_size = QLabel(media.size_str)
        lbl_size.setObjectName('label_muted')
        lbl_size.setFixedWidth(80)
        lbl_size.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        btn_dl = QPushButton('▶')
        btn_dl.setFixedWidth(32)
        btn_dl.setToolTip('Download this file')
        btn_dl.clicked.connect(lambda: self.download_requested.emit(self.media))

        layout.addWidget(lbl_icon)
        layout.addWidget(lbl_name)
        layout.addWidget(lbl_size)
        layout.addWidget(btn_dl)
