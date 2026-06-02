import { asset } from '../utils/basePath';
import CrownPicker from './CrownPicker.jsx';

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

function LensOptionRail({ optionRail }) {
  if (!optionRail) return null;

  const selectedIndex = optionRail.selectedIndex || 0;
  const options = optionRail.options || [];
  const disabled = Boolean(optionRail.disabled);

  const handleKeyDown = (event) => {
    if (disabled) return;
    if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
      event.preventDefault();
      optionRail.onStep?.(1);
    } else if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
      event.preventDefault();
      optionRail.onStep?.(-1);
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      optionRail.onConfirm?.(selectedIndex);
    }
  };

  return (
    <div
      className="activity-lens__option-rail"
      role="listbox"
      aria-label={optionRail.label || 'Lens response options'}
      aria-disabled={disabled ? 'true' : 'false'}
      tabIndex={disabled ? -1 : 0}
      onKeyDown={handleKeyDown}
    >
      {options.map((option, index) => (
        <span
          key={option.value || option.id || index}
          className={index === selectedIndex ? 'activity-lens__option is-selected' : 'activity-lens__option'}
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

function pickerOrientationClass(layout) {
  if (layout.mode !== 'picker') return '';
  return layout.pickerOrientation === 'horizontal'
    ? 'activity-screen-layout--picker-horizontal'
    : 'activity-screen-layout--picker-vertical';
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
  const className = [
    'activity-screen-layout',
    `activity-screen-layout--${layout.mode || 'single'}`,
    pickerOrientationClass(layout),
    layout.hideLabels ? 'activity-screen-layout--hide-labels' : '',
    layout.transparentItems ? 'activity-screen-layout--transparent-items' : '',
  ].filter(Boolean).join(' ');

  return (
    <div className={className}>
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
              {item.label && !layout.hideLabels ? <span>{item.label}</span> : null}
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
  crown = null,
  optionRail = null,
}) {
  const activityName = activity?.name || activity?.fallback_label || 'Activity';
  const total = progress?.total || sessionState?.total_rounds || 3;
  const current = progress?.current ?? sessionState?.current_round ?? 0;

  return (
    <div className="activity-lens">
      <div className="activity-lens__media">
        <ActivityScreenLayout activityName={activityName} assetSrc={assetSrc} screenLayout={screenLayout} />
      </div>

      {crown ? (
        <div className={`activity-lens__crown${crown.showList ? '' : ' activity-lens__crown--headless'}`}>
          <CrownPicker
            items={crown.items}
            index={crown.index}
            onStep={crown.onStep}
            onConfirm={crown.onConfirm}
            disabled={crown.disabled}
            confirmLabel={crown.confirmLabel}
          />
        </div>
      ) : null}

      <LensOptionRail optionRail={optionRail} />

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
