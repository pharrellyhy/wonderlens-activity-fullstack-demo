import { useState, useCallback, useEffect, useRef } from 'react';
import TopBar from './components/TopBar';
import ConversationPanel from './components/ConversationPanel';
import DebugPanel from './components/DebugPanel';
import DeviceScreen from './components/DeviceScreen';
import PhotoSelector from './components/PhotoSelector';
import PhotoGallery from './components/PhotoGallery';
import RetryButton from './components/RetryButton';
import ToyCameraFrame from './components/ToyCameraFrame';
import useSessionOrchestration from './hooks/useSessionOrchestration';

function getEndedStatusLabel(status) {
  if (status === 'completed') {
    return 'Activity complete!';
  }
  if (status === 'error') {
    return 'Session ended early';
  }
  return 'Session ended';
}

function getFooterIndicatorClass({ isActive, isEnded, error, loading }) {
  if (isActive) {
    return 'bg-[var(--color-forest)]';
  }
  if (isEnded) {
    return 'bg-[var(--color-sunflower)]';
  }
  if (error) {
    return 'bg-red-400';
  }
  if (loading) {
    return 'bg-[var(--color-teal)] animate-pulse';
  }
  return 'bg-gray-300';
}

function getFooterStatusLabel({ loading, turnPending, status }) {
  if (loading) {
    return 'generating...';
  }
  if (turnPending) {
    return 'thinking...';
  }
  return status || 'idle';
}

function App() {
  const [tier, setTier] = useState('T0');
  const [debugOpen, setDebugOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.key === 'd') {
        e.preventDefault();
        setDebugOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const {
    messages, sessionId, sessionState, screenFrame, loading, turnPending, error,
    latency, activityType, templateType, photoUrl, errorExit, lastWrongPhotoId,
    debugData, debugHistory, retryCount, isActive, isEnded, isInputDisabled,
    isSpeaking, audioInfo, ttsEnabled, toggleTts, silenceTimerOn, toggleSilenceTimer, isMicActive, sttMode, silenceTimer,
    animationState, currentClipUrl, isOneShot, onClipEnded,
    startSession, startDeepLinkSession, sendMessage, sendPhotoCollection, toggleMic, resetSession,
  } = useSessionOrchestration(tier);

  const deepLinkHandled = useRef(false);

  useEffect(() => {
    if (deepLinkHandled.current) return;
    const params = new URLSearchParams(window.location.search);
    const entity = params.get('entity');
    if (!entity) return;

    deepLinkHandled.current = true;
    const deepLinkTier = params.get('tier') || 'T0';
    const contextPath = params.get('context') || '';

    void (async () => {
      setTier(deepLinkTier);
      try {
        await startDeepLinkSession(entity, deepLinkTier, contextPath);
        window.history.replaceState({}, '', window.location.pathname);
      } catch {
        // Let the existing error UI handle failed deep-link starts.
      }
    })();
  }, [startDeepLinkSession, setTier]);

  const handleRetry = useCallback(() => resetSession(), [resetSession]);
  const showRetry = Boolean(error && !sessionId);
  const showPhotoSelector = !sessionId && !loading && !showRetry;

  const showPhotoGallery = templateType === 'cat5'
    && sessionState?.current_step?.startsWith('STEP_3_COLLECT_')
    && sessionState?.collection_phase !== 'detail'
    && isActive;

  return (
    <div className="app-shell flex flex-col bg-nature text-gray-800 font-sans">
      <TopBar
        tier={tier}
        onTierChange={setTier}
        activityName={activityType?.replace(/_/g, ' ')}
        onNewSession={resetSession}
        sessionActive={!!sessionId}
      />

      <h1 className="sr-only">WonderLens Activity Demo</h1>
      <main className="app-main flex flex-col flex-1 overflow-hidden px-3 pt-2 pb-3 gap-2.5 sm:gap-3 max-[380px]:px-2 max-[380px]:pt-1.5 max-[380px]:pb-2 max-[380px]:gap-2 max-w-4xl mx-auto w-full">
        {/* TOP — Device Screen in Toy Camera (flex ratio ~4:6 with conversation) */}
        <section className="app-top-panel h-[50%] max-h-[28rem] shrink min-h-0" aria-label="Device screen">
          <ToyCameraFrame videoMode={!!currentClipUrl}>
            {showPhotoGallery ? (
              <PhotoGallery
                onPhotoSelect={sendPhotoCollection}
                collectedPhotos={sessionState?.collected_photos || []}
                totalToCollect={sessionState?.total_rounds || 3}
                wrongPhotoId={lastWrongPhotoId}
                items={sessionState?.current_round_items || []}
                criterion={sessionState?.collection_criterion || ''}
              />
            ) : (
              <DeviceScreen
                screenFrame={screenFrame}
                photoUrl={photoUrl}
                sessionState={sessionState}
                clipUrl={currentClipUrl}
                isOneShot={isOneShot}
                onClipEnded={onClipEnded}
                animationState={animationState}
                isSpeaking={isSpeaking}
              />
            )}
          </ToyCameraFrame>
        </section>

        {/* BOTTOM — Conversation (takes all remaining space) */}
        <section className="flex-1 min-h-0 flex flex-col surface-primary overflow-hidden" aria-label="Conversation panel">
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
              isInputDisabled={isInputDisabled || showPhotoGallery}
              sttMode={sttMode}
              loading={loading}
              turnPending={turnPending}
              errorExit={errorExit}
              collectMode={showPhotoGallery}
              sessionState={sessionState}
              templateType={templateType}
            />
          )}
        </section>
      </main>

      {/* Error exit indicator */}
      {errorExit && (
        <div className="px-3 max-w-3xl mx-auto w-full mb-2">
          <div className="surface-card rounded-2xl p-3 max-[380px]:p-2.5 text-center border border-amber-200/50">
            <p className="text-xs text-amber-600">
              Session ended due to a connection issue. Your progress was saved!
            </p>
          </div>
        </div>
      )}

      {isEnded && (
        <div className="px-3 max-w-3xl mx-auto w-full mb-2">
          <div className="surface-card rounded-2xl p-4 max-[380px]:p-3 text-center">
            <p className="text-sm max-[380px]:text-xs text-gray-500 mb-2">
              {getEndedStatusLabel(sessionState?.status)}
            </p>
            <button
              onClick={resetSession}
              className="px-5 py-2 max-[380px]:px-4 max-[380px]:py-1.5 bg-[var(--color-forest)] text-white rounded-full hover:bg-[var(--color-forest-dark)] text-sm max-[380px]:text-xs font-semibold transition-all hover:shadow-md"
            >
              New Session
            </button>
          </div>
        </div>
      )}

      <footer
        className="app-footer flex flex-wrap items-center justify-between gap-x-4 gap-y-1.5 px-5 sm:px-6 py-3 sm:py-3.5 mx-auto mb-3 w-full max-w-4xl max-[380px]:mb-2 max-[380px]:px-3 max-[380px]:py-2 surface-card rounded-2xl text-gray-500 text-sm max-[380px]:text-[11px]"
        aria-label="Session status"
      >
        <div className="flex items-center gap-3 max-[380px]:gap-2">
          <span>Round: {
            templateType === 'cat5'
              ? (sessionState?.current_step?.startsWith('STEP_3_COLLECT_') && (sessionState?.collected_photos?.length ?? 0) > 0
                ? `${sessionState.collected_photos.length}/${sessionState?.total_rounds ?? '-'}`
                : '-')
              : (sessionState?.current_step?.startsWith('STEP_3_ROUND_')
                ? `${Math.max(sessionState?.current_round ?? 0, 1)}/${sessionState?.total_rounds ?? '-'}`
                : `-/${sessionState?.total_rounds ?? '-'}`)
          }</span>
          <span className="hidden sm:inline text-gray-300">|</span>
          <span className="hidden sm:inline">Latency: {latency ? `${latency}ms` : '-'}</span>
          <span className="text-gray-300">|</span>
          <span>Tier: {tier}</span>
          {templateType && (
            <>
              <span className="text-gray-300">|</span>
              <span className="capitalize">{templateType === 'cat1' ? 'Cat 1' : 'Cat 5'}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2 max-[380px]:gap-1.5">
          <span
            aria-hidden="true"
            className={`inline-block w-2 h-2 rounded-full ${getFooterIndicatorClass({
              isActive,
              isEnded,
              error,
              loading,
            })}`}
          />
          <span className="capitalize text-gray-500">
            {getFooterStatusLabel({ loading, turnPending, status: sessionState?.status })}
          </span>
          {isSpeaking && <span className="ml-2 text-[var(--color-teal)]">Speaking...</span>}
          <div className="ml-auto flex items-center gap-1.5 flex-nowrap whitespace-nowrap">
            <button
              onClick={toggleSilenceTimer}
              className={`px-2 py-0.5 rounded-full text-xs font-medium transition-colors cursor-pointer border ${silenceTimerOn ? 'border-[var(--color-forest)]/30 bg-[var(--color-forest)]/10 text-[var(--color-forest-dark)]' : 'border-gray-200 text-gray-400 hover:border-gray-300'}`}
              aria-label={silenceTimerOn ? 'Disable silence timer' : 'Enable silence timer'}
              title={silenceTimerOn ? 'Silence timer on (30s) — click to disable' : 'Silence timer off — click to enable'}
            >
              {silenceTimerOn ? '\u{23F1} Timer' : '\u{23F1} Timer'}
            </button>
            <button
              onClick={toggleTts}
              className={`px-2 py-0.5 rounded-full text-xs font-medium transition-colors cursor-pointer border ${ttsEnabled ? 'border-[var(--color-forest)]/30 bg-[var(--color-forest)]/10 text-[var(--color-forest-dark)]' : 'border-gray-200 text-gray-400 hover:border-gray-300'}`}
              aria-label={ttsEnabled ? 'Mute TTS' : 'Unmute TTS'}
              title={ttsEnabled ? 'TTS on — click to mute' : 'TTS off — click to unmute'}
            >
              {ttsEnabled ? '\u{1F50A} TTS' : '\u{1F507} TTS'}
            </button>
            {audioInfo && (
              <span className="px-1.5 py-0.5 rounded-full text-[10px] font-mono border border-gray-200 text-gray-500 bg-gray-50 whitespace-nowrap">
                {audioInfo.streaming ? 'Opus▸' : 'Opus'}
                {audioInfo.durationSec && <> {audioInfo.durationSec}s</>}
                {audioInfo.sizeKB !== '...' && <> {audioInfo.sizeKB}k</>}
                {audioInfo.pcmSizeKB && <>←{audioInfo.pcmSizeKB}k</>}
              </span>
            )}
          </div>
        </div>
      </footer>

      <DebugPanel
        debugData={debugData}
        debugHistory={debugHistory}
        sessionState={sessionState}
        templateType={templateType}
        isOpen={debugOpen}
      />

      {/* Debug toggle button — visible on all devices, replaces Ctrl+D on mobile */}
      <button
        onClick={() => setDebugOpen(prev => !prev)}
        className="fixed bottom-3 right-3 z-[60] w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold opacity-30 hover:opacity-80 transition-opacity cursor-pointer"
        style={{ backgroundColor: '#313244', color: '#89b4fa', border: '1px solid #45475a' }}
        title="Toggle debug panel (Ctrl+D)"
      >
        {debugOpen ? '×' : 'D'}
      </button>
    </div>
  );
}

export default App;
