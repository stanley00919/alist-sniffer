from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QCheckBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from typing import List
from core.media_file import MediaFile
from ui.widgets.media_list_item import MediaListItem


class MediaListWidget(QWidget):
    download_requested = pyqtSignal(list)  # List[MediaFile]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: List[MediaFile] = []
        self._checkboxes: List[QCheckBox] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        self.lbl_count = QLabel('No media found')
        self.lbl_count.setObjectName('label_muted')
        hdr.addWidget(self.lbl_count)
        hdr.addStretch()
        layout.addLayout(hdr)

        # List
        self.list_widget = QListWidget()
        self.list_widget.setSpacing(2)
        layout.addWidget(self.list_widget)

        # Action bar
        bar = QHBoxLayout()
        self.btn_select_all = QPushButton('Select All')
        self.btn_select_all.setObjectName('btn_secondary')
        self.btn_select_all.clicked.connect(self._select_all)

        self.btn_deselect = QPushButton('Deselect All')
        self.btn_deselect.setObjectName('btn_secondary')
        self.btn_deselect.clicked.connect(self._deselect_all)

        self.btn_dl_selected = QPushButton('Download Selected')
        self.btn_dl_selected.clicked.connect(self._download_selected)

        self.btn_dl_all = QPushButton('Download All')
        self.btn_dl_all.clicked.connect(self._download_all)

        bar.addWidget(self.btn_select_all)
        bar.addWidget(self.btn_deselect)
        bar.addStretch()
        bar.addWidget(self.btn_dl_selected)
        bar.addWidget(self.btn_dl_all)
        layout.addLayout(bar)

    def populate(self, media_files: List[MediaFile]):
        self.list_widget.clear()
        self._items = media_files
        self._checkboxes = []

        for mf in media_files:
            item_widget = QWidget()
            row = QHBoxLayout(item_widget)
            row.setContentsMargins(4, 2, 4, 2)
            row.setSpacing(6)

            cb = QCheckBox()
            cb.setChecked(True)
            self._checkboxes.append(cb)

            content = MediaListItem(mf)
            content.download_requested.connect(
                lambda m: self.download_requested.emit([m])
            )

            row.addWidget(cb)
            row.addWidget(content, 1)

            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(item_widget.sizeHint())
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, item_widget)

        count = len(media_files)
        self.lbl_count.setText(
            f'{count} media file{"s" if count != 1 else ""} found'
        )

    def _selected_media(self) -> List[MediaFile]:
        return [
            mf for mf, cb in zip(self._items, self._checkboxes)
            if cb.isChecked()
        ]

    def _select_all(self):
        for cb in self._checkboxes:
            cb.setChecked(True)

    def _deselect_all(self):
        for cb in self._checkboxes:
            cb.setChecked(False)

    def _download_selected(self):
        selected = self._selected_media()
        if selected:
            self.download_requested.emit(selected)

    def _download_all(self):
        if self._items:
            self.download_requested.emit(list(self._items))
