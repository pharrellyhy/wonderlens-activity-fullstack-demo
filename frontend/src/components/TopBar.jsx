import { CameraIcon, LeafIcon } from '../icons';

export default function TopBar({ tier, onTierChange, activityName, onNewSession, sessionActive }) {
  return (
    <div className="app-topbar flex flex-wrap items-center justify-between gap-2 px-4 sm:px-6 py-2.5 sm:py-3.5 mt-3 mx-3 max-w-4xl sm:mx-auto w-full max-[380px]:mt-2 max-[380px]:mx-2 max-[380px]:px-2.5 max-[380px]:py-1.5 bg-gradient-to-r from-[var(--color-forest)] to-[var(--color-forest-light)] rounded-2xl max-[380px]:rounded-[1.25rem] shadow-md">
      <div className="flex items-center gap-2.5 min-w-0">
        <div className="w-8 h-8 sm:w-10 sm:h-10 max-[380px]:w-6 max-[380px]:h-6 rounded-full bg-white/20 flex items-center justify-center shadow-sm">
          <CameraIcon className="w-4 h-4 sm:w-5 sm:h-5 max-[380px]:w-3 max-[380px]:h-3 text-white" />
        </div>
        <span className="text-lg sm:text-xl max-[380px]:text-sm font-bold font-display text-white tracking-tight truncate">
          WonderLens
        </span>
        <LeafIcon className="w-4 h-4 text-white/50 -ml-1 hidden sm:block" />
      </div>

      <div className="flex items-center gap-2 sm:gap-3 max-[380px]:w-full max-[380px]:justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <label className="text-sm text-white/70 font-medium uppercase tracking-wider hidden sm:inline">Tier</label>
          <select
            value={tier}
            onChange={(e) => onTierChange(e.target.value)}
            disabled={sessionActive}
            aria-label="Select age tier"
            className="text-sm sm:text-base max-[380px]:text-[11px] border border-white/30 rounded-xl px-3 sm:px-4 max-[380px]:px-1.5 py-2 sm:py-2.5 max-[380px]:py-1 min-h-[40px] sm:min-h-[48px] max-[380px]:min-h-[32px] bg-white/20 text-white disabled:opacity-50 focus:ring-2 focus:ring-white/50 focus:border-transparent outline-none transition-shadow"
          >
            <option value="T0" className="text-gray-800">T0 (2-4)</option>
            <option value="T1" className="text-gray-800">T1 (4-6)</option>
            <option value="T2" className="text-gray-800">T2 (6-8)</option>
          </select>
        </div>

        {activityName && (
          <span className="text-sm text-white/80 bg-white/15 px-3.5 py-1.5 rounded-full font-medium hidden sm:inline">
            {activityName}
          </span>
        )}

        <button
          onClick={onNewSession}
          aria-label="Start new session"
          className="text-sm sm:text-base max-[380px]:text-[11px] px-4 sm:px-5 max-[380px]:px-2.5 py-2 sm:py-2.5 max-[380px]:py-1 min-h-[40px] sm:min-h-[48px] max-[380px]:min-h-[32px] bg-white text-[var(--color-forest-dark)] rounded-full hover:bg-white/90 transition-all font-semibold shadow-sm hover:shadow-md"
        >
          New Session
        </button>
      </div>
    </div>
  );
}
