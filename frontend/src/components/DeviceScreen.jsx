import PhotoDisplay from '../widgets/PhotoDisplay';
import ProgressTracker from '../widgets/ProgressTracker';
import CharacterDisplay from '../widgets/CharacterDisplay';
import PhotoGrid from '../widgets/PhotoGrid';
import BadgeAward from '../widgets/BadgeAward';
import AnimationOverlay from '../widgets/AnimationOverlay';

const WIDGET_MAP = {
  photo_display: PhotoDisplay,
  progress_tracker: ProgressTracker,
  character_display: CharacterDisplay,
  photo_grid: PhotoGrid,
  badge_award: BadgeAward,
};

export default function DeviceScreen({ screenFrame, photoUrl, sessionState }) {
  if (!screenFrame) {
    return (
      <div className="h-full flex items-center justify-center bg-[#111] rounded-3xl border border-white/5">
        <div className="text-center text-neutral-600">
          <div className="text-5xl mb-3">📱</div>
          <p className="text-sm">Device screen will appear here</p>
        </div>
      </div>
    );
  }

  const WidgetComponent = WIDGET_MAP[screenFrame.widget];
  const params = screenFrame.widget_params || {};

  return (
    <div className="h-full flex flex-col bg-[#111] rounded-3xl overflow-hidden border border-white/5">
      <div className="flex-1 flex items-center justify-center p-4">
        <AnimationOverlay animation={screenFrame.animation}>
          {WidgetComponent ? (
            <WidgetComponent {...params} photoUrl={photoUrl} animation={screenFrame.animation} />
          ) : (
            <div className="text-center p-8 bg-white/5 rounded-2xl">
              <p className="text-neutral-400 text-sm">Widget: {screenFrame.widget}</p>
              <p className="text-neutral-500 text-xs mt-1">{JSON.stringify(params)}</p>
            </div>
          )}
        </AnimationOverlay>
      </div>

      {sessionState && (
        <div className="px-4 py-2 border-t border-white/5 text-xs text-neutral-600 flex justify-between">
          <span>Widget: {screenFrame.widget}</span>
          {screenFrame.animation && <span>Animation: {screenFrame.animation}</span>}
        </div>
      )}
    </div>
  );
}
