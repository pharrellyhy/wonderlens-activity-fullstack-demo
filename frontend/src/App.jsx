import { useState, useCallback } from 'react';
import TopBar from './components/TopBar';
import ConversationPanel from './components/ConversationPanel';
import DeviceScreen from './components/DeviceScreen';
import PhotoSelector from './components/PhotoSelector';
import PhotoGallery from './components/PhotoGallery';
import RetryButton from './components/RetryButton';
import useSessionOrchestration from './hooks/useSessionOrchestration';

function App() {
  const [tier, setTier] = useState('T0');

  const {
    messages, sessionId, sessionState, screenFrame, loading, turnPending, error,
    latency, activityType, templateType, photoUrl, errorExit, retryCount,
    isActive, isEnded, isInputDisabled,
    isSpeaking, isMicActive, sttMode, silenceTimer,
    startSession, sendMessage, sendPhotoCollection, toggleMic, resetSession,
  } = useSessionOrchestration(tier);

  const handleRetry = useCallback(() => resetSession(), [resetSession]);
  const showRetry = Boolean(error && !sessionId);
  const showPhotoSelector = !sessionId && !loading && !showRetry;

  // Determine if we should show the Cat 5 photo gallery
  const showPhotoGallery = templateType === 'cat5'
    && sessionState?.current_step?.startsWith('STEP_3_COLLECT_')
    && isActive;

  return (
    <div className="flex flex-col h-screen bg-mesh text-gray-800 font-sans">
      <TopBar
        tier={tier}
        onTierChange={setTier}
        activityName={activityType?.replace(/_/g, ' ')}
        onNewSession={resetSession}
        sessionActive={!!sessionId}
      />

      <main className="flex flex-col md:flex-row flex-1 overflow-hidden p-3 gap-3">
        {/* Conversation Panel */}
        <section
          className="w-full md:w-[55%] flex flex-col glass-strong rounded-3xl shadow-lg shadow-black/5 overflow-hidden"
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
              loading={loading}
              turnPending={turnPending}
              errorExit={errorExit}
            />
          )}
        </section>

        {/* Device Screen Panel */}
        <section
          className="w-full md:w-[45%] flex flex-col gap-3"
          aria-label="Device screen"
        >
          <div className="flex-1 glass rounded-3xl shadow-lg shadow-black/5 overflow-hidden p-4">
            {showPhotoGallery ? (
              <PhotoGallery
                onPhotoSelect={sendPhotoCollection}
                collectedPhotos={sessionState?.collected_photos || []}
                totalToCollect={sessionState?.total_rounds || 3}
              />
            ) : (
              <DeviceScreen
                screenFrame={screenFrame}
                photoUrl={photoUrl}
                sessionState={sessionState}
              />
            )}
          </div>

          {/* Error exit indicator */}
          {errorExit && (
            <div className="glass rounded-2xl p-3 text-center shadow-md shadow-black/5 border border-amber-200/50">
              <p className="text-xs text-amber-500">
                Session ended due to a connection issue. Your progress was saved!
              </p>
            </div>
          )}

          {isEnded && (
            <div className="glass rounded-2xl p-4 text-center shadow-md shadow-black/5">
              <p className="text-sm text-gray-500 mb-2">
                {sessionState?.status === 'completed' ? 'Activity complete!' :
                 sessionState?.status === 'error' ? 'Session ended early' :
                 'Session ended'}
              </p>
              <button
                onClick={resetSession}
                className="px-5 py-2 bg-indigo-500 text-white rounded-full hover:bg-indigo-600 text-sm font-semibold transition-all hover:shadow-md"
              >
                New Session
              </button>
            </div>
          )}
        </section>
      </main>

      <footer
        className="flex items-center justify-between mx-3 mb-3 px-5 py-2.5 glass rounded-2xl text-gray-400 text-xs"
        aria-label="Session status"
      >
        <div className="flex items-center gap-4">
          <span>Round: {sessionState?.current_round ?? 0}/{sessionState?.total_rounds ?? '-'}</span>
          <span className="text-gray-300">|</span>
          <span>Latency: {latency ? `${latency}ms` : '-'}</span>
          <span className="text-gray-300">|</span>
          <span>Tier: {tier}</span>
          {templateType && (
            <>
              <span className="text-gray-300">|</span>
              <span className="capitalize">{templateType === 'cat1' ? 'Cat 1' : 'Cat 5'}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-block w-2 h-2 rounded-full ${
            isActive ? 'bg-emerald-400' :
            isEnded ? 'bg-amber-400' :
            error ? 'bg-red-400' :
            loading ? 'bg-indigo-400 animate-pulse' :
            'bg-gray-300'
          }`} />
          <span className="capitalize text-gray-500">
            {loading ? 'generating...' :
             turnPending ? 'thinking...' :
             sessionState?.status || 'idle'}
          </span>
          {isSpeaking && <span className="ml-2 text-indigo-400">Speaking...</span>}
        </div>
      </footer>
    </div>
  );
}

export default App;
