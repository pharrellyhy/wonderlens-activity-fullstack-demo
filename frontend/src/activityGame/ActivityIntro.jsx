import { asset } from '../utils/basePath';

const MECHANIC_LABELS = {
  motion_voice: 'Voice play',
  decide: 'Make a choice',
  enumerate: 'Count along',
  care: 'Read a feeling',
  build: 'Build step by step',
  deduce: 'Guess the clue',
  collect: 'Treasure hunt',
  compare: 'Find the match',
  imagine: 'Unlock a story',
  predict: 'Plan ahead',
  sort: 'Sort it out',
  remember: 'Echo it back',
};

function titleCase(value) {
  return String(value || '')
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Brief, child-facing intro shown when an activity is selected but not yet
 * started. Distinct from the operator-facing detail view: just enough to set
 * expectations before pressing the device's green button.
 */
export default function ActivityIntro({ activity, iconSrc = '', roundCount = 3 }) {
  if (!activity) {
    return (
      <div className="activity-transcript__empty">
        <p>Select an activity and start when ready.</p>
      </div>
    );
  }

  const mechanicLabel = MECHANIC_LABELS[activity.mechanic] || titleCase(activity.mechanic);
  const concepts = (activity.core_ib_key_concepts || []).slice(0, 2).join(' & ');

  return (
    <div className="activity-intro" aria-label={`${activity.name} introduction`}>
      <div className="activity-intro__head">
        {iconSrc ? <img className="activity-intro__icon" src={asset(iconSrc)} alt="" aria-hidden="true" /> : null}
        <div>
          <p className="activity-intro__eyebrow">Up next</p>
          <p className="activity-intro__title">{activity.name}</p>
        </div>
      </div>

      {activity.premise ? <p className="activity-intro__premise">{activity.premise}</p> : null}

      <div className="activity-intro__chips">
        {mechanicLabel ? <span className="activity-intro__chip">{mechanicLabel}</span> : null}
        <span className="activity-intro__chip">{roundCount} short rounds</span>
        {concepts ? <span className="activity-intro__chip">{concepts}</span> : null}
      </div>

      <p className="activity-intro__hint">Press the green button on the device to begin.</p>
    </div>
  );
}
