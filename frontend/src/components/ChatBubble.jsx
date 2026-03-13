/**
 * Styled message bubble -- AI messages left-aligned, child messages right-aligned.
 * Props: { message } where message = { role: "ai"|"child", text, tone? }
 */
export default function ChatBubble({ message }) {
  const isAi = message.role === 'ai';

  return (
    <div className={`flex ${isAi ? 'justify-start' : 'justify-end'} opacity-0 animate-bubble-in`}>
      {isAi && (
        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center mr-2 mt-1 flex-shrink-0 shadow-sm">
          <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
      )}
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isAi
            ? 'bg-white/70 text-gray-700 shadow-sm rounded-bl-sm'
            : 'bg-gray-700 text-white rounded-br-sm shadow-sm'
        }`}
      >
        {message.tone && isAi && (
          <span className="inline-block text-[10px] uppercase tracking-wide font-semibold text-indigo-400 mb-1 bg-indigo-50 rounded-full px-2 py-0.5">
            {message.tone}
          </span>
        )}
        {message.tone && isAi && <br />}
        {message.text}
      </div>
    </div>
  );
}
