/**
 * Styled message bubble -- AI messages left-aligned, child messages right-aligned.
 * Props: { message } where message = { role: "ai"|"child", text, tone? }
 */
export default function ChatBubble({ message }) {
  const isAi = message.role === 'ai';

  return (
    <div className={`flex ${isAi ? 'justify-start' : 'justify-end'} opacity-0 animate-bubble-in`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isAi
            ? 'bg-[#1a1a1a] text-neutral-200 rounded-bl-sm'
            : 'bg-gradient-to-br from-fuchsia-500 to-purple-600 text-white rounded-br-sm'
        }`}
      >
        {message.tone && isAi && (
          <span className="inline-block text-[10px] uppercase tracking-wide font-semibold text-neutral-500 mb-1 bg-white/5 rounded-full px-2 py-0.5">
            {message.tone}
          </span>
        )}
        {message.tone && isAi && <br />}
        {message.text}
      </div>
    </div>
  );
}
