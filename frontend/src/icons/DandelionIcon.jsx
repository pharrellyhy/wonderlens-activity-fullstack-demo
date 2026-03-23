import { asset } from '../utils/basePath';

export default function DandelionIcon({ className = "w-6 h-6", ...props }) {
  return (
    <img src={asset('/icons/dandelion.png')} alt="Dandelion" className={className} draggable={false} {...props} />
  );
}
