import { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchActivities, fetchActivityAssetManifest } from '../utils/api';
import { assetForBeat, beatIdFromSessionState, screenLayoutForBeat } from './activityAssets';
import ActivityLibrary from './ActivityLibrary.jsx';
import ActivityTextInput from './ActivityTextInput.jsx';
import ActivityTranscript from './ActivityTranscript.jsx';
import useActivityTextSession from './useActivityTextSession.js';
import WonderLensDevice from './WonderLensDevice.jsx';

const EMPTY_LIST = [];

function isFinishedSession(sessionState) {
  return sessionState?.status === 'completed'
    || sessionState?.status === 'exited'
    || sessionState?.status === 'error';
}

function layoutModeForItems(items) {
  if (items.length >= 3) return 'picker';
  if (items.length === 2) return 'choice2';
  return 'single';
}

function collectionScreenLayout(baseLayout, items, selectedIndex = 0, selection = 'device-scroll') {
  if (!items.length) return baseLayout;

  return {
    ...(baseLayout || {}),
    mode: layoutModeForItems(items),
    selection,
    items: items.map((item, index) => ({
      id: item.id || `item_${index + 1}`,
      src: item.image || item.src || baseLayout?.background?.src || '',
      shape: 'circle',
      label: item.label || item.id || '',
      selected: index === selectedIndex,
    })),
  };
}

function assetItemCatalog(activityAsset) {
  const entries = new Map();
  for (const beat of activityAsset?.beats || []) {
    for (const item of beat.layout?.items || []) {
      if (!item.id || entries.has(item.id)) continue;
      entries.set(item.id, {
        id: item.id,
        label: item.label || item.id,
        image: item.src,
        src: item.src,
      });
    }
  }
  return entries;
}

export default function ActivityGameApp() {
  const [activities, setActivities] = useState([]);
  const [assetManifest, setAssetManifest] = useState({ activities: [] });
  const [selectedId, setSelectedId] = useState('');
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState('');
  const [cat3OptionIndex, setCat3OptionIndex] = useState(0);
  const [cat5ItemIndex, setCat5ItemIndex] = useState(0);
  const {
    messages,
    sessionId,
    sessionState,
    loading,
    turnPending,
    error,
    templateType,
    startActivity,
    sendMessage,
    sendCollectionItem,
    reset,
  } = useActivityTextSession();

  useEffect(() => {
    let mounted = true;
    void (async () => {
      try {
        const [data, manifest] = await Promise.all([
          fetchActivities(),
          fetchActivityAssetManifest(),
        ]);
        if (!mounted) return;
        const nextActivities = data.activities || [];
        setActivities(nextActivities);
        setAssetManifest(manifest);
        setSelectedId(nextActivities[0]?.id || '');
      } catch (err) {
        if (mounted) setCatalogError(err.message);
      } finally {
        if (mounted) setCatalogLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const selectedActivity = useMemo(
    () => activities.find((activity) => activity.id === selectedId) || activities[0] || null,
    [activities, selectedId],
  );

  const selectedAsset = useMemo(
    () => assetManifest.activities.find((entry) => entry.id === selectedActivity?.asset_manifest_id)
      || assetManifest.activities.find((entry) => entry.id === selectedActivity?.id),
    [assetManifest.activities, selectedActivity],
  );
  const assetByActivityId = useMemo(
    () => new Map((assetManifest.activities || []).map((entry) => [entry.id, entry])),
    [assetManifest.activities],
  );
  const selectedAssetItemsById = useMemo(
    () => assetItemCatalog(selectedAsset),
    [selectedAsset],
  );

  const beatId = beatIdFromSessionState(sessionState);
  const assetSrc = selectedAsset ? assetForBeat(selectedAsset, beatId) : '';
  const baseScreenLayout = selectedAsset ? screenLayoutForBeat(selectedAsset, beatId) : null;
  const sessionActive = Boolean(sessionId);
  const sessionFinished = isFinishedSession(sessionState);
  const currentStep = sessionState?.current_step || '';
  const activeTemplateType = sessionState?.template_type || templateType;
  const currentRoundItems = sessionState?.current_round_items || EMPTY_LIST;
  const collectedPhotoIds = sessionState?.collected_photos || EMPTY_LIST;
  const collectedTextItems = sessionState?.collected_text_items || EMPTY_LIST;
  const currentRoundItemsById = useMemo(
    () => new Map(currentRoundItems.map((item) => [item.id, item])),
    [currentRoundItems],
  );
  const collectedItems = useMemo(
    () => collectedPhotoIds.map((photoId, index) => {
      const currentRoundItem = currentRoundItemsById.get(photoId);
      const manifestItem = selectedAssetItemsById.get(photoId);
      const textLabel = photoId.startsWith('text_find_') ? collectedTextItems[index] : '';
      return {
        id: photoId,
        label: currentRoundItem?.label || manifestItem?.label || textLabel || photoId.replaceAll('_', ' '),
        image: currentRoundItem?.image || manifestItem?.image || manifestItem?.src || '',
        src: currentRoundItem?.image || manifestItem?.image || manifestItem?.src || '',
      };
    }),
    [collectedPhotoIds, collectedTextItems, currentRoundItemsById, selectedAssetItemsById],
  );
  const currentRoundHasCollectedItem = currentRoundItems.some(
    (item) => collectedPhotoIds.includes(item.id),
  );
  const currentRoundCollectedIndex = currentRoundItems.findIndex(
    (item) => collectedPhotoIds.includes(item.id),
  );
  const showCat5Selection = sessionActive
    && !sessionFinished
    && activeTemplateType === 'cat5'
    && currentStep.startsWith('STEP_3_COLLECT_')
    && sessionState?.collection_phase !== 'detail'
    && currentRoundItems.length > 0
    && !currentRoundHasCollectedItem;
  const showCat5Items = sessionActive
    && !sessionFinished
    && activeTemplateType === 'cat5'
    && currentStep.startsWith('STEP_3_COLLECT_')
    && currentRoundItems.length > 0;
  const showCat5CollectedItems = sessionActive
    && activeTemplateType === 'cat5'
    && (currentStep === 'STEP_4_SYNTHESIS' || currentStep.includes('CELEBRATE'))
    && collectedItems.length > 0;
  const showCat3Build = sessionActive
    && !sessionFinished
    && activeTemplateType === 'cat3'
    && currentStep.startsWith('STEP_3_BUILD_');
  const cat3Options = useMemo(() => [
    { label: 'Done', value: 'done' },
    { label: 'Help', value: 'help' },
  ], []);
  const inputDisabled = !sessionId || loading || turnPending || sessionFinished || showCat5Selection || showCat3Build;
  const activeCat5ItemIndex = currentRoundItems.length
    ? Math.min(cat5ItemIndex, currentRoundItems.length - 1)
    : 0;
  const displayedCat5ItemIndex = currentRoundCollectedIndex >= 0
    ? currentRoundCollectedIndex
    : activeCat5ItemIndex;
  const collectedSummaryIndex = collectedItems.length > 1 ? 1 : 0;
  const screenLayout = showCat5Items
    ? collectionScreenLayout(
      baseScreenLayout,
      currentRoundItems,
      displayedCat5ItemIndex,
      showCat5Selection ? 'device-scroll' : 'none',
    )
    : showCat5CollectedItems
      ? collectionScreenLayout(baseScreenLayout, collectedItems, collectedSummaryIndex, 'none')
      : baseScreenLayout;
  const lensInteraction = showCat3Build ? {
    type: 'cat3-build',
    options: cat3Options,
    selectedIndex: cat3OptionIndex,
    disabled: loading || turnPending,
  } : null;
  const progress = {
    current: sessionState?.current_round || 0,
    total: sessionState?.total_rounds || 3,
  };

  useEffect(() => {
    setCat3OptionIndex(0);
  }, [currentStep]);

  useEffect(() => {
    setCat5ItemIndex(0);
  }, [currentStep, currentRoundItems.length]);

  const handleStart = useCallback(async () => {
    if (!selectedActivity) return;
    await startActivity(selectedActivity.id, selectedActivity.tier || 'T1');
  }, [selectedActivity, startActivity]);

  const selectRelativeActivity = useCallback((offset) => {
    if (!activities.length || sessionActive) return;
    const currentIndex = activities.findIndex((activity) => activity.id === selectedActivity?.id);
    const baseIndex = currentIndex === -1 ? 0 : currentIndex;
    const nextIndex = (baseIndex + offset + activities.length) % activities.length;
    setSelectedId(activities[nextIndex].id);
  }, [activities, selectedActivity?.id, sessionActive]);

  const selectCat3Option = useCallback((offset) => {
    setCat3OptionIndex((index) => (index + offset + cat3Options.length) % cat3Options.length);
  }, [cat3Options.length]);

  const selectCat5Item = useCallback((offset) => {
    if (!currentRoundItems.length) return;
    setCat5ItemIndex((index) => (index + offset + currentRoundItems.length) % currentRoundItems.length);
  }, [currentRoundItems.length]);

  const confirmCat3Option = useCallback(async () => {
    const option = cat3Options[cat3OptionIndex] || cat3Options[0];
    if (!option || loading || turnPending) return;
    await sendMessage(option.value);
  }, [cat3OptionIndex, cat3Options, loading, sendMessage, turnPending]);

  const confirmCat5Item = useCallback(async () => {
    const item = currentRoundItems[activeCat5ItemIndex] || currentRoundItems[0];
    if (!item || loading || turnPending) return;
    await sendCollectionItem(item.id, item.label);
  }, [activeCat5ItemIndex, currentRoundItems, loading, sendCollectionItem, turnPending]);

  const isDeviceOptionMode = showCat3Build || showCat5Selection;
  const sessionStatus = sessionFinished ? 'completed' : sessionActive ? 'active' : 'ready';
  const handleScrollPrevious = showCat3Build
    ? () => selectCat3Option(-1)
    : showCat5Selection
      ? () => selectCat5Item(-1)
      : () => selectRelativeActivity(-1);
  const handleScrollNext = showCat3Build
    ? () => selectCat3Option(1)
    : showCat5Selection
      ? () => selectCat5Item(1)
      : () => selectRelativeActivity(1);
  const handlePrimaryAction = showCat3Build
    ? confirmCat3Option
    : showCat5Selection
      ? confirmCat5Item
      : handleStart;

  return (
    <main className="activity-game">
      <header className="activity-game__topbar">
        <h1>WonderLens Prototype</h1>
        <div className="activity-game__tester">
          <span>Tester Mode</span>
          <span className="activity-game__tester-dot" aria-hidden="true" />
          <span className="activity-game__tester-avatar" aria-label="Tester profile">TS</span>
        </div>
      </header>

      <section className="activity-game__stage" aria-label="Activity chooser and device preview">
        <ActivityLibrary
          activities={activities}
          selectedId={selectedActivity?.id || ''}
          assetByActivityId={assetByActivityId}
          loading={loading || catalogLoading}
          selectionLocked={sessionActive}
          sessionActive={sessionActive}
          onSelect={(nextId) => {
            if (!sessionActive) setSelectedId(nextId);
          }}
          onExit={reset}
        />

        <section className="activity-game__device" aria-label="WonderLens device">
          <div className="activity-game__section-head">
            <div className="activity-game__preview-title">
              <h2>Device Preview</h2>
              <h3>{selectedActivity?.name || 'Choose an activity'}</h3>
            </div>
            {selectedAsset?.icon ? (
              <img
                className="activity-game__preview-icon"
                src={selectedAsset.icon}
                alt={`${selectedActivity?.name || 'Selected activity'} icon`}
              />
            ) : null}
          </div>
          <WonderLensDevice
            activity={selectedActivity}
            sessionState={sessionState}
            assetSrc={assetSrc}
            screenLayout={screenLayout}
            progress={progress}
            isWaiting={loading || turnPending}
            interaction={lensInteraction}
            selectionLocked={sessionActive}
            scrollDisabled={sessionActive && !isDeviceOptionMode}
            scrollPreviousLabel={isDeviceOptionMode ? 'Previous device option' : 'Previous activity'}
            scrollNextLabel={isDeviceOptionMode ? 'Next device option' : 'Next activity'}
            scrollControlLabel={isDeviceOptionMode ? 'Pick' : 'Pick'}
            primaryLabel={isDeviceOptionMode ? 'Select' : 'Start'}
            primaryAriaLabel={isDeviceOptionMode ? 'Confirm selected device option' : 'Start activity'}
            primaryDisabled={isDeviceOptionMode ? loading || turnPending : sessionActive || loading || catalogLoading}
            onScrollPrevious={handleScrollPrevious}
            onScrollNext={handleScrollNext}
            onPrimaryAction={handlePrimaryAction}
          />
        </section>
      </section>

      <dl className="activity-game__metrics" aria-label="Session metrics">
        <div>
          <dt>Model</dt>
          <dd>Live backend</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{sessionStatus}</dd>
        </div>
        <div>
          <dt>Rounds</dt>
          <dd>{progress.current}/{progress.total}</dd>
        </div>
      </dl>

      {catalogError || error ? (
        <div className="activity-game__error" role="alert">
          {catalogError || error}
        </div>
      ) : null}

      <section className="activity-game__transcript-panel" aria-label="Activity text game">
        <ActivityTranscript messages={messages} loading={loading} turnPending={turnPending} />
        <ActivityTextInput disabled={inputDisabled} finished={sessionFinished} onSend={sendMessage} />
      </section>
    </main>
  );
}
