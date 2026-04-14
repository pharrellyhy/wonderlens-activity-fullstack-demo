/**
 * Explorer's Map — React + CSS widget for Cat 5 activities.
 *
 * Pure React component using Tailwind CSS, matching the visual language
 * of the existing widget system (BadgeAward, ProgressTracker).
 * No canvas — just styled divs, images, and CSS animations.
 */

import { asset } from '../utils/basePath';
import { CheckmarkIcon, StarIcon } from '../icons';

function ZoneSlot({ index, isRevealed, isActive, character }) {
  if (isRevealed && character) {
    return (
      <div className="flex flex-col items-center gap-1.5 animate-grow-in">
        {/* Character image */}
        <div className="relative">
          <div className="w-[clamp(4.5rem,18vw,6rem)] h-[clamp(4.5rem,18vw,6rem)] rounded-full bg-gradient-to-br from-[var(--color-forest)] to-[var(--color-forest-dark)] border-[3px] border-white/80 shadow-lg overflow-hidden animate-gentle-float"
            style={{ animationDelay: `${index * 200}ms` }}
          >
            <img
              src={asset(character.image)}
              alt={character.name || character.id}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Checkmark badge */}
          <div className="absolute -bottom-0.5 -right-0.5 w-6 h-6 rounded-full bg-[var(--color-forest)] border-2 border-white flex items-center justify-center shadow-sm">
            <CheckmarkIcon className="w-3 h-3 text-white" />
          </div>
        </div>

        {/* Character name */}
        {character.name && (
          <span className="px-3 py-1 bg-white/90 backdrop-blur-sm rounded-full text-sm font-semibold text-[var(--color-forest-dark)] shadow-sm border border-[var(--color-forest)]/15 max-w-[7rem] truncate animate-fade-in">
            {character.name}
          </span>
        )}
      </div>
    );
  }

  // Unrevealed fog zone
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div
        className={`w-[clamp(4.5rem,18vw,6rem)] h-[clamp(4.5rem,18vw,6rem)] rounded-full flex items-center justify-center transition-all duration-700
          ${isActive
            ? 'bg-[var(--color-sky-light)]/40 border-[3px] border-[var(--color-teal)]/60 border-dashed animate-gentle-glow shadow-md'
            : 'bg-[var(--color-sky-light)]/25 border-[3px] border-[var(--color-sky)]/30 border-dashed'
          }`}
      >
        <span className={`text-2xl font-bold transition-colors ${isActive ? 'text-[var(--color-teal)]' : 'text-[var(--color-sky)]/60'}`}>?</span>
      </div>
      <span className="text-xs text-gray-400 font-medium">{index + 1}</span>
    </div>
  );
}

function ConnectionDot() {
  return (
    <div className="flex items-center px-0.5 self-start mt-[clamp(2rem,8vw,2.8rem)]">
      <div className="flex gap-[3px]">
        <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-forest)]/25" />
        <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-forest)]/20" />
        <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-forest)]/15" />
      </div>
    </div>
  );
}

function ConnectionLine({ animated }) {
  return (
    <div className="flex items-center px-0.5 self-start mt-[clamp(2rem,8vw,2.8rem)]">
      <div className={`h-0.5 w-5 rounded-full ${animated ? 'bg-[var(--color-sunflower)] animate-sfx-pulse' : 'bg-[var(--color-forest)]/20'}`} />
    </div>
  );
}

function MapView({ revealed_zones, characters, total_zones, active_zone, game_phase }) {
  const isSynthesis = game_phase === 'synthesis';
  const zones = Array.from({ length: total_zones }, (_, i) => {
    const isRevealed = revealed_zones.includes(i);
    const character = characters.find((c) => c.zone_index === i);
    const isActive = active_zone === i;
    return { index: i, isRevealed, character, isActive };
  });

  return (
    <div className="flex items-start justify-center gap-1">
      {zones.map((zone, i) => (
        <div key={i} className="contents">
          {i > 0 && (isSynthesis && zone.isRevealed
            ? <ConnectionLine animated />
            : <ConnectionDot />
          )}
          <ZoneSlot
            index={zone.index}
            isRevealed={zone.isRevealed}
            isActive={zone.isActive}
            character={zone.character}
          />
        </div>
      ))}
    </div>
  );
}

function BadgeOverlay({ badge_title, badge_concepts }) {
  return (
    <div className="flex flex-col items-center gap-2 animate-badge-pop">
      {/* Badge circle */}
      <div className="relative">
        <div className="w-[clamp(5.5rem,22vw,7.5rem)] h-[clamp(5.5rem,22vw,7.5rem)] rounded-full bg-gradient-to-br from-[var(--color-sunflower)] via-[var(--color-sunflower-light)] to-[var(--color-forest)] shadow-lg flex items-center justify-center border-[3px] border-white/80">
          <div className="w-[clamp(3.5rem,15vw,5rem)] h-[clamp(3.5rem,15vw,5rem)] rounded-full bg-white/70 flex items-center justify-center">
            <span className="text-3xl">🏆</span>
          </div>
        </div>
        <div className="absolute -top-2 -right-2 animate-sparkle-large">
          <StarIcon className="w-5 h-5 text-[var(--color-sunflower)]" />
        </div>
        <div className="absolute -bottom-1.5 -left-2 animate-sparkle-large" style={{ animationDelay: '0.8s' }}>
          <StarIcon className="w-4.5 h-4.5 text-[var(--color-forest)]" />
        </div>
      </div>

      {/* Title */}
      <h3 className="text-lg font-bold font-display text-[var(--color-forest-dark)] text-center tracking-tight">
        {badge_title || 'Explorer'}
      </h3>

      {/* Concept pills */}
      {badge_concepts.length > 0 && (
        <div className="flex flex-wrap justify-center gap-2">
          {badge_concepts.map((concept, i) => (
            <span
              key={concept}
              className="px-4 py-1.5 bg-[var(--color-forest)]/10 text-[var(--color-forest-dark)] rounded-full text-sm font-medium border border-[var(--color-forest)]/20 shadow-sm animate-badge-pop"
              style={{ animationDelay: `${(i + 1) * 300}ms` }}
            >
              {concept}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function PhaseLabel({ game_phase, collected_count, total_zones }) {
  const config = {
    hook:          { text: 'Your adventure begins...',                icon: '✨', color: 'text-[var(--color-teal)]' },
    mission:       { text: 'Ready to explore?',                      icon: '🧭', color: 'text-[var(--color-forest)]' },
    collect_photo: { text: `Finding ${collected_count} of ${total_zones}`, icon: '🔍', color: 'text-[var(--color-forest)]' },
    collect_reveal:{ text: `Found ${collected_count} of ${total_zones}!`, icon: '🎉', color: 'text-[var(--color-forest)]' },
    collect_detail:{ text: `Found ${collected_count} of ${total_zones}!`, icon: '🎉', color: 'text-[var(--color-forest)]' },
    collect_named: { text: `Named ${collected_count} of ${total_zones}`,  icon: '🏷️', color: 'text-[var(--color-teal)]' },
    synthesis:     { text: 'All friends together!',                  icon: '🌟', color: 'text-[var(--color-sunflower-dark)]' },
  };

  const phase = config[game_phase];
  if (!phase) return null;

  return (
    <div className={`flex items-center justify-center gap-2 px-4 py-1.5 rounded-full bg-white/70 backdrop-blur-sm shadow-sm border border-[var(--color-forest)]/10 ${
      game_phase.startsWith('collect_reveal') ? 'animate-grow-in' : ''
    }`}>
      <span className="text-base">{phase.icon}</span>
      <p className={`text-base font-bold font-display tracking-tight ${phase.color}`}>
        {phase.text}
      </p>
    </div>
  );
}

export default function ExplorerMap({
  game_phase,
  revealed_zones = [],
  characters = [],
  active_zone,
  total_zones = 3,
  collected_count = 0,
  badge_title = '',
  badge_concepts = [],
}) {
  const isCelebrate = game_phase === 'celebrate' || game_phase === 'closing';

  return (
    <div className="w-full h-full flex flex-col items-center justify-center gap-4 p-4 max-[380px]:p-3 rounded-xl bg-gradient-to-b from-[var(--color-sky-light)]/20 via-white/40 to-[var(--color-forest)]/5">
      {isCelebrate ? (
        <BadgeOverlay badge_title={badge_title} badge_concepts={badge_concepts} />
      ) : (
        <>
          {/* Zone slots */}
          <MapView
            revealed_zones={revealed_zones}
            characters={characters}
            total_zones={total_zones}
            active_zone={active_zone}
            game_phase={game_phase}
          />

          {/* Phase label */}
          <PhaseLabel
            game_phase={game_phase}
            collected_count={collected_count}
            total_zones={total_zones}
          />

          {/* Progress bar */}
          {collected_count > 0 && !isCelebrate && (
            <div className="w-full max-w-[16rem]">
              <div className="h-2 rounded-full bg-[var(--color-sky-light)]/30 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[var(--color-forest)] to-[var(--color-teal)] transition-all duration-700 ease-out"
                  style={{ width: `${(collected_count / total_zones) * 100}%` }}
                />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
