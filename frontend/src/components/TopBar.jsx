export default function TopBar({ tier, onTierChange, activityName, onNewSession, sessionActive }) {
  return (
    <div className="flex items-center justify-between px-5 py-3 mx-3 mt-3 glass-strong rounded-2xl shadow-md shadow-black/5">
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center shadow-sm">
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <span className="text-lg font-bold font-display text-gray-800 tracking-tight">
          WonderLens
        </span>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-400 font-medium uppercase tracking-wider">Tier</label>
          <select
            value={tier}
            onChange={(e) => onTierChange(e.target.value)}
            disabled={sessionActive}
            aria-label="Select age tier"
            className="text-sm border border-gray-200/60 rounded-xl px-3 py-1.5 bg-white/50 text-gray-700 disabled:opacity-50 focus:ring-2 focus:ring-indigo-300 focus:border-transparent outline-none transition-shadow"
          >
            <option value="T0">T0 (2-4)</option>
            <option value="T1">T1 (4-6)</option>
            <option value="T2">T2 (6-8)</option>
          </select>
        </div>

        {activityName && (
          <span className="text-xs text-gray-500 bg-white/40 px-3 py-1.5 rounded-full font-medium">
            {activityName}
          </span>
        )}

        <button
          onClick={onNewSession}
          aria-label="Start new session"
          className="text-sm px-4 py-1.5 bg-gray-800 text-white rounded-full hover:bg-gray-700 transition-all font-semibold shadow-sm hover:shadow-md"
        >
          New Session
        </button>
      </div>
    </div>
  );
}
