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
  loading,
  turnPending,
  errorExit,
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
            className="ml-2 text-amber-400 hover:text-amber-600 font-bold"
            aria-label="Dismiss notification"
          >
            ✕
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
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center mb-4 shadow-lg shadow-indigo-200/50">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p className="text-sm font-semibold text-gray-500">No conversation yet</p>
            <p className="text-xs text-gray-400 mt-1">Select a photo to get started</p>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <div key={i} className={msg.errorExit ? 'border-l-2 border-amber-300 pl-2' : ''}>
                <ChatBubble message={msg} />
              </div>
            ))}

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
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center mr-2 mt-1 flex-shrink-0 shadow-sm">
                  <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div className="bg-white/70 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-gray-400 typing-dot" />
                  <span className="w-2 h-2 rounded-full bg-gray-400 typing-dot" />
                  <span className="w-2 h-2 rounded-full bg-gray-400 typing-dot" />
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
