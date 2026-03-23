/** Runtime base path — strips trailing slash for clean concatenation. */
const BASE = import.meta.env.BASE_URL.replace(/\/$/, '');
export default BASE;

/** Prefix an absolute path (e.g. "/icons/dog.png") with the base path. */
export function asset(path) {
  return `${BASE}${path}`;
}
