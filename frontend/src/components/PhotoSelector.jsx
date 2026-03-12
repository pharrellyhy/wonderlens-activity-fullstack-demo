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
      // If fetch fails (no image file), create a placeholder
      const canvas = document.createElement('canvas');
      canvas.width = 400;
      canvas.height = 400;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#f0f0f0';
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

  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <h2 className="text-2xl font-bold text-gray-700 mb-2">Pick a Photo to Explore!</h2>
      <p className="text-gray-500 mb-6">Select a demo photo or upload your own</p>

      {isLoading ? (
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 border-4 border-purple-300 border-t-purple-600 rounded-full animate-spin" />
          <p className="text-purple-600 font-medium">Starting your adventure...</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 sm:grid-cols-5 gap-4 mb-6">
            {DEMO_PHOTOS.map((photo) => (
              <button
                key={photo.id}
                onClick={() => handlePhotoClick(photo)}
                className="group relative w-24 h-24 rounded-xl overflow-hidden border-2 border-gray-200 hover:border-purple-400 hover:shadow-lg transition-all duration-200 cursor-pointer"
              >
                {!imageErrors[photo.id] ? (
                  <img
                    src={photo.src}
                    alt={photo.label}
                    className="w-full h-full object-cover"
                    onError={() => setImageErrors(prev => ({ ...prev, [photo.id]: true }))}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gray-50 text-4xl">
                    {photo.fallbackEmoji}
                  </div>
                )}
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
                <span className="absolute bottom-0 inset-x-0 text-xs text-center bg-white/80 py-0.5 truncate">
                  {photo.label}
                </span>
              </button>
            ))}
          </div>

          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`w-full max-w-md border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer ${
              dragOver ? 'border-purple-400 bg-purple-50' : 'border-gray-300 hover:border-gray-400'
            }`}
            onClick={() => {
              const input = document.createElement('input');
              input.type = 'file';
              input.accept = 'image/*';
              input.onchange = (e) => handleFileUpload(e.target.files[0]);
              input.click();
            }}
          >
            <p className="text-gray-500">
              <span className="text-2xl block mb-1">📷</span>
              Drop a photo here or click to upload
            </p>
          </div>
        </>
      )}
    </div>
  );
}
