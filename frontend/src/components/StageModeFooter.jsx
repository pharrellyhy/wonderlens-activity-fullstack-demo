import { SpeakerIcon } from '../icons';

function findLatestAi(messages) {
  if (!messages) return null;
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    if (messages[i].role === 'ai') return messages[i];
  }
  return null;
}

export default function StageModeFooter({ messages, isSpeaking }) {
  const latestAi = findLatestAi(messages);
  if (!latestAi) {
    return null;
  }

  return (
    <div className="h-12 flex items-center gap-2 px-4 surface-primary border-t border-black/5 animate-fade-in">
      <SpeakerIcon className={`w-4 h-4 shrink-0 ${isSpeaking ? 'text-[var(--color-forest)] animate-pulse' : 'text-gray-400'}`} />
      <p className="text-sm text-gray-700 truncate italic">
        &ldquo;{latestAi.text}&rdquo;
      </p>
    </div>
  );
}
