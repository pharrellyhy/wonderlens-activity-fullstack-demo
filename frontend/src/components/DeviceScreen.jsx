import { useEffect, useRef } from 'react';
import PhotoDisplay from '../widgets/PhotoDisplay';
import ProgressTracker from '../widgets/ProgressTracker';
import CharacterDisplay from '../widgets/CharacterDisplay';
import PhotoGrid from '../widgets/PhotoGrid';
import BadgeAward from '../widgets/BadgeAward';
import AnimationOverlay from '../widgets/AnimationOverlay';
import SfxIndicator from './SfxIndicator';
import useSfxPlayer from '../hooks/useSfxPlayer';
import { CameraIcon } from '../icons';

const WIDGET_MAP = {
  photo_display: PhotoDisplay,
  progress_tracker: ProgressTracker,
  character_display: CharacterDisplay,
  photo_grid: PhotoGrid,
  badge_award: BadgeAward,
};

function getFrameKey(screenFrame) {
  if (!screenFrame) {
    return 'empty-frame';
  }

  return JSON.stringify({
    widget: screenFrame.widget,
    trigger: screenFrame.trigger,
    animation: screenFrame.animation,
    widgetParams: screenFrame.widget_params,
    widgetLabel: screenFrame.widget_label,
    animationLabel: screenFrame.animation_label,
    sfxCue: screenFrame.sfx_cue,
    sfxLabel: screenFrame.sfx_label,
  });
}

export default function DeviceScreen({ screenFrame, photoUrl }) {
  const playSfx = useSfxPlayer();
  const lastSfxFrameRef = useRef(null);

  useEffect(() => {
    if (!screenFrame?.sfx_cue) return;
    const frameKey = getFrameKey(screenFrame);
    if (frameKey === lastSfxFrameRef.current) return;
    lastSfxFrameRef.current = frameKey;
    playSfx(screenFrame.sfx_cue);
  }, [screenFrame, playSfx]);

  if (!screenFrame) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl surface-accent flex items-center justify-center mx-auto mb-3 shadow-sm">
            <CameraIcon className="w-8 h-8 text-[var(--color-forest)]" />
          </div>
          <p className="text-sm text-gray-400 font-medium">Device screen will appear here</p>
        </div>
      </div>
    );
  }

  const frameKey = getFrameKey(screenFrame);
  const WidgetComponent = WIDGET_MAP[screenFrame.widget];
  const params = screenFrame.widget_params || {};

  return (
    <div
      key={frameKey}
      className="h-full flex flex-col transition-opacity duration-300 ease-in-out"
    >
      {/* Widget label header */}
      {screenFrame.widget_label && (
        <div className="px-3 pt-2 pb-1">
          <p className="text-xs font-medium text-[var(--color-forest)] text-center">{screenFrame.widget_label}</p>
        </div>
      )}

      <div className="flex-1 flex items-center justify-center min-h-0">
        <AnimationOverlay animation={screenFrame.animation}>
          {WidgetComponent ? (
            <WidgetComponent {...params} photoUrl={photoUrl} animation={screenFrame.animation} />
          ) : (
            <div className="text-center p-8 surface-card rounded-2xl">
              <p className="text-gray-500 text-sm">Widget: {screenFrame.widget}</p>
            </div>
          )}
        </AnimationOverlay>
      </div>

      {/* Animation label + SFX indicator */}
      <div className="flex items-center justify-between px-3 py-1.5 gap-2">
        {screenFrame.animation_label && (
          <p className="text-[10px] text-gray-400 italic truncate">{screenFrame.animation_label}</p>
        )}
        <SfxIndicator key={`sfx-${frameKey}`} sfxCue={screenFrame.sfx_cue} sfxLabel={screenFrame.sfx_label} />
      </div>
    </div>
  );
}
