import { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import TopBar from './components/TopBar';
import ConversationPanel from './components/ConversationPanel';
import DebugPanel from './components/DebugPanel';
import DeviceScreen from './components/DeviceScreen';
import PhotoSelector from './components/PhotoSelector';
import PhotoGallery from './components/PhotoGallery';
import RetryButton from './components/RetryButton';
import ToyCameraFrame from './components/ToyCameraFrame';
import ModePill from './components/feedback/ModePill';
import FeedbackFlagButton from './components/feedback/FeedbackFlagButton';
import FeedbackQuickFlag from './components/feedback/FeedbackQuickFlag';
import TesterIdentityModal from './components/feedback/TesterIdentityModal';
import FeedbackReviewScreen from './components/feedback/FeedbackReviewScreen';
import FeedbackGalleryPanel from './components/feedback/FeedbackGalleryPanel';
import { getInitialAppMode } from './components/feedback/appMode';
import useSessionOrchestration from './hooks/useSessionOrchestration';
import useFeedbackStore from './hooks/useFeedbackStore';
import { captureScreenshot } from './utils/captureScreenshot';

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

// Derive a flat turn snapshot for the feedback store. Fields default to
// empty/zero because the backend TurnSnapshot schema requires strings +
// an int; the tester can still flag moments with incomplete state (e.g.
// before the first AI reply arrives).
function buildTurnSnapshot({ messages, sessionState, screenFrame }) {
  const msgs = messages || [];
  let speakerText = '';
  let childTranscript = '';
  for (let i = msgs.length - 1; i >= 0; i--) {
    const m = msgs[i];
    if (!speakerText && m.role === 'ai' && typeof m.text === 'string') {
      speakerText = m.text;
    }
    if (!childTranscript && m.role === 'child' && typeof m.text === 'string' && !m.isSilent) {
      childTranscript = m.text;
    }
    if (speakerText && childTranscript) break;
  }
  return {
    step: sessionState?.current_step || '',
    speaker_text: speakerText,
    child_transcript: childTranscript,
    widget_type: screenFrame?.widget || '',
    recipe_round: Number(sessionState?.current_round || 0),
  };
}

// Map templateType → {category, photo_filename} for the feedback payload.
// Backend FeedbackActivity schema requires all three fields populated.
function deriveFeedbackActivity({ templateType, activityType }) {
  const category = templateType === 'cat5' ? 'cat5' : 'cat1';
  return {
    template_type: templateType || activityType || 'unknown',
    category,
    photo_filename: activityType || 'unknown',
  };
}

function App() {
  const [tier, setTier] = useState('T0');
  const [debugOpen, setDebugOpen] = useState(false);

  // Tester-feedback mode state — parallel surface gated by appMode.
  const [appMode, setAppMode] = useState(() => getInitialAppMode());
  const isDevMode = appMode === 'dev';
  const isTesterMode = appMode === 'tester';
  const feedbackStore = useFeedbackStore();
  const [quickFlagOpen, setQuickFlagOpen] = useState(false);
  // Frozen snapshot captured at the moment the tester clicks Flag:
  // { turnNumber, screenshotBlob, turnSnapshot }. Never updated while the
  // popover is open so the preview doesn't drift as the session advances.
  const [pendingFlagData, setPendingFlagData] = useState(null);
  const [identityModalOpen, setIdentityModalOpen] = useState(false);
  // `reviewOverride` records an explicit session-scoped intent:
  //   { id, state } where state is 'open' (force-open) or
  //   'dismissed' (sticky-close for this session).
  // Absent an override, visibility is derived from session lifecycle.
  const [reviewOverride, setReviewOverride] = useState(null);
  const appShellRef = useRef(null);

  const [galleryView, setGalleryView] = useState(() => {
    if (typeof window === 'undefined') return false;
    return new URLSearchParams(window.location.search).get('view') === 'feedback';
  });

  const setGalleryViewWithUrl = useCallback((on) => {
    const url = new URL(window.location.href);
    if (on) url.searchParams.set('view', 'feedback');
    else url.searchParams.delete('view');
    window.history.pushState({}, '', url);
    setGalleryView(on);
  }, []);

  const openGalleryView = useCallback(() => setGalleryViewWithUrl(true), [setGalleryViewWithUrl]);
  const closeGalleryView = useCallback(() => setGalleryViewWithUrl(false), [setGalleryViewWithUrl]);

  useEffect(() => {
    const handlePopState = () => {
      const viewParam = new URLSearchParams(window.location.search).get('view');
      setGalleryView(viewParam === 'feedback');
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+D only flips debug state in dev mode. Tester mode keeps the
      // panel mounted-less, so swallowing the shortcut would be a no-op.
      if (!isDevMode) return;
      if (e.ctrlKey && e.key === 'd') {
        e.preventDefault();
        setDebugOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isDevMode]);

  // Any open tester-feedback overlay freezes auto-advance + silence timer
  // so the session waits while the tester is reporting an issue.
  const autoAdvancePaused = isTesterMode && (quickFlagOpen || identityModalOpen);

  const {
    messages, sessionId, sessionState, screenFrame, loading, turnPending, error,
    latency, activityType, templateType, photoUrl, errorExit, lastWrongPhotoId,
    debugData, debugHistory, retryCount, isActive, isEnded, isInputDisabled,
    isSpeaking, audioInfo, ttsEnabled, toggleTts, silenceTimerOn, toggleSilenceTimer, isMicActive, sttMode, silenceTimer,
    animationState, currentScenario, currentClipUrl, isOneShot, onClipEnded,
    startSession, startDeepLinkSession, sendMessage, sendPhotoCollection, toggleMic, resetSession,
    awaitingManualAdvance, manualAdvance,
  } = useSessionOrchestration(tier, { testerMode: isTesterMode, autoAdvancePaused });

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

  // Capture a start timestamp that is stable for the lifetime of a given
  // sessionId. useMemo on [sessionId] gives us a deterministic value per
  // session without mutating refs during render or deferring via effect.
  const sessionStartedAt = useMemo(
    () => (sessionId ? new Date().toISOString() : null),
    [sessionId],
  );

  // Derived review visibility. The override is keyed by sessionId, so
  // switching to a new session transparently clears any previous intent
  // without needing an effect to reset state.
  const overrideForCurrent =
    reviewOverride && reviewOverride.id === sessionId ? reviewOverride.state : null;
  const reviewOpen = overrideForCurrent === 'open'
    || (overrideForCurrent !== 'dismissed'
      && isTesterMode
      && isEnded
      && Boolean(sessionId)
      && feedbackStore.hasFlags);

  // Freeze turn number + turn snapshot at click time so the popover never
  // drifts mid-review. captureScreenshot is async, so we snapshot the sync
  // state first and then attach the blob when it resolves.
  const captureFreshFlagData = useCallback(async () => {
    const turnNumber = sessionState?.turn_count ?? 0;
    const turnSnapshot = buildTurnSnapshot({ messages, sessionState, screenFrame });
    let screenshotBlob = null;
    try {
      screenshotBlob = await captureScreenshot(appShellRef.current);
    } catch (err) {
      console.warn('[feedback] screenshot capture failed', err);
    }
    return {
      turnNumber,
      turnSnapshot,
      screenshotBlob,
      editingFlagId: null,
      initialTags: [],
      initialQuickNote: '',
    };
  }, [messages, sessionState, screenFrame]);

  // Edit-in-place: if a flag already exists for this turn, reopen it so the
  // tester can revise tags/note. The original screenshot + turn_snapshot are
  // kept (they describe the moment first flagged, not the moment re-opened).
  const openFlagFlow = useCallback(async () => {
    if (quickFlagOpen) return;
    const turnNumber = sessionState?.turn_count ?? 0;
    const existing = feedbackStore.flags.find((f) => f.turn_number === turnNumber);
    if (existing) {
      setPendingFlagData({
        turnNumber,
        screenshotBlob: existing.screenshots?.[0]?.blob || null,
        turnSnapshot: existing.turn_snapshot,
        editingFlagId: existing.flag_id,
        initialTags: [...(existing.tags || [])],
        initialQuickNote: existing.quick_note || '',
      });
      setQuickFlagOpen(true);
      return;
    }
    const data = await captureFreshFlagData();
    setPendingFlagData(data);
    setQuickFlagOpen(true);
  }, [captureFreshFlagData, feedbackStore.flags, quickFlagOpen, sessionState?.turn_count]);

  const handleFlagClick = useCallback(async () => {
    if (!feedbackStore.testerAlias) {
      setIdentityModalOpen(true);
      return;
    }
    await openFlagFlow();
  }, [feedbackStore.testerAlias, openFlagFlow]);

  const handleIdentitySubmit = useCallback(
    (alias) => {
      feedbackStore.setTesterAlias(alias);
      setIdentityModalOpen(false);
      // Always continue the flag flow — skip path leaves alias empty and
      // the backend slugifier resolves it to "anon".
      void openFlagFlow();
    },
    [feedbackStore, openFlagFlow],
  );

  const handleQuickFlagSave = useCallback(
    ({ tags, quickNote }) => {
      if (!pendingFlagData) return;
      if (pendingFlagData.editingFlagId) {
        feedbackStore.updateFlag(pendingFlagData.editingFlagId, {
          tags,
          quick_note: quickNote,
        });
      } else {
        feedbackStore.addFlag({
          turnNumber: pendingFlagData.turnNumber,
          tags,
          quickNote,
          screenshot: pendingFlagData.screenshotBlob,
          turnSnapshot: pendingFlagData.turnSnapshot,
        });
      }
      setQuickFlagOpen(false);
      setPendingFlagData(null);
    },
    [feedbackStore, pendingFlagData],
  );

  const handleQuickFlagCancel = useCallback(() => {
    setQuickFlagOpen(false);
    setPendingFlagData(null);
  }, []);

  const handleReviewClose = useCallback(() => {
    if (sessionId) {
      setReviewOverride({ id: sessionId, state: 'dismissed' });
    } else {
      setReviewOverride(null);
    }
  }, [sessionId]);

  // Called right after a successful submit/download: clears flag blobs but
  // leaves the session alone so the review screen can show its thanks view.
  const handleReviewClearFlags = useCallback(() => {
    feedbackStore.clearSession();
  }, [feedbackStore]);

  // Called when the tester chooses "Start another session" from the thanks
  // view — now we actually reset the activity pipeline.
  const handleReviewNewSession = useCallback(() => {
    resetSession();
  }, [resetSession]);

  // In tester mode, the end-of-session button routes through the review
  // screen if there are flags; otherwise it behaves like dev mode.
  const handleNewSession = useCallback(() => {
    if (isTesterMode && feedbackStore.hasFlags && !reviewOpen && sessionId) {
      setReviewOverride({ id: sessionId, state: 'open' });
      return;
    }
    resetSession();
  }, [feedbackStore.hasFlags, isTesterMode, resetSession, reviewOpen, sessionId]);

  const feedbackActivity = deriveFeedbackActivity({ templateType, activityType });

  const handleRetry = useCallback(() => resetSession(), [resetSession]);
  const showRetry = Boolean(error && !sessionId);
  const showPhotoSelector = !sessionId && !loading && !showRetry;

  const showPhotoGallery = templateType === 'cat5'
    && sessionState?.current_step?.startsWith('STEP_3_COLLECT_')
    && sessionState?.collection_phase !== 'detail'
    && isActive;

  // Stage mode = grow the device panel whenever a "full-visual" widget is
  // showing. Triggered by widget, not step, so scene delivery during
  // STEP_4_SYNTHESIS also gets the bigger panel (not just celebrate/closing).
  const STAGE_MODE_WIDGETS = ['story_scene', 'story_loading', 'achievement_image', 'concept_reveal'];
  const stageMode = STAGE_MODE_WIDGETS.includes(screenFrame?.widget);

  if (galleryView && !sessionId) {
    return <FeedbackGalleryPanel onBack={closeGalleryView} />;
  }

  return (
    <div ref={appShellRef} className="app-shell flex flex-col bg-nature text-gray-800 font-sans">
      <TopBar
        tier={tier}
        onTierChange={setTier}
        activityName={activityType?.replace(/_/g, ' ')}
        onNewSession={handleNewSession}
        sessionActive={!!sessionId}
      />

      <h1 className="sr-only">WonderLens Activity Demo</h1>
      <main className={`app-main flex flex-col flex-1 overflow-hidden px-3 pt-2 pb-3 gap-2.5 sm:gap-3 max-[380px]:px-2 max-[380px]:pt-1.5 max-[380px]:pb-2 max-[380px]:gap-2 max-w-4xl mx-auto w-full ${stageMode ? 'stage-mode' : ''}`}>
        {/* TOP — Device Screen in Toy Camera.
         * Sizing is set via inline style with `flex: none` so that the
         * `height` property is authoritative (not subject to flex shrinking
         * when the conversation panel's basis competes for space). This was
         * the actual root cause of the "device panel too small" regression:
         * CSS was fine, but `flex: 1 1 78%` let the browser shrink the panel
         * to ~35% of the intended height under flex layout pressure.
         * `flex: none` = `flex: 0 0 auto` — don't grow, don't shrink, let
         * `height` rule the size. */}
        <section
          className="app-top-panel min-h-0"
          style={stageMode
            ? { flex: 'none', height: '78%', maxHeight: '56rem' }
            : { flex: 'none', height: '55%', maxHeight: '34rem' }
          }
          aria-label="Device screen"
        >
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
                currentScenario={currentScenario}
                isSpeaking={isSpeaking}
                activityType={activityType}
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
            <PhotoSelector
              onPhotoSelect={startSession}
              isLoading={loading}
              onOpenGallery={openGalleryView}
            />
          ) : (
            <ConversationPanel
              messages={messages}
              onSendMessage={sendMessage}
              onMicToggle={toggleMic}
              isMicActive={isMicActive}
              silenceTimer={silenceTimer}
              isInputDisabled={isInputDisabled || showPhotoGallery || (isTesterMode && awaitingManualAdvance)}
              sttMode={sttMode}
              loading={loading}
              turnPending={turnPending}
              errorExit={errorExit}
              collectMode={showPhotoGallery}
              sessionState={sessionState}
              templateType={templateType}
              advancePrompt={
                isTesterMode && awaitingManualAdvance && !quickFlagOpen && !identityModalOpen
                  ? { onAdvance: manualAdvance, disabled: turnPending || loading }
                  : null
              }
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
              onClick={handleNewSession}
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

      {isDevMode && (
        <DebugPanel
          debugData={debugData}
          debugHistory={debugHistory}
          sessionState={sessionState}
          templateType={templateType}
          isOpen={debugOpen}
        />
      )}

      {/* Debug toggle button — visible on all devices, replaces Ctrl+D on mobile */}
      {isDevMode && (
        <button
          onClick={() => setDebugOpen(prev => !prev)}
          className="fixed bottom-3 right-3 z-[60] w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold opacity-30 hover:opacity-80 transition-opacity cursor-pointer"
          style={{ backgroundColor: '#313244', color: '#89b4fa', border: '1px solid #45475a' }}
          title="Toggle debug panel (Ctrl+D)"
        >
          {debugOpen ? '×' : 'D'}
        </button>
      )}

      {/* Always-visible mode pill lets devs and testers swap surfaces. */}
      <ModePill onChange={setAppMode} />

      {isTesterMode && (
        <FeedbackFlagButton
          onClick={handleFlagClick}
          disabled={turnPending || loading || !sessionState}
        />
      )}

      {isTesterMode && identityModalOpen && (
        <TesterIdentityModal
          onSubmit={handleIdentitySubmit}
          onCancel={() => setIdentityModalOpen(false)}
        />
      )}

      {isTesterMode && quickFlagOpen && pendingFlagData && (
        <FeedbackQuickFlag
          screenshotBlob={pendingFlagData.screenshotBlob}
          turnNumber={pendingFlagData.turnNumber}
          initialTags={pendingFlagData.initialTags}
          initialQuickNote={pendingFlagData.initialQuickNote}
          isEditing={Boolean(pendingFlagData.editingFlagId)}
          onSave={handleQuickFlagSave}
          onCancel={handleQuickFlagCancel}
        />
      )}

      {isTesterMode && (
        <FeedbackReviewScreen
          isOpen={reviewOpen}
          flags={feedbackStore.flags}
          sessionId={sessionId}
          testerAlias={feedbackStore.testerAlias}
          activity={feedbackActivity}
          sessionStartedAt={sessionStartedAt}
          appMode="tester"
          buildPayload={feedbackStore.buildPayload}
          onUpdateFlag={feedbackStore.updateFlag}
          onDeleteFlag={feedbackStore.deleteFlag}
          onClose={handleReviewClose}
          onClearSession={handleReviewClearFlags}
          onNewSession={handleReviewNewSession}
        />
      )}
    </div>
  );
}

export default App;
