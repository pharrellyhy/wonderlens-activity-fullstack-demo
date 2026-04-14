import { useEffect } from 'react';
import { createPortal } from 'react-dom';

export default function ScreenshotLightbox({ src, alt, onClose }) {
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose?.();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  if (!src) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[80] bg-black/80 flex items-center justify-center p-4 cursor-zoom-out"
      role="dialog"
      aria-modal="true"
      aria-label="Screenshot preview"
      onClick={onClose}
    >
      <img
        src={src}
        alt={alt || 'Feedback screenshot'}
        className="max-w-[92vw] max-h-[92vh] rounded-xl shadow-2xl border border-white/10"
        onClick={(e) => e.stopPropagation()}
      />
      <button
        type="button"
        onClick={onClose}
        aria-label="Close preview"
        className="absolute top-4 right-4 text-white/80 hover:text-white text-sm font-medium rounded-full bg-black/40 px-3 py-1 cursor-pointer"
      >
        × close
      </button>
    </div>,
    document.body,
  );
}
