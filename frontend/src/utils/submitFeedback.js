import BASE from './basePath';
import { buildFeedbackZip } from './buildFeedbackZip';

function pad2(n) {
  return String(n).padStart(2, '0');
}

// Mirror backend feedback_storage.slugify_alias byte-for-byte: lowercase,
// spaces→dash, drop non-[a-z0-9-], strip leading/trailing dashes. No collapse.
function slugifyAlias(alias) {
  if (!alias) return 'anon';
  const cleaned = alias
    .trim()
    .toLowerCase()
    .replace(/ /g, '-')
    .replace(/[^a-z0-9-]+/g, '')
    .replace(/^-+|-+$/g, '');
  return cleaned || 'anon';
}

export function buildFolderNameClient(endedAt, alias, sessionId) {
  const d = endedAt instanceof Date ? endedAt : new Date(endedAt);
  const datePart = `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
  const timePart = `${pad2(d.getHours())}${pad2(d.getMinutes())}`;
  const short = (sessionId || '').slice(0, 6).toLowerCase() || 'nosess';
  return `${datePart}-${timePart}-${slugifyAlias(alias)}-${short}`;
}

function basename(path) {
  return (path || '').split('/').pop() || 'screenshot.png';
}

export async function submitFeedbackToBackend({ json, screenshots }) {
  const form = new FormData();
  form.append('feedback', JSON.stringify(json));
  for (const [relPath, blob] of Object.entries(screenshots || {})) {
    form.append('screenshots', blob, basename(relPath));
  }
  const res = await fetch(`${BASE}/api/feedback`, { method: 'POST', body: form });
  if (!res.ok) {
    let body = '';
    try {
      body = await res.text();
    } catch {
      // ignore body read errors
    }
    const err = new Error(res.statusText || `HTTP ${res.status}`);
    err.cause = body;
    throw err;
  }
  return res.json();
}

export async function downloadFeedbackZip({ json, screenshots, folderName }) {
  const blob = await buildFeedbackZip({
    folderName,
    feedbackJson: JSON.stringify(json, null, 2),
    screenshots,
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `wonderlens-feedback-${folderName}.zip`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
