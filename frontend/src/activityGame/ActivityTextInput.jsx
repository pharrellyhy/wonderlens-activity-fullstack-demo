import { useState } from 'react';

export default function ActivityTextInput({ disabled, onSend }) {
  const [value, setValue] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    const text = value.trim();
    if (!text || disabled) return;
    setValue('');
    await onSend(text);
  };

  return (
    <form className="activity-game__input" onSubmit={handleSubmit}>
      <label htmlFor="activity-text-input">Text response</label>
      <div>
        <input
          id="activity-text-input"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          disabled={disabled}
          placeholder="Type a response"
          autoComplete="off"
        />
        <button type="submit" disabled={disabled || !value.trim()}>
          Send
        </button>
      </div>
    </form>
  );
}
