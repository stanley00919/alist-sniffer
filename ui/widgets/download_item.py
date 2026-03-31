from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt
from ui.styles.theme import COLORS


STATUS_COLORS = {
    'active':    COLORS['primary'],
    'paused':    COLORS['warning'],
    'complete':  COLORS['success'],
    'exists':    COLORS['success'],
    'error':     COLORS['error'],
    'retrying':  COLORS['warning'],
    'waiting':   COLORS['text_muted'],
    'removed':   COLORS['text_muted'],
}


def _fmt_speed(bps: int) -> str:
    if bps < 1024:
        return f'{bps} B/s'
    elif bps < 1024 * 1024:
        return f'{bps / 1024:.1f} KB/s'
    return f'{bps / 1024 / 1024:.1f} MB/s'


def _fmt_eta(secs: int) -> str:
    if secs <= 0:
        return ''
    if secs < 60:
        return f'{secs}s'
    if secs < 3600:
        return f'{secs // 60}m {secs % 60}s'
    return f'{secs // 3600}h {(secs % 3600) // 60}m'


class DownloadItemWidget(QWidget):
    pause_requested  = pyqtSignal(str)   # gid
    resume_requested = pyqtSignal(str)
    cancel_requested = pyqtSignal(str)

    def __init__(self, gid: str, filename: str, parent=None):
        super().__init__(parent)
        self.gid = gid
        self._status = 'waiting'

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 6, 8, 6)
        outer.setSpacing(4)

        # Row 1: filename + buttons
        row1 = QHBoxLayout()
        self.lbl_name = QLabel(filename)
        self.lbl_name.setToolTip(filename)
        row1.addWidget(self.lbl_name, 1)

        self.btn_pause = QPushButton('⏸')
        self.btn_pause.setFixedWidth(32)
        self.btn_pause.setToolTip('Pause')
        self.btn_pause.clicked.connect(self._on_pause_resume)

        self.btn_cancel = QPushButton('✕')
        self.btn_cancel.setFixedWidth(32)
        self.btn_cancel.setObjectName('btn_danger')
        self.btn_cancel.setToolTip('Cancel & delete')
        self.btn_cancel.clicked.connect(lambda: self.cancel_requested.emit(self.gid))

        row1.addWidget(self.btn_pause)
        row1.addWidget(self.btn_cancel)
        outer.addLayout(row1)

        # Row 2: progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(8)
        self.progress.setTextVisible(False)
        outer.addWidget(self.progress)

        # Row 3: stats
        row3 = QHBoxLayout()
        self.lbl_status = QLabel('Waiting')
        self.lbl_status.setObjectName('label_muted')
        self.lbl_stats = QLabel('')
        self.lbl_stats.setObjectName('label_muted')
        self.lbl_stats.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row3.addWidget(self.lbl_status)
        row3.addStretch()
        row3.addWidget(self.lbl_stats)
        outer.addLayout(row3)

    def set_exists(self):
        """Mark this item as already present on disk — no download needed."""
        self._status = 'exists'
        self.progress.setValue(100)
        color = STATUS_COLORS['exists']
        self.lbl_status.setText('Already exists')
        self.lbl_status.setStyleSheet(f'color: {color}; font-size: 12px;')
        self.lbl_stats.setText('Skipped')
        self.btn_pause.setEnabled(False)

    def set_retrying(self, attempt: int, max_retries: int):
        """Show retrying state with attempt counter."""
        self._status = 'retrying'
        color = STATUS_COLORS['retrying']
        self.lbl_status.setText(f'Retrying ({attempt}/{max_retries})')
        self.lbl_status.setStyleSheet(f'color: {color}; font-size: 12px;')
        self.lbl_stats.setText('')
        self.btn_pause.setEnabled(False)

    def update_progress(self, data: dict):
        self._status = data.get('status', 'waiting')
        pct = data.get('percent', 0)
        speed = data.get('speed', 0)
        eta = data.get('eta', 0)
        error = data.get('error', '')

        self.progress.setValue(pct)

        color = STATUS_COLORS.get(self._status, COLORS['text_muted'])
        self.lbl_status.setText(self._status.capitalize())
        self.lbl_status.setStyleSheet(f'color: {color}; font-size: 12px;')

        if self._status == 'active':
            stats = f'{pct}%  {_fmt_speed(speed)}'
            if eta:
                stats += f'  ETA {_fmt_eta(eta)}'
            self.lbl_stats.setText(stats)
            self.btn_pause.setText('⏸')
            self.btn_pause.setToolTip('Pause')
            self.btn_pause.setEnabled(True)
        elif self._status == 'paused':
            self.lbl_stats.setText(f'{pct}% (paused)')
            self.btn_pause.setText('▶')
            self.btn_pause.setToolTip('Resume')
            self.btn_pause.setEnabled(True)
        elif self._status == 'complete':
            self.lbl_stats.setText('Complete')
            self.btn_pause.setEnabled(False)
        elif self._status == 'error':
            self.lbl_stats.setText(error or 'Error')
            self.btn_pause.setEnabled(False)

    def _on_pause_resume(self):
        if self._status == 'active':
            self.pause_requested.emit(self.gid)
        else:
            self.resume_requested.emit(self.gid)
