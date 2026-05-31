import { asset } from '../utils/basePath';

const CATEGORY_LABELS = {
  category_1: 'Cat1 · Verbal (in-device)',
  category_3: 'Cat3 · Build (guided)',
  category_5: 'Cat5 · Collect (out-of-device)',
};

function titleCase(value) {
  return String(value || '')
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function DetailRow({ label, value }) {
  if (!value) return null;
  return (
    <div className="activity-intro__row">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

/**
 * Tester-facing intro shown when an activity is selected but not yet started.
 * Surfaces the metadata a tester wants before a run (category/mechanic/tier/
 * rounds/concepts/source) plus the activity premise.
 */
export default function ActivityIntro({ activity, iconSrc = '', roundCount = 3 }) {
  if (!activity) {
    return (
      <div className="activity-transcript__empty">
        <p>Select an activity to see its details, then start when ready.</p>
      </div>
    );
  }

  const categoryLabel = CATEGORY_LABELS[activity.category] || titleCase(activity.category);
  const concepts = (activity.core_ib_key_concepts || []).join(' · ');

  return (
    <div className="activity-intro" aria-label={`${activity.name} details`}>
      <div className="activity-intro__head">
        {iconSrc ? <img className="activity-intro__icon" src={asset(iconSrc)} alt="" aria-hidden="true" /> : null}
        <div>
          <p className="activity-intro__eyebrow">Up next · activity details</p>
          <p className="activity-intro__title">{activity.name}</p>
        </div>
      </div>

      {activity.premise ? <p className="activity-intro__premise">{activity.premise}</p> : null}

      <dl className="activity-intro__details">
        <DetailRow label="Category" value={categoryLabel} />
        <DetailRow label="Mechanic" value={titleCase(activity.mechanic)} />
        <DetailRow label="Tier" value={(activity.tier || 'T1').toUpperCase()} />
        <DetailRow label="Rounds" value={String(roundCount)} />
        <DetailRow label="IB Focus" value={concepts} />
        <DetailRow label="Source" value={activity.source_export_id} />
      </dl>

      <p className="activity-intro__hint">Press the green button on the device to begin.</p>
    </div>
  );
}
