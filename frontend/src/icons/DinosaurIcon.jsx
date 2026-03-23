import { asset } from '../utils/basePath';

export default function DinosaurIcon({ className = "w-6 h-6", ...props }) {
  return (
    <img src={asset('/icons/dinosaur.png')} alt="Dinosaur" className={className} draggable={false} {...props} />
  );
}
