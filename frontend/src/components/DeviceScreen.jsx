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
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl">
        <div className="text-center text-gray-400">
          <div className="text-5xl mb-3">📱</div>
          <p className="text-sm">Device screen will appear here</p>
        </div>
      </div>
    );
  }

  const WidgetComponent = WIDGET_MAP[screenFrame.widget];
  const params = screenFrame.widget_params || {};

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl overflow-hidden">
      <div className="flex-1 flex items-center justify-center p-4">
        <AnimationOverlay animation={screenFrame.animation}>
          {WidgetComponent ? (
            <WidgetComponent {...params} photoUrl={photoUrl} animation={screenFrame.animation} />
          ) : (
            <div className="text-center p-8 bg-white/60 rounded-xl">
              <p className="text-gray-500 text-sm">Widget: {screenFrame.widget}</p>
              <p className="text-gray-400 text-xs mt-1">{JSON.stringify(params)}</p>
            </div>
          )}
        </AnimationOverlay>
      </div>

      {sessionState && (
        <div className="px-4 py-2 bg-white/40 border-t border-white/60 text-xs text-gray-500 flex justify-between">
          <span>Widget: {screenFrame.widget}</span>
          {screenFrame.animation && <span>Animation: {screenFrame.animation}</span>}
        </div>
      )}
    </div>
  );
}
