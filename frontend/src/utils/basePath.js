/** Runtime base path — strips trailing slash for clean concatenation. */
const BASE = import.meta.env.BASE_URL.replace(/\/$/, '');
export default BASE;

/** Prefix an absolute path (e.g. "/icons/dog.png") with the base path. Idempotent. */
export function asset(path) {
  if (!path || (BASE && path.startsWith(BASE))) return path;
  return `${BASE}${path}`;
}
