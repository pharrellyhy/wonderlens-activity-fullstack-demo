import { useEffect, useRef, useState } from 'react';

export default function ActivityTextInput({ disabled, finished = false, onSend }) {
  const [value, setValue] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    if (!disabled && !finished) {
      inputRef.current?.focus();
    }
  }, [disabled, finished]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const text = value.trim();
    if (!text || disabled || finished) return;
    setValue('');
    try {
      await onSend(text);
    } finally {
      if (!finished) {
        const focusInput = () => inputRef.current?.focus();
        if (typeof window.requestAnimationFrame === 'function') {
          window.requestAnimationFrame(focusInput);
        } else {
          focusInput();
        }
      }
    }
  };

  return (
    <form className="activity-game__input" onSubmit={handleSubmit}>
      <label htmlFor="activity-text-input">Text response</label>
      <div>
        <input
          id="activity-text-input"
          ref={inputRef}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          disabled={disabled || finished}
          placeholder={finished ? 'Activity finished' : 'Type a response'}
          autoComplete="off"
        />
        <button
          type="submit"
          disabled={disabled || finished || !value.trim()}
          aria-label="Send message"
        >
          <span aria-hidden="true">→</span>
        </button>
      </div>
    </form>
  );
}
