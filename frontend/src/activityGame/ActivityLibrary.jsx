export default function ActivityLibrary({
  activities,
  selectedId,
  assetByActivityId,
  loading,
  onSelect,
  onStart,
}) {
  return (
    <aside className="activity-game__library" aria-label="Activity library">
      <div className="activity-game__section-head">
        <h1>Activity library</h1>
        <span>{activities.length} activities</span>
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
            >
              {asset?.icon ? (
                <img className="activity-card__icon" src={asset.icon} alt={`${activity.name} icon`} />
              ) : null}
              <span className="activity-card__title">{activity.name}</span>
              <span className="activity-card__meta">
                {activity.mechanic} · {activity.tier}
              </span>
              <span className="activity-card__premise">{activity.premise}</span>
            </button>
          );
        })}
      </div>

      <button
        type="button"
        className="activity-game__start"
        onClick={onStart}
        disabled={loading || !selectedId}
      >
        Start activity
      </button>
    </aside>
  );
}
