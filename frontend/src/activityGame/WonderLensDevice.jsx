import ActivityLens from './ActivityLens.jsx';

export default function WonderLensDevice({
  activity,
  sessionState = null,
  assetSrc = '',
  screenLayout = null,
  progress = null,
  isWaiting = false,
  interaction = null,
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
            interaction={interaction}
          />
        </div>

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
