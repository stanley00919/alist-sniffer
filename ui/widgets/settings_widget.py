from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QFileDialog, QGroupBox
)
from PyQt6.QtCore import pyqtSignal
from core.db import Database


class SettingsWidget(QWidget):
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = Database.instance()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Download folder
        folder_group = QGroupBox('Download Folder')
        folder_lay = QHBoxLayout(folder_group)
        self.edit_folder = QLineEdit()
        self.btn_browse = QPushButton('Browse')
        self.btn_browse.setObjectName('btn_secondary')
        self.btn_browse.clicked.connect(self._browse_folder)
        folder_lay.addWidget(self.edit_folder)
        folder_lay.addWidget(self.btn_browse)
        layout.addWidget(folder_group)

        # Download engine
        engine_group = QGroupBox('Download Engine')
        engine_lay = QFormLayout(engine_group)
        self.spin_concurrent = QSpinBox()
        self.spin_concurrent.setRange(1, 10)
        self.spin_connections = QSpinBox()
        self.spin_connections.setRange(1, 32)
        self.spin_speed = QSpinBox()
        self.spin_speed.setRange(0, 100000)
        self.spin_speed.setSuffix(' KB/s  (0 = unlimited)')
        self.edit_proxy = QLineEdit()
        self.edit_proxy.setPlaceholderText('http://127.0.0.1:7890')
        engine_lay.addRow('Concurrent downloads:', self.spin_concurrent)
        engine_lay.addRow('Connections per file:', self.spin_connections)
        engine_lay.addRow('Speed limit:', self.spin_speed)
        engine_lay.addRow('HTTP Proxy:', self.edit_proxy)
        layout.addWidget(engine_group)

        # Sniffer
        sniff_group = QGroupBox('Sniffer')
        sniff_lay = QFormLayout(sniff_group)
        self.chk_headless = QCheckBox('Use headless browser (Playwright)')
        self.edit_ua = QLineEdit()
        self.spin_delay = QDoubleSpinBox()
        self.spin_delay.setRange(0.0, 10.0)
        self.spin_delay.setSingleStep(0.5)
        self.spin_delay.setDecimals(1)
        self.spin_delay.setSuffix(' s')
        sniff_lay.addRow(self.chk_headless)
        sniff_lay.addRow('Request delay:', self.spin_delay)
        sniff_lay.addRow('User-Agent:', self.edit_ua)
        layout.addWidget(sniff_group)

        # Performance
        perf_group = QGroupBox('Performance')
        perf_lay = QFormLayout(perf_group)
        self.spin_poll = QSpinBox()
        self.spin_poll.setRange(200, 5000)
        self.spin_poll.setSingleStep(100)
        self.spin_poll.setSuffix(' ms')
        perf_lay.addRow('Monitor poll interval:', self.spin_poll)
        perf_note = QLabel('Restart required for poll interval and aria2 engine changes.')
        perf_note.setObjectName('label_muted')
        perf_lay.addRow(perf_note)
        layout.addWidget(perf_group)

        # Notifications
        self.chk_notify = QCheckBox('Show OS notification when batch completes')
        layout.addWidget(self.chk_notify)

        # Save button
        self.btn_save = QPushButton('Save Settings')
        self.btn_save.clicked.connect(self._save)
        layout.addWidget(self.btn_save)
        layout.addStretch()

        self._load()

    def _load(self):
        s = self._db.all_settings()
        self.edit_folder.setText(s.get('download_folder', ''))
        self.spin_concurrent.setValue(int(s.get('concurrent_downloads', 3)))
        self.spin_connections.setValue(int(s.get('connections_per_file', 16)))
        self.spin_speed.setValue(int(s.get('speed_limit', 0)))
        self.edit_proxy.setText(s.get('proxy', ''))
        self.chk_headless.setChecked(s.get('use_headless', 'true') == 'true')
        self.edit_ua.setText(s.get('user_agent', ''))
        self.spin_delay.setValue(float(s.get('request_delay', 0.5)))
        self.chk_notify.setChecked(s.get('os_notifications', 'true') == 'true')
        self.spin_poll.setValue(int(s.get('poll_interval_ms', 500)))

    def _save(self):
        db = self._db
        db.set_setting('download_folder', self.edit_folder.text())
        db.set_setting('concurrent_downloads', str(self.spin_concurrent.value()))
        db.set_setting('connections_per_file', str(self.spin_connections.value()))
        db.set_setting('speed_limit', str(self.spin_speed.value()))
        db.set_setting('proxy', self.edit_proxy.text())
        db.set_setting('use_headless', 'true' if self.chk_headless.isChecked() else 'false')
        db.set_setting('user_agent', self.edit_ua.text())
        db.set_setting('request_delay', str(self.spin_delay.value()))
        db.set_setting('os_notifications', 'true' if self.chk_notify.isChecked() else 'false')
        db.set_setting('poll_interval_ms', str(self.spin_poll.value()))
        self.settings_saved.emit()

    def _browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, 'Select Download Folder')
        if path:
            self.edit_folder.setText(path)
