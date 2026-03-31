// Per-tab media URL store
const tabMedia = {};

const MEDIA_EXTS = [
  '.mp3', '.mp4', '.wav', '.flac', '.ogg', '.m4a',
  '.aac', '.opus', '.avi', '.mkv', '.webm', '.m3u8'
];

function isMediaUrl(url) {
  try {
    const path = new URL(url).pathname.toLowerCase();
    return MEDIA_EXTS.some(ext => path.endsWith(ext));
  } catch {
    return false;
  }
}

// Intercept network requests and record media URLs per tab
chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    if (details.tabId < 0) return;
    if (isMediaUrl(details.url)) {
      if (!tabMedia[details.tabId]) tabMedia[details.tabId] = [];
      if (!tabMedia[details.tabId].includes(details.url)) {
        tabMedia[details.tabId].push(details.url);
        const count = tabMedia[details.tabId].length;
        chrome.action.setBadgeText({ text: String(count), tabId: details.tabId });
        chrome.action.setBadgeBackgroundColor({ color: '#6C5CE7', tabId: details.tabId });
      }
    }
  },
  { urls: ['<all_urls>'] }
);

// Clear tab data when navigating away
chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
  if (changeInfo.status === 'loading') {
    tabMedia[tabId] = [];
    chrome.action.setBadgeText({ text: '', tabId });
  }
});

chrome.tabs.onRemoved.addListener((tabId) => {
  delete tabMedia[tabId];
});

// Message handler for popup requests
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'GET_MEDIA') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tabId = tabs[0]?.id;
      sendResponse({ urls: tabMedia[tabId] || [], tabUrl: tabs[0]?.url || '' });
    });
    return true; // async
  }
  if (msg.type === 'SEND_TO_SNIFFER') {
    fetch('http://localhost:9527/sniff', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: msg.url })
    })
    .then(r => r.json())
    .then(data => sendResponse({ ok: true, data }))
    .catch(err => sendResponse({ ok: false, error: err.message }));
    return true; // async
  }
});
