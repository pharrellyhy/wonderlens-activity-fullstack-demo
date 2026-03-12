/**
 * API client for WonderLens Activity Demo backend.
 */

export async function startSession(photo, tier) {
  const formData = new FormData();
  formData.append('photo', photo);
  formData.append('tier', tier);
  const res = await fetch('/api/start', { method: 'POST', body: formData });
  if (!res.ok) throw new Error(`Start failed: ${res.status}`);
  return res.json();
}

export async function sendTurn(sessionId, text, isSilent) {
  const res = await fetch('/api/turn', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, text, is_silent: isSilent }),
  });
  if (!res.ok) throw new Error(`Turn failed: ${res.status}`);
  return res.json();
}

export async function transcribeAudio(audioBlob) {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  const res = await fetch('/api/stt', { method: 'POST', body: formData });
  if (!res.ok) return null;
  return res.json();
}

export async function synthesizeSpeech(text, tier) {
  const res = await fetch('/api/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, tier }),
  });
  if (res.status === 204) return null;
  if (!res.ok) throw new Error(`TTS failed: ${res.status}`);
  return res.blob();
}
