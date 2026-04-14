import JSZip from 'jszip';

export async function buildFeedbackZip({ folderName, feedbackJson, screenshots }) {
  const zip = new JSZip();
  const root = zip.folder(folderName);
  root.file('feedback.json', feedbackJson);
  const entries = Object.entries(screenshots || {});
  if (entries.length > 0) {
    const shots = root.folder('screenshots');
    for (const [relPath, blob] of entries) {
      shots.file(relPath.replace(/^screenshots\//, ''), blob);
    }
  }
  return await zip.generateAsync({ type: 'blob' });
}
