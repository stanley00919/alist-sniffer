from dataclasses import dataclass, field
from urllib.parse import unquote, urlparse
import re
import os


MEDIA_EXTENSIONS = {
    'mp3', 'mp4', 'wav', 'flac', 'ogg', 'm4a',
    'avi', 'mkv', 'webm', 'm3u8', 'aac', 'opus',
}

_ILLEGAL_CHARS = re.compile(r'[\/:*?"<>|]')


def sanitize_filename(name: str) -> str:
    name = unquote(name)
    name = _ILLEGAL_CHARS.sub('_', name)
    name = name.strip('. ')
    return name[:255] or 'download'


def filename_from_url(url: str) -> str:
    path = urlparse(url).path
    name = os.path.basename(path)
    return sanitize_filename(name) if name else 'download'


@dataclass
class MediaFile:
    url: str
    filename: str = ''
    size: int = 0          # bytes; 0 = unknown
    media_type: str = ''   # e.g. 'audio/mpeg', extension, or raw ext
    page_url: str = ''

    def __post_init__(self):
        if not self.filename:
            self.filename = filename_from_url(self.url)
        if not self.media_type:
            ext = os.path.splitext(self.filename)[1].lstrip('.').lower()
            self.media_type = ext

    @property
    def size_str(self) -> str:
        if self.size <= 0:
            return 'Unknown'
        for unit in ('B', 'KB', 'MB', 'GB'):
            if self.size < 1024:
                return f'{self.size:.1f} {unit}'
            self.size /= 1024
        return f'{self.size:.1f} TB'

    @property
    def is_hls(self) -> bool:
        return self.media_type == 'm3u8'
