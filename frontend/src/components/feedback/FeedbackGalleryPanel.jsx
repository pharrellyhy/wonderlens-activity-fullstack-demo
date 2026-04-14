import { useEffect, useMemo, useState } from 'react';
import { fetchFeedbackList } from '../../utils/api.js';
import { FEEDBACK_TAGS } from './tags.js';
import { TAG_STYLES } from './tagStyles.js';
import FeedbackGalleryCard from './FeedbackGalleryCard.jsx';
import ScreenshotLightbox from './ScreenshotLightbox.jsx';

const TAG_FILTER_OPTIONS = [{ id: 'all', label: 'All', color: null }, ...FEEDBACK_TAGS];

export default function FeedbackGalleryPanel({ onBack }) {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTag, setActiveTag] = useState('all');
  const [activeTester, setActiveTester] = useState('all');
  const [sortOrder, setSortOrder] = useState('newest');
  const [lightbox, setLightbox] = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetchFeedbackList()
      .then((body) => {
        if (cancelled) return;
        setEntries(Array.isArray(body?.entries) ? body.entries : []);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err?.message || 'Failed to load feedback');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const testers = useMemo(() => {
    const set = new Set();
    for (const entry of entries) {
      const alias = entry?.session?.tester_alias;
      if (alias) set.add(alias);
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [entries]);

  const visibleEntries = useMemo(() => {
    const filtered = entries.filter((entry) => {
      const flag = entry?.flag || {};
      const session = entry?.session || {};
      if (activeTag !== 'all') {
        const tags = Array.isArray(flag.tags) ? flag.tags : [];
        if (!tags.includes(activeTag)) return false;
      }
      if (activeTester !== 'all' && session.tester_alias !== activeTester) {
        return false;
      }
      return true;
    });

    const direction = sortOrder === 'newest' ? -1 : 1;
    return filtered.slice().sort((a, b) => {
      const ta = Date.parse(a?.flag?.flagged_at) || 0;
      const tb = Date.parse(b?.flag?.flagged_at) || 0;
      return (ta - tb) * direction;
    });
  }, [entries, activeTag, activeTester, sortOrder]);

  return (
    <div className="min-h-screen bg-[var(--color-nature-warm)] px-4 py-6 sm:py-10">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between gap-3 flex-wrap mb-5">
          <div>
            <h1 className="text-2xl font-semibold text-[var(--color-forest-dark)]">
              Feedback gallery
            </h1>
            <p className="text-sm text-[var(--color-forest-dark)]/70">
              {loading ? 'Loading…' : `${visibleEntries.length} of ${entries.length} flags`}
            </p>
          </div>
          <button
            type="button"
            onClick={onBack}
            className="text-sm font-medium text-[var(--color-forest-dark)]/80 hover:text-[var(--color-forest-dark)] underline-offset-2 hover:underline cursor-pointer"
          >
            ← Back to photos
          </button>
        </div>

        <div className="surface-card rounded-2xl p-4 mb-4 flex flex-col gap-3">
          <div className="flex flex-wrap gap-2">
            {TAG_FILTER_OPTIONS.map((opt) => {
              const active = opt.id === activeTag;
              const styles = opt.color ? TAG_STYLES[opt.color] : null;
              const className = [
                'px-3 py-1 rounded-full text-xs font-semibold border transition',
                active
                  ? styles?.selected ||
                    'bg-[var(--color-forest)] text-white border-[var(--color-forest)]'
                  : styles?.idle ||
                    'bg-transparent text-[var(--color-forest-dark)]/80 border-[var(--color-forest)]/30 hover:bg-[var(--color-forest)]/10',
                'cursor-pointer',
              ].join(' ');
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setActiveTag(opt.id)}
                  className={className}
                  aria-pressed={active}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>

          <div className="flex flex-wrap items-center gap-3 text-sm">
            <label className="flex items-center gap-2 text-[var(--color-forest-dark)]/80">
              Tester
              <select
                value={activeTester}
                onChange={(e) => setActiveTester(e.target.value)}
                className="px-2 py-1 rounded-lg border border-[var(--color-forest)]/30 bg-white text-sm text-[var(--color-forest-dark)] focus:outline-none focus:ring-2 focus:ring-[var(--color-forest)]/40"
              >
                <option value="all">All testers</option>
                {testers.map((alias) => (
                  <option key={alias} value={alias}>
                    {alias}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              onClick={() => setSortOrder((prev) => (prev === 'newest' ? 'oldest' : 'newest'))}
              className="px-3 py-1 rounded-full border border-[var(--color-forest)]/30 text-xs font-semibold text-[var(--color-forest-dark)]/80 hover:bg-[var(--color-forest)]/10 cursor-pointer"
              aria-label="Toggle sort order"
            >
              {sortOrder === 'newest' ? 'Newest first ↓' : 'Oldest first ↑'}
            </button>
          </div>
        </div>

        {error ? (
          <div className="surface-card rounded-2xl p-6 text-center text-sm text-red-700">
            {error}
          </div>
        ) : loading ? (
          <div className="surface-card rounded-2xl p-10 text-center text-sm text-[var(--color-forest-dark)]/70">
            Loading feedback…
          </div>
        ) : visibleEntries.length === 0 ? (
          <div className="surface-card rounded-2xl p-10 text-center text-sm text-[var(--color-forest-dark)]/70">
            {entries.length === 0
              ? 'No feedback has been submitted yet.'
              : 'No flags match the current filters.'}
          </div>
        ) : (
          <ul className="space-y-3">
            {visibleEntries.map((entry) => (
              <FeedbackGalleryCard
                key={`${entry?.session?.folder_name}:${entry?.flag?.flag_id}`}
                entry={entry}
                onImageClick={(src, alt) => setLightbox({ src, alt })}
              />
            ))}
          </ul>
        )}
      </div>

      {lightbox ? (
        <ScreenshotLightbox
          src={lightbox.src}
          alt={lightbox.alt}
          onClose={() => setLightbox(null)}
        />
      ) : null}
    </div>
  );
}
