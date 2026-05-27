function ProgressDots({ current = 0, total = 3 }) {
  return (
    <div className="activity-lens__dots" aria-label={`Progress ${current} of ${total}`}>
      {Array.from({ length: total }, (_, index) => {
        const active = index < current;
        return <span key={index} className={active ? 'activity-lens__dot is-active' : 'activity-lens__dot'} />;
      })}
    </div>
  );
}

export default function ActivityLens({
  activity,
  latestAiText = '',
  sessionState,
  assetSrc = '',
  savedTokens = [],
  progress,
}) {
  const activityName = activity?.name || activity?.fallback_label || 'Activity';
  const mechanic = activity?.mechanic || '';
  const total = progress?.total || sessionState?.total_rounds || 3;
  const current = progress?.current ?? sessionState?.current_round ?? 0;
  const visibleTokens = savedTokens.slice(-3);
  const textDensity = latestAiText.length > 180
    ? 'is-dense'
    : latestAiText.length > 100
      ? 'is-compact'
      : '';

  return (
    <div className="activity-lens">
      <div className="activity-lens__media">
        {assetSrc ? (
          <img src={assetSrc} alt={`${activityName} visual`} />
        ) : (
          <div className="activity-lens__asset-fallback" aria-hidden="true" />
        )}
      </div>

      <div className="activity-lens__copy">
        <div className="activity-lens__meta">
          <p className="activity-lens__name">{activityName}</p>
          {mechanic ? <span className="activity-lens__mechanic">{mechanic}</span> : null}
        </div>
        <ProgressDots current={current} total={total} />
        {latestAiText ? <p className={`activity-lens__text ${textDensity}`.trim()}>{latestAiText}</p> : null}
        {visibleTokens.length ? (
          <div className="activity-lens__tokens" aria-label="Saved child text">
            {visibleTokens.map((token, index) => (
              <span key={`${token}-${index}`}>{token}</span>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
