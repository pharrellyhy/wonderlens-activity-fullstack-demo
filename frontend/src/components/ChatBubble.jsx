import { useEffect, useRef } from 'react';

/**
 * Styled message bubble -- AI messages left-aligned, child messages right-aligned.
 * Props: { message } where message = { role: "ai"|"child", text, tone? }
 */
export default function ChatBubble({ message }) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.classList.add('animate-bubble-in');
    }
  }, []);

  const isAi = message.role === 'ai';

  return (
    <div ref={ref} className={`flex ${isAi ? 'justify-start' : 'justify-end'} opacity-0 animate-bubble-in`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm transition-all ${
          isAi
            ? 'bg-gradient-to-br from-indigo-500 to-purple-500 text-white rounded-bl-md'
            : 'bg-slate-100 text-slate-800 rounded-br-md'
        }`}
      >
        {message.tone && isAi && (
          <span className="inline-block text-[10px] uppercase tracking-wide font-semibold opacity-70 mb-1 bg-white/20 rounded-full px-2 py-0.5">
            {message.tone}
          </span>
        )}
        {message.tone && isAi && <br />}
        {message.text}
      </div>
    </div>
  );
}
