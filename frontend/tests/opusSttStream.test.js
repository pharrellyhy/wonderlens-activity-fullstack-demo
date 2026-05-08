import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  chooseOpusMimeType,
  createSttStreamUrl,
  startBrowserOpusSttStream,
} from '../src/utils/opusSttStream.js';

class FakeWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  static instances = [];

  constructor(url) {
    this.url = url;
    this.readyState = FakeWebSocket.CONNECTING;
    this.sent = [];
    FakeWebSocket.instances.push(this);
  }

  send(data) {
    this.sent.push(data);
  }

  close() {
    this.readyState = FakeWebSocket.CLOSED;
    this.onclose?.({ code: 1000 });
  }

  open() {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.();
  }

  receiveJson(payload) {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }
}

class FakeMediaRecorder {
  static instances = [];
  static supportedTypes = new Set(['audio/webm;codecs=opus']);

  static isTypeSupported(type) {
    return FakeMediaRecorder.supportedTypes.has(type);
  }

  constructor(stream, options) {
    this.stream = stream;
    this.options = options;
    this.state = 'inactive';
    FakeMediaRecorder.instances.push(this);
  }

  start(timesliceMs) {
    this.timesliceMs = timesliceMs;
    this.state = 'recording';
  }

  stop() {
    this.state = 'inactive';
    this.onstop?.();
  }

  emitChunk(blob) {
    this.ondataavailable?.({ data: blob });
  }
}

describe('opusSttStream', () => {
  beforeEach(() => {
    FakeWebSocket.instances = [];
    FakeMediaRecorder.instances = [];
    FakeMediaRecorder.supportedTypes = new Set(['audio/webm;codecs=opus']);
  });

  it('chooses the first supported browser Opus MIME type', () => {
    const mediaRecorder = {
      isTypeSupported: (type) => type === 'audio/ogg;codecs=opus',
    };

    expect(chooseOpusMimeType(mediaRecorder)).toBe('audio/ogg;codecs=opus');
  });

  it('builds a WebSocket URL from the current browser location and base path', () => {
    const location = { protocol: 'https:', host: 'example.test' };

    expect(createSttStreamUrl('/wonderlens', location)).toBe('wss://example.test/wonderlens/api/stt/stream');
  });

  it('sends start JSON before binary MediaRecorder chunks and sends stop on request', async () => {
    const onTranscript = vi.fn();
    const stream = {
      getTracks: () => [{ stop: vi.fn() }],
    };
    const mediaDevices = {
      getUserMedia: vi.fn().mockResolvedValue(stream),
    };

    const sessionPromise = startBrowserOpusSttStream({
      wsUrl: 'ws://example.test/api/stt/stream',
      mediaDevices,
      WebSocketCtor: FakeWebSocket,
      MediaRecorderCtor: FakeMediaRecorder,
      onTranscript,
    });
    await Promise.resolve();
    const socket = FakeWebSocket.instances[0];
    socket.open();

    const session = await sessionPromise;
    const recorder = FakeMediaRecorder.instances[0];

    expect(mediaDevices.getUserMedia).toHaveBeenCalledWith({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });
    expect(recorder.options).toEqual({
      mimeType: 'audio/webm;codecs=opus',
      audioBitsPerSecond: 24000,
    });
    expect(recorder.timesliceMs).toBe(100);

    const startMessage = JSON.parse(socket.sent[0]);
    expect(startMessage).toMatchObject({
      type: 'start',
      audio: {
        codec: 'opus',
        container: 'webm',
        mime_type: 'audio/webm;codecs=opus',
        channels: 1,
        target_bitrate_bps: 24000,
        chunk_duration_ms: 100,
      },
      stt: {
        language: 'en-US',
        interim_results: true,
        provider: 'default',
      },
      client: {
        platform: 'browser',
      },
    });

    recorder.emitChunk(new Blob(['opus-data'], { type: 'audio/webm;codecs=opus' }));
    await Promise.resolve();

    expect(socket.sent[1]).toBeInstanceOf(ArrayBuffer);

    session.stop();
    expect(JSON.parse(socket.sent.at(-1))).toEqual({ type: 'stop', reason: 'user_stopped' });

    socket.receiveJson({ type: 'closed', reason: 'stream_complete', final_text: 'hello' });
    expect(onTranscript).toHaveBeenCalledWith('hello');
  });

  it('stops recording and releases microphone tracks when the server sends an error', async () => {
    const onError = vi.fn();
    const track = { stop: vi.fn() };
    const stream = {
      getTracks: () => [track],
    };
    const mediaDevices = {
      getUserMedia: vi.fn().mockResolvedValue(stream),
    };

    const sessionPromise = startBrowserOpusSttStream({
      wsUrl: 'ws://example.test/api/stt/stream',
      mediaDevices,
      WebSocketCtor: FakeWebSocket,
      MediaRecorderCtor: FakeMediaRecorder,
      onError,
    });
    await Promise.resolve();
    const socket = FakeWebSocket.instances[0];
    socket.open();

    await sessionPromise;
    const recorder = FakeMediaRecorder.instances[0];
    socket.receiveJson({ type: 'error', code: 'container_mismatch', message: 'bad header' });

    expect(onError).toHaveBeenCalledWith({ type: 'error', code: 'container_mismatch', message: 'bad header' });
    expect(recorder.state).toBe('inactive');
    expect(track.stop).toHaveBeenCalledTimes(1);
  });
});
