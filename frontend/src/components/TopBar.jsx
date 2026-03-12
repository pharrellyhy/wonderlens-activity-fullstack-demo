export default function TopBar({ tier, onTierChange, activityName, onNewSession, sessionActive }) {
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-white border-b border-gray-200 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xl font-bold bg-gradient-to-r from-purple-600 to-pink-500 bg-clip-text text-transparent">
          WonderLens Demo
        </span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-500 font-medium">Tier:</label>
          <select
            value={tier}
            onChange={(e) => onTierChange(e.target.value)}
            disabled={sessionActive}
            className="text-sm border border-gray-300 rounded-lg px-2 py-1 bg-white disabled:opacity-50 focus:ring-2 focus:ring-purple-300 focus:border-purple-400 outline-none"
          >
            <option value="T0">T0 (2-4)</option>
            <option value="T1">T1 (4-6)</option>
            <option value="T2">T2 (6-8)</option>
          </select>
        </div>

        {activityName && (
          <span className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full">
            {activityName}
          </span>
        )}

        <button
          onClick={onNewSession}
          className="text-sm px-4 py-1.5 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors font-medium disabled:opacity-50"
        >
          New Session
        </button>
      </div>
    </div>
  );
}
