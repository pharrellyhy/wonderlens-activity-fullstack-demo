/**
 * API client for WonderLens Activity Demo backend.
 */

import BASE from './basePath';

export async function startSession(photo, tier) {
  const formData = new FormData();
  formData.append('photo', photo);
  formData.append('tier', tier);
  const res = await fetch(`${BASE}/api/start`, { method: 'POST', body: formData });
  if (!res.ok) throw new Error(`Start failed: ${res.status}`);
  return res.json();
}

export async function sendTurn(sessionId, text, isSilent, photoId = null) {
  const body = { session_id: sessionId, text, is_silent: isSilent };
  if (photoId) body.photo_id = photoId;
  const res = await fetch(`${BASE}/api/turn`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Turn failed: ${res.status}`);
  return res.json();
}

export async function fetchActivities() {
  const res = await fetch(`${BASE}/api/activities`);
  if (!res.ok) throw new Error(`Activities failed: ${res.status}`);
  return res.json();
}

export async function fetchActivityAssetManifest() {
  const res = await fetch(`${BASE}/activity-assets/activity-assets.manifest.json`);
  if (!res.ok) throw new Error(`Activity assets failed: ${res.status}`);
  return res.json();
}

export async function startActivitySession(activityType, tier = 'T1') {
  const res = await fetch(`${BASE}/api/start-activity`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ activity_type: activityType, tier, interaction_mode: 'text' }),
  });
  if (!res.ok) throw new Error(`Activity start failed: ${res.status}`);
  return res.json();
}

/**
 * Combined turn + TTS endpoint. Streams Script Agent output with pipelined TTS.
 *
 * Binary protocol:
 *   [4-byte big-endian uint32: JSON length]
 *   [N bytes: JSON turn data]
 *   [remaining bytes: OGG/Opus audio]
 *
 * @returns {{ turnData: object, audioStream: ReadableStream|null }}
 */
export async function sendTurnSpeak(sessionId, text, isSilent, photoId = null) {
  const body = { session_id: sessionId, text, is_silent: isSilent };
  if (photoId) body.photo_id = photoId;

  const res = await fetch(`${BASE}/api/turn-speak`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    // Error responses are regular JSON
    const err = await res.json();
    throw new Error(err.error || `Turn-speak failed: ${res.status}`);
  }

  const reader = res.body.getReader();

  // Read 4-byte JSON length prefix
  let headerBuf = new Uint8Array(0);
  while (headerBuf.length < 4) {
    const { done, value } = await reader.read();
    if (done) throw new Error('Unexpected end of stream reading JSON header');
    const merged = new Uint8Array(headerBuf.length + value.length);
    merged.set(headerBuf);
    merged.set(value, headerBuf.length);
    headerBuf = merged;
  }

  const jsonLength = new DataView(headerBuf.buffer, headerBuf.byteOffset).getUint32(0, false);

  // Read JSON bytes (may span multiple chunks)
  let jsonBuf = headerBuf.slice(4); // leftover after the 4-byte header
  while (jsonBuf.length < jsonLength) {
    const { done, value } = await reader.read();
    if (done) throw new Error('Unexpected end of stream reading JSON body');
    const merged = new Uint8Array(jsonBuf.length + value.length);
    merged.set(jsonBuf);
    merged.set(value, jsonBuf.length);
    jsonBuf = merged;
  }

  const jsonBytes = jsonBuf.slice(0, jsonLength);
  const leftover = jsonBuf.slice(jsonLength);
  const turnData = JSON.parse(new TextDecoder().decode(jsonBytes));

  // Create a new ReadableStream for the remaining OGG/Opus audio data
  const audioStream = new ReadableStream({
    start(controller) {
      // Push any leftover bytes from the JSON read
      if (leftover.length > 0) {
        controller.enqueue(leftover);
      }
    },
    async pull(controller) {
      const { done, value } = await reader.read();
      if (done) {
        controller.close();
        return;
      }
      controller.enqueue(value);
    },
    cancel() {
      reader.cancel();
    },
  });

  return { turnData, audioStream };
}

export async function startDeepLinkSession(entity, tier, contextUrl = '') {
  const body = { entity, tier };
  if (contextUrl) {
    body.context_url = contextUrl;
  }
  const res = await fetch(`${BASE}/api/start-deep-link`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Deep link start failed: ${res.status}`);
  return res.json();
}

export async function transcribeAudio(audioBlob) {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  const res = await fetch(`${BASE}/api/stt`, { method: 'POST', body: formData });
  if (!res.ok) return null;
  return res.json();
}

export async function fetchFeedbackList() {
  const res = await fetch(`${BASE}/api/feedback/list`);
  if (!res.ok) throw new Error(`Feedback list failed: ${res.status}`);
  return res.json();
}

export function feedbackImageUrl(folderName, relativePath) {
  const encodedRelative = relativePath
    .split('/')
    .map(encodeURIComponent)
    .join('/');
  return `${BASE}/api/feedback/image/${encodeURIComponent(folderName)}/${encodedRelative}`;
}
