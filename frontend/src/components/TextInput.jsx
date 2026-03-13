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
    <form onSubmit={handleSubmit} className="flex items-center gap-2 px-4 py-3">
      <div className="flex-1 flex items-center gap-2 bg-white/50 border border-gray-200/50 rounded-full px-4 py-1 shadow-sm focus-within:ring-2 focus-within:ring-indigo-300 focus-within:border-transparent transition-shadow">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Ask me anything ..."
          disabled={disabled}
          className="flex-1 bg-transparent py-2 text-sm text-gray-700 placeholder-gray-400 focus:outline-none disabled:opacity-40 disabled:cursor-not-allowed"
        />
        <button
          type="button"
          onClick={onMicToggle}
          disabled={disabled}
          aria-label={isMicActive ? 'Stop recording' : 'Voice input'}
          aria-pressed={isMicActive}
          className={`w-8 h-8 flex items-center justify-center rounded-full transition-all ${
            isMicActive
              ? 'bg-red-500 text-white hover:bg-red-400 animate-pulse shadow-sm'
              : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100/50'
          } disabled:opacity-40 disabled:cursor-not-allowed`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
        className="w-10 h-10 flex items-center justify-center rounded-full bg-gray-800 text-white hover:bg-gray-700 transition-all shadow-sm hover:shadow-md disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
