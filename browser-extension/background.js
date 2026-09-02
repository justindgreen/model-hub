chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type !== 'meshory-import') return false;

  (async () => {
    const { serverUrl, apiKey } = await chrome.storage.sync.get(['serverUrl', 'apiKey']);
    if (!serverUrl) {
      sendResponse({ ok: false, error: 'Set the Meshory server URL in the extension popup first.' });
      return;
    }
    if (!apiKey) {
      sendResponse({ ok: false, error: 'Set the Meshory extension API key in the extension popup first (copy it from Meshory\'s Settings tab).' });
      return;
    }

    let imported = 0;
    const errors = [];

    for (const fileUrl of msg.fileUrls) {
      try {
        const fileResp = await fetch(fileUrl);
        if (!fileResp.ok) throw new Error(`download HTTP ${fileResp.status}`);
        const blob = await fileResp.blob();
        const filename = decodeURIComponent(fileUrl.split('/').pop().split('?')[0]) || 'model.stl';

        const form = new FormData();
        form.append('file', blob, filename);
        if (msg.sourceUrl) form.append('source_url', msg.sourceUrl);
        if (msg.designer) form.append('designer', msg.designer);
        if (msg.license) form.append('license', msg.license);

        const importResp = await fetch(`${serverUrl}/api/library/import`, {
          method: 'POST',
          headers: { 'X-Meshory-Api-Key': apiKey },
          body: form,
        });
        if (!importResp.ok) {
          const body = await importResp.text().catch(() => '');
          throw new Error(`import HTTP ${importResp.status} ${body.slice(0, 120)}`);
        }
        imported++;
      } catch (e) {
        errors.push(`${fileUrl.split('/').pop()}: ${e.message}`);
      }
    }

    sendResponse({ ok: true, imported, errors });
  })();

  return true; // keep the message channel open for the async response
});
