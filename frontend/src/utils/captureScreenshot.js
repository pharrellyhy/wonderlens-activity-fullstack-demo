import html2canvas from 'html2canvas-pro';

// Elements tagged with `data-feedback-overlay="true"` are stripped from the
// captured image — keeps the mode pill, flag button, popover, Continue button,
// and review overlays from polluting the tester's preview.
function shouldIgnore(node) {
  return node?.dataset?.feedbackOverlay === 'true';
}

export async function captureScreenshot(targetEl, options = {}) {
  if (!targetEl) return null;
  const canvas = await html2canvas(targetEl, {
    backgroundColor: null,
    logging: false,
    useCORS: true,
    scale: window.devicePixelRatio || 1,
    ignoreElements: shouldIgnore,
    ...options,
  });
  return await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
}

export function blobToDataUrl(blob) {
  if (!blob) return Promise.resolve(null);
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}
