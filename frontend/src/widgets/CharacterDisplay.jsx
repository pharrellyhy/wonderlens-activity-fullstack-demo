import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { getThemeForEntity } from './gameThemes';

const VIDEO_VOLUME = 0.4;
const VIDEO_VOLUME_DUCKED = 0.1;

export default function CharacterDisplay({
  description,
  animation,
  roundNumber = 1,
  entity,
  clipUrl,
  isOneShot,
  onClipEnded,
  isSpeaking = false,
}) {
  const theme = getThemeForEntity(entity);
  const hasVideo = !!clipUrl;
  const expectsVideo = !!theme?.videoPrefix;
  const [videoMuted, setVideoMuted] = useState(true);

  // Dual video crossfade state
  const videoARef = useRef(null);
  const videoBRef = useRef(null);
  const activeSlotRef = useRef('a');
  const [activeSlot, setActiveSlot] = useState('a');
  const [readyToShow, setReadyToShow] = useState(false);

  useEffect(() => {
    if (!clipUrl) return;
    console.log('[CharacterDisplay] loading clip:', clipUrl, 'isOneShot:', isOneShot);

    const nextSlot = activeSlotRef.current === 'a' ? 'b' : 'a';
    const nextVideo = nextSlot === 'a' ? videoARef.current : videoBRef.current;
    const oldVideo = nextSlot === 'a' ? videoBRef.current : videoARef.current;

    if (!nextVideo) return;

    let activated = false;

    const activate = (source) => {
      if (activated) return;
      activated = true;
      if (oldVideo) oldVideo.pause();
      // Unmute before playing — user has already interacted (clicked Start)
      if (unlockedRef.current) nextVideo.muted = false;
      nextVideo.play().catch(e => {
        console.warn('[CharacterDisplay] play failed, retrying muted:', e.message);
        nextVideo.muted = true;
        nextVideo.play().catch(() => {});
      });
      activeSlotRef.current = nextSlot;
      setActiveSlot(nextSlot);
      setReadyToShow(true);
    };

    const onCanPlay = () => activate('canplay');
    const onLoadedData = () => activate('loadeddata');
    const onError = () => {
      console.error('[CharacterDisplay] video error:', nextVideo.error?.message, clipUrl);
    };

    nextVideo.addEventListener('canplay', onCanPlay);
    nextVideo.addEventListener('loadeddata', onLoadedData);
    nextVideo.addEventListener('error', onError);
    nextVideo.src = clipUrl;
    nextVideo.loop = !isOneShot;
    nextVideo.load();

    // No timeout fallback — in production, clips may take several seconds
    // to load over the network. The crossfade keeps the old video visible
    // until the new one is ready; forcing a switch early shows a blank frame.

    return () => {
      nextVideo.removeEventListener('canplay', onCanPlay);
      nextVideo.removeEventListener('loadeddata', onLoadedData);
      nextVideo.removeEventListener('error', onError);
    };
  }, [clipUrl, isOneShot]);

  // Unmute videos after first user gesture (browser autoplay requires muted start)
  const unlockedRef = useRef(false);
  useLayoutEffect(() => {
    const unlock = () => {
      if (unlockedRef.current) return;
      unlockedRef.current = true;
      if (videoARef.current) videoARef.current.muted = false;
      if (videoBRef.current) videoBRef.current.muted = false;
      for (const evt of ['click', 'touchstart', 'keydown']) {
        document.removeEventListener(evt, unlock, true);
      }
    };
    for (const evt of ['click', 'touchstart', 'keydown']) {
      document.addEventListener(evt, unlock, { capture: true });
    }
    return () => {
      for (const evt of ['click', 'touchstart', 'keydown']) {
        document.removeEventListener(evt, unlock, true);
      }
    };
  }, []);

  // Control video volume: user-muted, ducked (during TTS), or normal
  useEffect(() => {
    const volume = videoMuted ? 0 : isSpeaking ? VIDEO_VOLUME_DUCKED : VIDEO_VOLUME;
    if (videoARef.current) videoARef.current.volume = volume;
    if (videoBRef.current) videoBRef.current.volume = volume;
  }, [isSpeaking, videoMuted]);

  // Handle one-shot ended
  useEffect(() => {
    const activeVideo = activeSlot === 'a' ? videoARef.current : videoBRef.current;
    if (!activeVideo || !isOneShot || !onClipEnded) return;

    const handleEnded = () => onClipEnded();
    activeVideo.addEventListener('ended', handleEnded);
    return () => activeVideo.removeEventListener('ended', handleEnded);
  }, [activeSlot, isOneShot, onClipEnded]);

  return (
    <div className={`relative ${hasVideo ? 'w-full h-full' : 'flex flex-col items-center gap-2.5 max-[380px]:gap-2 p-3 max-[380px]:p-2.5 w-full max-w-md'} overflow-hidden transition-all duration-500 ${animation === 'scene_transition' ? 'animate-fade-in' : ''}`}>
      {hasVideo ? (
        <>
          {/* Full-panel video — preload=auto for faster start in production */}
          <video
            ref={videoARef}
            className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-300 ease-in-out ${activeSlot === 'a' ? 'opacity-100' : 'opacity-0'}`}
            playsInline
            muted
            preload="auto"
            aria-hidden="true"
          />
          <video
            ref={videoBRef}
            className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-300 ease-in-out ${activeSlot === 'b' ? 'opacity-100' : 'opacity-0'}`}
            playsInline
            muted
            preload="auto"
            aria-hidden="true"
          />
          {/* Show character icon + loading spinner while first video loads */}
          {!readyToShow && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-b from-gray-50 to-gray-100 gap-3">
              <img src={theme.characterPng} alt="" className="w-28 h-28 sm:w-32 sm:h-32 object-contain animate-gentle-float" />
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-forest)]/40 animate-bounce [animation-delay:0ms]" />
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-forest)]/40 animate-bounce [animation-delay:150ms]" />
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-forest)]/40 animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          )}
          {/* Mute/unmute button */}
          <button
            onClick={() => setVideoMuted(prev => !prev)}
            className="absolute top-2 right-2 w-7 h-7 rounded-full bg-black/40 hover:bg-black/60 flex items-center justify-center text-white/80 hover:text-white transition-colors z-10"
            aria-label={videoMuted ? 'Unmute video' : 'Mute video'}
          >
            {videoMuted ? (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                <line x1="23" y1="9" x2="17" y2="15" />
                <line x1="17" y1="9" x2="23" y2="15" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
              </svg>
            )}
          </button>
        </>
      ) : (
        /* Static PNG — shown before game starts (Cat1) and for non-video games (Cat5) */
        <>
          <div className={`w-[clamp(2.8rem,12vw,3.25rem)] h-[clamp(2.8rem,12vw,3.25rem)] rounded-full ${theme.iconBg} ring-2 flex items-center justify-center shadow-sm animate-gentle-float`}>
            <img src={theme.characterPng} alt={entity || 'character'} className="w-[clamp(1.9rem,8vw,2.2rem)] h-[clamp(1.9rem,8vw,2.2rem)] object-contain" />
          </div>
          <div className="bg-white/80 rounded-xl max-[380px]:rounded-lg p-2.5 max-[380px]:p-2 w-full text-center shadow-sm">
            <p className="text-gray-700 font-medium text-xs">{description || `Scene ${roundNumber}`}</p>
          </div>
          {roundNumber > 0 && (
            <div className={`text-xs max-[380px]:text-[11px] ${theme.accent} ${theme.accentBg} px-3 max-[380px]:px-2 py-1 max-[380px]:py-0.5 rounded-full font-medium`}>
              Round {roundNumber}
            </div>
          )}
        </>
      )}

    </div>
  );
}
