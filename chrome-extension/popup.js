const mediaList = document.getElementById('media-list');
const statusEl  = document.getElementById('status');
const msgEl     = document.getElementById('msg');

let currentTabUrl = '';
let allUrls = [];

function showMsg(text, isErr = false) {
  msgEl.textContent = text;
  msgEl.className = isErr ? 'err' : '';
  setTimeout(() => { msgEl.textContent = ''; }, 3000);
}

function renderList(urls) {
  mediaList.innerHTML = '';
  if (urls.length === 0) {
    mediaList.innerHTML = '<div class="media-item" style="color:#A6ADC8">No media detected on this page yet.</div>';
    return;
  }
  urls.forEach(url => {
    const item = document.createElement('div');
    item.className = 'media-item';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = true;
    cb.dataset.url = url;
    const lbl = document.createElement('span');
    lbl.textContent = decodeURIComponent(url.split('/').pop().split('?')[0]) || url;
    lbl.title = url;
    item.appendChild(cb);
    item.appendChild(lbl);
    mediaList.appendChild(item);
  });
}

// Load media from background
chrome.runtime.sendMessage({ type: 'GET_MEDIA' }, (resp) => {
  allUrls = resp.urls || [];
  currentTabUrl = resp.tabUrl || '';
  statusEl.textContent = `${allUrls.length} media URL(s) detected`;
  renderList(allUrls);
});

// Send current page URL to sniffer
document.getElementById('btn-send-page').addEventListener('click', () => {
  if (!currentTabUrl) { showMsg('No tab URL available.', true); return; }
  chrome.runtime.sendMessage(
    { type: 'SEND_TO_SNIFFER', url: currentTabUrl },
    (resp) => {
      if (resp.ok) showMsg('Page URL sent to Sniffer!');
      else showMsg('Failed: ' + resp.error, true);
    }
  );
});

// Send selected media URLs
document.getElementById('btn-send-selected').addEventListener('click', () => {
  const checked = [...document.querySelectorAll('.media-item input:checked')];
  if (checked.length === 0) { showMsg('No URLs selected.', true); return; }
  let sent = 0;
  checked.forEach(cb => {
    chrome.runtime.sendMessage(
      { type: 'SEND_TO_SNIFFER', url: cb.dataset.url },
      (resp) => {
        sent++;
        if (sent === checked.length) {
          showMsg(`Sent ${sent} URL(s) to Sniffer!`);
        }
      }
    );
  });
});
