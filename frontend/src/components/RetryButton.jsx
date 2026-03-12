export default function RetryButton({ onRetry, retryCount = 0, maxRetries = 3 }) {
  if (retryCount >= maxRetries) {
    return (
      <div className="flex flex-col items-center gap-2 p-4">
        <div className="text-sm text-amber-600 bg-amber-50 px-3 py-1.5 rounded-full border border-amber-200">
          Using backup mode
        </div>
        <p className="text-xs text-gray-400">The experience continues with a pre-authored recipe</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3 p-6">
      <p className="text-gray-500 text-sm">Oops! Something went wrong.</p>
      <button
        onClick={onRetry}
        className="px-6 py-2.5 bg-purple-500 text-white rounded-xl hover:bg-purple-600 transition-colors font-medium shadow-md hover:shadow-lg"
      >
        Let&apos;s try again!
      </button>
      {retryCount > 0 && (
        <p className="text-xs text-gray-400">Attempt {retryCount} of {maxRetries}</p>
      )}
    </div>
  );
}
