const GAME_THEMES = {
  dog: {
    characterPng: '/icons/dog.png',
    gradient: 'from-blue-100 to-blue-300',
    border: 'border-blue-300/40',
    accent: 'text-blue-800',
    accentBg: 'bg-blue-800/10',
    iconBg: 'bg-white ring-blue-200/60',
    decorations: ['🐾', '🦴'],
  },
  cat: {
    characterPng: '/icons/cat.png',
    gradient: 'from-violet-100 to-violet-300',
    border: 'border-violet-300/40',
    accent: 'text-violet-800',
    accentBg: 'bg-violet-800/10',
    iconBg: 'bg-white ring-violet-200/60',
    decorations: ['🌙', '✨'],
  },
  dinosaur: {
    characterPng: '/icons/dinosaur.png',
    gradient: 'from-amber-50 to-amber-300',
    border: 'border-amber-300/40',
    accent: 'text-amber-800',
    accentBg: 'bg-amber-800/10',
    iconBg: 'bg-white ring-amber-200/60',
    decorations: ['🌋', '🦴'],
  },
  ladybug: {
    characterPng: '/icons/ladybug.png',
    gradient: 'from-red-100 to-red-300',
    border: 'border-red-300/40',
    accent: 'text-red-800',
    accentBg: 'bg-red-800/10',
    iconBg: 'bg-white ring-red-200/60',
    decorations: ['🍄', '🌺'],
  },
  dandelion: {
    characterPng: '/icons/dandelion.png',
    gradient: 'from-yellow-50 to-yellow-300',
    border: 'border-yellow-300/40',
    accent: 'text-yellow-800',
    accentBg: 'bg-yellow-800/10',
    iconBg: 'bg-white ring-yellow-200/60',
    decorations: ['🌾', '💨'],
  },
};

const DEFAULT_THEME = GAME_THEMES.dog;

export function getThemeForEntity(entity) {
  if (!entity) return DEFAULT_THEME;
  const key = entity.toLowerCase();
  return GAME_THEMES[key] || DEFAULT_THEME;
}
