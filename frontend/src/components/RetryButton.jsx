export default function RetryButton({ onRetry, retryCount = 0, maxRetries = 3 }) {
  if (retryCount >= maxRetries) {
    return (
      <div className="flex flex-col items-center gap-2 p-4">
        <div className="text-sm text-amber-600 surface-card px-4 py-2 rounded-full border border-amber-200/50">
          Using backup mode
        </div>
        <p className="text-xs text-gray-500">The experience continues with a pre-authored recipe</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3 p-6">
      <p className="text-gray-500 text-sm">Oops! Something went wrong.</p>
      <button
        onClick={onRetry}
        className="px-6 py-2.5 bg-[var(--color-forest)] text-white rounded-full hover:bg-[var(--color-forest-dark)] transition-all font-semibold shadow-sm hover:shadow-md"
      >
        Let&apos;s try again!
      </button>
      {retryCount > 0 && (
        <p className="text-xs text-gray-500">Attempt {retryCount} of {maxRetries}</p>
      )}
    </div>
  );
}
