export default function FeedbackFlagButton({ onClick, disabled = false }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      data-feedback-overlay="true"
      aria-label="Flag this moment"
      title="Flag this moment"
      className={[
        'fixed bottom-3 right-3 z-[60] w-14 h-14 rounded-full flex items-center justify-center',
        'bg-[var(--color-sunflower)] text-[var(--color-forest-dark)]',
        'border-2 border-[var(--color-forest-dark)]/30',
        'shadow-lg transition-all duration-200',
        disabled
          ? 'opacity-40 cursor-not-allowed'
          : 'cursor-pointer hover:scale-105 hover:shadow-xl hover:bg-[var(--color-sunflower-light)]',
      ].join(' ')}
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        width="26"
        height="26"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.25"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M4 21V4" />
        <path d="M4 4h12l-2 4 2 4H4" />
      </svg>
    </button>
  );
}
