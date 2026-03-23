import { asset } from '../utils/basePath';

export default function DogIcon({ className = "w-6 h-6", ...props }) {
  return (
    <img src={asset('/icons/dog.png')} alt="Dog" className={className} draggable={false} {...props} />
  );
}
