import { CameraIcon, LeafIcon } from '../icons';

export default function TopBar({ tier, onTierChange, activityName, onNewSession, sessionActive }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 px-4 sm:px-5 py-3 mx-3 mt-3 bg-gradient-to-r from-[var(--color-forest)] to-[var(--color-forest-light)] rounded-2xl shadow-md">
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center shadow-sm">
          <CameraIcon className="w-4 h-4 text-white" />
        </div>
        <span className="text-lg font-bold font-display text-white tracking-tight">
          WonderLens
        </span>
        <LeafIcon className="w-4 h-4 text-white/50 -ml-1 hidden sm:block" />
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <div className="flex items-center gap-2">
          <label className="text-xs text-white/70 font-medium uppercase tracking-wider hidden sm:inline">Tier</label>
          <select
            value={tier}
            onChange={(e) => onTierChange(e.target.value)}
            disabled={sessionActive}
            aria-label="Select age tier"
            className="text-sm border border-white/30 rounded-xl px-3 py-2 min-h-[44px] bg-white/20 text-white disabled:opacity-50 focus:ring-2 focus:ring-white/50 focus:border-transparent outline-none transition-shadow"
          >
            <option value="T0" className="text-gray-800">T0 (2-4)</option>
            <option value="T1" className="text-gray-800">T1 (4-6)</option>
            <option value="T2" className="text-gray-800">T2 (6-8)</option>
          </select>
        </div>

        {activityName && (
          <span className="text-xs text-white/80 bg-white/15 px-3 py-1.5 rounded-full font-medium hidden sm:inline">
            {activityName}
          </span>
        )}

        <button
          onClick={onNewSession}
          aria-label="Start new session"
          className="text-sm px-4 py-2 min-h-[44px] bg-white text-[var(--color-forest-dark)] rounded-full hover:bg-white/90 transition-all font-semibold shadow-sm hover:shadow-md"
        >
          New Session
        </button>
      </div>
    </div>
  );
}
