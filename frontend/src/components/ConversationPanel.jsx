import { useEffect, useRef, useState } from 'react';
import ChatBubble from './ChatBubble';
import TextInput from './TextInput';

export default function ConversationPanel({
  messages,
  onSendMessage,
  onMicToggle,
  isMicActive,
  silenceTimer,
  isInputDisabled,
  sttMode,
}) {
  const scrollRef = useRef(null);
  const [sttBannerDismissed, setSttBannerDismissed] = useState(false);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const showTimer = silenceTimer?.isRunning && silenceTimer?.progress > 0;
  const showSttBanner = sttMode === 'browser' && !sttBannerDismissed;

  return (
    <>
      {/* STT fallback banner */}
      {showSttBanner && (
        <div className="flex items-center justify-between px-4 py-2 bg-amber-500/10 border-b border-amber-500/20 text-amber-400 text-xs">
          <span>Server speech-to-text unavailable — using browser fallback</span>
          <button
            onClick={() => setSttBannerDismissed(true)}
            className="ml-2 text-amber-500 hover:text-amber-300 font-bold"
            aria-label="Dismiss notification"
          >
            ✕
          </button>
        </div>
      )}

      {/* Chat Bubble List */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-5 py-4 space-y-3"
        role="log"
        aria-live="polite"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-neutral-600">
            <div className="text-5xl mb-3 opacity-30">💬</div>
            <p className="text-sm font-medium">No conversation yet</p>
            <p className="text-xs mt-1">Select a photo and start a session</p>
          </div>
        ) : (
          messages.map((msg, i) => <ChatBubble key={i} message={msg} />)
        )}
      </div>

      {/* Silence Timer Bar */}
      {showTimer && (
        <div className="px-5 py-1.5">
          <div className="flex items-center gap-2 text-xs text-fuchsia-400 mb-1">
            <span className="inline-block w-2 h-2 rounded-full bg-fuchsia-400 animate-pulse" />
            <span>
              Waiting... {Math.round(silenceTimer.elapsed / 1000)}s / {Math.round(silenceTimer.timeout / 1000)}s
            </span>
          </div>
          <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
            <div
              className="h-full bg-fuchsia-500 rounded-full transition-all duration-100 ease-linear"
              style={{ width: `${silenceTimer.progress * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Text Input */}
      <TextInput
        onSubmit={onSendMessage}
        onMicToggle={onMicToggle}
        isMicActive={isMicActive}
        disabled={isInputDisabled}
      />
    </>
  );
}
