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
      className="activity-lens__interaction activity-lens__build-panel activity-lens__build-panel--compact"
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

function pickerItemClass(index, selectedIndex, total) {
  if (total <= 0) return '';
  if (index === selectedIndex) return 'is-current';
  const previousIndex = (selectedIndex - 1 + total) % total;
  const nextIndex = (selectedIndex + 1) % total;
  if (index === previousIndex) return 'is-adjacent is-previous';
  if (index === nextIndex) return 'is-adjacent is-next';
  return 'is-offscreen';
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
  const selectedIndex = Math.max(0, items.findIndex((item) => item.selected));

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
          {items.map((item, index) => (
            <div
              key={item.id}
              className={[
                'activity-screen-layout__item',
                `activity-screen-layout__item--${item.shape || 'circle'}`,
                item.selected ? 'is-selected' : '',
                layout.mode === 'picker' ? pickerItemClass(index, selectedIndex, items.length) : '',
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

      {layout.mode === 'singleText' && layout.text ? (
        <p className="activity-screen-layout__text">{layout.text}</p>
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
