import { useState, useCallback } from 'react';
import TopBar from './components/TopBar';
import ConversationPanel from './components/ConversationPanel';
import DeviceScreen from './components/DeviceScreen';
import PhotoSelector from './components/PhotoSelector';
import RetryButton from './components/RetryButton';
import useSessionOrchestration from './hooks/useSessionOrchestration';

function App() {
  const [tier, setTier] = useState('T0');

  const {
    messages, sessionId, sessionState, screenFrame, loading, error,
    latency, activityType, photoUrl, retryCount,
    isActive, isEnded, isInputDisabled,
    isSpeaking, isMicActive, sttMode, silenceTimer,
    startSession, sendMessage, toggleMic, resetSession,
  } = useSessionOrchestration(tier);

  const handleRetry = useCallback(() => resetSession(), [resetSession]);
  const showRetry = Boolean(error && !sessionId);
  const showPhotoSelector = !sessionId && !loading && !showRetry;

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0a] text-white font-sans">
      <TopBar
        tier={tier}
        onTierChange={setTier}
        activityName={activityType?.replace(/_/g, ' ')}
        onNewSession={resetSession}
        sessionActive={!!sessionId}
      />

      <main className="flex flex-col md:flex-row flex-1 overflow-hidden">
        {/* Conversation Panel */}
        <section
          className="w-full md:w-[55%] flex flex-col border-r border-white/5 bg-[#0a0a0a]"
          aria-label="Conversation panel"
        >
          {showRetry ? (
            <div className="flex-1 flex items-center justify-center">
              <RetryButton onRetry={handleRetry} retryCount={retryCount} maxRetries={3} />
            </div>
          ) : showPhotoSelector ? (
            <PhotoSelector onPhotoSelect={startSession} isLoading={loading} />
          ) : (
            <ConversationPanel
              messages={messages}
              onSendMessage={sendMessage}
              onMicToggle={toggleMic}
              isMicActive={isMicActive}
              silenceTimer={silenceTimer}
              isInputDisabled={isInputDisabled}
              sttMode={sttMode}
            />
          )}
        </section>

        {/* Device Screen Panel */}
        <section
          className="w-full md:w-[45%] flex flex-col bg-[#0a0a0a] p-4"
          aria-label="Device screen"
        >
          <DeviceScreen
            screenFrame={screenFrame}
            photoUrl={photoUrl}
            sessionState={sessionState}
          />

          {isEnded && (
            <div className="mt-3 text-center">
              <p className="text-sm text-neutral-500 mb-2">
                {sessionState?.status === 'completed' ? 'Activity complete!' : 'Session ended'}
              </p>
              <button
                onClick={resetSession}
                className="px-5 py-2 bg-fuchsia-500 text-white rounded-full hover:bg-fuchsia-400 text-sm font-semibold transition-colors"
              >
                New Session
              </button>
            </div>
          )}
        </section>
      </main>

      <footer
        className="flex items-center justify-between px-5 py-2 bg-[#111] border-t border-white/5 text-neutral-500 text-xs flex-shrink-0"
        aria-label="Session status"
      >
        <div className="flex items-center gap-4">
          <span>Round: {sessionState?.current_round ?? 0}/{sessionState?.total_rounds ?? '-'}</span>
          <span className="text-neutral-700">|</span>
          <span>Latency: {latency ? `${latency}ms` : '-'}</span>
          <span className="text-neutral-700">|</span>
          <span>Tier: {tier}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-block w-2 h-2 rounded-full ${
            isActive ? 'bg-emerald-400' :
            isEnded ? 'bg-amber-400' :
            error ? 'bg-red-400' :
            loading ? 'bg-fuchsia-400 animate-pulse' :
            'bg-neutral-600'
          }`} />
          <span className="capitalize">
            {loading ? 'generating...' : sessionState?.status || 'idle'}
          </span>
          {isSpeaking && <span className="ml-2 text-fuchsia-400">Speaking...</span>}
        </div>
      </footer>
    </div>
  );
}

export default App;
