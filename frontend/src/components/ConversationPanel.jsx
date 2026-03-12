import { useEffect, useRef } from 'react';
import ChatBubble from './ChatBubble';
import TextInput from './TextInput';

export default function ConversationPanel({
  messages,
  onSendMessage,
  onMicToggle,
  isMicActive,
  silenceTimer,
  isInputDisabled,
}) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const showTimer = silenceTimer?.isRunning && silenceTimer?.progress > 0;

  return (
    <>
      {/* Chat Bubble List */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-400">
            <div className="text-5xl mb-3 opacity-40">💬</div>
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
          <div className="flex items-center gap-2 text-xs text-amber-600 mb-1">
            <span className="inline-block w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span>
              Waiting... {Math.round(silenceTimer.elapsed / 1000)}s / {Math.round(silenceTimer.timeout / 1000)}s
            </span>
          </div>
          <div className="w-full h-1.5 bg-amber-100 rounded-full overflow-hidden">
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
