import { useState } from 'react';

const DEMO_PHOTOS = [
  { id: 'dog', label: 'Stuffed Dog', src: '/photos/dog.jpg', fallbackEmoji: '🐶' },
  { id: 'ladybug', label: 'Ladybug', src: '/photos/ladybug.jpg', fallbackEmoji: '🐞' },
  { id: 'cat', label: 'Cat', src: '/photos/cat.jpg', fallbackEmoji: '🐱' },
  { id: 'dinosaur', label: 'Dinosaur', src: '/photos/dinosaur.jpg', fallbackEmoji: '🦕' },
  { id: 'dandelion', label: 'Dandelion', src: '/photos/dandelion.jpg', fallbackEmoji: '🌼' },
];

export default function PhotoSelector({ onPhotoSelect, isLoading }) {
  const [dragOver, setDragOver] = useState(false);
  const [imageErrors, setImageErrors] = useState({});

  const handleFileUpload = (file) => {
    if (file && file.type.startsWith('image/')) {
      onPhotoSelect(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFileUpload(file);
  };

  const handlePhotoClick = async (photo) => {
    if (isLoading) return;
    try {
      const res = await fetch(photo.src);
      const contentType = res.headers.get('content-type') || '';
      if (!res.ok || !contentType.startsWith('image/')) {
        throw new Error('Demo photo unavailable');
      }
      const blob = await res.blob();
      const file = new File([blob], `${photo.id}.jpg`, { type: 'image/jpeg' });
      onPhotoSelect(file);
    } catch {
      const canvas = document.createElement('canvas');
      canvas.width = 400;
      canvas.height = 400;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#1a1a1a';
      ctx.fillRect(0, 0, 400, 400);
      ctx.font = '120px serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(photo.fallbackEmoji, 200, 200);
      canvas.toBlob((blob) => {
        const file = new File([blob], `${photo.id}.jpg`, { type: 'image/jpeg' });
        onPhotoSelect(file);
      }, 'image/jpeg');
    }
  };

  const handleDropZoneKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = (ev) => handleFileUpload(ev.target.files[0]);
      input.click();
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <h2 className="text-2xl font-bold font-display text-white mb-2">Pick a Photo to Explore!</h2>
      <p className="text-neutral-500 mb-6">Select a demo photo or upload your own</p>

      {isLoading ? (
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 border-4 border-neutral-800 border-t-fuchsia-500 rounded-full animate-spin" />
          <p className="text-fuchsia-400 font-medium">Starting your adventure...</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 mb-6">
            {DEMO_PHOTOS.map((photo) => (
              <button
                key={photo.id}
                onClick={() => handlePhotoClick(photo)}
                className="group relative w-24 h-24 rounded-2xl overflow-hidden border border-white/10 hover:border-fuchsia-500/50 transition-all duration-200 cursor-pointer"
              >
                {!imageErrors[photo.id] ? (
                  <img
                    src={photo.src}
                    alt={photo.label}
                    className="w-full h-full object-cover"
                    onError={() => setImageErrors(prev => ({ ...prev, [photo.id]: true }))}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-[#1a1a1a] text-4xl">
                    {photo.fallbackEmoji}
                  </div>
                )}
                <div className="absolute inset-0 bg-black/0 group-hover:bg-fuchsia-500/10 transition-colors" />
                <span className="absolute bottom-0 inset-x-0 text-xs text-center text-neutral-300 bg-black/60 py-0.5 truncate">
                  {photo.label}
                </span>
              </button>
            ))}
          </div>

          <div
            role="button"
            tabIndex={0}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onKeyDown={handleDropZoneKeyDown}
            className={`w-full max-w-md border-2 border-dashed rounded-2xl p-6 text-center transition-colors cursor-pointer ${
              dragOver ? 'border-fuchsia-500 bg-fuchsia-500/10' : 'border-white/10 hover:border-white/20'
            }`}
            onClick={() => {
              const input = document.createElement('input');
              input.type = 'file';
              input.accept = 'image/*';
              input.onchange = (e) => handleFileUpload(e.target.files[0]);
              input.click();
            }}
          >
            <p className="text-neutral-500">
              <span className="text-2xl block mb-1">📷</span>
              Drop a photo here or click to upload
            </p>
          </div>
        </>
      )}
    </div>
  );
}
