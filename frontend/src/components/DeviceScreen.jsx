import { useEffect, useRef } from 'react';
import PhotoDisplay from '../widgets/PhotoDisplay';
import ProgressTracker from '../widgets/ProgressTracker';
import CharacterDisplay from '../widgets/CharacterDisplay';
import PhotoGrid from '../widgets/PhotoGrid';
import BadgeAward from '../widgets/BadgeAward';
import ExplorerMap from '../canvas/ExplorerMap';
import AnimationOverlay from '../widgets/AnimationOverlay';
import SfxIndicator from './SfxIndicator';
import useSfxPlayer from '../hooks/useSfxPlayer';
import { BadgeIcon, CameraIcon } from '../icons';
import { asset } from '../utils/basePath';

const WIDGET_MAP = {
  photo_display: PhotoDisplay,
  progress_tracker: ProgressTracker,
  character_display: CharacterDisplay,
  photo_grid: PhotoGrid,
  badge_award: BadgeAward,
  explorer_map: ExplorerMap,
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
    screenFrame.widget_params?.photo_id,
    screenFrame.widget_params?.game_phase,
    screenFrame.widget_params?.collected_count,
  ].join('|');
}

function entityFromActivity(activityType) {
  if (!activityType) return null;
  const parts = activityType.split('_');
  return parts[parts.length - 1] || null;
}

const ANIM_STATE_COLORS = {
  scenario: 'bg-emerald-500',
  idle: 'bg-gray-400',
  speaking: 'bg-blue-400',
  waving: 'bg-purple-400',
  celebrating: 'bg-yellow-500',
  excited: 'bg-orange-400',
  encouraging: 'bg-teal-400',
  surprised: 'bg-pink-400',
};

export default function DeviceScreen({ screenFrame, photoUrl, sessionState, clipUrl, isOneShot, onClipEnded, animationState, currentScenario, isSpeaking, activityType }) {
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
  // In video mode, always render CharacterDisplay regardless of backend widget
  // (celebrate/closing steps use badge_award, but we want the video to play)
  const isVideoMode = !!clipUrl;
  const WidgetComponent = isVideoMode ? CharacterDisplay : WIDGET_MAP[screenFrame.widget];
  const params = screenFrame.widget_params || {};

  // character_display has its own gentle-float; suppress all overlay animations
  // except scene_transition (crossfade between rounds)
  let overlayAnimation = screenFrame.animation;
  if (isVideoMode && overlayAnimation !== 'scene_transition') {
    overlayAnimation = 'appear';
  }

  // In video mode, use a stable key so frame changes (celebrate → closing)
  // don't remount the CharacterDisplay and reset its video playback state.
  // Non-video widgets still use the full frameKey for proper transitions.
  const containerKey = isVideoMode ? 'video-player' : frameKey;

  return (
    <div
      key={containerKey}
      className="h-full flex flex-col transition-opacity duration-300 ease-in-out"
    >
      {/* Widget label header (hidden in full-panel video mode — info moves to bottom overlay) */}
      {screenFrame.widget_label && !isVideoMode && (
        <div className="px-2.5 pt-1.5 pb-1 max-[380px]:px-2 max-[380px]:pt-1">
          <p className="text-[11px] max-[380px]:text-[10px] font-medium text-[var(--color-forest)] text-center">{screenFrame.widget_label}</p>
        </div>
      )}

      <div className={`flex-1 min-h-0 grid place-items-center ${isVideoMode ? '' : 'px-2 pb-1 max-[380px]:px-1.5 max-[380px]:pb-0.5'}`}>
        {screenFrame.widget === 'explorer_map' && WidgetComponent ? (
          <div className="w-full h-full">
            <WidgetComponent {...params} />
          </div>
        ) : (
          <AnimationOverlay animation={overlayAnimation} className="flex h-full w-full items-center justify-center">
            {WidgetComponent ? (
              <div className={`relative ${isVideoMode ? 'w-full h-full' : 'w-full max-w-[17rem] sm:max-w-[18.5rem] max-h-full flex items-center justify-center'}`}>
                <WidgetComponent
                  {...params}
                  {...(isVideoMode ? { entity: entityFromActivity(activityType), clipUrl, isOneShot, onClipEnded, isSpeaking } : {})}
                  photoUrl={asset(params.photoUrl) || photoUrl}
                  animation={screenFrame.animation}
                  sessionState={sessionState}
                />
                {/* Badge + IB concepts overlay on top of video during celebrate/closing */}
                {isVideoMode && screenFrame.widget === 'badge_award' && (
                  <div className="absolute bottom-3 left-3 right-3 z-10 flex flex-col gap-1.5 animate-badge-pop">
                    <div className="flex items-center gap-2 bg-black/50 backdrop-blur-sm rounded-full pl-1.5 pr-3 py-1.5 shadow-lg self-start">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[var(--color-sunflower)] to-[var(--color-forest)] flex items-center justify-center border-2 border-white/60">
                        <BadgeIcon className="w-4 h-4 text-white" />
                      </div>
                      <span className="text-white text-xs font-semibold truncate max-w-[8rem]">
                        {params.title || 'Explorer'}
                      </span>
                    </div>
                    {params.concepts?.length > 0 && (
                      <div className="flex items-center gap-1.5 self-start">
                        {params.concepts.map((concept) => (
                          <span key={concept} className="px-2.5 py-1 bg-white/90 backdrop-blur-sm rounded-full text-[11px] font-semibold text-[var(--color-forest-dark)] shadow-sm border border-[var(--color-forest)]/20">
                            {concept}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center p-8 surface-card rounded-2xl">
                <p className="text-gray-500 text-sm">Widget: {screenFrame.widget}</p>
              </div>
            )}
          </AnimationOverlay>
        )}
      </div>

      {/* Animation label + SFX + emotion/scenario indicators */}
      <div className="flex items-center justify-between px-2.5 py-1 max-[380px]:px-2 max-[380px]:py-0.5 gap-1.5 max-[380px]:gap-1">
        <div className="flex items-center gap-1.5 min-w-0">
          {screenFrame.animation_label && (
            <p className="text-[9px] max-[380px]:text-[8px] text-gray-400 italic truncate">{screenFrame.animation_label}</p>
          )}
          {animationState && (
            <>
              <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono text-white shrink-0 ${ANIM_STATE_COLORS[animationState] || 'bg-gray-400'}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${animationState === 'scenario' ? 'bg-white animate-pulse' : 'bg-white/60'}`} />
                {animationState}
              </span>
              {animationState === 'scenario' && currentScenario && (
                <span className="text-[9px] text-gray-500 truncate">{currentScenario}</span>
              )}
            </>
          )}
        </div>
        <SfxIndicator key={`sfx-${frameKey}`} sfxCue={screenFrame.sfx_cue} sfxLabel={screenFrame.sfx_label} />
      </div>
    </div>
  );
}
