# WebMedia Sniffer

A Windows desktop application that sniffs multimedia download links (MP3, MP4, video, audio) from web pages and batch-downloads them using aria2 — the industry-standard multi-threaded download engine.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-purple.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
[**Chinese version (中文版)**](README_zh.md)

---

## Features

### Intelligent Media Detection
- **Multi-engine sniffing**: Playwright (headless Chromium) + BeautifulSoup fallback
- **Network intercept**: Captures media URLs from XHR responses, CDN redirects, and dynamic content
- **AList V3 support**: Special handler for AList-based sites (e.g., asmrgay.com) — uses browser session cookies + API calls to get signed download URLs
- **HLS/M3U8 parsing**: Detects M3U8 playlists and resolves the best-quality stream URL
- **Content-Length filtering**: Filters out tiny placeholder files below a configurable minimum size

### Powerful Download Engine
- **aria2c** — battle-tested, supports segmented multi-connection downloads (up to 16 connections per file)
- **Resume support**: Pause, resume, and cancel downloads at any time
- **Auto-retry**: Automatic retry with configurable attempt count on transient failures
- **Speed limiting**: Optional per-task speed limit
- **HTTP proxy support**: Route downloads through a proxy

### Organized Downloads
- **Subfolder by domain**: Automatically creates subfolders based on the source domain (e.g., `Downloads/asmrgay.com/`)
- **Filename sanitization**: Handles Unicode filenames and strips illegal Windows characters
- **Duplicate handling**: Automatically renames files to avoid overwrites (e.g., `file.mp3` -> `file.mp3.1`)

### User Experience
- **Dark theme**: Catppuccin-inspired dark UI out of the box
- **Real-time progress**: Live progress bars, speed, and ETA per download
- **Start All / Pause All**: Global download queue controls
- **OS notifications**: Windows toast notifications when downloads complete
- **Chrome Extension**: One-click "Send to Sniffer" from any browser tab
- **Cancel Sniff**: Abort an ongoing sniff operation at any time

---

## Installation

### Prerequisites

- **Python 3.12+**
- **Windows 10 or 11**
- **Git**

### Step 1: Clone the Repository

```bash
git clone https://github.com/stanley00919/alist-sniffer.git
cd alist-sniffer
```

### Step 2: Create a Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install Playwright Chromium

```bash
playwright install chromium
```

### Step 5: Run the Application

```bash
python main.py
```

---

## Usage

### Sniffing Media from a URL

1. Launch the application
2. Paste a webpage URL into the input bar (e.g., `https://www.asmrgay.com/asmr/...`)
3. Click **Sniff**
4. Review the detected media files in the list
5. Use checkboxes to select the files you want
6. Click **Download Selected** or **Download All**

The application will queue the downloads in aria2 and begin downloading immediately.

### Download Manager

The **Download Manager** tab shows all active, paused, and completed downloads:
- **Progress bar** with percentage and speed
- **Pause / Resume** individual downloads
- **Cancel** a download (deletes partial file)
- **Start All / Pause All** for bulk queue control
- **Clear Completed** removes finished items from the list
- **Open Folder** button appears when a download completes — click to open the save location in Explorer

### Settings

| Setting | Description |
|---------|-------------|
| Download folder | Root directory for all downloads |
| Concurrent downloads | Max simultaneous downloads (1-10) |
| Connections per file | Split size per file (1-32) |
| Speed limit | Max speed in KB/s (0 = unlimited) |
| HTTP Proxy | Proxy URL (e.g., `http://127.0.0.1:7890`) |
| Request delay | Seconds to wait after page load before sniffing |
| Monitor poll interval | How often to refresh download status (200-5000ms) |
| Min file size | Ignore media files smaller than this (bytes) |
| Subfolder pattern | Create subfolders by pattern (e.g., `{domain}`) |
| OS notifications | Show Windows toast on completion |
| User-Agent | Custom browser User-Agent string |

### Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **Load unpacked** and select the `chrome-extension/` folder in this project
4. Browse to any webpage with media
5. Click the **WebMedia Sniffer** extension icon in the toolbar
6. Click **Send Page URL to Sniffer** — the desktop app will automatically sniff the URL

---

## Architecture

```
webmedia-sniffer/
├── main.py                    # Entry point
├── core/
│   ├── sniffer.py             # SnifferEngine + SnifferWorker (QThread)
│   ├── alist_sniffer.py       # AList V3 API sniffer (Playwright cookies + /api/fs/list)
│   ├── aria2_manager.py       # aria2c subprocess + RPC client
│   ├── download_monitor.py    # Polls aria2 RPC every N ms, emits signals
│   ├── hls_parser.py          # M3U8 playlist parser (selects best-quality stream)
│   ├── media_file.py          # MediaFile dataclass
│   ├── db.py                  # SQLite (settings + download history)
│   ├── chrome_ext_api.py      # Flask server on port 9527 for Chrome ext
│   └── notifier.py            # Windows toast notifications
├── ui/
│   ├── main_window.py         # MainWindow (signal/slot hub)
│   └── widgets/
│       ├── url_input.py       # URL input + Sniff/Cancel button
│       ├── media_list.py      # Sniffed media list with checkboxes
│       ├── media_list_item.py # Individual media row
│       ├── download_item.py   # Download progress row
│       ├── download_manager.py # Download queue panel
│       ├── folder_tree.py     # Download folder tree panel
│       └── settings_widget.py # Settings form
└── chrome-extension/           # Chrome extension (Manifest V3)
```

---

## AList V3 Sites

This application was built specifically for **AList V3** sites like [asmrgay.com](https://www.asmrgay.com).

These sites are Single-Page Applications (SPAs) — the file list is not in the static HTML. The sniffer:
1. Launches a headless Chromium browser
2. Navigates to the page to obtain session cookies
3. Calls the `/api/fs/list` API with those cookies
4. Extracts signed download URLs from the JSON response

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| GUI | PyQt6 |
| Download Engine | aria2c (RPC via aria2p) |
| Browser Automation | Playwright (Chromium) |
| HTML Parsing | BeautifulSoup4 + lxml |
| HTTP Client | httpx |
| Local API | Flask |
| Notifications | winotify |
| Database | SQLite |

---

## License

MIT License
