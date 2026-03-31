import sqlite3
import os
import secrets
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'webmedia.db')


class Database:
    _instance: Optional['Database'] = None

    def __init__(self, path: str = DB_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    @classmethod
    def instance(cls) -> 'Database':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_schema(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS downloads (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                gid         TEXT UNIQUE,
                url         TEXT NOT NULL,
                filename    TEXT,
                output_path TEXT,
                status      TEXT DEFAULT 'queued',
                created_at  TEXT,
                updated_at  TEXT
            );
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        self._conn.commit()
        self._ensure_defaults()

    def _ensure_defaults(self):
        defaults = {
            'download_folder':      os.path.expanduser('~/Downloads'),
            'concurrent_downloads': '3',
            'connections_per_file': '16',
            'rpc_port':             '6800',
            'rpc_secret':           secrets.token_hex(16),
            'speed_limit':          '0',
            'request_delay':        '0.5',
            'use_headless':         'true',
            'proxy':                '',
            'os_notifications':     'true',
            'user_agent':           (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
            'min_file_size':        '1024',
            'subfolder_pattern':    '{domain}',
            'auto_retry':           'true',
            'max_retries':          '3',
        }
        for key, value in defaults.items():
            self._conn.execute(
                'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                (key, value)
            )
        self._conn.commit()

    # --- Settings ---

    def get_setting(self, key: str) -> Optional[str]:
        row = self._conn.execute(
            'SELECT value FROM settings WHERE key = ?', (key,)
        ).fetchone()
        return row['value'] if row else None

    def set_setting(self, key: str, value: str):
        self._conn.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            (key, value)
        )
        self._conn.commit()

    def all_settings(self) -> dict:
        rows = self._conn.execute('SELECT key, value FROM settings').fetchall()
        return {r['key']: r['value'] for r in rows}

    # --- Downloads ---

    def insert_download(self, gid: str, url: str, filename: str, output_path: str) -> int:
        now = datetime.utcnow().isoformat()
        cur = self._conn.execute(
            'INSERT OR IGNORE INTO downloads (gid, url, filename, output_path, status, created_at, updated_at) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (gid, url, filename, output_path, 'queued', now, now)
        )
        self._conn.commit()
        return cur.lastrowid

    def update_download_status(self, gid: str, status: str):
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            'UPDATE downloads SET status = ?, updated_at = ? WHERE gid = ?',
            (status, now, gid)
        )
        self._conn.commit()

    def delete_download(self, gid: str):
        self._conn.execute('DELETE FROM downloads WHERE gid = ?', (gid,))
        self._conn.commit()

    def get_all_downloads(self) -> list:
        rows = self._conn.execute(
            'SELECT * FROM downloads ORDER BY created_at DESC'
        ).fetchall()
        return [dict(r) for r in rows]

    def get_incomplete_downloads(self) -> list:
        rows = self._conn.execute(
            "SELECT * FROM downloads WHERE status NOT IN ('complete', 'error') ORDER BY created_at"
        ).fetchall()
        return [dict(r) for r in rows]
