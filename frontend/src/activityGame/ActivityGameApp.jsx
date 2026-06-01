import { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchActivities, fetchActivityAssetManifest } from '../utils/api';
import { assetForBeat, beatIdFromSessionState, screenLayoutForBeat } from './activityAssets';
import ActivityLibrary from './ActivityLibrary.jsx';
import ActivityTextInput from './ActivityTextInput.jsx';
import ActivityTranscript from './ActivityTranscript.jsx';
import CrownPicker from './CrownPicker.jsx';
import useActivityTextSession from './useActivityTextSession.js';
import WonderLensDevice from './WonderLensDevice.jsx';

const EMPTY_LIST = [];
const DEFAULT_GRID_SIZE = 1;
const MIN_GRID_SIZE = 0.88;
const MAX_GRID_SIZE = 1.5;

// Cat1 activities whose round screens present concrete pickable options: the
// device scroll highlights an option card and the green select button sends
// its label as the turn. The backend treats the label as a normal text turn,
// so the directive speaker still drives the conversation.
const CAT1_CHOICE_SELECT_ACTIVITY_IDS = new Set([
  'activity_recognition_pop_challenge',
  'activity_vegetable_sort',
  'activity_animal_sound_imitation',
]);

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
  const [cat1ChoiceIndex, setCat1ChoiceIndex] = useState(0);
  const [gridSize, setGridSize] = useState(DEFAULT_GRID_SIZE);
  const {
    messages,
    sessionId,
    sessionState,
    loading,
    turnPending,
    error,
    templateType,
    screenFrame,
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

  const beatId = beatIdFromSessionState(sessionState, screenFrame);
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
  const cat1ChoiceItems = baseScreenLayout?.items || EMPTY_LIST;
  const showCat1Choice = sessionActive
    && !sessionFinished
    && activeTemplateType === 'cat1'
    && currentStep.startsWith('STEP_3_ROUND_')
    && CAT1_CHOICE_SELECT_ACTIVITY_IDS.has(selectedActivity?.id)
    && cat1ChoiceItems.length > 0;
  const activeCat1ChoiceIndex = cat1ChoiceItems.length
    ? Math.min(cat1ChoiceIndex, cat1ChoiceItems.length - 1)
    : 0;
  const cat3Options = useMemo(() => [
    { label: 'Done', value: 'done' },
    { label: 'Help', value: 'help' },
  ], []);
  const inputDisabled = !sessionId || loading || turnPending || sessionFinished
    || showCat5Selection || showCat3Build || showCat1Choice;
  const activeCat5ItemIndex = currentRoundItems.length
    ? Math.min(cat5ItemIndex, currentRoundItems.length - 1)
    : 0;
  const displayedCat5ItemIndex = currentRoundCollectedIndex >= 0
    ? currentRoundCollectedIndex
    : activeCat5ItemIndex;
  const collectedSummaryIndex = collectedItems.length > 1 ? 1 : 0;
  const screenLayout = showCat1Choice
    ? {
      ...baseScreenLayout,
      selection: 'device-scroll',
      items: cat1ChoiceItems.map((item, index) => ({ ...item, selected: index === activeCat1ChoiceIndex })),
    }
    : showCat5Items
      ? collectionScreenLayout(
        baseScreenLayout,
        currentRoundItems,
        displayedCat5ItemIndex,
        showCat5Selection ? 'device-scroll' : 'none',
      )
      : showCat5CollectedItems
        ? collectionScreenLayout(baseScreenLayout, collectedItems, collectedSummaryIndex, 'none')
        : baseScreenLayout;
  const progress = {
    current: sessionState?.current_round || 0,
    total: sessionState?.total_rounds || 3,
  };

  useEffect(() => {
    setCat3OptionIndex(0);
    setCat1ChoiceIndex(0);
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

  const confirmCat5Item = useCallback(async (itemIndex = activeCat5ItemIndex) => {
    const item = currentRoundItems[itemIndex] || currentRoundItems[0];
    if (!item || loading || turnPending) return;
    await sendCollectionItem(item.id, item.label);
  }, [activeCat5ItemIndex, currentRoundItems, loading, sendCollectionItem, turnPending]);

  const selectCat1Choice = useCallback((offset) => {
    if (!cat1ChoiceItems.length) return;
    setCat1ChoiceIndex((index) => (index + offset + cat1ChoiceItems.length) % cat1ChoiceItems.length);
  }, [cat1ChoiceItems.length]);

  const confirmCat1Choice = useCallback(async (itemIndex = activeCat1ChoiceIndex) => {
    const item = cat1ChoiceItems[itemIndex] || cat1ChoiceItems[0];
    if (!item || loading || turnPending) return;
    await sendMessage(item.label || item.id, { isSelection: true });
  }, [activeCat1ChoiceIndex, cat1ChoiceItems, loading, sendMessage, turnPending]);

  const isDeviceOptionMode = showCat3Build || showCat5Selection || showCat1Choice;
  const sessionStatus = sessionFinished ? 'completed' : sessionActive ? 'active' : 'ready';

  const libraryItems = useMemo(
    () => activities.map((activity) => ({ id: activity.id, label: activity.name })),
    [activities],
  );
  const libraryIndex = Math.max(0, activities.findIndex((activity) => activity.id === selectedActivity?.id));

  const crownItems = showCat3Build
    ? cat3Options.map((option) => ({ id: option.value, label: option.label }))
    : showCat5Selection
      ? currentRoundItems.map((item) => ({ id: item.id, label: item.label, image: item.image }))
      : showCat1Choice
        ? cat1ChoiceItems.map((item) => ({ id: item.id, label: item.label, image: item.src }))
        : libraryItems;
  const crownIndex = showCat3Build
    ? cat3OptionIndex
    : showCat5Selection
      ? activeCat5ItemIndex
      : showCat1Choice
        ? activeCat1ChoiceIndex
        : libraryIndex;
  const crownDisabled = isDeviceOptionMode
    ? loading || turnPending
    : sessionActive || loading || catalogLoading;
  const crownStep = useCallback((direction) => {
    if (showCat3Build) selectCat3Option(direction);
    else if (showCat5Selection) selectCat5Item(direction);
    else if (showCat1Choice) selectCat1Choice(direction);
    else selectRelativeActivity(direction);
  }, [selectCat3Option, selectCat5Item, selectCat1Choice, selectRelativeActivity, showCat3Build, showCat5Selection, showCat1Choice]);
  const crownConfirm = useCallback((focusedIndex) => {
    if (showCat3Build) void confirmCat3Option();
    else if (showCat5Selection) void confirmCat5Item(focusedIndex);
    else if (showCat1Choice) void confirmCat1Choice(focusedIndex);
    else void handleStart();
  }, [confirmCat3Option, confirmCat5Item, confirmCat1Choice, handleStart, showCat3Build, showCat5Selection, showCat1Choice]);
  const lensInteraction = showCat3Build
    ? {
      type: 'cat3-build',
      selectedIndex: cat3OptionIndex,
      options: cat3Options,
      disabled: loading || turnPending,
      onStep: selectCat3Option,
      onConfirm: crownConfirm,
    }
    : null;

  const handleScrollPrevious = useCallback(() => crownStep(-1), [crownStep]);
  const handleScrollNext = useCallback(() => crownStep(1), [crownStep]);
  const handlePrimaryAction = useCallback(() => crownConfirm(crownIndex), [crownConfirm, crownIndex]);
  const handleGridSizeChange = useCallback((event) => {
    setGridSize(Number(event.target.value));
  }, []);
  const gridSizePercent = Math.round(gridSize * 100);
  const activityGameStyle = useMemo(() => ({
    '--activity-game-size': gridSize.toFixed(2),
  }), [gridSize]);

  // The crown is a watch-style wheel; when a device-option picker is showing
  // (Cat3 Done/Help, Cat5 item selection) let the keyboard up/down arrows drive
  // it even when the small in-lens listbox is not focused. Skip when the user is
  // typing in the transcript input or already inside the crown listbox, which
  // owns its own arrow handling.
  useEffect(() => {
    if (!isDeviceOptionMode) return undefined;
    const handleDeviceArrowKeys = (event) => {
      if (event.defaultPrevented || (event.key !== 'ArrowUp' && event.key !== 'ArrowDown')) return;
      if (event.target?.closest?.('input, textarea, [contenteditable="true"], .crown-picker')) return;
      event.preventDefault();
      crownStep(event.key === 'ArrowUp' ? -1 : 1);
    };
    window.addEventListener('keydown', handleDeviceArrowKeys);
    return () => window.removeEventListener('keydown', handleDeviceArrowKeys);
  }, [isDeviceOptionMode, crownStep]);

  return (
    <div className="activity-game-shell" style={activityGameStyle}>
      <div className="activity-game__grid-toolbar" aria-label="Layout controls">
        <label className="activity-game__grid-size">
          <span>Grid</span>
          <input
            type="range"
            min={MIN_GRID_SIZE}
            max={MAX_GRID_SIZE}
            step="0.02"
            value={gridSize}
            aria-label="Activity game grid size"
            onChange={handleGridSizeChange}
          />
          <output>{gridSizePercent}%</output>
        </label>
      </div>

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
            crown={showCat3Build ? null : {
              items: crownItems,
              index: crownIndex,
              onStep: crownStep,
              onConfirm: crownConfirm,
              disabled: crownDisabled,
              confirmLabel: isDeviceOptionMode ? 'Select' : 'Start',
              // Cat3 uses a visible in-lens Done/Help strip. Cat5, Cat1, and
              // the library already have visible choices elsewhere, so their
              // crown picker remains keyboard-only.
              showList: false,
            }}
            progress={progress}
            isWaiting={loading || turnPending}
            interaction={lensInteraction}
            selectionLocked={sessionActive}
            scrollDisabled={sessionActive && !isDeviceOptionMode}
            scrollPreviousLabel={isDeviceOptionMode ? 'Previous device option' : 'Previous activity'}
            scrollNextLabel={isDeviceOptionMode ? 'Next device option' : 'Next activity'}
            scrollControlLabel="Pick"
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
        <ActivityTranscript
          messages={messages}
          loading={loading}
          turnPending={turnPending}
          introActivity={sessionActive ? null : selectedActivity}
          introIconSrc={selectedAsset?.icon || ''}
          introRoundCount={(selectedAsset?.beats || []).filter((beat) => beat.id.startsWith('round_')).length || 3}
        />
        <ActivityTextInput disabled={inputDisabled} finished={sessionFinished} onSend={sendMessage} />
      </section>
    </main>
    </div>
  );
}
