# WebMedia Sniffer

一款 Windows 桌面应用程序，可从网页嗅探多媒体下载链接（MP3、MP4、视频、音频），并使用 aria2 多线程下载引擎批量下载文件。

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-purple.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 功能特点

### 智能媒体检测
- **多引擎嗅探**：Playwright（无头 Chromium）+ BeautifulSoup 备选方案
- **网络拦截**：捕获 XHR 响应、CDN 重定向和动态内容中的媒体 URL
- **AList V3 支持**：专为 AList 网站（如 asmrgay.com）设计 — 通过浏览器会话 Cookie + API 调用获取签名下载链接
- **HLS/M3U8 解析**：检测 M3U8 播放列表并解析最高画质流 URL
- **文件大小过滤**：按可配置的最小文件大小过滤无效占位文件

### 强大的下载引擎
- **aria2c** — 久经考验，支持分段多连接下载（每个文件最多 16 个连接）
- **断点续传**：支持随时暂停、恢复和取消下载
- **自动重试**：临时失败时自动重试，可配置重试次数
- **速度限制**：可选的每任务限速
- **HTTP 代理支持**：通过代理服务器路由下载

### 文件管理
- **按域名分类**：自动按来源域名创建子文件夹（如 `Downloads/asmrgay.com/`）
- **文件名清理**：处理 Unicode 文件名，剥离非法 Windows 字符
- **重复文件处理**：自动重命名文件避免覆盖（如 `file.mp3` -> `file.mp3.1`）

### 用户体验
- **深色主题**：开箱即用的 Catppuccin 风格深色界面
- **实时进度**：每个下载任务实时显示进度条、速度和预计剩余时间
- **全部开始 / 全部暂停**：全局下载队列控制
- **系统通知**：下载完成时显示 Windows 气泡通知
- **Chrome 扩展**：一键"发送到嗅探器"
- **取消嗅探**：随时中止正在进行的嗅探操作

---

## 安装

### 环境要求

- **Python 3.12+**
- **Windows 10 或 11**
- **Git**

### 步骤 1：克隆仓库

```bash
git clone https://github.com/stanley00919/alist-sniffer.git
cd alist-sniffer
```

### 步骤 2：创建虚拟环境

```bash
python -m venv venv
venv\Scripts\activate
```

### 步骤 3：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 4：安装 Playwright Chromium

```bash
playwright install chromium
```

### 步骤 5：运行应用程序

```bash
python main.py
```

---

## 使用方法

### 嗅探网页媒体

1. 启动应用程序
2. 将网页 URL 粘贴到输入框中（如 `https://www.asmrgay.com/asmr/...`）
3. 点击 **嗅探（Sniff）**
4. 在列表中查看检测到的媒体文件
5. 通过复选框选择需要下载的文件
6. 点击 **下载选中** 或 **下载全部**

应用程序将把下载任务加入 aria2 队列并立即开始下载。

### 下载管理器

**下载管理器** 选项卡显示所有活动、暂停和已完成的下载任务：
- 带百分比和速度的**进度条**
- 单个下载的**暂停 / 恢复**按钮
- **取消**下载（删除部分文件）
- **全部开始 / 全部暂停** 批量队列控制
- **清除已完成** 从列表中移除已完成项目
- 下载完成时出现**打开文件夹**按钮 — 点击后在资源管理器中打开保存位置

### 设置

| 设置项 | 说明 |
|--------|------|
| 下载文件夹 | 所有下载的根目录 |
| 并发下载数 | 最大同时下载数（1-10） |
| 单文件连接数 | 每个文件的分段数（1-32） |
| 速度限制 | 最大速度 KB/s（0 = 不限速） |
| HTTP 代理 | 代理 URL（如 `http://127.0.0.1:7890`） |
| 请求延迟 | 页面加载后等待秒数再嗅探 |
| 监控轮询间隔 | 刷新下载状态的间隔（200-5000ms） |
| 最小文件大小 | 忽略小于此字节数的媒体文件 |
| 子文件夹模式 | 按模式创建子文件夹（如 `{domain}`） |
| 系统通知 | 下载完成时显示 Windows 气泡通知 |
| User-Agent | 自定义浏览器 User-Agent 字符串 |

### Chrome 扩展

1. 打开 Chrome，访问 `chrome://extensions/`
2. 启用**开发者模式**（右上角开关）
3. 点击**加载已解压的扩展程序**，选择本项目中的 `chrome-extension/` 文件夹
4. 浏览到任意含有媒体的网页
5. 点击工具栏中的 **WebMedia Sniffer** 扩展图标
6. 点击**发送页面 URL 到嗅探器** — 桌面应用程序将自动开始嗅探

---

## 项目结构

```
webmedia-sniffer/
├── main.py                    # 入口文件
├── core/
│   ├── sniffer.py             # SnifferEngine + SnifferWorker（QThread）
│   ├── alist_sniffer.py       # AList V3 API 嗅探器（Playwright Cookie + /api/fs/list）
│   ├── aria2_manager.py       # aria2c 子进程 + RPC 客户端
│   ├── download_monitor.py    # 轮询 aria2 RPC 并发送信号
│   ├── hls_parser.py          # M3U8 播放列表解析器（选择最高画质流）
│   ├── media_file.py          # MediaFile 数据类
│   ├── db.py                  # SQLite（设置 + 下载历史）
│   ├── chrome_ext_api.py      # 端口 9527 的 Flask 服务器（供 Chrome 扩展调用）
│   └── notifier.py            # Windows 气泡通知
├── ui/
│   ├── main_window.py         # MainWindow（信号/槽中枢）
│   └── widgets/
│       ├── url_input.py       # URL 输入框 + 嗅探/取消按钮
│       ├── media_list.py      # 嗅探结果媒体列表（带复选框）
│       ├── media_list_item.py # 单条媒体行
│       ├── download_item.py   # 下载进度行
│       ├── download_manager.py # 下载队列面板
│       ├── folder_tree.py     # 下载文件夹树面板
│       └── settings_widget.py # 设置表单
└── chrome-extension/           # Chrome 扩展（Manifest V3）
```

---

## AList V3 网站

本应用程序专为 **AList V3** 网站设计，如 [asmrgay.com](https://www.asmrgay.com)。

这类网站是单页应用（SPA）— 文件列表不在静态 HTML 中。嗅探器的工作流程：
1. 启动无头 Chromium 浏览器
2. 导航至目标页面以获取会话 Cookie
3. 携带这些 Cookie 调用 `/api/fs/list` API
4. 从 JSON 响应中提取签名下载 URL

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 图形界面 | PyQt6 |
| 下载引擎 | aria2c（通过 aria2p 的 RPC） |
| 浏览器自动化 | Playwright（Chromium） |
| HTML 解析 | BeautifulSoup4 + lxml |
| HTTP 客户端 | httpx |
| 本地 API | Flask |
| 通知 | winotify |
| 数据库 | SQLite |

---

## 开源协议

MIT License
