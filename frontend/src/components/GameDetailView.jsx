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

const SUPPORT_LABELS = {
  supported: 'Supported',
  degraded: 'Degraded',
  unsupported: 'Unsupported',
};

const ASSET_LABELS = {
  ready: 'Assets ready',
  partial: 'Assets partial',
  blocked: 'Assets blocked',
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

function StatusChip({ children, tone = 'neutral' }) {
  const toneClass = {
    neutral: 'bg-[var(--color-forest)]/10 text-[var(--color-forest-dark)]',
    good: 'bg-[var(--color-nature-grass)] text-[var(--color-forest-dark)]',
    warn: 'bg-amber-100 text-amber-700',
    danger: 'bg-red-100 text-red-700',
  }[tone];
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${toneClass}`}>
      {children}
    </span>
  );
}

function assetDetailText(detail) {
  const required = detail?.required_missing || [];
  const optional = detail?.optional_missing || [];
  const parts = [];
  if (required.length) parts.push(`Missing required: ${required.join(', ')}`);
  if (optional.length) parts.push(`Missing optional: ${optional.join(', ')}`);
  return parts.join(' · ');
}

function hasMissingRequiredAssets(detail) {
  return (detail?.required_missing || []).length > 0;
}

export default function GameDetailView({ photo, onBack, onStart, isLoading }) {
  const s = photo.summary || {};
  const isCat1 = s.category === 'category_1';
  const [showSteps, setShowSteps] = useState(false);
  const supportStatus = s.support_status || 'supported';
  const assetReadiness = s.asset_readiness || 'ready';
  const isBlocked = supportStatus === 'unsupported' || assetReadiness === 'blocked' || hasMissingRequiredAssets(s.asset_readiness_detail);
  const assetDetail = assetDetailText(s.asset_readiness_detail);

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
          <StatusChip>
            {CATEGORY_LABELS[s.category] || s.category}
          </StatusChip>
          {s.tier && (
            <StatusChip>
              {s.tierLabel || s.tier} &middot; Ages {s.ages}
            </StatusChip>
          )}
          {s.source === 'autodesign' && (
            <StatusChip tone="good">Imported</StatusChip>
          )}
          <StatusChip tone={supportStatus === 'degraded' ? 'warn' : supportStatus === 'unsupported' ? 'danger' : 'good'}>
            {SUPPORT_LABELS[supportStatus] || formatSummaryLabel(supportStatus)}
          </StatusChip>
          <StatusChip tone={assetReadiness === 'partial' ? 'warn' : assetReadiness === 'blocked' ? 'danger' : 'good'}>
            {ASSET_LABELS[assetReadiness] || formatSummaryLabel(assetReadiness)}
          </StatusChip>
        </div>
        {s.entity_binding?.entity_id && (
          <p className="mt-2 text-xs text-gray-500">
            Entity binding: <span className="font-semibold text-[var(--color-forest-dark)]">{s.entity_binding.entity_id}</span>
          </p>
        )}
        {(s.degraded_reasons?.length > 0 || s.support_reasons?.length > 0 || assetDetail) && (
          <div className="mt-3 max-w-lg rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
            {[...(s.degraded_reasons || []), ...(s.support_reasons || [])].map((reason) => (
              <p key={reason}>{reason}</p>
            ))}
            {assetDetail && <p>{assetDetail}</p>}
          </div>
          )}
      </div>

      {/* About This Game */}
      <div className="w-full max-w-lg rounded-2xl max-[380px]:rounded-xl bg-white/70 border border-[var(--color-forest)]/10 p-4 max-[380px]:p-3 mb-4 shadow-sm">
        <h3 className="text-sm font-bold text-[var(--color-forest-dark)] mb-2">About This Game</h3>

        {/* Plain-language summary */}
        {s.plain_description ? (
          <p className="text-sm max-[380px]:text-xs text-gray-600 mb-3">{s.plain_description}</p>
        ) : s.metaphor ? (
          <p className="text-sm max-[380px]:text-xs text-gray-600 italic mb-3">&ldquo;{s.metaphor}&rdquo;</p>
        ) : null}

        {s.role_title && (
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs text-gray-500">You earn the title:</span>
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

      {/* How It Works — always-visible steps */}
      <div className="w-full max-w-lg rounded-2xl max-[380px]:rounded-xl bg-white/70 border border-[var(--color-forest)]/10 p-4 max-[380px]:p-3 mb-6 max-[380px]:mb-4 shadow-sm">
        <h3 className="text-sm font-bold text-[var(--color-forest-dark)] mb-3">How It Works</h3>

        {/* Steps list — always visible */}
        {s.steps_summary && s.steps_summary.length > 0 && (
          <>
            <ol className="space-y-1.5 mb-3">
              {s.steps_summary.map((step, i) => (
                <li key={i} className="flex items-start gap-2.5 max-[380px]:gap-2">
                  <span className="flex-shrink-0 w-5 h-5 max-[380px]:w-4.5 max-[380px]:h-4.5 rounded-full bg-[var(--color-forest)]/10 text-[var(--color-forest-dark)] text-[11px] max-[380px]:text-[10px] font-bold flex items-center justify-center mt-0.5">
                    {i + 1}
                  </span>
                  <span className="text-sm max-[380px]:text-xs text-gray-600">{step}</span>
                </li>
              ))}
            </ol>
          </>
        )}

        {/* Expandable technical details */}
        <button
          onClick={() => setShowSteps(!showSteps)}
          className="text-xs font-medium text-[var(--color-forest)] hover:text-[var(--color-forest-dark)] transition-colors cursor-pointer"
        >
          {showSteps ? '▾ Hide details' : '▸ Game design details'}
        </button>
        {showSteps && (
          <div className="mt-2 space-y-2 pt-2 border-t border-[var(--color-forest)]/10">
            {isCat1 ? (
              <>
                {s.game_mechanic && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">Game type:</span>
                    <span className="text-xs font-medium text-[var(--color-forest-dark)]">{formatSummaryLabel(s.game_mechanic)}</span>
                    <span className="text-xs text-gray-400">&middot;</span>
                    <span className="text-xs text-gray-500">{s.round_count} rounds</span>
                  </div>
                )}
                {s.round_scenarios && (
                  <div className="text-xs text-gray-500">
                    <span className="font-medium text-gray-600">Round scenarios: </span>
                    {s.round_scenarios.map((sc, i) => (
                      <span key={i} className="capitalize">{sc}{i < s.round_scenarios.length - 1 ? ' → ' : ''}</span>
                    ))}
                  </div>
                )}
                {s.escalation_axis && (
                  <div className="text-xs text-gray-500">Escalation: <span className="italic">{s.escalation_axis}</span></div>
                )}
              </>
            ) : (
              <>
                {s.collection_criterion && (
                  <div className="text-xs text-gray-500">Mission: <span className="text-gray-600">{s.collection_criterion}</span></div>
                )}
                {s.collection_count && (
                  <div className="text-xs text-gray-500">Items to find: <span className="font-medium text-[var(--color-forest-dark)]">{s.collection_count}</span></div>
                )}
                {s.synthesis_type && (
                  <div className="text-xs text-gray-500">Wraps up with: <span className="text-gray-600">{formatSummaryLabel(s.synthesis_type)}</span></div>
                )}
                {s.observation_angle && (
                  <div className="text-xs text-gray-500">Observation focus: <span className="text-gray-600 capitalize">{s.observation_angle}</span></div>
                )}
                {s.collectible_previews && s.collectible_previews.length > 0 && (
                  <div className="grid grid-cols-4 max-[380px]:gap-1.5 gap-2 pt-1">
                    {s.collectible_previews.map((item) => <CollectiblePreview key={item.label} item={item} />)}
                  </div>
                )}
              </>
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
        disabled={isLoading || isBlocked}
        className="w-full max-w-lg py-3 max-[380px]:py-2.5 rounded-2xl max-[380px]:rounded-xl font-bold text-white text-sm max-[380px]:text-xs bg-gradient-to-r from-[var(--color-forest)] to-[var(--color-forest-dark)] shadow-lg hover:shadow-xl hover:scale-[1.01] active:scale-[0.99] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-4 h-4 max-[380px]:w-3.5 max-[380px]:h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Starting...
          </span>
        ) : isBlocked ? (
          'Start unavailable'
        ) : (
          'Start Adventure →'
        )}
      </button>
    </div>
  );
}
