from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from ui.widgets.download_item import DownloadItemWidget


class DownloadManagerWidget(QWidget):
    pause_requested  = pyqtSignal(str)
    resume_requested = pyqtSignal(str)
    cancel_requested = pyqtSignal(str)
    start_all_requested = pyqtSignal()
    pause_all_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: dict = {}  # gid -> (DownloadItemWidget, QListWidgetItem)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Global controls row
        controls_row = QHBoxLayout()
        self.btn_start_all = QPushButton('▶ Start All')
        self.btn_start_all.setObjectName('btn_secondary')
        self.btn_start_all.clicked.connect(self.start_all_requested)
        self.btn_pause_all = QPushButton('⏸ Pause All')
        self.btn_pause_all.setObjectName('btn_secondary')
        self.btn_pause_all.clicked.connect(self.pause_all_requested)
        controls_row.addWidget(self.btn_start_all)
        controls_row.addWidget(self.btn_pause_all)
        controls_row.addStretch()
        layout.addLayout(controls_row)

        # Stats bar
        stats_row = QHBoxLayout()
        self.lbl_stats = QLabel('No downloads')
        self.lbl_stats.setObjectName('label_muted')
        self.btn_clear = QPushButton('Clear Completed')
        self.btn_clear.setObjectName('btn_secondary')
        self.btn_clear.clicked.connect(self._clear_completed)
        stats_row.addWidget(self.lbl_stats)
        stats_row.addStretch()
        stats_row.addWidget(self.btn_clear)
        layout.addLayout(stats_row)

        # List
        self.list_widget = QListWidget()
        self.list_widget.setSpacing(2)
        self.list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.list_widget.setMinimumHeight(200)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.list_widget)

    def add_download(self, gid: str, filename: str):
        if gid in self._items:
            return
        widget = DownloadItemWidget(gid, filename)
        widget.pause_requested.connect(self.pause_requested)
        widget.resume_requested.connect(self.resume_requested)
        widget.cancel_requested.connect(self.cancel_requested)

        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, widget)
        self._items[gid] = (widget, list_item)
        self._update_stats()

    def update_progress(self, statuses: list):
        status_map = {s['gid']: s for s in statuses}
        for gid, (widget, _) in self._items.items():
            if gid in status_map:
                widget.update_progress(status_map[gid])
        self._update_stats()

    def remove_download(self, gid: str):
        if gid not in self._items:
            return
        _, list_item = self._items.pop(gid)
        row = self.list_widget.row(list_item)
        self.list_widget.takeItem(row)
        self._update_stats()

    def _clear_completed(self):
        to_remove = [
            gid for gid, (w, _) in self._items.items()
            if w._status in ('complete', 'error', 'removed')
        ]
        for gid in to_remove:
            self.remove_download(gid)

    def _update_stats(self):
        total = len(self._items)
        active = sum(
            1 for w, _ in self._items.values() if w._status == 'active'
        )
        done = sum(
            1 for w, _ in self._items.values() if w._status == 'complete'
        )
        if total == 0:
            self.lbl_stats.setText('No downloads')
        else:
            self.lbl_stats.setText(
                f'Total: {total}  |  Active: {active}  |  Completed: {done}'
            )
