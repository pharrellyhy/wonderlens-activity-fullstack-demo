import { useState, useRef, useEffect } from 'react';

export default function TextInput({ onSubmit, onMicToggle, isMicActive, disabled }) {
  const [text, setText] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.focus();
    }
  }, [disabled]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setText('');
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2 max-[380px]:gap-1.5 px-4 max-[380px]:px-3 py-3 max-[380px]:py-2.5">
      <div className="flex-1 flex items-center gap-2 max-[380px]:gap-1.5 bg-white border border-[var(--color-forest)]/20 rounded-full px-4 max-[380px]:px-3 py-1 shadow-sm focus-within:ring-2 focus-within:ring-[var(--color-forest)]/30 focus-within:border-[var(--color-forest)]/40 transition-shadow">
        <input
          ref={inputRef}
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Ask me anything ..."
          aria-label="Type your message"
          disabled={disabled}
          className="flex-1 bg-transparent py-2 max-[380px]:py-1.5 text-sm max-[380px]:text-xs text-gray-700 placeholder-gray-400 focus:outline-none disabled:opacity-40 disabled:cursor-not-allowed"
        />
        <button
          type="button"
          onClick={onMicToggle}
          disabled={disabled}
          aria-label={isMicActive ? 'Stop recording' : 'Voice input'}
          aria-pressed={isMicActive}
          className={`w-9 h-9 sm:w-11 sm:h-11 max-[380px]:w-8 max-[380px]:h-8 flex items-center justify-center rounded-full transition-all ${
            isMicActive
              ? 'bg-red-500 text-white hover:bg-red-400 animate-pulse shadow-sm'
              : 'text-[var(--color-teal)] hover:text-[var(--color-teal-light)] hover:bg-[var(--color-teal)]/10'
          } disabled:opacity-40 disabled:cursor-not-allowed`}
        >
          <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 max-[380px]:w-3 max-[380px]:h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            />
          </svg>
        </button>
      </div>
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        aria-label="Send message"
        className="w-9 h-9 sm:w-11 sm:h-11 max-[380px]:w-8 max-[380px]:h-8 flex items-center justify-center rounded-full bg-[var(--color-forest)] text-white hover:bg-[var(--color-forest-dark)] transition-all shadow-sm hover:shadow-md disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 max-[380px]:w-3 max-[380px]:h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2.5}
            d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18"
          />
        </svg>
      </button>
    </form>
  );
}
