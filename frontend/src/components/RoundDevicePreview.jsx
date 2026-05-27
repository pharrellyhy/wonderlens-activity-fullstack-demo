import { asset } from '../utils/basePath';

function stepLabel(step) {
  if (!step) return 'Ready';
  return step
    .replace(/^STEP_\d_/, '')
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/^\w/, (letter) => letter.toUpperCase());
}

function pickImage({ screenFrame, photoUrl, sessionState }) {
  const params = screenFrame?.widget_params || {};
  return (
    params.image ||
    params.image_url ||
    params.src ||
    sessionState?.current_round_items?.[0]?.image ||
    photoUrl ||
    ''
  );
}

export default function RoundDevicePreview({ screenFrame, photoUrl, sessionState, isSpeaking = false }) {
  const image = pickImage({ screenFrame, photoUrl, sessionState });
  const title = screenFrame?.widget_label || stepLabel(sessionState?.current_step);
  const prompt = sessionState?.collection_phase === 'detail'
    ? 'Look close'
    : (sessionState?.collection_criterion || screenFrame?.widget_params?.description || '');
  const total = Math.max(Number(sessionState?.total_rounds || 0), 1);
  const current = Math.max(Number(sessionState?.current_round || 0), sessionState?.collected_photos?.length || 0, 1);

  return (
    <div className="round-device-preview">
      <div className="round-device-preview__status">
        <span className="round-device-preview__title">{title}</span>
        {isSpeaking && <span className="round-device-preview__speak">Voice</span>}
      </div>
      <div className="round-device-preview__image">
        {image ? (
          <img src={asset(image)} alt="" />
        ) : (
          <span aria-hidden="true">★</span>
        )}
      </div>
      <p>{prompt}</p>
      <div className="round-device-preview__dots" aria-label={`Round ${Math.min(current, total)} of ${total}`}>
        {Array.from({ length: total }).map((_, idx) => (
          <span
            key={idx}
            className={idx < current ? 'round-device-preview__dot round-device-preview__dot--filled' : 'round-device-preview__dot'}
          />
        ))}
      </div>
    </div>
  );
}
