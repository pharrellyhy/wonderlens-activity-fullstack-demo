export default function TopBar({ tier, onTierChange, activityName, onNewSession, sessionActive }) {
  return (
    <div className="flex items-center justify-between px-4 py-3 bg-[#111] border-b border-white/5">
      <div className="flex items-center gap-2.5">
        <div className="w-2 h-2 rounded-full bg-fuchsia-500" />
        <span className="text-lg font-bold font-display text-white">
          WonderLens Demo
        </span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <label className="text-sm text-neutral-500 font-medium">Tier:</label>
          <select
            value={tier}
            onChange={(e) => onTierChange(e.target.value)}
            disabled={sessionActive}
            aria-label="Select age tier"
            className="text-sm border border-white/10 rounded-lg px-2 py-1 bg-white/5 text-neutral-200 disabled:opacity-50 focus:ring-1 focus:ring-fuchsia-500 focus:border-fuchsia-500 outline-none"
          >
            <option value="T0">T0 (2-4)</option>
            <option value="T1">T1 (4-6)</option>
            <option value="T2">T2 (6-8)</option>
          </select>
        </div>

        {activityName && (
          <span className="text-sm text-neutral-400 bg-white/5 px-3 py-1 rounded-full">
            {activityName}
          </span>
        )}

        <button
          onClick={onNewSession}
          aria-label="Start new session"
          className="text-sm px-4 py-1.5 bg-fuchsia-500 text-white rounded-full hover:bg-fuchsia-400 transition-colors font-semibold disabled:opacity-50"
        >
          New Session
        </button>
      </div>
    </div>
  );
}
