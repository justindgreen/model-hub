(function () {
  const FILE_EXT_RE = /\.(stl|3mf|step|stp|obj|fbx|zip)(\?|$)/i;

  function isModelPage() {
    const p = location.pathname;
    return /\/model\//i.test(p) || /\/models?\//i.test(p) || /3d-model/i.test(p);
  }

  // JSON-LD is a standardized way sites embed structured metadata (schema.org).
  // Reading it is far more resilient to markup/redesign changes than CSS selectors.
  function readJsonLd() {
    const out = { name: null, author: null, license: null };
    document.querySelectorAll('script[type="application/ld+json"]').forEach((script) => {
      let data;
      try { data = JSON.parse(script.textContent); } catch (e) { return; }
      const items = Array.isArray(data) ? data : [data];
      for (const item of items) {
        if (!item || typeof item !== 'object') continue;
        if (item.name && !out.name) out.name = item.name;
        if (item.author) {
          out.author = typeof item.author === 'string' ? item.author : (item.author.name || out.author);
        }
        if (item.creator) {
          out.author = out.author || (typeof item.creator === 'string' ? item.creator : item.creator.name);
        }
        if (item.license && !out.license) out.license = item.license;
      }
    });
    return out;
  }

  function readMeta(name) {
    const el = document.querySelector(`meta[property="${name}"], meta[name="${name}"]`);
    return el ? el.content : null;
  }

  function findFileLinks() {
    const links = new Set();
    document.querySelectorAll('a[href]').forEach((a) => {
      if (FILE_EXT_RE.test(a.href)) links.add(a.href);
    });
    return Array.from(links);
  }

  function collectMetadata() {
    const ld = readJsonLd();
    return {
      title: ld.name || readMeta('og:title') || document.title,
      designer: ld.author || readMeta('author') || '',
      license: ld.license || '',
      sourceUrl: location.href,
      fileLinks: findFileLinks(),
    };
  }

  function buildButton() {
    const btn = document.createElement('button');
    btn.id = 'meshory-import-btn';
    btn.textContent = '📦 Send to Meshory';
    btn.addEventListener('click', openPanel);
    document.body.appendChild(btn);
  }

  function openPanel() {
    const existing = document.getElementById('meshory-panel');
    if (existing) { existing.remove(); return; }

    const meta = collectMetadata();
    const panel = document.createElement('div');
    panel.id = 'meshory-panel';
    panel.innerHTML = `
      <h3>Send to Meshory</h3>
      ${meta.fileLinks.length === 0
        ? `<p class="meshory-warn">No direct model file links found on this page. Open the actual download link in a new tab, then use the extension from that page/tab.</p>`
        : `<label>Files</label>
           <div id="meshory-files">
             ${meta.fileLinks.map((f, i) => `
               <label class="meshory-file-row">
                 <input type="checkbox" value="${encodeURIComponent(f)}" checked>
                 <span>${decodeURIComponent(f.split('/').pop().split('?')[0])}</span>
               </label>`).join('')}
           </div>`}
      <label>Designer</label>
      <input id="meshory-designer" value="${(meta.designer || '').replace(/"/g, '&quot;')}">
      <label>License</label>
      <input id="meshory-license" value="${(meta.license || '').replace(/"/g, '&quot;')}">
      <div id="meshory-status"></div>
      <div class="meshory-actions">
        <button id="meshory-cancel">Cancel</button>
        <button id="meshory-send" ${meta.fileLinks.length === 0 ? 'disabled' : ''}>Import</button>
      </div>
    `;
    document.body.appendChild(panel);

    panel.querySelector('#meshory-cancel').addEventListener('click', () => panel.remove());
    panel.querySelector('#meshory-send').addEventListener('click', () => sendImport(panel, meta));
  }

  function sendImport(panel, meta) {
    const status = panel.querySelector('#meshory-status');
    const checked = Array.from(panel.querySelectorAll('#meshory-files input:checked'))
      .map((el) => decodeURIComponent(el.value));
    if (checked.length === 0) {
      status.textContent = 'Select at least one file.';
      status.className = 'meshory-err';
      return;
    }
    const designer = panel.querySelector('#meshory-designer').value;
    const license = panel.querySelector('#meshory-license').value;

    status.textContent = `Importing ${checked.length} file(s)…`;
    status.className = '';

    chrome.runtime.sendMessage(
      { type: 'meshory-import', fileUrls: checked, sourceUrl: meta.sourceUrl, designer, license },
      (response) => {
        if (!response) {
          status.textContent = 'No response from extension background worker.';
          status.className = 'meshory-err';
          return;
        }
        if (response.ok) {
          status.textContent = `Imported ${response.imported}/${checked.length}.` +
            (response.errors.length ? ` Errors: ${response.errors.join('; ')}` : '');
          status.className = response.errors.length ? 'meshory-err' : 'meshory-ok';
        } else {
          status.textContent = response.error || 'Import failed.';
          status.className = 'meshory-err';
        }
      }
    );
  }

  if (isModelPage()) {
    buildButton();
  }
})();
