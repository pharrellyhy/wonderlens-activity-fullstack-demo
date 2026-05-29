import { asset } from '../utils/basePath';

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

function Cat3BuildPanel({ interaction }) {
  const selectedIndex = interaction.selectedIndex || 0;
  const options = interaction.options || [];

  return (
    <div
      className="activity-lens__interaction activity-lens__build-panel"
      role="listbox"
      aria-label="Build response options"
      aria-disabled={interaction.disabled ? 'true' : 'false'}
    >
      {options.map((option, index) => (
        <span
          key={option.value}
          className={index === selectedIndex ? 'activity-lens__build-option is-selected' : 'activity-lens__build-option'}
          role="option"
          aria-selected={index === selectedIndex ? 'true' : 'false'}
        >
          {option.label}
        </span>
      ))}
    </div>
  );
}

function ActivityScreenLayout({ activityName, assetSrc, screenLayout }) {
  const layout = screenLayout || {
    mode: 'single',
    background: { src: assetSrc, fit: 'cover' },
    items: [],
  };
  const backgroundSrc = layout.background?.src || assetSrc;
  const backgroundFit = layout.background?.fit || 'cover';
  const items = Array.isArray(layout.items) ? layout.items : [];

  return (
    <div className={`activity-screen-layout activity-screen-layout--${layout.mode || 'single'}`}>
      {backgroundSrc ? (
        <img
          key={backgroundSrc}
          className={`activity-screen-layout__background activity-screen-layout__background--${backgroundFit}`}
          src={asset(backgroundSrc)}
          alt={`${activityName} visual`}
        />
      ) : (
        <div className="activity-lens__asset-fallback" aria-hidden="true" />
      )}

      {items.length > 0 ? (
        <div className="activity-screen-layout__items" aria-hidden="true">
          {items.map((item) => (
            <div
              key={item.id}
              className={[
                'activity-screen-layout__item',
                `activity-screen-layout__item--${item.shape || 'circle'}`,
                item.selected ? 'is-selected' : '',
              ].filter(Boolean).join(' ')}
            >
              {item.src ? (
                <img src={asset(item.src)} alt="" aria-hidden="true" />
              ) : null}
              {item.label ? <span>{item.label}</span> : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export default function ActivityLens({
  activity,
  sessionState,
  assetSrc = '',
  screenLayout = null,
  progress,
  isWaiting = false,
  interaction = null,
}) {
  const activityName = activity?.name || activity?.fallback_label || 'Activity';
  const total = progress?.total || sessionState?.total_rounds || 3;
  const current = progress?.current ?? sessionState?.current_round ?? 0;

  return (
    <div className="activity-lens">
      <div className="activity-lens__media">
        <ActivityScreenLayout activityName={activityName} assetSrc={assetSrc} screenLayout={screenLayout} />
      </div>

      {interaction?.type === 'cat3-build' ? (
        <Cat3BuildPanel interaction={interaction} />
      ) : null}

      <div className="activity-lens__copy">
        <ProgressDots current={current} total={total} />
        {isWaiting ? (
          <div className="activity-lens__waiting" role="status" aria-live="polite" aria-label="WonderLens is thinking">
            <span aria-hidden="true" />
            <span>Thinking</span>
          </div>
        ) : null}
      </div>
    </div>
  );
}
