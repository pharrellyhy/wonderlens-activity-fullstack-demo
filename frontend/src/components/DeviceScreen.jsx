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
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl bg-white/40 border border-white/50 flex items-center justify-center mx-auto mb-3 shadow-sm">
            <span className="text-3xl">📱</span>
          </div>
          <p className="text-sm text-gray-400 font-medium">Device screen will appear here</p>
        </div>
      </div>
    );
  }

  const WidgetComponent = WIDGET_MAP[screenFrame.widget];
  const params = screenFrame.widget_params || {};

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 flex items-center justify-center">
        <AnimationOverlay animation={screenFrame.animation}>
          {WidgetComponent ? (
            <WidgetComponent {...params} photoUrl={photoUrl} animation={screenFrame.animation} />
          ) : (
            <div className="text-center p-8 bg-white/40 rounded-2xl border border-white/50">
              <p className="text-gray-500 text-sm">Widget: {screenFrame.widget}</p>
              <p className="text-gray-400 text-xs mt-1">{JSON.stringify(params)}</p>
            </div>
          )}
        </AnimationOverlay>
      </div>

      {sessionState && (
        <div className="px-3 py-2 bg-white/30 rounded-xl mt-2 text-xs text-gray-400 flex justify-between">
          <span>Widget: {screenFrame.widget}</span>
          {screenFrame.animation && <span>Animation: {screenFrame.animation}</span>}
        </div>
      )}
    </div>
  );
}
