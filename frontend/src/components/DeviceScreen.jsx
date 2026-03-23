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

  return [
    screenFrame.widget,
    screenFrame.trigger,
    screenFrame.animation,
    screenFrame.widget_label,
    screenFrame.animation_label,
    screenFrame.sfx_cue,
    screenFrame.sfx_label,
    screenFrame.widget_params?.filled,
    screenFrame.widget_params?.total,
    screenFrame.widget_params?.description,
    screenFrame.widget_params?.title,
    screenFrame.widget_params?.roundNumber,
  ].join('|');
}

export default function DeviceScreen({ screenFrame, photoUrl, sessionState }) {
  const { play: playSfx } = useSfxPlayer();
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
          <div className="w-11 h-11 max-[380px]:w-10 max-[380px]:h-10 rounded-2xl max-[380px]:rounded-xl surface-accent flex items-center justify-center mx-auto mb-2.5 max-[380px]:mb-2 shadow-sm">
            <CameraIcon className="w-5 h-5 max-[380px]:w-4.5 max-[380px]:h-4.5 text-[var(--color-forest)]" />
          </div>
          <p className="text-sm max-[380px]:text-xs text-gray-500 font-medium">Device screen will appear here</p>
        </div>
      </div>
    );
  }

  const frameKey = getFrameKey(screenFrame);
  const WidgetComponent = WIDGET_MAP[screenFrame.widget];
  const params = screenFrame.widget_params || {};

  // character_display has its own gentle-float; suppress all overlay animations
  // except scene_transition (crossfade between rounds)
  let overlayAnimation = screenFrame.animation;
  if (screenFrame.widget === 'character_display' && overlayAnimation !== 'scene_transition') {
    overlayAnimation = 'appear';
  }

  return (
    <div
      key={frameKey}
      className="h-full flex flex-col transition-opacity duration-300 ease-in-out"
    >
      {/* Widget label header */}
      {screenFrame.widget_label && (
        <div className="px-2.5 pt-1.5 pb-1 max-[380px]:px-2 max-[380px]:pt-1">
          <p className="text-[11px] max-[380px]:text-[10px] font-medium text-[var(--color-forest)] text-center">{screenFrame.widget_label}</p>
        </div>
      )}

      <div className="flex-1 flex items-center justify-center min-h-0 px-2 pb-1 max-[380px]:px-1.5 max-[380px]:pb-0.5">
        <AnimationOverlay animation={overlayAnimation}>
          {WidgetComponent ? (
            <div className="w-full max-w-md max-h-full flex items-center justify-center">
              <WidgetComponent {...params} photoUrl={photoUrl} animation={screenFrame.animation} sessionState={sessionState} />
            </div>
          ) : (
            <div className="text-center p-8 surface-card rounded-2xl">
              <p className="text-gray-500 text-sm">Widget: {screenFrame.widget}</p>
            </div>
          )}
        </AnimationOverlay>
      </div>

      {/* Animation label + SFX indicator */}
      <div className="flex items-center justify-between px-2.5 py-1 max-[380px]:px-2 max-[380px]:py-0.5 gap-1.5 max-[380px]:gap-1">
        {screenFrame.animation_label && (
          <p className="text-[9px] max-[380px]:text-[8px] text-gray-400 italic truncate">{screenFrame.animation_label}</p>
        )}
        <SfxIndicator key={`sfx-${frameKey}`} sfxCue={screenFrame.sfx_cue} sfxLabel={screenFrame.sfx_label} />
      </div>
    </div>
  );
}
