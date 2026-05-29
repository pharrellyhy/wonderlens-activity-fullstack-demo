import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { CompassIcon } from '../icons';

const STREAM_INTERVAL_MS = 24;
const STREAM_STEPS = 32;

function prefersReducedMotion() {
  return typeof window !== 'undefined'
    && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}

function useTypewriterText(text, enabled) {
  const shouldAnimate = enabled && !prefersReducedMotion();
  const characters = useMemo(() => Array.from(text), [text]);
  const [visibleCount, setVisibleCount] = useState(shouldAnimate ? 0 : characters.length);

  useEffect(() => {
    if (!shouldAnimate) {
      return undefined;
    }

    const charactersPerStep = Math.max(1, Math.ceil(characters.length / STREAM_STEPS));
    let index = 0;

    const timer = window.setInterval(() => {
      index = Math.min(index + charactersPerStep, characters.length);
      setVisibleCount(index);
      if (index >= characters.length) {
        window.clearInterval(timer);
      }
    }, STREAM_INTERVAL_MS);

    return () => window.clearInterval(timer);
  }, [characters, shouldAnimate]);

  return shouldAnimate ? characters.slice(0, visibleCount).join('') : text;
}

function MessageAvatar({ role }) {
  if (role === 'ai') {
    return (
      <span className="activity-message__avatar activity-message__avatar--ai" aria-label="WonderLens profile">
        <CompassIcon />
      </span>
    );
  }

  return <span className="activity-message__avatar activity-message__avatar--child" aria-label="Child profile" />;
}

function MessageText({ text, streaming, onStreamUpdate }) {
  const displayed = useTypewriterText(text, streaming);
  const isStreaming = streaming && displayed.length < text.length;

  useEffect(() => {
    if (streaming) onStreamUpdate?.();
  }, [displayed, onStreamUpdate, streaming]);

  return (
    <p>
      {displayed}
      {isStreaming ? <span className="activity-message__cursor" aria-hidden="true" /> : null}
    </p>
  );
}

function PendingMessage({ label }) {
  return (
    <div className="activity-message is-ai is-pending" role="status" aria-live="polite">
      <MessageAvatar role="ai" />
      <div className="activity-message__bubble">
        <span className="activity-message__speaker">WonderLens</span>
        <span className="activity-message__typing" aria-label={label}>
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </span>
      </div>
    </div>
  );
}

export default function ActivityTranscript({ messages, loading, turnPending }) {
  const messagesRef = useRef(null);
  const latestAiIndex = useMemo(() => {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      if (messages[index].role === 'ai') return index;
    }
    return -1;
  }, [messages]);
  const waitingLabel = loading ? 'WonderLens is starting' : 'WonderLens is thinking';
  const scrollToBottom = useCallback(() => {
    const node = messagesRef.current;
    if (!node) return;
    if (typeof node.scrollTo === 'function') {
      node.scrollTo({ top: node.scrollHeight, behavior: 'smooth' });
    } else {
      node.scrollTop = node.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [loading, messages, scrollToBottom, turnPending]);

  return (
    <section className="activity-game__transcript" aria-label="Activity transcript">
      <div className="activity-game__section-head">
        <h2>Transcript</h2>
        <span>{turnPending ? 'thinking' : loading ? 'starting' : 'ready'}</span>
      </div>

      <div className="activity-transcript__messages" ref={messagesRef}>
        {messages.length ? messages.map((message, index) => (
          <div
            key={`${message.role}-${index}-${message.text}`}
            className={message.role === 'child' ? 'activity-message is-child' : 'activity-message is-ai'}
          >
            <MessageAvatar role={message.role} />
            <div className="activity-message__bubble">
              <span className="activity-message__speaker">{message.role === 'child' ? 'You' : 'WonderLens'}</span>
              <MessageText
                text={message.text}
                streaming={message.role === 'ai' && index === latestAiIndex}
                onStreamUpdate={scrollToBottom}
              />
            </div>
          </div>
        )) : (
          <div className="activity-transcript__empty">
            <p>Select an activity and start when ready.</p>
          </div>
        )}
        {loading || turnPending ? <PendingMessage label={waitingLabel} /> : null}
      </div>
    </section>
  );
}
