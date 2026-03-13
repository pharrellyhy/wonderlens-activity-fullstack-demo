export default function BinocularsIcon({ className = "w-6 h-6", ...props }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" {...props}>
      <circle cx="7" cy="17" r="4" />
      <circle cx="17" cy="17" r="4" />
      <path d="M7 13V5a2 2 0 012-2h1" />
      <path d="M17 13V5a2 2 0 00-2-2h-1" />
      <path d="M11 5h2" />
    </svg>
  );
}
