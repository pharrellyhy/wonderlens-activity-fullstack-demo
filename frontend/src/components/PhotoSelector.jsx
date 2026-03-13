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
      ctx.fillStyle = '#f5f3ff';
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
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center mb-4 shadow-lg shadow-indigo-200/50">
        <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </div>
      <h2 className="text-2xl font-bold font-display text-gray-800 mb-1 tracking-tight">Pick a Photo to Explore!</h2>
      <p className="text-gray-400 text-sm mb-8">Select a demo photo or upload your own</p>

      {isLoading ? (
        <div className="flex flex-col items-center gap-4">
          <div className="w-14 h-14 border-[3px] border-gray-200 border-t-indigo-500 rounded-full animate-spin" />
          <p className="text-indigo-500 font-medium text-sm">Starting your adventure...</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 mb-8">
            {DEMO_PHOTOS.map((photo) => (
              <button
                key={photo.id}
                onClick={() => handlePhotoClick(photo)}
                className="group relative w-24 h-24 rounded-2xl overflow-hidden bg-white/50 border border-gray-200/50 hover:border-indigo-300 hover:shadow-lg hover:shadow-indigo-100/50 transition-all duration-200 cursor-pointer hover:scale-105"
              >
                {!imageErrors[photo.id] ? (
                  <img
                    src={photo.src}
                    alt={photo.label}
                    className="w-full h-full object-cover"
                    onError={() => setImageErrors(prev => ({ ...prev, [photo.id]: true }))}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 text-4xl">
                    {photo.fallbackEmoji}
                  </div>
                )}
                <span className="absolute bottom-0 inset-x-0 text-[11px] text-center text-gray-600 bg-white/80 backdrop-blur-sm py-1 truncate font-medium">
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
            className={`w-full max-w-md border-2 border-dashed rounded-2xl p-6 text-center transition-all cursor-pointer ${
              dragOver ? 'border-indigo-400 bg-indigo-50/50 scale-[1.01]' : 'border-gray-200 hover:border-gray-300 hover:bg-white/30'
            }`}
            onClick={() => {
              const input = document.createElement('input');
              input.type = 'file';
              input.accept = 'image/*';
              input.onchange = (e) => handleFileUpload(e.target.files[0]);
              input.click();
            }}
          >
            <p className="text-gray-400 text-sm">
              Drop a photo here or <span className="text-indigo-500 font-medium">click to upload</span>
            </p>
          </div>
        </>
      )}
    </div>
  );
}
