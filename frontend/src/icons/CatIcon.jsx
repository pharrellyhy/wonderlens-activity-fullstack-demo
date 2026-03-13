export default function CatIcon({ className = "w-6 h-6", ...props }) {
  return (
    <img src="/icons/cat.png" alt="Cat" className={className} draggable={false} {...props} />
  );
}
