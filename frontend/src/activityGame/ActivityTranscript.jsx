export default function ActivityTranscript({ messages, loading, turnPending }) {
  return (
    <section className="activity-game__transcript" aria-label="Activity transcript">
      <div className="activity-game__section-head">
        <h2>Transcript</h2>
        <span>{turnPending ? 'thinking' : loading ? 'starting' : 'ready'}</span>
      </div>

      <div className="activity-transcript__messages">
        {messages.length ? messages.map((message, index) => (
          <div
            key={`${message.role}-${index}-${message.text}`}
            className={message.role === 'child' ? 'activity-message is-child' : 'activity-message is-ai'}
          >
            <span>{message.role === 'child' ? 'You' : 'WonderLens'}</span>
            <p>{message.text}</p>
          </div>
        )) : (
          <div className="activity-transcript__empty">
            <p>Select an activity and start when ready.</p>
          </div>
        )}
      </div>
    </section>
  );
}
