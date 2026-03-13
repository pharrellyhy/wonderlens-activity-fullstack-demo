export default function DogIcon({ className = "w-6 h-6", ...props }) {
  return (
    <img src="/icons/dog.png" alt="Dog" className={className} draggable={false} {...props} />
  );
}
