import { useState, useEffect, useRef } from 'react';
import AiAvatar from './AiAvatar';

const CHARS_PER_FRAME = 2;
const FRAME_INTERVAL = 30; // ~33fps is enough for text reveal

function useTypewriter(text, enabled) {
  const [displayed, setDisplayed] = useState(enabled ? '' : text);
  const [done, setDone] = useState(!enabled);
  const indexRef = useRef(0);
  const lastTimeRef = useRef(0);
  const rafRef = useRef(null);

  useEffect(() => {
    if (!enabled) return;

    const step = (timestamp) => {
      if (timestamp - lastTimeRef.current >= FRAME_INTERVAL) {
        lastTimeRef.current = timestamp;
        indexRef.current = Math.min(indexRef.current + CHARS_PER_FRAME, text.length);
        setDisplayed(text.slice(0, indexRef.current));
        if (indexRef.current >= text.length) {
          setDone(true);
          return;
        }
      }
      rafRef.current = requestAnimationFrame(step);
    };

    rafRef.current = requestAnimationFrame(step);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [text, enabled]);

  return {
    displayed: enabled ? displayed : text,
    done: enabled ? done : true,
  };
}

export default function ChatBubble({ message, isLatestAi }) {
  const isAi = message.role === 'ai';
  const { displayed, done } = useTypewriter(message.text, isAi && isLatestAi);

  return (
    <div className={`flex ${isAi ? 'justify-start' : 'justify-end'} opacity-0 animate-bubble-in`}>
      {isAi && (
        <AiAvatar size="sm" className="mr-2 mt-1" />
      )}
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isAi
            ? 'bg-white text-gray-700 shadow-sm rounded-bl-sm border border-[var(--color-forest)]/10'
            : 'bg-[var(--color-forest)] text-white rounded-br-sm shadow-sm'
        }`}
      >
        {message.tone && isAi && (
          <span className="inline-block text-xs uppercase tracking-wide font-semibold text-[var(--color-forest)] mb-1 bg-[var(--color-forest)]/10 rounded-full px-2 py-0.5">
            {message.tone}
          </span>
        )}
        {message.tone && isAi && <br />}
        {displayed}
        {isAi && !done && <span className="inline-block w-0.5 h-4 bg-[var(--color-forest)] ml-0.5 animate-pulse align-text-bottom" />}
      </div>
    </div>
  );
}
