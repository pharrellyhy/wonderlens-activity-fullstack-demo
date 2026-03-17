import { useEffect, useRef, useState } from 'react';
import ChatBubble from './ChatBubble';
import TextInput from './TextInput';
import AiAvatar from './AiAvatar';

export default function ConversationPanel({
  messages,
  onSendMessage,
  onMicToggle,
  isMicActive,
  silenceTimer,
  isInputDisabled,
  sttMode,
  loading,
  turnPending,
  errorExit,
  collectMode,
}) {
  const scrollRef = useRef(null);
  const [sttBannerDismissed, setSttBannerDismissed] = useState(false);

  const isWaiting = loading || turnPending;

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isWaiting]);

  const showTimer = silenceTimer?.isRunning && silenceTimer?.progress > 0;
  const showSttBanner = sttMode === 'browser' && !sttBannerDismissed;

  return (
    <>
      {/* STT fallback banner */}
      {showSttBanner && (
        <div className="flex items-center justify-between px-4 py-2 bg-amber-50/80 border-b border-amber-200/50 text-amber-600 text-xs">
          <span>Server speech-to-text unavailable — using browser fallback</span>
          <button
            onClick={() => setSttBannerDismissed(true)}
            className="ml-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-amber-400 hover:text-amber-600 font-bold"
            aria-label="Dismiss notification"
          >
            x
          </button>
        </div>
      )}

      {/* Chat Bubble List */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-5 py-4 space-y-4"
        role="log"
        aria-live="polite"
      >
        {messages.length === 0 && !isWaiting ? (
          <div className="flex flex-col items-center justify-center h-full">
            <AiAvatar size="md" className="mb-4" />
            <p className="text-sm font-semibold text-gray-500">No conversation yet</p>
            <p className="text-xs text-gray-500 mt-1">Select a photo to get started</p>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => {
              const isLatestAi = msg.role === 'ai' && !messages.slice(i + 1).some((m) => m.role === 'ai');
              return (
                <div
                  key={`${i}-${msg.role}-${isLatestAi ? 'latest' : 'static'}-${msg.text}`}
                  className={msg.errorExit ? 'border-l-2 border-amber-300 pl-2' : ''}
                >
                  <ChatBubble message={msg} isLatestAi={isLatestAi} />
                </div>
              );
            })}

            {/* Error exit warning */}
            {errorExit && (
              <div className="flex items-center gap-2 px-3 py-2 bg-amber-50/80 rounded-xl text-xs text-amber-600">
                <span className="w-4 h-4 flex items-center justify-center rounded-full bg-amber-200 text-amber-700 text-[10px] font-bold flex-shrink-0">!</span>
                <span>Session ended due to a connection issue</span>
              </div>
            )}

            {/* Typing indicator */}
            {isWaiting && (
              <div className="flex justify-start animate-fade-in">
                <AiAvatar size="sm" className="mr-2 mt-1" />
                <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm flex items-center gap-1.5 border border-[var(--color-forest)]/10">
                  <span className="w-2 h-2 rounded-full bg-[var(--color-forest)] typing-dot" />
                  <span className="w-2 h-2 rounded-full bg-[var(--color-forest)] typing-dot" />
                  <span className="w-2 h-2 rounded-full bg-[var(--color-forest)] typing-dot" />
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Silence Timer Bar */}
      {showTimer && (
        <div className="px-5 py-1.5">
          <div className="flex items-center gap-2 text-xs text-amber-500 mb-1">
            <span className="inline-block w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span>
              Waiting... {Math.round(silenceTimer.elapsed / 1000)}s / {Math.round(silenceTimer.timeout / 1000)}s
            </span>
          </div>
          <div className="w-full h-1 bg-gray-200/50 rounded-full overflow-hidden">
            <div
              className="h-full bg-amber-400 rounded-full transition-all duration-100 ease-linear"
              style={{ width: `${silenceTimer.progress * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Text Input or collection hint */}
      {collectMode ? (
        <div className="px-4 py-3 text-center">
          <p className="text-xs text-[var(--color-teal)] font-medium">
            Tap a photo in the camera above to collect it!
          </p>
        </div>
      ) : (
        <TextInput
          onSubmit={onSendMessage}
          onMicToggle={onMicToggle}
          isMicActive={isMicActive}
          disabled={isInputDisabled}
        />
      )}
    </>
  );
}
