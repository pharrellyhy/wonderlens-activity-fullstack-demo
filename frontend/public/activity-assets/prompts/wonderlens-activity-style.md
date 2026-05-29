# WonderLens Activity Asset Style

Use case: illustration-story

Asset type: WonderLens activity game display asset.

Style: flat Nordic children's illustration matching the quiet white WonderLens prototype. Use the approved flat nursery references as the active style target: asymmetric simple animal silhouettes, large blocky body shapes, muted salmon and dusty blue characters, sparse black decorative strokes and arc eyes, pale cheeks, thin colored-pencil linework, light paper grain inside subjects, airy nursery composition, and generous negative space. Keep shapes readable and graphic, with no generic chibi/toy character vocabulary, no glossy eyes, no dimensional modeling, no bevels, no hard shadows, no deep perspective, no heavy texture, and no cartoon clutter.

Reference image: `style-reference-flat-nordic.png` (in this folder) is the active visual target — three exemplars: (1) a clean flat object/house on white, (2) a salmon-and-dusty-blue fox character with closed arc eyes, pale cheeks, and sparse dash/circle marks on white, and (3) a full-bleed airy nursery scene with soft pencil-grain texture. Match its palette, linework, and composition: item/object/character assets on clean white like exemplars 1–2; beat/background scenes full-bleed and softly painterly like exemplar 3.

Stroke system: match the banana pilot's quiet graphic treatment. Build objects and people from broad flat color fills. Use linework only for arc eyes, tiny facial marks, and sparse short texture dashes. Do not use thick outlines, raised seams, helmet panel strokes, clothing construction lines, or internal contour bands.

Palette: start from a blank clean white or barely tinted white background, then use restrained boho pastels inside the subject: oatmeal beige, muted sage, dusty teal-blue, soft terracotta/salmon, warm brown, mustard/ochre, blush pink, pale leaf green, and muted sky accent. Brighter yellow, coral, cyan, or lavender are allowed only as tiny accents. Do not let mint, blue, purple, black, neon pink, or neon cyan dominate the screen. Avoid beige or peach washes behind the subject unless a specific scene beat needs a room wall.

Composition: generate square source art. Background scenes are full-bleed 512x512 images that can be clipped by the device's circular lens. Item, object, and character assets are separate reusable PNGs with one centered subject per file, generous clean white padding, and no baked UI frame unless the frame itself is the intended object.

Constraints: no circular or oval image mask, no baked-in lens border, no rim, no vignette, no black corners, no transparent margin, no colored border, no readable text, no letters, no numbers, no logos, no watermark, no UI labels, no combined multi-image source asset.

Output: commit final beat PNGs and item PNGs as separate 512x512 files. Resize generated outputs as needed, then use `scripts/build_activity_screen_assets.py` only to rebuild manifest screen layouts and validate item paths.

Workflow: generate with Codex built-in imagegen, copy selected outputs from `/Users/pharrelly/.codex/generated_images/...` into `frontend/public/activity-assets/<activity_id>/` or `frontend/public/activity-assets/<activity_id>/items/`, and keep the original generated files in place.
