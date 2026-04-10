import { SpeakerIcon } from '../icons';

export default function StageModeFooter({ messages, isSpeaking }) {
  const latestAi = [...(messages || [])].reverse().find((m) => m.role === 'ai');
  if (!latestAi) {
    return <div className="h-12" aria-hidden="true" />;
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
