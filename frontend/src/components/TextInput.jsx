import { useState } from 'react';

/**
 * Text field + submit button + mic toggle button.
 * Props: { onSubmit, onMicToggle, isMicActive, disabled }
 */
export default function TextInput({ onSubmit, onMicToggle, isMicActive, disabled }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setText('');
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2 px-4 py-3 border-t border-white/5 bg-[#0a0a0a]">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Send message..."
        disabled={disabled}
        className="flex-1 rounded-full border border-white/10 px-4 py-2.5 text-sm bg-[#1a1a1a] text-white placeholder-neutral-500 focus:outline-none focus:ring-1 focus:ring-fuchsia-500 focus:border-fuchsia-500 disabled:opacity-40 disabled:cursor-not-allowed"
      />
      <button
        type="button"
        onClick={onMicToggle}
        disabled={disabled}
        aria-label={isMicActive ? 'Stop recording' : 'Voice input'}
        aria-pressed={isMicActive}
        className={`w-10 h-10 flex items-center justify-center rounded-full transition-colors ${
          isMicActive
            ? 'bg-fuchsia-500 text-white hover:bg-fuchsia-400 animate-pulse'
            : 'bg-white/5 text-neutral-400 hover:text-white hover:bg-white/10'
        } disabled:opacity-40 disabled:cursor-not-allowed`}
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
          />
        </svg>
      </button>
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        aria-label="Send message"
        className="w-10 h-10 flex items-center justify-center rounded-full bg-fuchsia-500 text-white hover:bg-fuchsia-400 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
          />
        </svg>
      </button>
    </form>
  );
}
