import { useState, useRef, useCallback, useEffect } from 'react';
import { transcribeAudio } from '../utils/api';

const BrowserSpeechRecognition =
  typeof window === 'undefined'
    ? null
    : window.SpeechRecognition || window.webkitSpeechRecognition;

export default function useSpeechRecognition() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [resultId, setResultId] = useState(0);
  const [mode, setMode] = useState('server'); // 'server' | 'browser'
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const recognitionRef = useRef(null);

  // --- Browser Web Speech API fallback ---

  const startBrowser = useCallback(() => {
    if (!BrowserSpeechRecognition) return;

    const recognition = new BrowserSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      setTranscript(text);
      setResultId((prev) => prev + 1);
      setIsListening(false);
    };

    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
    setTranscript('');
  }, []);

  const stopBrowser = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsListening(false);
  }, []);

  // --- Server-side STT via MediaRecorder + /api/stt ---

  const startServer = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      const recorder = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());

        const blob = new Blob(chunksRef.current, { type: mimeType });
        if (blob.size < 1000) {
          setIsListening(false);
          return;
        }

        const result = await transcribeAudio(blob);
        if (result?.text) {
          setTranscript(result.text);
          setResultId((prev) => prev + 1);
        }
        setIsListening(false);
      };

      recorderRef.current = recorder;
      recorder.start();
      setIsListening(true);
      setTranscript('');
    } catch {
      setMode('browser');
      startBrowser();
    }
  }, [startBrowser]);

  const stopServer = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state === 'recording') {
      recorderRef.current.stop();
    }
    recorderRef.current = null;
  }, []);

  // --- Unified interface ---

  const start = useCallback(() => {
    if (mode === 'server') {
      startServer();
    } else {
      startBrowser();
    }
  }, [mode, startServer, startBrowser]);

  const stop = useCallback(() => {
    if (mode === 'server') {
      stopServer();
    } else {
      stopBrowser();
    }
  }, [mode, stopServer, stopBrowser]);

  const toggle = useCallback(() => {
    if (isListening) {
      stop();
    } else {
      start();
    }
  }, [isListening, start, stop]);

  useEffect(() => stop, [stop]);

  return {
    isListening,
    transcript,
    resultId,
    mode,
    supported: true, // server STT always available; browser is optional fallback
    start,
    stop,
    toggle,
  };
}
