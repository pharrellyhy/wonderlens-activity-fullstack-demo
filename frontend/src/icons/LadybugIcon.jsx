export default function LadybugIcon({ className = "w-6 h-6", ...props }) {
  return (
    <img src="/icons/ladybug.png" alt="Ladybug" className={className} draggable={false} {...props} />
  );
}
