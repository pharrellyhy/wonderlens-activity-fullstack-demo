export default function RetryButton({ onRetry, retryCount = 0, maxRetries = 3 }) {
  if (retryCount >= maxRetries) {
    return (
      <div className="flex flex-col items-center gap-2 p-4">
        <div className="text-sm text-amber-400 bg-amber-500/10 px-3 py-1.5 rounded-full border border-amber-500/20">
          Using backup mode
        </div>
        <p className="text-xs text-neutral-500">The experience continues with a pre-authored recipe</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3 p-6">
      <p className="text-neutral-400 text-sm">Oops! Something went wrong.</p>
      <button
        onClick={onRetry}
        className="px-6 py-2.5 bg-fuchsia-500 text-white rounded-full hover:bg-fuchsia-400 transition-colors font-semibold"
      >
        Let&apos;s try again!
      </button>
      {retryCount > 0 && (
        <p className="text-xs text-neutral-500">Attempt {retryCount} of {maxRetries}</p>
      )}
    </div>
  );
}
