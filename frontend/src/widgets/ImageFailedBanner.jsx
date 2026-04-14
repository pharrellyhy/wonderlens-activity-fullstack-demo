// Muted amber pill shown in the top-right of a widget when its image was
// supposed to render from generated output but the worker reported a real
// failure (vs. "still pending"). Tester-facing — real users rarely see this
// because failures are infrequent and the underlying fallback graphic still
// carries the experience.
export default function ImageFailedBanner({ label = "Couldn't create this image" }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="absolute top-3 right-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-100/95 border border-amber-300 text-amber-900 text-[11px] font-semibold shadow-sm backdrop-blur-sm animate-fade-in pointer-events-none"
    >
      <svg
        aria-hidden="true"
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 9v4" />
        <path d="M12 17h.01" />
        <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
      </svg>
      <span>{label}</span>
    </div>
  );
}
