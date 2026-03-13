export default function BadgeAward({ title, concepts = [], animation, entity }) {
  return (
    <div className={`flex flex-col items-center gap-4 p-6 ${
      animation === 'badge_reveal' ? 'animate-bounce-in' : ''
    }`}>
      {/* Badge */}
      <div className="relative">
        <div className="w-32 h-32 rounded-full bg-gradient-to-br from-amber-300 via-yellow-400 to-orange-400 shadow-lg shadow-amber-200/50 flex items-center justify-center border-4 border-white/80">
          <div className="w-24 h-24 rounded-full bg-white/60 backdrop-blur-sm flex items-center justify-center">
            <span className="text-4xl">🏆</span>
          </div>
        </div>
        <span className="absolute -top-2 -right-2 text-2xl animate-spin-slow">✨</span>
        <span className="absolute -bottom-1 -left-2 text-xl animate-ping">⭐</span>
      </div>

      {/* Title */}
      <h2 className="text-xl font-bold font-display text-center text-gray-800 tracking-tight">
        {title || 'Explorer'}
      </h2>

      {entity && (
        <p className="text-sm text-gray-400">{entity}</p>
      )}

      {/* Concepts */}
      {concepts.length > 0 && (
        <div className="flex flex-wrap justify-center gap-2 mt-2">
          {concepts.map((concept, i) => (
            <span
              key={i}
              className="px-4 py-1.5 bg-white/50 text-indigo-600 rounded-full text-sm font-medium border border-indigo-100 shadow-sm"
              style={{ animationDelay: `${i * 300}ms` }}
            >
              {concept}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
