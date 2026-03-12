import { useState, useCallback, useEffect, useRef } from 'react';
import TopBar from './components/TopBar';
import ConversationPanel from './components/ConversationPanel';
import DeviceScreen from './components/DeviceScreen';
import PhotoSelector from './components/PhotoSelector';
import RetryButton from './components/RetryButton';
import useConversation from './hooks/useConversation';
import useSilenceTimer from './hooks/useSilenceTimer';
import useSpeechRecognition from './hooks/useSpeechRecognition';
import useTTS from './hooks/useTTS';

function App() {
  const [tier, setTier] = useState('T0');
  const [retryCount, setRetryCount] = useState(0);
  const silenceTimerRef = useRef({ start() {}, clear() {} });

  const {
    messages,
    sessionId,
    sessionState,
    screenFrame,
    loading,
    turnPending,
    error,
    latency,
    activityType,
    photoUrl,
    start,
    sendMessage,
    sendSilence,
    reset,
  } = useConversation();

  const isActive = sessionState?.status === 'active';
  const isEnded = sessionState?.status === 'completed' || sessionState?.status === 'exited';
  const isInputDisabled = isEnded || loading || turnPending;

  const handleSpeakingDone = useCallback(() => {
    if (sessionState?.status === 'active') {
      silenceTimerRef.current.start();
    }
  }, [sessionState?.status]);

  const { isSpeaking, speak, stop } = useTTS(handleSpeakingDone);

  const handleSilence = useCallback(() => {
    if (sessionState?.status === 'active') {
      sendSilence();
    }
  }, [sendSilence, sessionState?.status]);

  const silenceTimer = useSilenceTimer(
    tier,
    handleSilence,
    isActive && !isSpeaking && !turnPending,
  );

  useEffect(() => {
    silenceTimerRef.current = silenceTimer;
  }, [silenceTimer]);

  const speech = useSpeechRecognition();

  useEffect(() => {
    if (!speech.resultId || !speech.transcript || !isActive) return;
    silenceTimer.clear();
    sendMessage(speech.transcript);
  }, [isActive, sendMessage, silenceTimer, speech.resultId, speech.transcript]);

  useEffect(() => {
    if (messages.length === 0) return;
    const lastMsg = messages[messages.length - 1];
    if (lastMsg.role !== 'ai') return;
    silenceTimer.clear();
    speak(lastMsg.text, tier);
  }, [messages, silenceTimer, speak, tier]);

  useEffect(() => {
    if (isInputDisabled) {
      silenceTimer.clear();
    }
  }, [isInputDisabled, silenceTimer]);

  const handleStartSession = useCallback(async (photo) => {
    try {
      setRetryCount(0);
      await start(photo, tier);
    } catch {
      setRetryCount(prev => prev + 1);
    }
  }, [start, tier]);

  const handleSendMessage = useCallback((text) => {
    if (!text.trim() || !isActive || turnPending) return;
    silenceTimer.clear();
    sendMessage(text);
  }, [isActive, sendMessage, silenceTimer, turnPending]);

  const handleMicToggle = useCallback(() => {
    if (turnPending) return;
    if (speech.isListening) {
      speech.stop();
    } else {
      silenceTimer.clear();
      speech.start();
    }
  }, [silenceTimer, speech, turnPending]);

  const handleNewSession = useCallback(() => {
    stop();
    silenceTimer.clear();
    speech.stop();
    reset();
    setRetryCount(0);
  }, [reset, silenceTimer, speech, stop]);

  const handleRetry = useCallback(() => {
    // User would need to re-select a photo, so just reset
    handleNewSession();
  }, [handleNewSession]);

  // Show photo selector if no session
  const showPhotoSelector = !sessionId && !loading;

  return (
    <div className="flex flex-col h-screen bg-slate-50 text-slate-800 font-sans">
      {/* Top Bar */}
      <TopBar
        tier={tier}
        onTierChange={setTier}
        activityName={activityType?.replace(/_/g, ' ')}
        onNewSession={handleNewSession}
        sessionActive={!!sessionId}
      />

      {/* Main Content */}
      <main className="flex flex-1 overflow-hidden">
        {/* Conversation Panel (Left ~55%) */}
        <section className="w-[55%] flex flex-col border-r border-slate-200 bg-white">
          {showPhotoSelector ? (
            <PhotoSelector onPhotoSelect={handleStartSession} isLoading={loading} />
          ) : error && !sessionId ? (
            <div className="flex-1 flex items-center justify-center">
              <RetryButton onRetry={handleRetry} retryCount={retryCount} maxRetries={3} />
            </div>
          ) : (
            <ConversationPanel
              messages={messages}
              onSendMessage={handleSendMessage}
              onMicToggle={handleMicToggle}
              isMicActive={speech.isListening}
              silenceTimer={silenceTimer}
              isInputDisabled={isInputDisabled}
            />
          )}
        </section>

        {/* Device Screen Panel (Right ~45%) */}
        <section className="w-[45%] flex flex-col bg-gradient-to-b from-violet-50 to-sky-50 p-4">
          <DeviceScreen
            screenFrame={screenFrame}
            photoUrl={photoUrl}
            sessionState={sessionState}
          />

          {/* Session ended message */}
          {isEnded && (
            <div className="mt-3 text-center">
              <p className="text-sm text-gray-600 mb-2">
                {sessionState?.status === 'completed' ? 'Activity complete!' : 'Session ended'}
              </p>
              <button
                onClick={handleNewSession}
                className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 text-sm font-medium"
              >
                New Session
              </button>
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="flex items-center justify-between px-5 py-2 bg-slate-800 text-slate-300 text-xs flex-shrink-0">
        <div className="flex items-center gap-4">
          <span>Round: {sessionState?.current_round ?? 0}/{sessionState?.total_rounds ?? '-'}</span>
          <span className="text-slate-500">|</span>
          <span>Latency: {latency ? `${latency}ms` : '-'}</span>
          <span className="text-slate-500">|</span>
          <span>Tier: {tier}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-block w-2 h-2 rounded-full ${
            isActive ? 'bg-emerald-400' :
            isEnded ? 'bg-amber-400' :
            error ? 'bg-red-400' :
            loading ? 'bg-blue-400 animate-pulse' :
            'bg-slate-500'
          }`} />
          <span className="capitalize">
            {loading ? 'generating...' : sessionState?.status || 'idle'}
          </span>
          {isSpeaking && <span className="ml-2 text-blue-300">Speaking...</span>}
        </div>
      </footer>
    </div>
  );
}

export default App;
