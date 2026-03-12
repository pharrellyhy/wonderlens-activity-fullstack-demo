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
    <form onSubmit={handleSubmit} className="flex items-center gap-2 px-4 py-3 border-t border-slate-200 bg-slate-50">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type here..."
        disabled={disabled}
        className="flex-1 rounded-full border border-slate-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent bg-white disabled:bg-slate-100 disabled:text-slate-400 disabled:cursor-not-allowed"
      />
      <button
        type="button"
        onClick={onMicToggle}
        disabled={disabled}
        className={`w-10 h-10 flex items-center justify-center rounded-full transition-colors shadow-sm ${
          isMicActive
            ? 'bg-red-500 text-white hover:bg-red-600 animate-pulse'
            : 'bg-indigo-500 text-white hover:bg-indigo-600'
        } disabled:opacity-40 disabled:cursor-not-allowed`}
        title={isMicActive ? 'Stop recording' : 'Voice input'}
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
        className="w-10 h-10 flex items-center justify-center rounded-full bg-emerald-500 text-white hover:bg-emerald-600 transition-colors shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
        title="Send"
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
