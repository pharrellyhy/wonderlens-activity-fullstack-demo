import { CompassIcon } from '../icons';

const SIZES = {
  sm: { outer: 'w-7 h-7', icon: 'w-3.5 h-3.5', shadow: 'shadow-sm' },
  md: { outer: 'w-14 h-14', icon: 'w-7 h-7', shadow: 'shadow-lg' },
};

export default function AiAvatar({ size = 'sm', className = '' }) {
  const s = SIZES[size] || SIZES.sm;
  return (
    <div className={`${s.outer} rounded-full bg-gradient-to-br from-[var(--color-forest)] to-[var(--color-teal)] flex items-center justify-center ${s.shadow} flex-shrink-0 ${className}`}>
      <CompassIcon className={`${s.icon} text-white`} />
    </div>
  );
}
