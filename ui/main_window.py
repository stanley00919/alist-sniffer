import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QLabel, QStatusBar, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QCloseEvent

from core.db import Database
from core.aria2_manager import Aria2Manager
from core.download_monitor import DownloadMonitor
from core.sniffer import SnifferWorker
from core.media_file import MediaFile
from core.chrome_ext_api import ChromeExtServer
from ui.widgets.url_input import URLInputWidget
from ui.widgets.media_list import MediaListWidget
from ui.widgets.folder_tree import FolderTreeWidget
from ui.widgets.download_manager import DownloadManagerWidget
from ui.widgets.settings_widget import SettingsWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._db = Database.instance()
        self._max_retries = int(self._db.get_setting('max_retries') or 3)
        self._aria2 = Aria2Manager(
            rpc_port=int(self._db.get_setting('rpc_port') or 6800),
            rpc_secret=self._db.get_setting('rpc_secret') or '',
            max_concurrent=int(self._db.get_setting('concurrent_downloads') or 3),
            connections_per_file=int(self._db.get_setting('connections_per_file') or 16),
            speed_limit=int(self._db.get_setting('speed_limit') or 0),
            proxy=self._db.get_setting('proxy') or '',
        )
        self._monitor = DownloadMonitor(
            self._aria2,
            poll_interval_ms=int(self._db.get_setting('poll_interval_ms') or 500),
            max_retries=self._max_retries,
        )
        self._sniffer_worker: SnifferWorker | None = None
        self._chrome_server = ChromeExtServer(port=9527)
        self._last_statuses: dict = {}  # gid -> status string, to avoid redundant DB writes
        self._download_info: dict = {}  # gid -> {url, filename, out_dir, referer} for retry

        self.setWindowTitle('WebMedia Sniffer')
        self.resize(1200, 800)
        self._build_ui()
        self._folder_refresh_timer = QTimer()
        self._folder_refresh_timer.setSingleShot(True)
        self._folder_refresh_timer.setInterval(3000)  # refresh folder tree 3s after last completion
        self._folder_refresh_timer.timeout.connect(self.folder_tree.refresh)
        self._monitor.progress_updated.connect(self._on_progress)
        self._monitor.download_complete.connect(self._on_dl_complete)
        self._monitor.download_error.connect(self._on_dl_error)
        self._chrome_server.url_received.connect(self._on_ext_url)
        self.url_input.cancel_requested.connect(self._on_sniff_cancel)
        self.dl_manager.start_all_requested.connect(self._on_start_all)
        self.dl_manager.pause_all_requested.connect(self._on_pause_all)
        # Defer aria2 start until after window is shown
        QTimer.singleShot(500, self._deferred_start)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # URL bar
        self.url_input = URLInputWidget()
        self.url_input.sniff_requested.connect(self._on_sniff)
        root.addWidget(self.url_input)

        # Splitter: folder tree | media list
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.folder_tree = FolderTreeWidget()
        dl_folder = self._db.get_setting('download_folder') or os.path.expanduser('~/Downloads')
        self.folder_tree.set_root(dl_folder)
        splitter.addWidget(self.folder_tree)

        self.media_list = MediaListWidget()
        self.media_list.download_requested.connect(self._on_download_requested)
        splitter.addWidget(self.media_list)
        splitter.setSizes([220, 980])
        root.addWidget(splitter, 1)

        # Tab: download manager + settings
        self.tabs = QTabWidget()
        self.dl_manager = DownloadManagerWidget()
        self.dl_manager.pause_requested.connect(self._on_pause)
        self.dl_manager.resume_requested.connect(self._on_resume)
        self.dl_manager.cancel_requested.connect(self._on_cancel)
        self.tabs.addTab(self.dl_manager, 'Download Manager')

        self.settings_widget = SettingsWidget()
        self.settings_widget.settings_saved.connect(self._on_settings_saved)
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setWidget(self.settings_widget)
        self.tabs.addTab(settings_scroll, 'Settings')
        root.addWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready')

    def _deferred_start(self):
        self._start_aria2()
        self._monitor.start()
        self._chrome_server.start()

    # ------------------------------------------------------------------
    # aria2 lifecycle
    # ------------------------------------------------------------------

    def _start_aria2(self):
        try:
            self._aria2.start()
        except FileNotFoundError:
            QMessageBox.warning(
                self,
                'aria2c not found',
                'aria2c.exe was not found in bin/ or PATH.\n'
                'Please download aria2 and place aria2c.exe in the bin/ folder,\n'
                'or add it to your system PATH, then restart the app.'
            )
        except Exception as e:
            QMessageBox.critical(self, 'aria2 Error', str(e))

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @pyqtSlot(str)
    def _on_sniff(self, url: str):
        self.url_input.set_busy(True)
        self.status_bar.showMessage(f'Sniffing {url} ...')
        self._sniffer_worker = SnifferWorker(
            url=url,
            user_agent=self._db.get_setting('user_agent') or '',
            request_delay=float(self._db.get_setting('request_delay') or 0.5),
            use_headless=(self._db.get_setting('use_headless') or 'true') == 'true',
        )
        self._sniffer_worker.results_ready.connect(self._on_sniff_done)
        self._sniffer_worker.error.connect(self._on_sniff_error)
        self._sniffer_worker.status.connect(self.status_bar.showMessage)
        self._sniffer_worker.start()

    @pyqtSlot(list)
    def _on_sniff_done(self, media_files: list):
        self.url_input.set_busy(False)
        self.media_list.populate(media_files)
        self.status_bar.showMessage(f'Found {len(media_files)} media file(s).')

    @pyqtSlot(str)
    def _on_sniff_error(self, msg: str):
        self.url_input.set_busy(False)
        self.status_bar.showMessage(f'Sniff error: {msg}')
        QMessageBox.warning(self, 'Sniff Error', msg)

    @pyqtSlot(list)
    def _on_download_requested(self, media_files: list):
        dl_folder = self._db.get_setting('download_folder') or os.path.expanduser('~/Downloads')
        if not self._aria2.is_running:
            QMessageBox.warning(self, 'Not Ready', 'aria2 is not running.')
            return
        for mf in media_files:
            local_path = os.path.join(dl_folder, mf.filename)
            # Check if file already exists and size matches
            if os.path.isfile(local_path) and (mf.size <= 0 or os.path.getsize(local_path) == mf.size):
                # Use a synthetic gid for the exists entry
                fake_gid = f'exists_{mf.filename}'
                self._db.insert_download(fake_gid, mf.url, mf.filename, dl_folder)
                self._db.update_download_status(fake_gid, 'complete')
                self.dl_manager.add_download(fake_gid, mf.filename)
                widget, _ = self.dl_manager._items.get(fake_gid, (None, None))
                if widget:
                    widget.set_exists()
                self.tabs.setCurrentIndex(0)
                self.status_bar.showMessage(f'{mf.filename} already exists — skipped.')
                continue
            try:
                gid = self._aria2.add(
                    url=mf.url,
                    out_dir=dl_folder,
                    filename=mf.filename,
                    referer=mf.page_url or mf.url,
                )
                self._download_info[gid] = {
                    'url': mf.url,
                    'filename': mf.filename,
                    'out_dir': dl_folder,
                    'referer': mf.page_url or mf.url,
                }
                self._db.insert_download(gid, mf.url, mf.filename, dl_folder)
                self.dl_manager.add_download(gid, mf.filename)
                self.tabs.setCurrentIndex(0)
            except Exception as e:
                self.status_bar.showMessage(f'Failed to queue {mf.filename}: {e}')

    @pyqtSlot(list)
    def _on_progress(self, statuses: list):
        self.dl_manager.update_progress(statuses)
        for s in statuses:
            gid, status = s['gid'], s['status']
            if self._last_statuses.get(gid) != status:
                self._last_statuses[gid] = status
                self._db.update_download_status(gid, status)

    @pyqtSlot(str)
    def _on_dl_complete(self, gid: str):
        self._db.update_download_status(gid, 'complete')
        self._download_info.pop(gid, None)
        self._folder_refresh_timer.start()  # debounced: refresh folder tree 3s after last completion
        notify = (self._db.get_setting('os_notifications') or 'true') == 'true'
        if notify:
            from core.notifier import notify as send_notify
            send_notify('Download Complete', 'A download has finished.')

    @pyqtSlot(str, str)
    def _on_dl_error(self, gid: str, msg: str):
        if msg.startswith('__retry__'):
            attempt = int(msg.split('__retry__')[1])
            info = self._download_info.get(gid)
            if not info:
                return
            # Show retrying state in UI
            widget, _ = self.dl_manager._items.get(gid, (None, None))
            if widget:
                widget.set_retrying(attempt, self._max_retries)
            self.status_bar.showMessage(
                f'Retrying {info["filename"]} (attempt {attempt}/{self._max_retries})...'
            )
            # Remove the failed job from aria2 and re-add
            try:
                self._aria2.remove(gid, delete_file=False)
            except Exception:
                pass
            try:
                new_gid = self._aria2.add(
                    url=info['url'],
                    out_dir=info['out_dir'],
                    filename=info['filename'],
                    referer=info['referer'],
                )
                # Remap all tracking dicts from old gid to new gid
                self._download_info[new_gid] = self._download_info.pop(gid)
                self._last_statuses.pop(gid, None)
                self._db.update_download_status(gid, 'retrying')
                self._monitor.update_gid(gid, new_gid)
                # Update the UI item to track the new gid
                if gid in self.dl_manager._items:
                    item_tuple = self.dl_manager._items.pop(gid)
                    self.dl_manager._items[new_gid] = item_tuple
                    item_tuple[0].gid = new_gid
            except Exception as e:
                self.status_bar.showMessage(f'Retry failed for {info["filename"]}: {e}')
        else:
            # Permanent failure — retries exhausted
            self._db.update_download_status(gid, 'error')
            info = self._download_info.pop(gid, {})
            name = info.get('filename', gid)
            self.status_bar.showMessage(f'Download failed: {name} — {msg}')

    @pyqtSlot(str)
    def _on_pause(self, gid: str):
        self._aria2.pause(gid)
        self._db.update_download_status(gid, 'paused')

    @pyqtSlot(str)
    def _on_resume(self, gid: str):
        self._aria2.resume(gid)
        self._db.update_download_status(gid, 'active')

    @pyqtSlot(str)
    def _on_cancel(self, gid: str):
        self._aria2.remove(gid, delete_file=True)
        self._db.delete_download(gid)
        self.dl_manager.remove_download(gid)

    @pyqtSlot()
    def _on_sniff_cancel(self):
        if self._sniffer_worker and self._sniffer_worker.isRunning():
            self._sniffer_worker.terminate()
        self.url_input.set_busy(False)
        self.status_bar.showMessage('Sniff cancelled.')

    @pyqtSlot()
    def _on_start_all(self):
        for s in self._aria2.get_all():
            if s['status'] in ('paused', 'waiting'):
                self._aria2.resume(s['gid'])

    @pyqtSlot()
    def _on_pause_all(self):
        for s in self._aria2.get_all():
            if s['status'] == 'active':
                self._aria2.pause(s['gid'])

    @pyqtSlot()
    def _on_settings_saved(self):
        if self._aria2.is_running:
            self._aria2.apply_options(
                max_concurrent=int(self._db.get_setting('concurrent_downloads') or 3),
                connections_per_file=int(self._db.get_setting('connections_per_file') or 16),
                speed_limit=int(self._db.get_setting('speed_limit') or 0),
                proxy=self._db.get_setting('proxy') or '',
            )
        self.status_bar.showMessage('Settings saved. Poll interval and sniffer changes require restart.')

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    @pyqtSlot(str)
    def _on_ext_url(self, url: str):
        self.url_input.set_url(url)
        self.raise_()
        self.activateWindow()
        self._on_sniff(url)

    def closeEvent(self, event: QCloseEvent):
        self._monitor.stop()
        self._aria2.stop()
        event.accept()
