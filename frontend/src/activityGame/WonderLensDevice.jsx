import ActivityLens from './ActivityLens.jsx';

export default function WonderLensDevice({
  activity,
  latestAiText = '',
  sessionState = null,
  assetSrc = '',
  savedTokens = [],
  progress = null,
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
            aria-label="Previous activity"
            onClick={onScrollPrevious}
          />
          <button
            type="button"
            className="wonderlens-device__scroll-hit wonderlens-device__scroll-hit--down"
            aria-label="Next activity"
            onClick={onScrollNext}
          />
          <span className="wonderlens-device__scroll-arc" aria-hidden="true" />
        </div>

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
