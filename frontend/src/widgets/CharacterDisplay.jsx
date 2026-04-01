import { useEffect, useRef, useState } from 'react';
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
  const [videoMuted, setVideoMuted] = useState(false);

  // Dual video crossfade state
  const videoARef = useRef(null);
  const videoBRef = useRef(null);
  const activeSlotRef = useRef('a');
  const [activeSlot, setActiveSlot] = useState('a');
  const [readyToShow, setReadyToShow] = useState(false);
  const currentUrlRef = useRef(null);

  useEffect(() => {
    if (!clipUrl || clipUrl === currentUrlRef.current) return;
    currentUrlRef.current = clipUrl;

    const nextSlot = activeSlotRef.current === 'a' ? 'b' : 'a';
    const nextVideo = nextSlot === 'a' ? videoARef.current : videoBRef.current;
    const oldVideo = nextSlot === 'a' ? videoBRef.current : videoARef.current;

    if (!nextVideo) return;

    nextVideo.src = clipUrl;
    nextVideo.loop = !isOneShot;
    nextVideo.load();

    const handleCanPlay = () => {
      if (oldVideo) oldVideo.pause();
      nextVideo.play().catch(() => {});
      activeSlotRef.current = nextSlot;
      setActiveSlot(nextSlot);
      setReadyToShow(true);
      nextVideo.removeEventListener('canplay', handleCanPlay);
    };

    nextVideo.addEventListener('canplay', handleCanPlay);

    return () => {
      nextVideo.removeEventListener('canplay', handleCanPlay);
    };
  }, [clipUrl, isOneShot]);

  // Control video volume: muted, ducked (during TTS), or normal
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
    <div className={`relative w-full h-full overflow-hidden transition-all duration-500 ${animation === 'scene_transition' ? 'animate-fade-in' : ''}`}>
      {hasVideo ? (
        <>
          {/* Full-panel video */}
          <video
            ref={videoARef}
            className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-200 ease-in-out ${activeSlot === 'a' ? 'opacity-100' : 'opacity-0'}`}
            playsInline
            aria-hidden="true"
          />
          <video
            ref={videoBRef}
            className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-200 ease-in-out ${activeSlot === 'b' ? 'opacity-100' : 'opacity-0'}`}
            playsInline
            aria-hidden="true"
          />
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
      ) : expectsVideo ? (
        /* Video expected but not loaded yet — show nothing */
        null
      ) : (
        /* Static PNG fallback for non-video games (Cat5) */
        <div className="h-full flex flex-col items-center justify-center gap-2.5 p-3">
          <div className={`w-[clamp(2.8rem,12vw,3.25rem)] h-[clamp(2.8rem,12vw,3.25rem)] rounded-full ${theme.iconBg} ring-2 flex items-center justify-center shadow-sm animate-gentle-float`}>
            <img src={theme.characterPng} alt={entity || 'character'} className="w-[clamp(1.9rem,8vw,2.2rem)] h-[clamp(1.9rem,8vw,2.2rem)] object-contain" />
          </div>
          <div className="bg-white/80 rounded-xl p-2.5 w-full max-w-md text-center shadow-sm">
            <p className="text-gray-700 font-medium text-xs">{description || `Scene ${roundNumber}`}</p>
          </div>
          {roundNumber > 0 && (
            <div className={`text-xs ${theme.accent} ${theme.accentBg} px-3 py-1 rounded-full font-medium`}>
              Round {roundNumber}
            </div>
          )}
        </div>
      )}

    </div>
  );
}
