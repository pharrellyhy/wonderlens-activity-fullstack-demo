export default function ActivityLibrary({
  activities,
  selectedId,
  assetByActivityId,
  loading,
  selectionLocked = false,
  sessionActive = false,
  onSelect,
  onExit,
}) {
  return (
    <aside className="activity-game__library" aria-label="Activity library">
      <div className="activity-game__section-head">
        <h1>Activities</h1>
        <span className="activity-game__library-add" aria-hidden="true">+</span>
      </div>

      <div className="activity-game__list">
        {activities.map((activity) => {
          const selected = activity.id === selectedId;
          const asset = assetByActivityId?.get(activity.asset_manifest_id) || assetByActivityId?.get(activity.id);
          return (
            <button
              type="button"
              key={activity.id}
              className={selected ? 'activity-card is-selected' : 'activity-card'}
              onClick={() => onSelect(activity.id)}
              aria-pressed={selected}
              disabled={selectionLocked}
            >
              {asset?.icon ? (
                <img className="activity-card__icon" src={asset.icon} alt={`${activity.name} icon`} />
              ) : null}
              <span className="activity-card__title">{activity.name}</span>
              <span className="activity-card__meta">
                {activity.mechanic} · {activity.tier}
              </span>
              {selected ? <span className="activity-card__status" aria-hidden="true" /> : null}
            </button>
          );
        })}
      </div>

      {sessionActive ? (
        <button type="button" className="activity-game__exit" onClick={onExit} disabled={loading}>
          Exit activity
        </button>
      ) : null}
    </aside>
  );
}
