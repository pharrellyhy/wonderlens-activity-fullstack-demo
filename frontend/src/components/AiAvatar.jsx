import { CompassIcon } from '../icons';

const SIZES = {
  sm: { outer: 'w-6 h-6 sm:w-7 sm:h-7 lg:w-8 lg:h-8', icon: 'w-3 h-3 sm:w-3.5 sm:h-3.5 lg:w-4 lg:h-4', shadow: 'shadow-sm' },
  md: { outer: 'w-10 h-10 sm:w-12 sm:h-12 lg:w-14 lg:h-14', icon: 'w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7', shadow: 'shadow-lg' },
};

export default function AiAvatar({ size = 'sm', className = '' }) {
  const s = SIZES[size] || SIZES.sm;
  return (
    <div className={`${s.outer} rounded-full bg-gradient-to-br from-[var(--color-forest)] to-[var(--color-teal)] flex items-center justify-center ${s.shadow} flex-shrink-0 ${className}`}>
      <CompassIcon className={`${s.icon} text-white`} />
    </div>
  );
}
