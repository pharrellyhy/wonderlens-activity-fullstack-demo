import ActivityLens from './ActivityLens.jsx';

export default function WonderLensDevice({
  activity,
  latestAiText = '',
  sessionState = null,
  assetSrc = '',
  savedTokens = [],
  progress = null,
  onScrollNext,
  onPrimaryAction,
}) {
  return (
    <div className="wonderlens-device-shell">
      <div className="wonderlens-device" data-testid="wonderlens-device">
        <div className="wonderlens-device__left-grip" aria-hidden="true" />

        <button
          type="button"
          className="wonderlens-device__scroll"
          aria-label="Scroll activity lens"
          onClick={onScrollNext}
        >
          <span aria-hidden="true" />
        </button>

        <div className="wonderlens-device__lens">
          <ActivityLens
            activity={activity}
            latestAiText={latestAiText}
            sessionState={sessionState}
            assetSrc={assetSrc}
            savedTokens={savedTokens}
            progress={progress}
          />
        </div>

        <div className="wonderlens-device__small-button" aria-hidden="true" />

        <button
          type="button"
          className="wonderlens-device__primary"
          aria-label="Start or restart activity"
          onClick={onPrimaryAction}
        />
      </div>
    </div>
  );
}
