const serverUrlInput = document.getElementById('serverUrl');
const apiKeyInput = document.getElementById('apiKey');
const statusEl = document.getElementById('status');

function setStatus(msg, ok) {
  statusEl.textContent = msg;
  statusEl.className = ok ? 'ok' : 'err';
}

chrome.storage.sync.get(['serverUrl', 'apiKey'], (r) => {
  if (r.serverUrl) serverUrlInput.value = r.serverUrl;
  if (r.apiKey) apiKeyInput.value = r.apiKey;
});

document.getElementById('save').addEventListener('click', async () => {
  let url = serverUrlInput.value.trim().replace(/\/+$/, '');
  const apiKey = apiKeyInput.value.trim();
  if (!url) return setStatus('Enter a server URL first.', false);
  if (!/^https?:\/\//.test(url)) url = 'http://' + url;

  let origin;
  try {
    origin = new URL(url).origin + '/*';
  } catch (e) {
    return setStatus('That does not look like a valid URL.', false);
  }

  chrome.permissions.request({ origins: [origin] }, (granted) => {
    if (!granted) return setStatus('Permission denied -- cannot reach that server.', false);
    chrome.storage.sync.set({ serverUrl: url, apiKey }, () => setStatus('Saved.', true));
  });
});

document.getElementById('test').addEventListener('click', async () => {
  const url = serverUrlInput.value.trim().replace(/\/+$/, '');
  if (!url) return setStatus('Enter a server URL first.', false);
  setStatus('Testing…', true);
  try {
    const resp = await fetch(url + '/api/health');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();
    setStatus(data.status === 'ok' ? 'Connected!' : 'Unexpected response.', data.status === 'ok');
  } catch (e) {
    setStatus('Could not reach server: ' + e.message, false);
  }
});
