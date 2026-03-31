from PyQt6.QtCore import QThread, pyqtSignal
from core.aria2_manager import Aria2Manager


class DownloadMonitor(QThread):
    """Polls aria2 RPC every poll_interval_ms and emits progress signals."""
    progress_updated = pyqtSignal(list)   # list of status dicts
    download_complete = pyqtSignal(str)   # gid
    download_error = pyqtSignal(str, str) # gid, error message (permanent — retries exhausted)

    def __init__(self, manager: Aria2Manager, poll_interval_ms: int = 500, max_retries: int = 3):
        super().__init__()
        self._manager = manager
        self._running = False
        self._known_complete: set = set()
        self._known_error: set = set()      # gids already reported as permanent error
        self._retry_counts: dict = {}       # gid -> retry attempt count
        self._poll_interval_ms = poll_interval_ms
        self._max_retries = max_retries

    def update_gid(self, old_gid: str, new_gid: str):
        """Called by MainWindow after a retry re-adds a download with a new GID."""
        count = self._retry_counts.pop(old_gid, 0)
        self._retry_counts[new_gid] = count
        self._known_error.discard(old_gid)

    def run(self):
        self._running = True
        while self._running:
            if self._manager.is_running:
                statuses = self._manager.get_all()
                self.progress_updated.emit(statuses)
                for s in statuses:
                    gid = s['gid']
                    if s['status'] == 'complete' and gid not in self._known_complete:
                        self._known_complete.add(gid)
                        self._retry_counts.pop(gid, None)
                        self.download_complete.emit(gid)
                    elif s['status'] == 'error' and gid not in self._known_error:
                        retries = self._retry_counts.get(gid, 0)
                        if retries < self._max_retries:
                            self._retry_counts[gid] = retries + 1
                            # Signal MainWindow to retry; pass retry count for status display
                            self.download_error.emit(gid, f'__retry__{retries + 1}')
                        else:
                            self._known_error.add(gid)
                            self.download_error.emit(gid, s.get('error') or 'Download failed')
            self.msleep(self._poll_interval_ms)

    def stop(self):
        self._running = False
        self.wait()
