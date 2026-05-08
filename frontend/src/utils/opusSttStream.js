import BASE from './basePath';

export const OPUS_MIME_CANDIDATES = [
  'audio/webm;codecs=opus',
  'audio/ogg;codecs=opus',
  'audio/webm',
  'audio/ogg',
];

const DEFAULT_AUDIO_CONSTRAINTS = {
  channelCount: 1,
  echoCancellation: true,
  noiseSuppression: true,
  autoGainControl: true,
};

export function chooseOpusMimeType(MediaRecorderCtor = globalThis.MediaRecorder) {
  if (!MediaRecorderCtor?.isTypeSupported) return null;
  return OPUS_MIME_CANDIDATES.find((type) => MediaRecorderCtor.isTypeSupported(type)) ?? null;
}

export function createSttStreamUrl(basePath = BASE, locationObj = globalThis.location) {
  const protocol = locationObj.protocol === 'https:' ? 'wss:' : 'ws:';
  const normalizedBase = basePath && basePath !== '/' ? basePath.replace(/\/$/, '') : '';
  return `${protocol}//${locationObj.host}${normalizedBase}/api/stt/stream`;
}

function containerForMimeType(mimeType) {
  return mimeType.includes('ogg') ? 'ogg' : 'webm';
}

function waitForWebSocketOpen(socket, WebSocketCtor, timeoutMs) {
  if (socket.readyState === WebSocketCtor.OPEN) return Promise.resolve();

  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      cleanup();
      reject(new Error('Timed out opening STT WebSocket'));
    }, timeoutMs);

    function cleanup() {
      clearTimeout(timeoutId);
      socket.onopen = null;
      socket.onerror = null;
      socket.onclose = null;
    }

    socket.onopen = () => {
      cleanup();
      resolve();
    };
    socket.onerror = () => {
      cleanup();
      reject(new Error('Failed to open STT WebSocket'));
    };
    socket.onclose = () => {
      cleanup();
      reject(new Error('STT WebSocket closed before opening'));
    };
  });
}

function stopStreamTracks(stream) {
  stream?.getTracks?.().forEach((track) => track.stop());
}

export async function startBrowserOpusSttStream({
  wsUrl = createSttStreamUrl(),
  language = 'en-US',
  interimResults = true,
  provider = 'default',
  mediaDevices = globalThis.navigator?.mediaDevices,
  WebSocketCtor = globalThis.WebSocket,
  MediaRecorderCtor = globalThis.MediaRecorder,
  onTranscript = () => {},
  onWarning = () => {},
  onError = () => {},
  onClosed = () => {},
  websocketOpenTimeoutMs = 2500,
} = {}) {
  if (!mediaDevices?.getUserMedia) {
    throw new Error('Browser microphone capture is not available');
  }
  if (!WebSocketCtor) {
    throw new Error('WebSocket is not available');
  }

  const mimeType = chooseOpusMimeType(MediaRecorderCtor);
  if (!mimeType) {
    throw new Error('Opus MediaRecorder is not supported on this browser');
  }

  const stream = await mediaDevices.getUserMedia({ audio: DEFAULT_AUDIO_CONSTRAINTS });
  const socket = new WebSocketCtor(wsUrl);
  socket.binaryType = 'arraybuffer';

  try {
    await waitForWebSocketOpen(socket, WebSocketCtor, websocketOpenTimeoutMs);
  } catch (error) {
    stopStreamTracks(stream);
    throw error;
  }

  const container = containerForMimeType(mimeType);
  socket.send(JSON.stringify({
    type: 'start',
    audio: {
      codec: 'opus',
      container,
      mime_type: mimeType,
      channels: 1,
      target_bitrate_bps: 24000,
      chunk_duration_ms: 100,
    },
    stt: {
      language,
      interim_results: interimResults,
      provider,
    },
    client: {
      platform: 'browser',
      sdk_version: '1.0.0',
    },
  }));

  const recorder = new MediaRecorderCtor(stream, {
    mimeType,
    audioBitsPerSecond: 24000,
  });
  let stopped = false;
  let pendingStopReason = null;

  function sendStop(reason) {
    if (socket.readyState === WebSocketCtor.OPEN) {
      socket.send(JSON.stringify({ type: 'stop', reason }));
    }
  }

  function stopRecorderAndTracks(reason = null) {
    if (stopped) return;
    stopped = true;
    pendingStopReason = reason;
    if (recorder.state !== 'inactive') {
      recorder.stop();
      return;
    }
    stopStreamTracks(stream);
    if (pendingStopReason) sendStop(pendingStopReason);
  }

  socket.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data);
      if (message.type === 'transcript' && message.text) {
        onTranscript(message.text);
      } else if (message.type === 'warning') {
        onWarning(message);
      } else if (message.type === 'error') {
        stopRecorderAndTracks();
        onError(message);
      } else if (message.type === 'closed') {
        stopRecorderAndTracks();
        if (message.final_text) onTranscript(message.final_text);
        onClosed(message);
      }
    } catch {
      stopRecorderAndTracks();
      onError({ type: 'error', code: 'invalid_server_message', message: 'Invalid STT server message' });
    }
  };

  socket.onerror = () => {
    stopRecorderAndTracks();
    onError({ type: 'error', code: 'websocket_error', message: 'STT WebSocket error' });
  };

  recorder.ondataavailable = async (event) => {
    if (event.data.size === 0 || socket.readyState !== WebSocketCtor.OPEN) return;
    socket.send(await event.data.arrayBuffer());
  };

  recorder.onstop = () => {
    stopStreamTracks(stream);
    if (pendingStopReason) sendStop(pendingStopReason);
  };

  recorder.start(100);

  return {
    stop(reason = 'user_stopped') {
      stopRecorderAndTracks(reason);
    },
  };
}
