import { asset } from '../utils/basePath';

export default function LadybugIcon({ className = "w-6 h-6", ...props }) {
  return (
    <img src={asset('/icons/ladybug.png')} alt="Ladybug" className={className} draggable={false} {...props} />
  );
}
