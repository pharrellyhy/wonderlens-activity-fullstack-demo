import { useState } from 'react';
import { LeafIcon } from '../icons';
import { asset } from '../utils/basePath';

function formatSummaryLabel(str) {
  if (!str) return '';
  return str
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

const CATEGORY_LABELS = {
  category_1: 'In-Device Verbal',
  category_5: 'Out-of-Device Collection',
};

function CollectiblePreview({ item }) {
  const [showFallbackIcon, setShowFallbackIcon] = useState(false);

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="w-12 h-12 max-[380px]:w-10 max-[380px]:h-10 rounded-xl max-[380px]:rounded-lg bg-[var(--color-nature-canvas-bg)] border border-[var(--color-forest)]/10 flex items-center justify-center overflow-hidden">
        {showFallbackIcon ? (
          <span className="text-lg max-[380px]:text-base" aria-hidden="true">🔍</span>
        ) : (
          <img
            src={asset(item.image)}
            alt={item.label}
            className="w-10 h-10 max-[380px]:w-8 max-[380px]:h-8 object-contain"
            onError={() => setShowFallbackIcon(true)}
          />
        )}
      </div>
      <span className="text-[10px] max-[380px]:text-[9px] text-gray-500 text-center leading-tight">{item.label}</span>
    </div>
  );
}

export default function GameDetailView({ photo, onBack, onStart, isLoading }) {
  const s = photo.summary || {};
  const isCat1 = s.category === 'category_1';

  return (
    <div className="flex flex-col items-center h-full p-6 max-[380px]:p-4 overflow-y-auto">
      {/* Back link */}
      <div className="w-full max-w-lg mb-4 max-[380px]:mb-3">
        <button
          onClick={onBack}
          className="text-sm max-[380px]:text-xs text-[var(--color-forest)] hover:text-[var(--color-forest-dark)] font-medium transition-colors cursor-pointer"
        >
          &larr; Back to games
        </button>
      </div>

      {/* Hero */}
      <div className="flex flex-col items-center mb-6 max-[380px]:mb-4">
        <div className="w-12 h-12 sm:w-16 sm:h-16 max-[380px]:w-10 max-[380px]:h-10 rounded-2xl max-[380px]:rounded-xl overflow-hidden shadow-lg mb-3 max-[380px]:mb-2 ring-2 ring-[var(--color-forest)]/20">
          <img src={photo.src} alt={photo.label} className="w-full h-full object-cover" />
        </div>
        <h2 className="text-xl sm:text-2xl max-[380px]:text-lg font-bold font-display text-[var(--color-forest-dark)] tracking-tight mb-2 text-center">
          {photo.label}
        </h2>
        <div className="flex flex-wrap gap-2 justify-center">
          <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--color-forest)]/10 text-[var(--color-forest-dark)]">
            {CATEGORY_LABELS[s.category] || s.category}
          </span>
          {s.tier && (
            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--color-nature-warm)] text-[var(--color-forest-dark)]">
              {s.tierLabel || s.tier} &middot; Ages {s.ages}
            </span>
          )}
        </div>
      </div>

      {/* About This Activity */}
      <div className="w-full max-w-lg rounded-2xl max-[380px]:rounded-xl bg-white/70 border border-[var(--color-forest)]/10 p-4 max-[380px]:p-3 mb-4 shadow-sm">
        <h3 className="text-sm font-bold text-[var(--color-forest-dark)] mb-2">About This Activity</h3>
        {s.metaphor && (
          <p className="text-sm max-[380px]:text-xs text-gray-600 italic mb-3">&ldquo;{s.metaphor}&rdquo;</p>
        )}
        {s.role_title && (
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs text-gray-500">Your child earns the title:</span>
            <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-gradient-to-r from-[var(--color-forest)] to-[var(--color-forest-dark)] text-white">
              {s.role_title}
            </span>
          </div>
        )}

        {/* IB tags */}
        <div className="flex flex-wrap gap-1.5">
          {s.ib_theme && (
            <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-[var(--color-nature-sky)] text-[var(--color-forest-dark)]">
              {s.ib_theme}
            </span>
          )}
          {s.ib_key_concept && (
            <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-[var(--color-nature-grass)] text-[var(--color-forest-dark)]">
              {s.ib_key_concept}
            </span>
          )}
          {s.concepts_earned?.filter((c) => c !== s.ib_key_concept).map((concept) => (
            <span
              key={concept}
              className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-[var(--color-nature-grass)] text-[var(--color-forest-dark)]"
            >
              {concept}
            </span>
          ))}
        </div>
      </div>

      {/* How It Works — adaptive */}
      <div className="w-full max-w-lg rounded-2xl max-[380px]:rounded-xl bg-white/70 border border-[var(--color-forest)]/10 p-4 max-[380px]:p-3 mb-6 max-[380px]:mb-4 shadow-sm">
        <h3 className="text-sm font-bold text-[var(--color-forest-dark)] mb-3">How It Works</h3>

        {isCat1 ? (
          /* Cat1: game mechanic, round scenarios, escalation */
          <div className="space-y-3">
            {s.game_mechanic && (
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-[var(--color-forest)]/10 text-[var(--color-forest-dark)]">
                  {formatSummaryLabel(s.game_mechanic)}
                </span>
                <span className="text-xs text-gray-400">&middot;</span>
                <span className="text-xs text-gray-500">{s.round_count} rounds</span>
              </div>
            )}

            {s.round_scenarios && (
              <ol className="space-y-1.5">
                {s.round_scenarios.map((scenario, i) => (
                  <li key={i} className="flex items-start gap-2.5 max-[380px]:gap-2">
                    <span className="flex-shrink-0 w-5 h-5 max-[380px]:w-4.5 max-[380px]:h-4.5 rounded-full bg-[var(--color-forest)]/10 text-[var(--color-forest-dark)] text-[11px] max-[380px]:text-[10px] font-bold flex items-center justify-center mt-0.5">
                      {i + 1}
                    </span>
                    <span className="text-sm max-[380px]:text-xs text-gray-600 capitalize">{scenario}</span>
                  </li>
                ))}
              </ol>
            )}

            {s.escalation_axis && (
              <div className="flex items-center gap-2 pt-1">
                <div className="flex-1 h-1 rounded-full bg-gradient-to-r from-[var(--color-nature-grass)] to-[var(--color-forest)]" />
                <span className="text-[11px] text-gray-400 italic whitespace-nowrap">{s.escalation_axis}</span>
              </div>
            )}
          </div>
        ) : (
          /* Cat5: collection mission */
          <div className="space-y-3">
            {s.collection_criterion && (
              <p className="text-sm text-gray-600">
                <span className="font-medium text-[var(--color-forest-dark)]">Mission:</span>{' '}
                {s.collection_criterion}
              </p>
            )}

            {s.collection_count && (
              <p className="text-xs text-gray-500">
                Find <span className="font-semibold text-[var(--color-forest-dark)]">{s.collection_count}</span> items to complete the collection
              </p>
            )}

            {/* Collectible previews grid */}
            {s.collectible_previews && s.collectible_previews.length > 0 && (
              <div className="grid grid-cols-4 max-[380px]:gap-1.5 gap-2 pt-1">
                {s.collectible_previews.map((item) => <CollectiblePreview key={item.label} item={item} />)}
              </div>
            )}

            {s.synthesis_type && (
              <div className="flex items-center gap-2 pt-1">
                <LeafIcon className="w-3.5 h-3.5 text-[var(--color-forest)]/40" />
                <span className="text-xs text-gray-500">
                  Wraps up with: <span className="font-medium text-[var(--color-forest-dark)]">{formatSummaryLabel(s.synthesis_type)}</span>
                </span>
              </div>
            )}

            {s.observation_angle && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">
                  Observation focus: <span className="font-medium text-[var(--color-forest-dark)] capitalize">{s.observation_angle}</span>
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="flex items-center gap-2 w-full max-w-lg mb-4 max-[380px]:mb-3">
        <div className="flex-1 h-px bg-[var(--color-forest)]/15" />
        <LeafIcon className="w-4 h-4 max-[380px]:w-3.5 max-[380px]:h-3.5 text-[var(--color-forest)]/25" />
        <div className="flex-1 h-px bg-[var(--color-forest)]/15" />
      </div>

      {/* Start button */}
      <button
        onClick={onStart}
        disabled={isLoading}
        className="w-full max-w-lg py-3 max-[380px]:py-2.5 rounded-2xl max-[380px]:rounded-xl font-bold text-white text-sm max-[380px]:text-xs bg-gradient-to-r from-[var(--color-forest)] to-[var(--color-forest-dark)] shadow-lg hover:shadow-xl hover:scale-[1.01] active:scale-[0.99] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-4 h-4 max-[380px]:w-3.5 max-[380px]:h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Starting...
          </span>
        ) : (
          'Start Adventure →'
        )}
      </button>
    </div>
  );
}
