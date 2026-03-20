# Plan: Redesign CharacterDisplay Widget

## Context

The CharacterDisplay widget uses infinite CSS animations (`animate-sparkle-large` / `animate-gentle-glow`) that make the character icon continuously bounce/pulse — distracting during gameplay. The widget also uses generic exploration icons (compass, binoculars) instead of the actual game character, and has a one-size-fits-all color scheme.

**Goal:** Replace with a "Rich Scene Window" — larger game character icon, per-game color themes, subtle decorative elements, and a gentle non-distracting float animation.

## Design Decisions

- **Layout**: Rich scene window with 72-80px character icon circle, themed gradient background, description card
- **Icon**: Game character PNG (dog.png, cat.png, etc.) — consistent throughout session
- **Colors**: Per-game gradients (dog=blue, cat=purple, dinosaur=amber, ladybug=coral, dandelion=golden)
- **Animation**: Gentle float (translateY ±3px, 3.5s) replaces infinite bounce/pulse
- **Transitions**: Crossfade ~400ms between rounds (existing `animate-fade-in`)
- **Decorations**: Subtle themed elements at 10-12% opacity in corners

## Implementation Steps

### Step 1: Add gentle-float animation to CSS

**File:** `frontend/src/index.css`

Add `gentle-float` keyframe and `.animate-gentle-float` utility class.

### Step 2: Create game theme config

**File:** `frontend/src/widgets/gameThemes.js` (NEW)

Map entity names → visual theme (character PNG path, gradient classes, accent color, decorative elements).

### Step 3: Rewrite CharacterDisplay component

**File:** `frontend/src/widgets/CharacterDisplay.jsx`

- Remove `ROUND_COLORS`, `ROUND_ICONS`, and SVG icon imports
- Import `getThemeForEntity` from `./gameThemes`
- Use `<img src={theme.characterPng}>` (72-80px circle) with `animate-gentle-float`
- Apply per-game gradient background and accent colors from theme
- Add subtle decorative emoji at corners (10-12% opacity)
- Show round label pill badge
- Keep crossfade on `scene_transition`

### Step 4: Override infinite animations for character_display in DeviceScreen

**File:** `frontend/src/components/DeviceScreen.jsx`

Remap `sparkle_highlight` → `appear` and `gentle_pulse` → `appear` for `character_display` widget only.

## Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `docs/plans/character-display-redesign.md` | CREATE | Design plan |
| `frontend/src/index.css` | MODIFY | Add gentle-float keyframe |
| `frontend/src/widgets/gameThemes.js` | CREATE | Per-game theme config |
| `frontend/src/widgets/CharacterDisplay.jsx` | REWRITE | Rich scene window layout |
| `frontend/src/components/DeviceScreen.jsx` | MODIFY | Override infinite anims for character_display |
