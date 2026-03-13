import { CompassIcon } from '../icons';

export default function ChatBubble({ message }) {
  const isAi = message.role === 'ai';

  return (
    <div className={`flex ${isAi ? 'justify-start' : 'justify-end'} opacity-0 animate-bubble-in`}>
      {isAi && (
        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[var(--color-forest)] to-[var(--color-teal)] flex items-center justify-center mr-2 mt-1 flex-shrink-0 shadow-sm">
          <CompassIcon className="w-3.5 h-3.5 text-white" />
        </div>
      )}
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isAi
            ? 'bg-white text-gray-700 shadow-sm rounded-bl-sm border border-[var(--color-forest)]/10'
            : 'bg-[var(--color-forest)] text-white rounded-br-sm shadow-sm'
        }`}
      >
        {message.tone && isAi && (
          <span className="inline-block text-[10px] uppercase tracking-wide font-semibold text-[var(--color-forest)] mb-1 bg-[var(--color-forest)]/10 rounded-full px-2 py-0.5">
            {message.tone}
          </span>
        )}
        {message.tone && isAi && <br />}
        {message.text}
      </div>
    </div>
  );
}
