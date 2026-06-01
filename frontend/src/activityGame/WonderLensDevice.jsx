import ActivityLens from './ActivityLens.jsx';

function DeviceOptionRail({ optionRail }) {
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
      className="wonderlens-device__option-rail"
      role="listbox"
      aria-label={optionRail.label || 'Device response options'}
      aria-disabled={disabled ? 'true' : 'false'}
      tabIndex={disabled ? -1 : 0}
      onKeyDown={handleKeyDown}
    >
      {options.map((option, index) => (
        <span
          key={option.value || option.id || index}
          className={index === selectedIndex ? 'wonderlens-device__option is-selected' : 'wonderlens-device__option'}
          role="option"
          aria-selected={index === selectedIndex ? 'true' : 'false'}
        >
          {option.label}
        </span>
      ))}
    </div>
  );
}

export default function WonderLensDevice({
  activity,
  sessionState = null,
  assetSrc = '',
  screenLayout = null,
  progress = null,
  isWaiting = false,
  crown = null,
  optionRail = null,
  selectionLocked = false,
  scrollDisabled = selectionLocked,
  scrollPreviousLabel = 'Previous activity',
  scrollNextLabel = 'Next activity',
  scrollControlLabel = 'Pick',
  primaryLabel = 'Start',
  primaryAriaLabel = 'Start or restart activity',
  primaryDisabled = false,
  onScrollPrevious,
  onScrollNext,
  onPrimaryAction,
}) {
  return (
    <div className="wonderlens-device-shell">
      <div className="wonderlens-device" data-testid="wonderlens-device">
        <div className="wonderlens-device__left-grip" aria-hidden="true" />

        <div className="wonderlens-device__scroll" role="group" aria-label="Scroll activity lens">
          <button
            type="button"
            className="wonderlens-device__scroll-hit wonderlens-device__scroll-hit--up"
            aria-label={scrollPreviousLabel}
            disabled={scrollDisabled}
            onClick={onScrollPrevious}
          />
          <button
            type="button"
            className="wonderlens-device__scroll-hit wonderlens-device__scroll-hit--down"
            aria-label={scrollNextLabel}
            disabled={scrollDisabled}
            onClick={onScrollNext}
          />
          <span className="wonderlens-device__scroll-arc" aria-hidden="true" />
          <span className="wonderlens-device__control-label wonderlens-device__control-label--scroll" aria-hidden="true">
            {scrollControlLabel}
          </span>
        </div>

        <div className="wonderlens-device__lens">
          <ActivityLens
            activity={activity}
            sessionState={sessionState}
            assetSrc={assetSrc}
            screenLayout={screenLayout}
            progress={progress}
            isWaiting={isWaiting}
            crown={crown}
          />
        </div>

        <DeviceOptionRail optionRail={optionRail} />

        <div className="wonderlens-device__small-button" aria-hidden="true" />

        <button
          type="button"
          className="wonderlens-device__primary"
          aria-label={primaryAriaLabel}
          disabled={primaryDisabled}
          onClick={onPrimaryAction}
        >
          <span className="wonderlens-device__primary-arrow" aria-hidden="true" />
        </button>
        <span className="wonderlens-device__control-label wonderlens-device__control-label--primary" aria-hidden="true">
          {primaryLabel}
        </span>
      </div>
    </div>
  );
}
