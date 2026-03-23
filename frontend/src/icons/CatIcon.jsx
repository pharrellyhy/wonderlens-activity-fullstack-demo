import { asset } from '../utils/basePath';

export default function CatIcon({ className = "w-6 h-6", ...props }) {
  return (
    <img src={asset('/icons/cat.png')} alt="Cat" className={className} draggable={false} {...props} />
  );
}
