export default function ActivityLibrary({
  activities,
  selectedId,
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
          return (
            <button
              type="button"
              key={activity.id}
              className={selected ? 'activity-card is-selected' : 'activity-card'}
              onClick={() => onSelect(activity.id)}
              aria-pressed={selected}
            >
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
