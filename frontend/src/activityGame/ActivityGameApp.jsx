import { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchActivities, fetchActivityAssetManifest } from '../utils/api';
import { assetForBeat, beatIdFromSessionState } from './activityAssets';
import ActivityLibrary from './ActivityLibrary.jsx';
import ActivityTextInput from './ActivityTextInput.jsx';
import ActivityTranscript from './ActivityTranscript.jsx';
import useActivityTextSession from './useActivityTextSession.js';
import WonderLensDevice from './WonderLensDevice.jsx';

function latestAiText(messages) {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    if (messages[index].role === 'ai') return messages[index].text;
  }
  return '';
}

function childTokens(messages) {
  return messages
    .filter((message) => message.role === 'child' && message.text)
    .map((message) => message.text);
}

export default function ActivityGameApp() {
  const [activities, setActivities] = useState([]);
  const [assetManifest, setAssetManifest] = useState({ activities: [] });
  const [selectedId, setSelectedId] = useState('');
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState('');
  const {
    messages,
    sessionId,
    sessionState,
    loading,
    turnPending,
    error,
    startActivity,
    sendMessage,
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

  const beatId = beatIdFromSessionState(sessionState);
  const assetSrc = selectedAsset ? assetForBeat(selectedAsset, beatId) : '';
  const savedTokens = childTokens(messages);
  const progress = {
    current: sessionState?.current_round || 0,
    total: sessionState?.total_rounds || 3,
  };

  const handleStart = useCallback(async () => {
    if (!selectedActivity) return;
    await startActivity(selectedActivity.id, selectedActivity.tier || 'T1');
  }, [selectedActivity, startActivity]);

  const selectRelativeActivity = useCallback((offset) => {
    if (!activities.length) return;
    const currentIndex = activities.findIndex((activity) => activity.id === selectedActivity?.id);
    const baseIndex = currentIndex === -1 ? 0 : currentIndex;
    const nextIndex = (baseIndex + offset + activities.length) % activities.length;
    setSelectedId(activities[nextIndex].id);
  }, [activities, selectedActivity?.id]);

  return (
    <main className="activity-game">
      <ActivityLibrary
        activities={activities}
        selectedId={selectedActivity?.id || ''}
        assetByActivityId={assetByActivityId}
        loading={loading || catalogLoading}
        onSelect={setSelectedId}
        onStart={handleStart}
      />

      <section className="activity-game__work" aria-label="Activity text game">
        <div className="activity-game__status">
          <div className="activity-game__status-main">
            {selectedAsset?.icon ? (
              <img
                className="activity-game__status-icon"
                src={selectedAsset.icon}
                alt={`${selectedActivity?.name || 'Selected activity'} icon`}
              />
            ) : null}
            <div>
              <p>{sessionId ? 'Session active' : 'Text only'}</p>
              <h2>{selectedActivity?.name || 'Choose an activity'}</h2>
            </div>
          </div>
          {selectedActivity?.core_ib_key_concepts?.length ? (
            <span>Core IB Key Concepts: {selectedActivity.core_ib_key_concepts.join(', ')}</span>
          ) : null}
        </div>

        {catalogError || error ? (
          <div className="activity-game__error" role="alert">
            {catalogError || error}
          </div>
        ) : null}

        <ActivityTranscript messages={messages} loading={loading} turnPending={turnPending} />
        <ActivityTextInput disabled={!sessionId || loading || turnPending} onSend={sendMessage} />
      </section>

      <section className="activity-game__device" aria-label="WonderLens device">
        <WonderLensDevice
          activity={selectedActivity}
          latestAiText={latestAiText(messages)}
          sessionState={sessionState}
          assetSrc={assetSrc}
          savedTokens={savedTokens}
          progress={progress}
          onScrollPrevious={() => selectRelativeActivity(-1)}
          onScrollNext={() => selectRelativeActivity(1)}
          onPrimaryAction={handleStart}
        />
      </section>
    </main>
  );
}
