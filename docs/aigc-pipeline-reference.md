# AIGC Pipeline Reference — Cat1 & Cat5

A self-contained developer reference for everything image- and animation-related in the WonderLens Activity Demo. Read this end-to-end and you should be able to extend the system without opening the source. Every reproduced block cites its source path and line range so the doc can be re-synced if the code drifts.

> Sibling docs: `cat5-image-asset-list.md` (per-asset checklist for static Cat5 icons), `game-pipeline-overview.md` (general agent pipeline), `tester-guide.md` (operator-facing). This document is the *developer* reference for the AIGC slice.

---

## Table of contents

1. [Overview & TL;DR](#1-overview--tldr)
2. [Architecture map](#2-architecture-map)
3. [Cat5 live image generation](#3-cat5-live-image-generation)
   - 3.1 [Synthesis formats](#31-synthesis-formats)
   - 3.2 [The synthesis handler](#32-the-synthesis-handler)
   - 3.3 [The image generator](#33-the-image-generator)
   - 3.4 [Concurrency, retry, throttling](#34-concurrency-retry-throttling)
   - 3.5 [Prompts, captions, achievement template](#35-prompts-captions-achievement-template)
   - 3.6 [Reference image chain](#36-reference-image-chain)
   - 3.7 [Storage and serving](#37-storage-and-serving)
4. [Cat5 frontend rendering](#4-cat5-frontend-rendering)
5. [Cat1 pre-generated character animation](#5-cat1-pre-generated-character-animation)
6. [Configuration reference](#6-configuration-reference)
7. [Extension recipes](#7-extension-recipes)
8. [Failure modes & debugging](#8-failure-modes--debugging)
9. [Test coverage](#9-test-coverage)
10. [Recent history pointers](#10-recent-history-pointers)
11. [Glossary](#11-glossary)

---

## 1. Overview & TL;DR

**Cat1** (`mood_changer_dog`, `dream_whisperer_cat`, `time_machine_dinosaur`) and **Cat5** (`polka_dot_patrol`, `fluffy_expedition_dandelion`) both ship AI-generated content, but in completely different ways:

- **Cat1 uses pre-generated MP4 video clips** stored under `frontend/public/videos/` and selected at runtime by `useCharacterAnimation`. The clips can be generated offline with the Veo 3.1 tooling under `tools/`; no image or video generator runs during a Cat1 session.
- **Cat5 generates images live** during `STEP_4_SYNTHESIS` via Imagen 3 (`gemini-2.5-flash-image`). Scene images are produced sequentially with a reference-image chain for character consistency, then streamed to the frontend as base64 JPEG data URLs embedded in turn responses.

### Decision matrix

| Activity | Category | AIGC kind | Format | Asset count | Where it lives |
|---|---|---|---|---|---|
| `mood_changer_dog` | Cat 1 | Pre-rendered MP4 | `useCharacterAnimation` clip selection | 9 character + 8 scenario clips | `frontend/public/videos/character/mood_changer_dog/`, `.../scenario/mood_changer_dog/` |
| `dream_whisperer_cat` | Cat 1 | Pre-rendered MP4 | Same as above | 9 character + 8 scenario clips | `frontend/public/videos/character/dream_whisperer_cat/`, `.../scenario/dream_whisperer_cat/` |
| `time_machine_dinosaur` | Cat 1 | Pre-rendered MP4 | Same as above | 9 character + 8 scenario clips | `frontend/public/videos/character/time_machine_dinosaur/`, `.../scenario/time_machine_dinosaur/` |
| `polka_dot_patrol` | Cat 5 | Live Imagen 3 | `comparison_reveal` | 1 reveal scene + 1 achievement | `backend/data/images/{session_id}/scene_1.png`, `achievement.png` |
| `fluffy_expedition_dandelion` | Cat 5 | Live Imagen 3 | `collaborative_story` | 3 story scenes + 1 achievement | `backend/data/images/{session_id}/scene_{1,2,3}.png`, `achievement.png` |

### Where to look first

| Task | Start at |
|---|---|
| Run / debug live image gen | `backend/image_gen.py`, `backend/turn_handling/synthesis.py` |
| Add a new Cat5 activity | `backend/games/<id>.md`, `backend/synthesis_formats/`, `frontend/src/widgets/gameThemes.js` |
| Add a new Cat1 activity (with character video) | `tools/generate_character_clips.py`, `tools/character_clip_prompts.yaml`, `frontend/public/videos/{character,scenario}/<activity>/`, `frontend/src/widgets/gameThemes.js`, `frontend/src/hooks/useCharacterAnimation.js` |
| Disable AIGC for local dev | `backend/.env` → `IMAGEN_ENABLED=false` (or `imagen_enabled: false` in `config.yaml`) |
| Inspect saved generated images | `backend/data/images/{session_id}/scene_*.png`, `achievement.png` |

---

## 2. Architecture map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Agent pipeline                                 │
│                                                                             │
│   POST /api/start ──► Director Agent ──► Script Agent ──► Visual Agent     │
│                       (creative dir)     (dialogue text)   (screen frames)  │
│                                                  │                  │       │
│                                                  └─────► Recipe Assembler   │
│                                                          (merges, validates)│
│                                                          │                  │
│   POST /api/turn-speak ──► turn_handling/core.py ───────►│                  │
│                                                          ▼                  │
│   STEP_4_SYNTHESIS  ──►  turn_handling/synthesis.py                         │
│                          ├── _generate_structured_output (LLM → JSON)       │
│                          ├── start_scene_images (kicks off worker)          │
│                          │       │                                          │
│                          │       ▼                                          │
│                          │   image_gen.py: _scene_image_worker             │
│                          │   (sequential Imagen calls, anchor + ref chain) │
│                          │                                                  │
│                          └── _deliver_scene (awaits future, builds turn)   │
│                                                                             │
│   Turn JSON ──► frontend (StoryScene, AchievementImage, …)                 │
│   (image_data_url is base64 JPEG embedded inline)                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**What is in the pipeline:**
- `Director` plans round count and emotional arc (LLM, ~150 ms).
- `Script Agent` generates dialogue and — for Cat5 only — the structured story JSON that drives Imagen.
- `Visual Agent` selects widgets and frames (rule-based, no LLM, no image calls).
- `Recipe Assembler` validates and merges Script + Visual output into a recipe.
- `synthesis.py` is the only place that calls `image_gen.py`. It runs *during a turn*, not at session start.

**What is NOT in the pipeline:**
- The Visual Agent does **not** call Imagen.
- The Recipe Assembler does **not** trigger image generation.
- The frontend does **not** poll for images. The backend awaits the per-scene future (with a 30-second timeout) and inlines the data URL into the turn response.
- Cat1 has **no Imagen call** anywhere. Its runtime animation is purely `<video>` elements driven by `useCharacterAnimation`; video generation is an offline build-time step handled by `tools/generate_character_clips.py`.

---

## 3. Cat5 live image generation

This is the deep dive. Skim it on first read; come back when you need to extend.

### 3.1 Synthesis formats

Cat5 activities pick a *synthesis format* that decides scene count, prompt template, and downstream UI. Format files live in `backend/synthesis_formats/*.md` with YAML frontmatter and named body sections (`# system_prompt`, `# user_prompt`, `# direction_template`).

The mapping from Cat5 game → format is set in the game's YAML frontmatter under `story_scaffold.synthesis_format`:

- `fluffy_expedition_dandelion` → `collaborative_story` (3 scenes)
- `polka_dot_patrol` → `comparison_reveal` (1 scene)

A third format `sorting_challenge` exists in the registry but is not currently used by any of the demo's two Cat5 games. Adding a game that uses it is just a one-line change in the game's `story_scaffold.synthesis_format`.

#### `collaborative_story.md` (verbatim)

Source: `backend/synthesis_formats/collaborative_story.md` (full file).

```markdown
---
id: collaborative_story
display_name: "Collaborative Story"
scene_count: 3
scene_aspect_ratio: "16:9"
achievement_aspect_ratio: "1:1"
max_tokens: 2048
temperature: 0.7
min_sentences_total:
  T0: 7
  T1: 9
  T2: 12
direction_max_sentences:
  T0: 8
  T1: 11
  T2: 14
direction_tier_sentences:
  T0: "4-6"
  T1: "6-10"
  T2: "8-14"
is_naming_game: true
confirm_goes_to: "child_try"
supports_delegation: true
invite_templates:
  - "[gentle] Would you like to make up a little story about {names}?"
  - "[curious] What if {names} went on an adventure? Would you like to tell that story?"
  - "[whispering] I wonder what {names} would do together... would you like to imagine?"
invite_direction: "Invite the child to make up a little story about {names}. Keep it warm and simple — ask if they'd like to imagine what {names} might do together."
---

# system_prompt
You are a warm storyteller for young children. Generate a structured 3-scene story as a JSON object. Output ONLY valid JSON.

# user_prompt
Characters: {characters}
Sensory details the child shared: {details}
Tier: {tier}
Child's story attempt to expand (if any): {child_story}

Generate a JSON object with this EXACT structure:
{{"scenes": [{{"narration": "Scene 1 text (2-4 sentences)", "image_description": "Watercolor illustration description under 50 words", "caption": "Short 4-8 word caption for this scene"}},{{"narration": "Scene 2 text (2-4 sentences)", "image_description": "Watercolor illustration description under 50 words", "caption": "Short 4-8 word caption for this scene"}},{{"narration": "Scene 3 text (2-4 sentences)", "image_description": "Watercolor illustration description under 50 words", "caption": "Short 4-8 word caption for this scene"}}]}}

SCENE STRUCTURE:
Scene 1 — Opening + Surprise: Set the scene. Something unexpected happens.
Scene 2 — Try and Struggle: A character tries to solve it. It doesn't work. Another has an idea.
Scene 3 — Breakthrough + Warm Ending: They figure it out together. End with comfort.

RULES:
- Use ALL characters by name. Every character appears in at least 2 scenes.
- Start scene 1 narration with an emotion tag like [gentle] or [warm].
- Real emotions (scared, proud, cozy), real dialogue in quotes.
- Warm ending on comfort, not excitement.
- Image descriptions: watercolor storybook style. Characters are NOT human — they are the actual items listed above (petals, caterpillars, moss, seeds, etc.) drawn as cute animated versions. Include character names + physical traits, mood/lighting cues. Each image will have ONE short hand-lettered caption painted along the bottom — describe the scene as if it's a storybook page.
- Captions: 4-8 words each, present tense, concrete and punchy. Examples: "A sudden gust scatters the leaves.", "They stretch to reach the sky.", "Tucked together, warm and safe." Avoid names already visible in the picture.

# direction_template
Tell a COMPLETE story about {chars_desc}. The story must have:
- BEGINNING: Set the scene. The characters are together and something happens{theme_suffix}.
- MIDDLE: Each character uses their special trait to help. Show what each one DOES, not just what they are.
- END: The problem is solved and the friends celebrate together.

{premise_line}{child_story_line}Length: {tier_sentences} sentences. Do NOT end with a question. End the story with a warm conclusion.
```

Notes:

- Doubled `{{` / `}}` are literal braces — Python's `str.format()` would expand single braces against the template variables built in `_build_template_variables`. The doubled JSON skeleton lets the prompt show the LLM the desired shape without breaking templating.
- `image_description` is a free-text field per scene that becomes the Imagen prompt (after wrapping with the style prefix and consistency suffix in `image_gen.generate_image`).
- `caption` is overridden at post-processing time if missing or too long; see `_condense_caption` (`synthesis.py:134-155`).

#### `comparison_reveal.md` (verbatim)

Source: `backend/synthesis_formats/comparison_reveal.md` (full file).

```markdown
---
id: comparison_reveal
display_name: "Comparison Reveal"
scene_count: 1
scene_aspect_ratio: "16:9"
achievement_aspect_ratio: "1:1"
max_tokens: 1024
temperature: 0.7
min_sentences_total:
  T0: 3
  T1: 3
  T2: 3
direction_max_sentences:
  T0: 6
  T1: 8
  T2: 11
direction_tier_sentences:
  T0: "4-6"
  T1: "6-10"
  T2: "8-14"
is_naming_game: false
confirm_goes_to: "generate"
supports_delegation: true
invite_templates:
  - "[curious] Would you like to see how the {obs_angle} looks different on each one?"
invite_direction: |-
  Invite the child to compare all their finds together. Ask if they'd like to see how the {obs_angle} looks different on each one.
---

# system_prompt
You are a warm guide for young children exploring patterns and observations. Generate a JSON object. Output ONLY valid JSON.

# user_prompt
Items collected: {items}
Observation angle: {obs_angle}
Details the child noticed: {details}
Tier: {tier}

Generate a JSON object with this EXACT structure:
{{"scenes": [{{"narration": "Comparison text (3-5 sentences)", "image_description": "Reveal image description under 50 words", "caption": "Short 4-8 word caption highlighting the comparison"}}]}}

NARRATION RULES:
- Start with an emotion tag like [excited] or [curious]
- Help the child compare the {obs_angle} across all {count} items
- Point out how the {obs_angle} looks different on each
- Reference the child's observations when possible
- 3-5 warm sentences, end with celebration (not a question)

IMAGE DESCRIPTION: Watercolor storybook illustration showing all {count} items ({items}) arranged side by side in a row, each clearly showing their different {obs_angle}. Soft pastel tones, warm lighting. The image will have ONE short hand-lettered caption painted along the bottom.

CAPTION: 4-8 words highlighting the observation angle, e.g. "Every {obs_angle} is different.", "Look how they compare!"

# direction_template
Guide a fun comparison of all the finds. Observations collected: {obs_list}.
Help the child see how the same thing ({obs_angle}) looks DIFFERENT on each item. {theme_angle_suffix}{sorting_suffix}{goal_suffix}
Length: {tier_sentences} sentences. End warmly — do NOT end with a question.
```

Note: Per the synthesis prompt the LLM is asked to produce 1 scene (a side-by-side reveal of all collected items at once) plus a creative-naming nudge. The achievement image is added on top of that — it does not come from the LLM.

#### `sorting_challenge.md` (verbatim)

Source: `backend/synthesis_formats/sorting_challenge.md` (full file).

```markdown
---
id: sorting_challenge
display_name: "Sorting Challenge"
scene_count: 1
scene_aspect_ratio: "16:9"
achievement_aspect_ratio: "1:1"
max_tokens: 1024
temperature: 0.7
min_sentences_total:
  T0: 3
  T1: 3
  T2: 3
direction_max_sentences:
  T0: 6
  T1: 8
  T2: 11
direction_tier_sentences:
  T0: "4-6"
  T1: "6-10"
  T2: "8-14"
is_naming_game: false
confirm_goes_to: "generate"
supports_delegation: true
invite_templates:
  - "[curious] Would you like to see how your finds line up from one end to the other?"
invite_direction: |-
  Invite the child to see all their finds arranged in an order. Ask if they'd like to discover the pattern that lines them up together.
---

# system_prompt
You are a warm guide for young children discovering order and sequence. Generate a JSON object. Output ONLY valid JSON.

# user_prompt
Items collected: {items}
Observation angle: {obs_angle}
Details the child noticed: {details}
Tier: {tier}
{sorting_suffix}

Generate a JSON object with this EXACT structure:
{{"scenes": [{{"narration": "Sorting reveal text (3-5 sentences)", "image_description": "Ordered lineup image description under 50 words", "caption": "Short 4-8 word caption naming the pattern"}}]}}

NARRATION RULES:
- Start with an emotion tag like [delighted] or [curious]
- Name the sorted order you see across the {count} finds
- Walk through the lineup from one end to the other — point out how the {obs_angle} changes step by step
- Reference the child's observations when possible
- 3-5 warm sentences, end with celebration (not a question)

IMAGE DESCRIPTION: Watercolor storybook illustration showing all {count} items ({items}) arranged in a clear left-to-right lineup that reveals the sorted order of their {obs_angle}. Soft pastel tones, warm lighting. The image will have ONE short hand-lettered caption painted along the bottom.

CAPTION: 4-8 words naming the sorted sequence, e.g. "Smallest to biggest!", "A cozy little lineup."

# direction_template
Guide a warm sorting reveal of all the finds. Observations collected: {obs_list}.
Line the items up in order by {obs_angle}. {sorting_suffix}{goal_suffix}
Walk the child through the lineup from one end to the other, naming each find as you go. Length: {tier_sentences} sentences. End warmly — do NOT end with a question.
```

#### How a format becomes a Python object

The registry loader walks `backend/synthesis_formats/*.md` once at first lookup and caches the parsed `SynthesisFormat` instances behind a `MappingProxyType`. The full schema:

Source: `backend/synthesis_formats/loader.py:43-83`.

```python
class SynthesisFormat(BaseModel):
    """Schema for one synthesis format loaded from a markdown file."""
    # --- Identity ---
    id: str
    display_name: str

    # --- Scene layout ---
    scene_count: int = Field(ge=1, le=5)
    scene_aspect_ratio: str = "16:9"
    achievement_aspect_ratio: str = "1:1"

    # --- LLM parameters ---
    max_tokens: int = 2048
    temperature: float = 0.7

    # --- Length constraints (keyed by tier: "T0", "T1", "T2") ---
    min_sentences_total: dict[str, int]
    direction_max_sentences: dict[str, int]
    direction_tier_sentences: dict[str, str]

    # --- Game behaviour flags ---
    is_naming_game: bool = True
    confirm_goes_to: Literal["child_try", "generate"] = "child_try"
    supports_delegation: bool = True

    # --- Invite templates ---
    invite_templates: list[str]
    invite_direction: str

    # --- Raw prompt bodies (populated from markdown body sections) ---
    system_prompt: str = Field(min_length=1)
    user_prompt: str = Field(min_length=1)
    direction_template: str = Field(min_length=1)
```

Key constraint: `scene_count` is bounded to `[1, 5]` — adding a 7-scene epic format requires raising this ceiling.

The loader splits the body on bare `# section_name` headings and merges YAML frontmatter with the body sections. Required body sections are `system_prompt`, `user_prompt`, `direction_template` — missing any one raises `ValueError` at startup.

Public lookup API (cached):

```python
fmt = get_format("collaborative_story")  # ValueError on unknown id
print(fmt.scene_count, fmt.system_prompt)
```

### 3.2 The synthesis handler

`backend/turn_handling/synthesis.py` is the only call site of `image_gen`. Two key flows:

1. **Generate phase** — the child has confirmed (or stayed silent) and the AI is producing the story. This calls the LLM, parses the result, and kicks off image generation in the background.
2. **Scene delivery phases** — once the LLM result lands, each scene is delivered as a separate auto-advance turn, awaiting that scene's image future on the way through.

#### Per-scene timeout

Source: `backend/turn_handling/synthesis.py:55-59`.

```python
# Per-scene image wait timeout. Each Imagen call takes ~3-5s and retries add
# another ~3s, so ~15s is the realistic worst case for a single scene. 30s
# gives a 2x margin — any longer and a stuck generation would appear to the
# child as a prolonged hang rather than a fallback to no-image rendering.
_SCENE_IMAGE_WAIT_TIMEOUT_S = 30.0
```

#### Achievement template

The LLM's own achievement description was producing images that looked identical to scene 3, so it is overridden post-parse with a deterministic celebration-poster template that picks rotating props and a caption.

Source: `backend/turn_handling/synthesis.py:70-92` (data) and `backend/turn_handling/synthesis.py:95-123` (function).

```python
_CELEBRATION_PROPS = [
    "soft paper confetti drifting down and a warm golden sunburst halo glowing behind them",
    "tiny paper flags held above their heads and a curved ribbon banner arching overhead",
    "small paper crowns perched on each one and gentle golden particles floating around",
    "a bright spotlight beam from above and tiny bursts of coloured confetti around them",
    "a wreath of soft flower petals framing them and warm sparkles shimmering in the air",
    "a cozy campfire glow behind them and a string of tiny paper bunting stretched overhead",
]

_CELEBRATION_CAPTIONS = [
    "We did it!",
    "What a team!",
    "Friends forever.",
    "Our first adventure.",
    "A brave new team!",
    "Together we shine.",
]


def _build_achievement_prompt(characters: str, role_title: str | None) -> tuple[str, str]:
    """Return a (description, caption) pair for the achievement image.

    This is intentionally *not* derived from the LLM's story output — the
    LLM kept producing achievement descriptions that looked identical to
    scene 3 (the warm ending). Using a deterministic template forces the
    celebration image to be visually distinct: a centered hero poster with
    rotating celebration props instead of a narrative scene.

    Character names are interpolated so the characters themselves still
    match the story, but the composition is locked.
    """
    props = random.choice(_CELEBRATION_PROPS)
    description = (
        f"A celebration poster in soft watercolor storybook style: {characters} all centered "
        "side by side at the front of the frame, facing the viewer in a proud hero pose, "
        f"warmly smiling. {props}. Bright high-key lighting, rich cheerful colors, "
        "iconic centered composition. This is a CELEBRATION PORTRAIT, not a narrative scene — "
        "no ongoing action, no environment details, just the characters being celebrated."
    )
    if role_title:
        caption = f"A new {role_title}!"
        # Keep the caption within the ≤6-word budget; fall back if the role
        # title is itself long (rare, but role_title is LLM-generated).
        if len(caption.split()) > 6:
            caption = random.choice(_CELEBRATION_CAPTIONS)
    else:
        caption = random.choice(_CELEBRATION_CAPTIONS)
    return description, caption
```

#### Caption fallback

Source: `backend/turn_handling/synthesis.py:134-155`.

```python
def _condense_caption(text: str, max_words: int = 8) -> str | None:
    """Trim a longer string down to a short in-image caption.

    Returns None if the input is empty. Otherwise strips leading emotion
    tags like ``[gentle]``, takes the first sentence, removes trailing
    punctuation / quotes, and truncates to ``max_words`` words. Used as a
    fallback when the LLM's own caption field is missing.
    """
    if not text:
        return None
    cleaned = re.sub(r"^\s*\[[^\]]+\]\s*", "", text).strip()
    if not cleaned:
        return None
    first = re.split(r"[.!?]", cleaned, maxsplit=1)[0].strip().strip("\"“”'")
    if not first:
        return None
    words = first.split()
    if len(words) > max_words:
        first = " ".join(words[:max_words])
    return first or None
```

#### `_generate_structured_output`: the LLM call that drives image gen

This produces a `StructuredStory` and **immediately kicks off** scene image generation, then returns. Image generation continues in the background while later turns await the futures.

Source: `backend/turn_handling/synthesis.py:310-400` (full function).

```python
async def _generate_structured_output(
    state: SessionStateModel,
    fmt: SynthesisFormat,
) -> StructuredStory | None:
    """Format-agnostic structured story generator driven by a SynthesisFormat.

    Renders the format's system_prompt and user_prompt templates, calls the LLM
    with the format's temperature and max_tokens, then validates, post-processes,
    and kicks off progressive scene image generation.
    """
    settings = get_settings()
    variables = _build_template_variables(state, fmt)
    system_prompt = fmt.system_prompt.format(**variables)
    user_prompt = fmt.user_prompt.format(**variables)
    characters = str(variables["characters"])

    try:
        start = time.perf_counter()
        client = AsyncOpenAI(
            api_key=settings.ali_api_key,
            base_url=settings.ali_base_url,
            max_retries=0,
            timeout=httpx.Timeout(60.0, connect=15.0),
        )
        response = await client.chat.completions.create(
            model=settings.ali_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=fmt.temperature,
            max_tokens=fmt.max_tokens,
            response_format={"type": "json_object"},
            extra_body={"enable_thinking": False},
        )
        raw_text = response.choices[0].message.content or ""
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info("Structured story LLM response (%dms): %s", latency_ms, raw_text[:200])

        raw = json.loads(raw_text)
        story = StructuredStory.model_validate(raw)

    except (json.JSONDecodeError, ValidationError) as exc:
        logger.error("Failed to parse structured story JSON: %s", exc)
        return None
    except (httpx.HTTPError, openai.OpenAIError) as exc:
        logger.error("Structured story LLM call failed: %s", exc)
        return None

    if len(story.scenes) != fmt.scene_count:
        logger.warning(
            "Structured story has %d scenes (expected %d), falling back",
            len(story.scenes), fmt.scene_count,
        )
        return None

    # Normalise captions
    scene_captions: list[str | None] = []
    for scene in story.scenes:
        scene.caption = _condense_caption(scene.caption or "", max_words=10) or _condense_caption(
            scene.narration, max_words=8
        )
        scene_captions.append(scene.caption)

    # Override the LLM's achievement description with a deterministic celebration-poster template
    achievement_desc, achievement_caption = _build_achievement_prompt(characters, _role_title_for(state))
    story.achievement_description = achievement_desc
    story.achievement_caption = achievement_caption

    # Progressive scene image generation — scene 1 is delivered while 2, 3 are mid-generation
    scene_descs = [s.image_description for s in story.scenes]
    start_scene_images(
        state.session_id,
        scene_descs,
        story.achievement_description,
        scene_captions=scene_captions,
        achievement_caption=story.achievement_caption,
    )

    # image_data_urls intentionally left None — _deliver_scene fills them from futures
    return story
```

The LLM provider is **DashScope/ALI Qwen** (`AsyncOpenAI` pointed at `settings.ali_base_url` with `settings.ali_model` — `qwen3.5-plus` by default). The image model is independent — Vertex Imagen 3.

#### `_await_scene_image` / `_await_achievement_image`

Source: `backend/turn_handling/synthesis.py:483-525`.

```python
async def _await_scene_image(session_id: str, scene_index: int) -> str | None:
    """Await the progressive future for a given scene index, if any.

    Returns the base64 data URL if the scene image landed in time, None on
    timeout / cancellation / missing session. Missing session is the normal
    case when the image was generated up front (e.g. by the blocking
    ``generate_scene_images`` wrapper used for comparison_reveal) so the
    caller can fall back to whatever ``StoryScene.image_data_url`` already
    holds.
    """
    session = get_scene_session(session_id)
    if session is None:
        return None
    if scene_index >= len(session.scene_futures):
        return None
    future = session.scene_futures[scene_index]
    try:
        return await asyncio.wait_for(asyncio.shield(future), timeout=_SCENE_IMAGE_WAIT_TIMEOUT_S)
    except asyncio.TimeoutError:
        logger.warning("Scene %d image not ready after %.0fs", scene_index + 1, _SCENE_IMAGE_WAIT_TIMEOUT_S)
        return None
    except asyncio.CancelledError:
        logger.warning("Scene %d image wait cancelled", scene_index + 1)
        return None


async def _await_achievement_image(session_id: str) -> str | None:
    """Await the progressive achievement image future, if any."""
    session = get_scene_session(session_id)
    if session is None:
        return None
    try:
        return await asyncio.wait_for(
            asyncio.shield(session.achievement_future),
            timeout=_SCENE_IMAGE_WAIT_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        logger.warning("Achievement image not ready after %.0fs", _SCENE_IMAGE_WAIT_TIMEOUT_S)
        return None
    except asyncio.CancelledError:
        logger.warning("Achievement image wait cancelled")
        return None
```

Key design choice: `asyncio.shield(future)`. If the wait times out, the underlying worker keeps running. The next retry of the same scene delivery can re-await the same future — that's how progressive delivery survives a slow first scene without abandoning the work.

#### `_deliver_scene`: per-scene auto-advance turn

This is what the frontend actually receives turn-by-turn during synthesis.

Source: `backend/turn_handling/synthesis.py:527-630` (full function).

```python
async def _deliver_scene(state: SessionStateModel, scene_number: int) -> TurnResult:
    """Deliver a scene as a deterministic auto-advance turn.

    Awaits the per-scene future from the progressive image session so scene
    N ships the moment its image is ready — without waiting for scenes
    N+1..M. When the last scene is delivered, the achievement image future
    is also awaited so the downstream celebrate frame has the URL available.
    """
    story = state.structured_story
    if story is None:
        raise RuntimeError("_deliver_scene called without structured_story")
    scene = story.scenes[scene_number - 1]
    is_last = scene_number == len(story.scenes)

    # Populate the image data URL lazily: the scene may have been pre-filled
    # by the blocking path (comparison_reveal) or it may still be mid-flight
    # in a progressive session. Only cache a NON-None result — if the wait
    # timed out here, a later retry delivery of the same scene should get
    # another chance to read the future (the background worker keeps running
    # even after a wait_for timeout thanks to asyncio.shield).
    if scene.image_data_url is None and not scene.image_failed:
        resolved = await _await_scene_image(state.session_id, scene_number - 1)
        if resolved is not None:
            scene.image_data_url = resolved
        else:
            # Distinguish a confirmed failure from "still pending": the
            # worker flips session.scene_failed[i] only on real failures.
            image_session = get_scene_session(state.session_id)
            if image_session and scene_number - 1 < len(image_session.scene_failed):
                scene.image_failed = image_session.scene_failed[scene_number - 1]

    # On the final scene, pull the achievement image forward too so it's
    # ready by the time the celebrate frame is built on the next turn.
    # Same rule: only cache a non-None result so a retry can re-await.
    if is_last and story.achievement_image_data_url is None and not story.achievement_image_failed:
        resolved_ach = await _await_achievement_image(state.session_id)
        if resolved_ach is not None:
            story.achievement_image_data_url = resolved_ach
        else:
            image_session = get_scene_session(state.session_id)
            if image_session and image_session.achievement_failed:
                story.achievement_image_failed = True

    sfx = "celebration_fanfare" if is_last else "story_page_turn"
    widget_params: dict = {
        "scene_number": scene_number,
        "total_scenes": len(story.scenes),
    }
    if scene.image_data_url:
        widget_params["image_data_url"] = scene.image_data_url
        widget_params["image_status"] = "ready"
    elif scene.image_failed:
        widget_params["image_status"] = "failed"
    else:
        widget_params["image_status"] = "pending"

    turn_response = TurnResponse(
        dialogue=scene.narration,
        tone_marker="gentle",
        screen_widget="story_scene",
        screen_widget_params=widget_params,
        stay_on_step=not is_last,
        sfx_cue=sfx,
    )
    # ... (constructs ScreenFrame, advances state, returns TurnResult)
```

The contract that the frontend consumes:

| `image_data_url` | `image_failed` | Resulting `image_status` |
|---|---|---|
| present (string) | — | `"ready"` |
| `None` | `True` | `"failed"` |
| `None` | `False` | `"pending"` |

`"pending"` shows a placeholder; `"failed"` shows the muted amber `ImageFailedBanner` overlay.

#### Synthesis phase machine

`state.synthesis_phase` walks through these values during `STEP_4_SYNTHESIS`:

```
invite ──► evaluate ──► (if substantive+good) ──► <legacy monolithic path>
                ├──► improve ──► generate
                ├──► generate (silence/confirm/decline)
                └──► generate (off_topic after second prompt)

generate ──► loading screen + auto-advance ──► _generate_structured_output
                ├──► structured story OK ──► scene_1, scene_2, scene_3 (auto-advance)
                └──► fallback monolithic ScriptAgent (no images)

scene_N ──► _deliver_scene(N) ──► auto-advance to scene_(N+1) or to STEP_5_CELEBRATE
```

`scene_count == 1` (`comparison_reveal`) collapses to a single `scene_1` delivery that also pulls the achievement image forward.

#### `StructuredStory` and `StoryScene` schema

Source: `backend/schemas/structured_story.py` (full file).

```python
"""Pydantic schema for structured scene-by-scene story output."""

from pydantic import BaseModel, Field


class StoryScene(BaseModel):
    """A single scene in the structured story."""

    narration: str = Field(description="The narration text for this scene (2-5 sentences)")
    image_description: str = Field(description="Visual description for Imagen generation")
    image_data_url: str | None = Field(default=None, description="Base64 data URL of generated image")
    image_failed: bool = Field(
        default=False,
        description="True when the image generation worker confirmed failure (vs. still in-flight)",
    )
    caption: str | None = Field(
        default=None,
        description="Short (<= 10 word) caption baked into the bottom of the image as hand-lettered text",
    )


class StructuredStory(BaseModel):
    """A complete structured story with scenes and achievement image.

    Scene count varies by synthesis format:
    - collaborative_story: 3 story scenes (beginning, middle, end)
    - comparison_reveal: 1 reveal scene (items shown side by side)
    """

    scenes: list[StoryScene] = Field(description="Story scenes (3 for story, 1 for comparison reveal)")
    # achievement_description is always overwritten post-parse with a
    # deterministic celebration-poster template (see _build_achievement_prompt
    # in turn_handling/synthesis.py). We keep it optional with a default of ""
    # so LLM responses that omit the field — which they will, because the
    # prompt no longer asks for it — validate cleanly.
    achievement_description: str = Field(
        default="",
        description="Visual description for achievement summary image (filled in post-parse)",
    )
    achievement_image_data_url: str | None = Field(default=None, description="Base64 data URL of achievement image")
    achievement_image_failed: bool = Field(
        default=False,
        description="True when the achievement image generation worker confirmed failure",
    )
    achievement_caption: str | None = Field(
        default=None,
        description="Short (<= 6 word) caption baked into the achievement image",
    )
```

Field-by-field intent:

- `narration` — what the AI says when this scene plays. Renders as turn dialogue.
- `image_description` — the prompt fragment passed to Imagen. Wrapped with the global style prefix and an optional consistency suffix when references are passed.
- `image_data_url` — populated by `_deliver_scene` from the worker's future. `None` while pending, never holds an empty string.
- `image_failed` — flipped to `True` only by the worker on a confirmed generation failure. `False` while still in-flight.
- `caption` — short ≤10-word string baked into the image as hand-lettered text. Optional; if `None`, no caption renders.
- `achievement_description` — overwritten post-parse with the deterministic poster template; the LLM's value is discarded.
- `achievement_caption` — overwritten with `f"A new {role_title}!"` when role_title fits in 6 words, otherwise picked from `_CELEBRATION_CAPTIONS`.

### 3.3 The image generator

`backend/image_gen.py` is ~460 lines and does everything Imagen-related. The full file is reproduced in chunks below.

#### Module docstring and constants

Source: `backend/image_gen.py:1-69`.

```python
"""Image generation using Imagen 3 via Vertex AI / Google GenAI SDK.

Follows the same dual-auth pattern as tts.py:
- If google_cloud_project set → Vertex AI client
- Otherwise → API key client (gemini_api_key)

Scene images are generated SEQUENTIALLY with the first successful image
used as a reference anchor for subsequent images. This keeps character
designs, colors, and art style visually consistent across scenes — the
previous parallel batching produced noticeably different characters per
scene because each call was independent.

Progressive delivery: the sequential worker publishes each finished image
via a per-session ``asyncio.Future`` the moment it resolves, so scene 1
can be delivered to the frontend while scenes 2 and 3 are still mid-
generation. See ``start_scene_images`` / ``get_scene_futures``.
"""

import asyncio
import base64
import io
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from PIL import Image

# (logger import omitted for brevity)

_STYLE_PREFIX = "Soft watercolor children's storybook illustration. Gentle pastel tones, warm lighting."

_CONSISTENCY_SUFFIX = (
    " Keep the character designs, proportions, colors, and art style visually consistent with the reference image(s)."
)

_CAPTION_PREFIX = (
    ' Include exactly ONE short hand-lettered caption along the bottom of the illustration that reads EXACTLY: "'
)
_CAPTION_SUFFIX = (
    '". Paint it in a cozy hand-lettered storybook style, clearly readable,'
    " no other words, no extra letters, no speech bubbles elsewhere in the image."
)

_MAX_RETRIES = 2
_RETRY_DELAY = 3.0

# Single-flight gate around the Imagen API call.
_imagen_semaphore = asyncio.Semaphore(1)
```

These four constants drive the prompt assembly:

- `_STYLE_PREFIX` is **always** prepended. Changing it changes every image in every Cat5 session.
- `_CONSISTENCY_SUFFIX` is appended only when at least one reference image is passed. Without references it is omitted — Imagen ignores reference instructions if there are none.
- `_CAPTION_PREFIX` / `_CAPTION_SUFFIX` wrap the caption in a quoted instruction. The double quotes around the caption are deliberate — Imagen renders quoted text more reliably than unquoted strings.

#### Client factory

Source: `backend/image_gen.py:72-85`.

```python
@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    """Get or create the image generation client (same auth pattern as TTS)."""
    settings = get_settings()
    if settings.google_cloud_project:
        client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location="global",
        )
    else:
        client = genai.Client(api_key=settings.gemini_api_key)
    logger.info("Initialized image generation client")
    return client
```

Auth modes:

| `google_cloud_project` set? | Mode | Notes |
|---|---|---|
| Yes | Vertex AI | Uses service account at `google_application_credentials`. Region pinned to `"global"` (Imagen 3 is not regional). |
| No | API key | Uses `gemini_api_key` (AI Studio). Same SDK, different auth. |

#### `generate_image`: the single Imagen call

This is the only function that talks to the Imagen API. Everything else in this module wraps it.

Source: `backend/image_gen.py:100-191`.

```python
async def generate_image(
    prompt: str,
    aspect_ratio: str = "16:9",
    reference: bytes | None = None,
    anchor: bytes | None = None,
    caption: str | None = None,
) -> bytes | None:
    """Generate a single image, optionally threaded with reference images."""
    settings = get_settings()
    if not settings.imagen_enabled:
        logger.info("Imagen disabled, skipping image generation")
        return None

    full_prompt = f"{_STYLE_PREFIX} {prompt}"
    if reference or anchor:
        full_prompt += _CONSISTENCY_SUFFIX
    if caption:
        # String concatenation rather than .format() so a caption
        # containing literal "{" or "}" (possible from an LLM) can't
        # trigger a KeyError / IndexError at runtime. We also strip any
        # pre-existing double quotes from the caption so they don't
        # collide with the quoted-instruction wrapper.
        safe_caption = caption.strip().replace('"', "").replace("“", "").replace("”", "")
        if safe_caption:
            full_prompt += _CAPTION_PREFIX + safe_caption + _CAPTION_SUFFIX

    contents: list = [full_prompt]
    if anchor:
        contents.append(types.Part.from_bytes(data=anchor, mime_type="image/png"))
    if reference and reference is not anchor:
        contents.append(types.Part.from_bytes(data=reference, mime_type="image/png"))

    client = _get_client()

    wait_start = time.perf_counter()
    async with _imagen_semaphore:
        wait_ms = int((time.perf_counter() - wait_start) * 1000)
        if wait_ms >= 100:
            logger.info("Imagen waited %dms for semaphore", wait_ms)

        for attempt in range(_MAX_RETRIES):
            try:
                start = time.perf_counter()
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=settings.imagen_model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                    ),
                )
                latency_ms = int((time.perf_counter() - start) * 1000)
                image_bytes = _extract_image_bytes(response)
                has_refs = bool(anchor or reference)
                logger.info(
                    "Imagen generated image (%d bytes, %dms, refs=%s)",
                    len(image_bytes), latency_ms, "yes" if has_refs else "no",
                )
                return image_bytes

            except (genai_errors.ClientError, genai_errors.APIError) as exc:
                is_retryable = "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc)
                if not is_retryable or attempt == _MAX_RETRIES - 1:
                    logger.error("Imagen generation failed (attempt %d): %s", attempt + 1, exc)
                    return None
                logger.warning("Imagen rate-limited, retrying in %.1fs", _RETRY_DELAY)
                await asyncio.sleep(_RETRY_DELAY)

            except Exception as exc:
                logger.error("Imagen unexpected error: %s", exc)
                return None

    return None
```

Walkthrough:

1. **Disabled-path early return.** `imagen_enabled = False` skips the API call entirely. The worker treats `None` as a failure and the frontend renders the fallback (placeholder for scenes, `FallbackTrophy` for achievement).
2. **Prompt assembly.** Style prefix → user description → optional consistency suffix → optional caption.
3. **Reference parts.** Anchor goes in first, then the previous-scene reference. Both are passed as PNG bytes via `types.Part.from_bytes`.
4. **Semaphore acquisition.** Logs if the wait exceeded 100 ms — useful for spotting bursts in the wild.
5. **Retry loop.** Up to 2 attempts. Only `RESOURCE_EXHAUSTED` / `429` errors are retryable; everything else fails fast.
6. **Inline-data extraction.** Imagen 3 returns the PNG bytes inside `response.parts[*].inline_data.data`.

#### Downscaling and base64 wrapping

Source: `backend/image_gen.py:194-215`.

```python
def _downscale_to_jpeg(image_bytes: bytes, max_dim: int = 768, quality: int = 85) -> bytes:
    """Downscale an image and re-encode as JPEG for much smaller payload.

    Gemini 2.5 Flash Image returns ~1024x1024 PNGs at ~1.3MB each. Base64-
    encoded inline that's ~1.75MB of text in the turn JSON response — large
    enough to cause noticeable rendering lag when the browser decodes it.
    Downscaling to 768 on the longest side + JPEG 85% quality reduces the
    payload ~10x with no visible quality loss for watercolor art.
    """
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=quality, optimize=True)
    return out.getvalue()


def image_to_base64(image_bytes: bytes, mime: str = "image/png") -> str:
    """Convert raw image bytes to a base64-encoded data URL string."""
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{encoded}"
```

The PNG returned by Imagen is the *anchor source* (kept full-resolution for character consistency on subsequent calls). The downscaled JPEG is the *wire payload* — what gets base64'd and shipped to the frontend.

#### Disk persistence

Source: `backend/image_gen.py:218-228`.

```python
_IMAGES_DIR = Path(__file__).parent / "data" / "images"


def _save_image(image_bytes: bytes, session_id: str, filename: str) -> Path:
    """Save image bytes to disk and return the file path."""
    session_dir = _IMAGES_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / filename
    path.write_bytes(image_bytes)
    logger.info("Saved image: %s (%d bytes)", path, len(image_bytes))
    return path
```

Every successful image is persisted to `backend/data/images/{session_id}/`. This is the original ~1.3 MB PNG, not the downscaled JPEG.

Sample tree (live, observed in this repo):

```
backend/data/images/
├── 0d5f54d7-f054-4233-8a61-47654c64849a/
│   ├── achievement.png    1.3 MB
│   └── scene_1.png        1.3 MB
├── 3282adea-21e9-4d09-a048-f70554d06e08/
│   ├── achievement.png
│   ├── scene_1.png
│   ├── scene_2.png
│   └── scene_3.png
└── …
```

These files are not served. They exist for debugging — if a tester reports a bad image, you can grab the PNG straight from disk to inspect what Imagen produced.

#### `_SceneSession`: per-session state

Source: `backend/image_gen.py:231-252`.

```python
@dataclass
class _SceneSession:
    """Per-session state for progressive scene image delivery.

    ``scene_futures`` holds one future per scene description (in order),
    ``achievement_future`` holds the future for the achievement image, and
    ``task`` is kept as a strong reference so the event loop doesn't garbage-
    collect the background worker while it's still running.

    ``scene_failed`` + ``achievement_failed`` are mutated by the worker
    when generation returns no bytes. They let callers distinguish a
    confirmed failure from "still pending" when a future resolves to None.
    """

    scene_futures: list[asyncio.Future[str | None]]
    achievement_future: asyncio.Future[str | None]
    scene_failed: list[bool] = field(default_factory=list)
    achievement_failed: bool = False
    task: asyncio.Task[None] | None = field(default=None, repr=False)


_scene_sessions: dict[str, _SceneSession] = {}
```

Module-level `_scene_sessions` is keyed by `session_id` (the UUID minted at `/api/start`). The dict holds a strong reference to each `asyncio.Task` so it isn't garbage-collected mid-run.

#### `_process_generated_image`

Source: `backend/image_gen.py:255-266`.

```python
def _process_generated_image(img_bytes: bytes, session_id: str, filename: str, label: str) -> str:
    """Save PNG to disk and return a downscaled JPEG data URL for the browser."""
    _save_image(img_bytes, session_id, filename)
    jpeg_bytes = _downscale_to_jpeg(img_bytes, max_dim=768, quality=85)
    logger.info(
        "%s downscaled: %d bytes -> %d bytes (%.1f%%)",
        label, len(img_bytes), len(jpeg_bytes), 100 * len(jpeg_bytes) / len(img_bytes),
    )
    return image_to_base64(jpeg_bytes, mime="image/jpeg")
```

#### `_scene_image_worker`: the sequential generator

Source: `backend/image_gen.py:269-352`.

```python
async def _scene_image_worker(
    session: "_SceneSession",
    session_id: str,
    scene_descriptions: list[str],
    achievement_description: str,
    scene_captions: list[str | None],
    achievement_caption: str | None,
) -> None:
    """Sequential scene generator that resolves each future as its image lands.

    Generation order is preserved (later scenes use earlier images as
    anchor/reference for character consistency), but each finished image is
    published immediately so callers awaiting scene N don't have to wait for
    scenes N+1..M to finish.

    On failure the worker records the outcome on the shared
    ``_SceneSession`` (``scene_failed[i] = True`` or ``achievement_failed =
    True``) so callers can distinguish "generation failed" from "still
    pending" when a future resolves to None.
    """
    sid = session_id or "unknown"
    anchor_bytes: bytes | None = None  # first successful scene — character canon
    previous_bytes: bytes | None = None  # immediately preceding scene — style continuity

    def _set(future: asyncio.Future[str | None], value: str | None) -> None:
        if not future.done():
            future.set_result(value)

    for i, desc in enumerate(scene_descriptions):
        data_url: str | None = None
        caption = scene_captions[i] if i < len(scene_captions) else None
        try:
            img_bytes = await generate_image(
                desc,
                aspect_ratio="16:9",
                reference=previous_bytes,
                anchor=anchor_bytes,
                caption=caption,
            )
        except Exception as exc:
            logger.error("Scene %d generation raised: %s", i + 1, exc)
            img_bytes = None

        if img_bytes:
            data_url = _process_generated_image(img_bytes, sid, f"scene_{i + 1}.png", f"Scene {i + 1}")
            # Keep the ORIGINAL PNG bytes as the reference/anchor for the
            # next generation — full resolution gives Gemini more detail
            # to lock onto for character consistency.
            if anchor_bytes is None:
                anchor_bytes = img_bytes
            previous_bytes = img_bytes
        else:
            logger.error("Scene %d image generation failed", i + 1)
            session.scene_failed[i] = True

        _set(session.scene_futures[i], data_url)

    # Achievement image: use the anchor + the last scene as references.
    # 16:9 matches the landscape device panel — a 1:1 square would leave
    # large empty bands on the sides after object-contain scaling.
    achievement_url: str | None = None
    try:
        achievement_bytes = await generate_image(
            achievement_description,
            aspect_ratio="16:9",
            reference=previous_bytes,
            anchor=anchor_bytes,
            caption=achievement_caption,
        )
    except Exception as exc:
        logger.error("Achievement generation raised: %s", exc)
        achievement_bytes = None

    if achievement_bytes:
        achievement_url = _process_generated_image(achievement_bytes, sid, "achievement.png", "Achievement")
    else:
        logger.error("Achievement image generation failed")
        session.achievement_failed = True

    _set(session.achievement_future, achievement_url)
```

Notable decisions:

- **Sequential, not parallel.** Each `generate_image` call awaits the previous one, both for reference chaining and to play nicely with the semaphore (which would force serialization anyway).
- **Anchor only set on first success.** If scene 1 fails, scene 2 becomes the anchor on its success; downstream scenes still chain to it.
- **`previous_bytes` updates only on success.** Scene 3 can still chain off scene 1 if scene 2 fails.
- **Both calls hardcode `aspect_ratio="16:9"`** (lines 307 and 337). The `scene_aspect_ratio` / `achievement_aspect_ratio` fields in the format frontmatter are **currently informational only** — the worker does not read them. Changing the worker to honor those fields is a small edit (thread the format object into `_scene_image_worker` and pass `fmt.scene_aspect_ratio` / `fmt.achievement_aspect_ratio` instead of the hardcoded literals) but is a deliberate non-goal in the current design: 16:9 matches the landscape device panel, and a 1:1 achievement left visible dead-space bands after `object-contain` scaling in `AchievementImage`.
- **Failure flags are mutated, then the future is resolved.** `_deliver_scene` reads `scene_failed[i]` only after its own `await _await_scene_image` returns `None`, so the ordering matters — set the flag, then resolve.

#### `start_scene_images`: public entry point

Source: `backend/image_gen.py:355-415`.

```python
def start_scene_images(
    session_id: str,
    scene_descriptions: list[str],
    achievement_description: str,
    scene_captions: list[str | None] | None = None,
    achievement_caption: str | None = None,
) -> _SceneSession:
    """Kick off sequential scene image generation as a background task.

    Returns immediately with a ``_SceneSession`` whose futures resolve
    progressively as each image lands.

    If a session already exists for ``session_id``, its previous worker is
    cancelled before the new one starts — this keeps reset / retry flows
    from leaking stale tasks.
    """
    clear_scene_session(session_id)

    # Normalise captions to a list aligned with scene_descriptions
    normalized_captions: list[str | None]
    if scene_captions is None:
        normalized_captions = [None] * len(scene_descriptions)
    elif len(scene_captions) < len(scene_descriptions):
        normalized_captions = list(scene_captions) + [None] * (len(scene_descriptions) - len(scene_captions))
    else:
        normalized_captions = list(scene_captions)

    loop = asyncio.get_running_loop()
    scene_futures: list[asyncio.Future[str | None]] = [loop.create_future() for _ in scene_descriptions]
    achievement_future: asyncio.Future[str | None] = loop.create_future()

    session = _SceneSession(
        scene_futures=scene_futures,
        achievement_future=achievement_future,
        scene_failed=[False] * len(scene_descriptions),
    )
    _scene_sessions[session_id] = session

    session.task = asyncio.create_task(
        _scene_image_worker(
            session, session_id, scene_descriptions,
            achievement_description, normalized_captions, achievement_caption,
        ),
        name=f"scene-images-{session_id}",
    )
    return session
```

#### Session lifecycle helpers

Source: `backend/image_gen.py:418-432`.

```python
def get_scene_session(session_id: str) -> _SceneSession | None:
    """Look up the active scene-image session for ``session_id``, if any."""
    return _scene_sessions.get(session_id)


def clear_scene_session(session_id: str) -> None:
    """Cancel and drop any scene-image session registered for ``session_id``."""
    session = _scene_sessions.pop(session_id, None)
    if session is None:
        return
    if session.task is not None and not session.task.done():
        session.task.cancel()
    for fut in (*session.scene_futures, session.achievement_future):
        if not fut.done():
            fut.cancel()
```

`clear_scene_session` runs at the top of `start_scene_images` so a retry flow (child changes their mind, or the synthesis re-fires) doesn't leak the previous task.

#### `generate_scene_images`: the blocking wrapper

Source: `backend/image_gen.py:435-462`.

```python
async def generate_scene_images(
    scene_descriptions: list[str],
    achievement_description: str,
    session_id: str = "",
    scene_captions: list[str | None] | None = None,
    achievement_caption: str | None = None,
) -> tuple[list[str | None], str | None]:
    """Generate all scene images + achievement and wait for them.

    Thin wrapper around ``start_scene_images`` preserved for callers that
    want the old "block until everything is ready" behaviour (comparison
    reveal, ad-hoc scripts, tests). Progressive callers should use
    ``start_scene_images`` directly and await individual futures.
    """
    session = start_scene_images(
        session_id, scene_descriptions, achievement_description,
        scene_captions=scene_captions, achievement_caption=achievement_caption,
    )
    scene_urls = [await fut for fut in session.scene_futures]
    achievement_url = await session.achievement_future
    return scene_urls, achievement_url
```

This is **not currently used by the live synthesis path** — `_generate_structured_output` always calls `start_scene_images` directly so it can return early and let `_deliver_scene` await per-scene. `generate_scene_images` is preserved for tests and any one-shot script that wants synchronous semantics.

### 3.4 Concurrency, retry, throttling

Three constants govern the throttling behavior. All live in `backend/image_gen.py`:

```python
_MAX_RETRIES = 2          # image_gen.py:61
_RETRY_DELAY = 3.0        # image_gen.py:62 (seconds)
_imagen_semaphore = asyncio.Semaphore(1)  # image_gen.py:69
```

And one in `backend/turn_handling/synthesis.py`:

```python
_SCENE_IMAGE_WAIT_TIMEOUT_S = 30.0  # synthesis.py:59
```

#### Why `Semaphore(1)`, not `Semaphore(N)`

Vertex Imagen's per-project burst limit was the bottleneck for this demo. `comparison_reveal` fires its single scene image and the achievement image back-to-back; with two concurrent sessions you'd get four near-simultaneous calls, well above the burst threshold and triggering 429s.

Single-permit serialization is simpler than queueing-with-backoff and was sufficient because Imagen latency (~3–5 s) is much smaller than the worst-case wait the user can tolerate (the 30 s scene timeout). Multiplying out: with a single permit, one concurrent Cat5 session paying 4 calls = ~16–20 s end-to-end — well within budget. Two concurrent Cat5 sessions = ~32–40 s end-to-end, which approaches the timeout — but that scenario is rare in the demo and the fallback (placeholder + `image_status: "pending"`) is benign.

If you ever need to raise concurrency, raise the permit count and stress-test against the actual project quota; do not assume the burst limit will scale linearly.

#### Retry policy

Only `RESOURCE_EXHAUSTED` and `429` errors are retried. Everything else (auth failures, malformed prompts, model not found) fails on the first attempt — there's nothing a retry would fix.

The retry sleeps for 3 s before re-attempting. With `_MAX_RETRIES = 2` you get at most one retry: attempt 0, sleep 3 s, attempt 1.

#### Per-scene timeout

`_SCENE_IMAGE_WAIT_TIMEOUT_S = 30.0` is a per-scene cap on the *frontend-facing* wait. The background worker keeps running past it (`asyncio.shield`); a subsequent retry of the same scene delivery can re-await the same future and pick up the result if it landed late.

Math behind 30 s:

- Best case: one Imagen call, ~3–5 s.
- Worst case under the semaphore: previous-scene's Imagen call (3–5 s) plus this scene's call (3–5 s) plus a 429 retry (3 s + 3–5 s) ≈ 14 s.
- Doubling that as headroom = 28 s, rounded to 30 s.

#### Wait-time logging

If the semaphore wait exceeds 100 ms, `image_gen.py` logs the wait. Useful for noticing burst contention you didn't expect. Lower this threshold if you're tuning.

### 3.5 Prompts, captions, achievement template

#### Prompt assembly recipe

```
[STYLE_PREFIX] [scene image_description] [CONSISTENCY_SUFFIX if refs] [CAPTION_PREFIX safe_caption CAPTION_SUFFIX if caption]
```

Concrete example for `fluffy_expedition_dandelion` scene 1 with caption "A breeze finds the soft friends":

```
Soft watercolor children's storybook illustration. Gentle pastel tones, warm lighting. Cloud Puff (a fluffy seed) and Fuzzy Friend (a woolly caterpillar) dozing beneath a curling fern, soft golden afternoon light, cozy storybook composition. Keep the character designs, proportions, colors, and art style visually consistent with the reference image(s). Include exactly ONE short hand-lettered caption along the bottom of the illustration that reads EXACTLY: "A breeze finds the soft friends". Paint it in a cozy hand-lettered storybook style, clearly readable, no other words, no extra letters, no speech bubbles elsewhere in the image.
```

Notes:

- The first scene's call has no `reference` and no `anchor`, so `_CONSISTENCY_SUFFIX` is **not** appended. The second scene's call has both, so the suffix appears.
- The caption is double-quote-stripped before being wrapped (`safe_caption = caption.strip().replace('"', "").replace("“", "").replace("”", "")`) to avoid colliding with the wrapping quotes.
- String concatenation, not `.format()`, is used for caption injection — a literal `{` or `}` in a caption would otherwise raise `KeyError`/`IndexError` at runtime.

#### Caption rules

| Aspect | Rule | Source |
|---|---|---|
| Length | ≤10 words | `_condense_caption(text, max_words=10)` for scenes; ≤6 words for achievement (`role_title` budget) |
| Tone | Present tense, concrete, punchy | `collaborative_story.md` rules |
| Style in image | "Cozy hand-lettered storybook" | `_CAPTION_SUFFIX` |
| Position | Bottom of image | `_CAPTION_PREFIX` |
| When omitted | If `caption is None`, the image is rendered without any text | `generate_image` checks `if caption:` |

The fallback chain in `synthesis.py` for scene captions:

```python
scene.caption = _condense_caption(scene.caption or "", max_words=10) or _condense_caption(
    scene.narration, max_words=8
)
```

So: prefer the LLM's `caption` field. If that's empty/None, distill the scene's narration to 8 words. If both are empty, the scene renders captionless.

Achievement captions:

```python
if role_title:
    caption = f"A new {role_title}!"
    if len(caption.split()) > 6:
        caption = random.choice(_CELEBRATION_CAPTIONS)
else:
    caption = random.choice(_CELEBRATION_CAPTIONS)
```

Examples: `"A new Fluffy Expedition Explorer!"` is 5 words — fits, used. `"A new Polka-Dot Patrol Officer!"` is 5 words — fits. A generic Cat5 with no role title falls back to one of `["We did it!", "What a team!", "Friends forever.", ...]`.

#### Achievement template, reproduced again for emphasis

The LLM **does not** describe the achievement. The composition is locked. The only variables are characters (interpolated), props (rotated), and caption (computed).

This was a deliberate workaround for an LLM regression: the model kept producing achievement descriptions that read like "characters together in a warm scene" — which is exactly what scene 3 already is. The deterministic poster forces a different composition (centered hero pose, celebratory props, high-key lighting).

### 3.6 Reference image chain

Diagram:

```
Scene 1 generation:
  prompt = STYLE + desc1 + (no consistency, no refs)
  refs   = (none)
  ↓
  scene_1_bytes  ──────────► becomes anchor (first success only)
                   ↓
                   becomes previous_bytes

Scene 2 generation:
  prompt = STYLE + desc2 + CONSISTENCY_SUFFIX
  refs   = [anchor=scene_1_bytes, reference=scene_1_bytes]   # collapsed: passes once
  ↓
  scene_2_bytes  ──────────► becomes new previous_bytes (anchor unchanged)

Scene 3 generation:
  prompt = STYLE + desc3 + CONSISTENCY_SUFFIX
  refs   = [anchor=scene_1_bytes, reference=scene_2_bytes]
  ↓
  scene_3_bytes  ──────────► becomes new previous_bytes

Achievement generation:
  prompt = STYLE + achievement_description + CONSISTENCY_SUFFIX
  refs   = [anchor=scene_1_bytes, reference=scene_3_bytes]
```

The collapse (`reference is not anchor` check in `generate_image`) keeps scene 2 from passing the same image twice as both anchor and reference — Imagen's reference handling treats duplicates as redundant and the second one is wasted token budget.

**Why two references, not just anchor?** Anchor alone is insufficient — character drift accumulated between scene 1 and scene 3 because Imagen "forgot" scene 2's pose/composition cues. Anchor + previous gives the model a stable character canon (anchor) plus immediate style continuity (previous), which empirically holds character identity across all three scenes.

**Why full-resolution PNG, not the downscaled JPEG?** Reference comprehension scales with resolution. The JPEG is for the wire payload only; the worker keeps the original 1.3 MB PNG in memory exactly so it can use it as the next reference.

### 3.7 Storage and serving

**On disk:**

```
backend/data/images/
  {session_id}/
    scene_1.png     # ~1.3 MB raw PNG (also held in worker memory)
    scene_2.png     # if collaborative_story
    scene_3.png     # if collaborative_story
    achievement.png # always (assuming success)
```

**On the wire:**

- No separate `/api/image/{id}` endpoint exists.
- Generated images are inlined into the turn JSON as base64 JPEG data URLs (~150 KB each after downscaling).
- This avoids CORS issues and keeps image delivery synchronous with turn flow — the frontend doesn't have to wait for a separate fetch to render the scene.

**Why data URLs:** the `/api/turn-speak` endpoint already streams a length-prefixed JSON + audio binary to the frontend; pushing the image inline keeps the protocol single-channel. The trade-off — every turn carries the image in the payload, no caching — is acceptable because each scene image is delivered once.

---

## 4. Cat5 frontend rendering

The frontend never calls Imagen directly. It receives `widget_params` from the backend and renders the appropriate widget. The backend has already populated `image_data_url` (or marked the image as `pending`/`failed`) by the time the frame arrives.

### 4.1 Widget map

Source: `frontend/src/components/DeviceScreen.jsx:19-31`.

```jsx
const WIDGET_MAP = {
  photo_display: PhotoDisplay,
  progress_tracker: ProgressTracker,
  character_display: CharacterDisplay,
  photo_grid: PhotoGrid,
  photo_recall_grid: PhotoRecallGrid,
  badge_award: BadgeAward,
  story_scene: StoryScene,
  story_loading: StoryLoading,
  achievement_image: AchievementImage,
  concept_reveal: ConceptReveal,
  explorer_map: ExplorerMap,
};
```

Cat5 image-rendering widgets:

- `story_scene` — renders a single scene during `STEP_4_SYNTHESIS` scene-delivery turns.
- `story_loading` — placeholder bookshelf mascot shown during the synthesis loading turn (just before scene 1 lands).
- `achievement_image` — renders the celebration poster on `STEP_5_CELEBRATE`.
- `photo_grid` / `photo_recall_grid` — display collected static-icon images during `STEP_3_COLLECT_*` and the synthesis invite.

### 4.2 `StoryScene` (verbatim)

Source: `frontend/src/widgets/StoryScene.jsx` (full file).

```jsx
import ImageFailedBanner from './ImageFailedBanner';

export default function StoryScene({ image_data_url, image_status, scene_number, animation }) {
  const failed = image_status === 'failed';
  return (
    <div className={`relative flex flex-col items-center w-full h-full p-3 ${
      animation === 'appear' ? 'animate-fade-in' : ''
    }`}>
      {/* Scene image — fills the whole widget area. Progress dots live in
       * DeviceScreen's bottom indicator row so they stay visible even when
       * the image is tall (stage mode on celebrate/closing). */}
      <div className="flex-1 min-h-0 w-full flex items-center justify-center overflow-hidden">
        {image_data_url ? (
          <img
            src={image_data_url}
            alt={`Story scene ${scene_number}`}
            className="w-full h-full rounded-2xl shadow-lg object-contain animate-fade-in transition-transform duration-300 ease-out hover:scale-[1.03] hover:shadow-2xl"
          />
        ) : (
          <div className="w-full h-full rounded-2xl bg-gradient-to-br from-[var(--color-sunflower-light)]/20 to-[var(--color-forest)]/10 flex items-center justify-center">
            <p className="text-lg text-gray-400 font-display">Scene {scene_number}</p>
          </div>
        )}
      </div>
      {failed && <ImageFailedBanner />}
    </div>
  );
}
```

State branches:

- `image_data_url` truthy → `<img>` with the inline JPEG.
- `image_data_url` null → gradient placeholder labeled `Scene N`.
- `image_status === 'failed'` → overlay `ImageFailedBanner` on top of whichever variant rendered.

The progress dots (`scene 1 of 3` style) are rendered by `DeviceScreen` itself, not by `StoryScene`, so they remain visible even when the image fills the widget area. See `frontend/src/components/DeviceScreen.jsx:207-223` for the absolute-positioned dot row.

### 4.3 `AchievementImage` (verbatim)

Source: `frontend/src/widgets/AchievementImage.jsx` (full file).

```jsx
import FallbackTrophy from './FallbackTrophy';
import ImageFailedBanner from './ImageFailedBanner';

export default function AchievementImage({ image_data_url, image_status, title, animation, entity }) {
  const failed = image_status === 'failed';
  return (
    <div className={`relative flex flex-col h-full w-full p-4 ${animation === 'badge_reveal' ? 'animate-celebration-large' : ''}`}>
      <h2 className="text-2xl max-[380px]:text-xl font-bold font-display text-center text-[var(--color-forest-dark)] tracking-tight pb-3 shrink-0">
        {title || 'Explorer'}
      </h2>
      <div className="flex-1 min-h-0 w-full flex items-center justify-center">
        {image_data_url ? (
          <img
            src={image_data_url}
            alt="Your adventure"
            className="max-w-full max-h-full rounded-3xl shadow-2xl object-contain animate-fade-in transition-transform duration-300 ease-out hover:scale-[1.03] hover:shadow-[0_25px_60px_-10px_rgba(76,175,80,0.35)]"
          />
        ) : (
          <FallbackTrophy entity={entity} />
        )}
      </div>
      {failed && <ImageFailedBanner />}
    </div>
  );
}
```

`FallbackTrophy` (verbatim, source `frontend/src/widgets/FallbackTrophy.jsx`) renders a gradient circle with the game's entity icon (e.g. `/icons/dandelion.png`) and a row of decorative sparkles when no `image_data_url` is available:

```jsx
import { useState } from 'react';
import { asset } from '../utils/basePath';

export default function FallbackTrophy({ entity }) {
  const [iconFailed, setIconFailed] = useState(false);
  const showIcon = entity && !iconFailed;

  return (
    <div className="w-full h-full rounded-3xl bg-gradient-to-br from-[var(--color-sunflower-light)]/30 via-white/50 to-[var(--color-forest)]/10 flex items-center justify-center">
      <div className="relative">
        <div className="w-40 h-40 max-[380px]:w-32 max-[380px]:h-32 rounded-full bg-gradient-to-br from-[var(--color-sunflower)] via-[var(--color-sunflower-light)] to-[var(--color-forest)] shadow-xl flex items-center justify-center border-4 border-white/80">
          <div className="w-28 h-28 max-[380px]:w-24 max-[380px]:h-24 rounded-full bg-white/80 flex items-center justify-center overflow-hidden">
            {showIcon ? (
              <img
                src={asset(`/icons/${entity}.png`)}
                alt={entity}
                className="w-[90%] h-[90%] object-contain"
                onError={() => setIconFailed(true)}
              />
            ) : (
              <span className="text-6xl max-[380px]:text-5xl">🏆</span>
            )}
          </div>
        </div>
        {/* sparkles … */}
      </div>
    </div>
  );
}
```

Fallback chain:

1. `image_data_url` present → render the generated achievement.
2. No `image_data_url` and entity icon exists at `/icons/{entity}.png` → render the gradient circle with the icon.
3. No `image_data_url` and entity icon failed/missing → render the gradient circle with a 🏆 emoji.

### 4.4 `ImageFailedBanner` (verbatim)

Source: `frontend/src/widgets/ImageFailedBanner.jsx` (full file).

```jsx
// Muted amber pill shown in the top-right of a widget when its image was
// supposed to render from generated output but the worker reported a real
// failure (vs. "still pending"). Tester-facing — real users rarely see this
// because failures are infrequent and the underlying fallback graphic still
// carries the experience.
export default function ImageFailedBanner({ label = "Couldn't create this image" }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="absolute top-3 right-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-100/95 border border-amber-300 text-amber-900 text-[11px] font-semibold shadow-sm backdrop-blur-sm animate-fade-in pointer-events-none"
    >
      {/* triangle-warning icon SVG */}
      <span>{label}</span>
    </div>
  );
}
```

When it shows: only when `image_status === 'failed'`. **Not** during `pending` — pending shows the placeholder/`FallbackTrophy` without any banner so a slow generation doesn't worry the child.

### 4.5 `StoryLoading` (placeholder during synthesis)

Source: `frontend/src/widgets/StoryLoading.jsx` (selected lines).

```jsx
export default function StoryLoading() {
  return (
    <div className="flex flex-col items-center justify-center gap-6 p-6 h-full select-none">
      {/* Animated storybook mascot */}
      <div className="relative" style={{ animation: 'gentle-float 3s ease-in-out infinite' }}>
        {/* SVG of a book with shimmering pages */}
      </div>
      {/* Shimmer text */}
      <p className="text-xl … story-loading-shimmer">Creating your adventure</p>
      <p className="text-sm text-gray-400 mt-2 animate-pulse">Bringing everything together...</p>
      {/* Bouncing dots */}
    </div>
  );
}
```

This is what the child sees during the gap between confirming the synthesis invite and the first scene image landing. It's an entirely synthetic placeholder — no real progress signal — but the auto-advance turn it sits on resolves the moment scene 1's future settles, so empirically it's brief.

### 4.6 `image_status` lifecycle (frontend ↔ backend contract)

| Backend state | `widget_params.image_status` | `widget_params.image_data_url` | Frontend renders |
|---|---|---|---|
| Worker hasn't finished yet | `"pending"` | not set | Gradient placeholder / `FallbackTrophy`, no banner |
| Worker succeeded | `"ready"` | base64 JPEG data URL | `<img>` with the image |
| Worker reported failure | `"failed"` | not set | Placeholder / `FallbackTrophy` **plus** `ImageFailedBanner` overlay |

The contract is enforced at two backend sites:

- `_deliver_scene` for scene images (`synthesis.py:570-581`).
- `_get_screen_frame` celebrate path for achievement images (`state_machine.py:325-347`):

```python
# state_machine.py:326-347 — Cat5 STEP_5_CELEBRATE achievement_image frame
structured = context.get("structured_story")
achievement_url = structured.achievement_image_data_url if structured else None
achievement_failed = bool(structured.achievement_image_failed) if structured else False
role_title = creative_slots.role_title if isinstance(creative_slots, Cat5CreativeSlots) else "Explorer"
widget_params: dict = {"title": role_title, "entity": entity}
if achievement_url:
    widget_params["image_data_url"] = achievement_url
    widget_params["image_status"] = "ready"
elif achievement_failed:
    widget_params["image_status"] = "failed"
else:
    widget_params["image_status"] = "pending"
return ScreenFrame(
    widget="achievement_image",
    widget_params=widget_params,
    animation="badge_reveal",
    trigger="on_correct",
    sfx_cue="badge_awarded",
)
```

### 4.7 No client-side polling

The frontend does **not** retry, poll, or refetch images. The backend's per-turn await (with `asyncio.shield`) handles all the slowness. From the frontend's perspective, every turn either has the image inline or it doesn't, and the next turn might.

This is a deliberate simplification — adding polling would complicate the React state machine for a marginal UX gain (the 30-second timeout already covers the vast majority of real waits).

---

## 5. Cat1 pre-generated character animation

Cat1 has no Imagen calls. Its "AIGC" is a curated catalogue of MP4 video clips, generated offline with `tools/generate_character_clips.py` (or otherwise sourced), versioned into the repo, and selected at runtime by `useCharacterAnimation`.

### 5.1 Clip catalogue

Two clip types per Cat1 entity:

1. **Character state clips** — what the character does at any given moment.
2. **Scenario world clips** — the round's setting (the "world" the character is in).

Directory layout (verbatim from `frontend/public/videos/`):

```
frontend/public/videos/
├── character/
│   ├── mood_changer_dog/
│   │   ├── dog_celebrating.mp4    2.5M
│   │   ├── dog_encouraging.mp4    2.0M
│   │   ├── dog_excited.mp4        2.5M
│   │   ├── dog_idle.mp4           1.8M
│   │   ├── dog_listening.mp4      2.1M
│   │   ├── dog_speaking.mp4       2.4M
│   │   ├── dog_surprised.mp4      2.2M
│   │   ├── dog_thinking.mp4       1.8M
│   │   └── dog_waving.mp4         1.9M
│   ├── dream_whisperer_cat/      (cat_*, same 9 states)
│   └── time_machine_dinosaur/    (dinosaur_*, same 9 states)
└── scenario/
    ├── mood_changer_dog/
    │   ├── scenario_bath_time.mp4         3.4M
    │   ├── scenario_best_friend.mp4       2.6M
    │   ├── scenario_butterfly.mp4         2.3M
    │   ├── scenario_favorite_treat.mp4    2.1M
    │   ├── scenario_muddy_puddle.mp4      3.3M
    │   ├── scenario_thunder.mp4           2.2M
    │   ├── scenario_tripped_bump.mp4      2.1M
    │   └── scenario_warm_sunshine.mp4     1.8M
    ├── dream_whisperer_cat/      (8 scenario clips)
    └── time_machine_dinosaur/    (8 scenario clips)
```

Character state names come from this set (used as filename suffixes after the entity prefix):

```
idle, listening, speaking, thinking, excited, encouraging, surprised, celebrating, waving
```

Filename pattern: `{videoBasePath}/{videoPrefix}_{state}.mp4`.

For dog: `videoBasePath = "/videos/character/mood_changer_dog"`, `videoPrefix = "dog"`. So the speaking clip is `/videos/character/mood_changer_dog/dog_speaking.mp4`.

Scenario filename pattern: `{scenarioBasePath}/scenario_{slug}.mp4`. Slugs are not the round-scenario text — they're a separate mapping (see below).

### 5.2 Build-time generation tools

Cat1 video is generated ahead of time, not during `/api/start` or `/api/turn-speak`. You do not need to open the tool source to operate it; the complete contract is below.

The build-time generator is `tools/generate_character_clips.py`. It reads `tools/character_clip_prompts.yaml`, calls Veo 3.1 through Vertex AI, saves MP4 files, polls long-running video operations every 20 seconds, and uses `ffmpeg` to extract a first-frame style reference when available.

Runtime never reads generated files from the tool directly. Runtime reads only `frontend/public/videos/...` through the paths declared in `frontend/src/widgets/gameThemes.js`.

#### Fixed generation settings

The current generator uses these settings:

```python
PROMPTS_FILE = Path(__file__).parent / "character_clip_prompts.yaml"
OUTPUT_DIR = Path(__file__).parent.parent / "frontend" / "public" / "video" / "character"
VEO_MODEL = "veo-3.1-fast-generate-001"
ASPECT_RATIO = "16:9"
POLL_INTERVAL_S = 20
MAX_POLL_S = 600
REFERENCE_STATE = "idle"
```

Important path note: current runtime paths and checked-in assets use **plural** `frontend/public/videos/...`, but the generator setting above currently points at **singular** `frontend/public/video/character`. Until the tool is aligned with runtime, move generated files into `frontend/public/videos/{character,scenario}/...` before smoke testing, or adjust `OUTPUT_DIR` locally as part of a dedicated tool fix.

Other fixed behavior:

| Setting | Current value / behavior |
|---|---|
| Video model | `veo-3.1-fast-generate-001` |
| Auth mode | `genai.Client(vertexai=True)`; use Application Default Credentials or `GOOGLE_APPLICATION_CREDENTIALS` plus project env |
| Aspect ratio | `16:9` |
| Videos per prompt | 1 |
| Duration | 8 seconds for every state and scenario clip |
| Person generation | `dont_allow` |
| Poll timeout | 600 seconds per clip |
| Reference frame tool | `ffmpeg -y -i <video> -vframes 1 -q:v 2 <tmp.png>` |

If `ffmpeg` is missing, the generator can still call Veo, but it cannot extract the idle reference frame. That means later clips may drift in style or character design.

#### CLI reference

Run from the repo root.

| Command | What it does |
|---|---|
| `uv run python tools/generate_character_clips.py --dry-run` | Print all character-state prompts and output paths. No API calls. |
| `uv run python tools/generate_character_clips.py` | Generate all character-state clips for every configured Cat1 activity. |
| `uv run python tools/generate_character_clips.py --character mood_changer_dog` | Generate all character-state clips for one activity. |
| `uv run python tools/generate_character_clips.py --character mood_changer_dog --state excited` | Generate one state for one activity. |
| `uv run python tools/generate_character_clips.py --character mood_changer_dog --state excited --ref frontend/public/videos/character/mood_changer_dog/dog_idle.mp4` | Generate one state using a chosen video as the visual reference source. |
| `uv run python tools/generate_character_clips.py --scenarios --dry-run` | Print all scenario prompts and output paths. No API calls. |
| `uv run python tools/generate_character_clips.py --scenarios` | Generate all scenario clips for every configured Cat1 activity. |
| `uv run python tools/generate_character_clips.py --scenarios --character time_machine_dinosaur` | Generate scenario clips for one activity. |

Flag details:

| Flag | Applies to | Meaning |
|---|---|---|
| `--dry-run` | character + scenario modes | Prints prompts/output paths only. Safe for CI and documentation checks. |
| `--character <activity_id>` | character + scenario modes | Limits generation to one activity key from the prompt YAML, e.g. `mood_changer_dog`. |
| `--state <state>` | character mode | Limits generation to one character state, e.g. `excited`. Ignored by scenario mode. |
| `--scenarios` | scenario mode | Switches from character-state generation to scenario-world generation. |
| `--ref <video_path>` | character mode | Extracts the first frame from the provided video and uses it as the style reference. |

#### What the prompt YAML owns

- `defaults.style` locks the toy-rendered look and the still-open / still-close loop rule.
- `characters.<activity>.prefix` drives the output filename prefix: `dog`, `cat`, `dinosaur`.
- `characters.<activity>.base` defines the recurring character identity.
- `characters.<activity>.states` defines state-specific actions. Current states are `idle`, `listening`, `thinking`, `speaking`, `excited`, `encouraging`, `surprised`, `waving`, and `celebrating`.
- `scenarios.<activity>.clips` defines the round-world clips by slug. Those slugs must match the value side of `SCENARIO_SLUGS` in `gameThemes.js`.

Current expected count from the YAML:

| Clip group | Count |
|---|---:|
| Character state clips | 3 activities × 9 states = 27 |
| Scenario world clips | 3 activities × 8 scenarios = 24 |
| Total Cat1 MP4s | 51 |

Minimal YAML shape for adding a new Cat1 activity:

```yaml
defaults:
  resolution: "480x480"
  style: >
    3D rendered toy aesthetic, Pixar-inspired, warm lighting. No text or UI elements.
    The first 2 seconds hold the resting pose, the middle 4 seconds perform the action,
    and the final 2 seconds return to the exact same resting pose for seamless looping.
  loop_duration: "4s"
  oneshot_duration: "3s"

characters:
  kindness_practice_bunny:
    prefix: bunny
    base: >
      A cute stuffed bunny toy with soft cream fur, floppy ears, and a small stitched smile.
      Centered in frame, sitting upright, facing slightly toward camera in a warm playroom.
    states:
      idle:
        type: loop
        action: >
          The bunny breathes gently with a calm expression and tiny ear twitches.
      listening:
        type: loop
        action: >
          The bunny leans forward, ears perked, eyes attentive.
      thinking:
        type: loop
        action: >
          The bunny tilts its head and taps one paw thoughtfully.
      speaking:
        type: loop
        action: >
          The bunny nods and sways gently as if talking warmly.
      excited:
        type: oneshot
        action: >
          The bunny bounces happily with bright eyes.
      encouraging:
        type: oneshot
        action: >
          The bunny gives a slow, reassuring nod.
      surprised:
        type: oneshot
        action: >
          The bunny pops upright with wide curious eyes.
      waving:
        type: oneshot
        action: >
          The bunny raises one paw and waves hello or goodbye.
      celebrating:
        type: loop
        action: >
          The bunny dances in place with proud, happy energy.

scenarios:
  kindness_practice_bunny:
    style: >
      Warm, child-friendly scene. Soft lighting.
    clips:
      sharing_blocks: "Sitting near colorful blocks, watching two toys share pieces kindly."
      helping_friend: "Beside a smaller toy that dropped something, leaning in to help."
```

#### Character clip generation flow

1. Load `characters` from the prompt YAML.
2. Optionally filter by `--character` and/or `--state`.
3. Generate `idle` first when present. That clip becomes the style reference.
4. Extract the first frame with `ffmpeg`.
5. Generate every remaining state with the idle frame as `image=` reference.
6. Save each MP4 as `{OUTPUT_DIR}/{activity}/{prefix}_{state}.mp4`.

#### Scenario clip generation flow

Scenario clips use the same CLI with `--scenarios`. The tool loads `scenarios.<activity>.clips`, prepends the character's base description, appends the scenario style plus global defaults, and writes `scenario_<clip_id>.mp4`.

For scenario generation, the tool extracts `{prefix}_idle.mp4` as a visual reference when it exists. Generate or provide the idle character clip first if consistency matters.

#### Runtime handoff checklist

After a real generation run:

1. Place character files at `frontend/public/videos/character/<activity>/<prefix>_<state>.mp4`.
2. Place scenario files at `frontend/public/videos/scenario/<activity>/scenario_<slug>.mp4`.
3. Confirm `GAME_THEMES.<entity>.videoBasePath`, `videoPrefix`, and `scenarioBasePath` point to the same activity.
4. Confirm every `scenarios.<activity>.clips` slug from the YAML has a matching `SCENARIO_SLUGS` value.
5. Smoke a Cat1 session: `STEP_2_*` should resolve `<prefix>_waving.mp4`, `STEP_3_*` should resolve `scenario_<slug>.mp4`, and `STEP_4_CELEBRATE` should resolve `<prefix>_celebrating.mp4`.

### 5.3 `gameThemes.js` (the manifest)

Source: `frontend/src/widgets/gameThemes.js:1-8` (dog entry).

```javascript
const GAME_THEMES = {
  dog: {
    characterPng: `${BASE}/icons/dog.png`,
    videoBasePath: `${BASE}/videos/character/mood_changer_dog`,
    videoPrefix: 'dog',
    scenarioBasePath: `${BASE}/videos/scenario/mood_changer_dog`,
    /* particles, gradient, etc. for theming */
  },
  /* cat, dinosaur — same shape with different paths and prefix */
  /* ladybug, dandelion — entries WITHOUT videoBasePath (Cat5 has no clips) */
};
```

A Cat5 entity (`ladybug`, `dandelion`) is in the same manifest but **lacks `videoBasePath`/`videoPrefix`**. The `useCharacterAnimation` hook uses this absence to short-circuit (`hasVideo = false`); the animation system never tries to load video for Cat5.

#### Scenario slug mapping (verbatim)

Source: `frontend/src/widgets/gameThemes.js:194-226`.

```javascript
const SCENARIO_SLUGS = {
  mood_changer_dog: {
    'warm sunshine on belly': 'warm_sunshine',
    'tripped and went bump': 'tripped_bump',
    'favorite treat arrives': 'favorite_treat',
    'sees a butterfly flying by': 'butterfly',
    'hears thunder outside': 'thunder',
    'best friend comes to visit': 'best_friend',
    'bath time surprise': 'bath_time',
    'found a muddy puddle': 'muddy_puddle',
  },
  dream_whisperer_cat: {
    'floating on a cloud in the sky': 'floating_cloud',
    'swimming in a milk ocean': 'milk_ocean',
    'magical garden of favorites': 'magical_garden',
    'chasing a glowing star through the dark': 'glowing_star',
    'riding on a giant friendly bird': 'giant_bird',
    'exploring a castle made of yarn balls': 'yarn_castle',
    'bouncing on a rainbow bridge': 'rainbow_bridge',
    'hiding in a cozy cave of pillows': 'pillow_cave',
  },
  time_machine_dinosaur: {
    'prehistoric jungle': 'prehistoric_jungle',
    'rumbling volcano': 'rumbling_volcano',
    'peaceful lake at sunset': 'lake_sunset',
    'a snowy mountain top': 'snowy_mountain',
    'a dark spooky cave': 'spooky_cave',
    'a field of giant flowers': 'giant_flowers',
    'a stormy ocean beach': 'stormy_beach',
    'meeting another friendly dinosaur': 'friendly_dinosaur',
  },
};

export function getScenarioSlug(activityType, scenarioText) {
  const slugs = SCENARIO_SLUGS[activityType];
  if (!slugs || !scenarioText) return null;
  return slugs[scenarioText] || null;
}
```

The keys here must exactly match the `scenario` field of each round in the game's YAML (e.g. `backend/games/mood_changer_dog.md` has `scenario: "Morning! The warm sunshine lands on the doggy's belly. ..."` for round 1 — but the key here is the simpler `creative_slots.round_scenarios` entry `"warm sunshine on belly"`). The frontend gets the simpler form via `currentScenario` from the session state.

### 5.4 `useCharacterAnimation` (verbatim)

Source: `frontend/src/hooks/useCharacterAnimation.js` (full file, ~145 lines).

```javascript
import { useState, useCallback, useEffect, useRef } from 'react';
import { getThemeForEntity, getScenarioSlug } from '../widgets/gameThemes';

const ONE_SHOT_STATES = new Set(['excited', 'encouraging', 'surprised']);

function entityFromActivity(activityType) {
  if (!activityType) return null;
  const parts = activityType.split('_');
  return parts[parts.length - 1] || null;
}

/**
 * Manages character animation state and video clip selection.
 *
 * Priority (highest to lowest):
 * 1. Session lifecycle: waving at start/end
 * 2. AI response: emotion clip (excited, encouraging, surprised, speaking)
 * 3. TTS active: speaking clip
 * 4. Round idle: scenario clip loops as the "world"
 * 5. Default: character idle clip
 */
export default function useCharacterAnimation({
  isSpeaking,
  characterState,
  messageCount,
  currentStep,
  currentRound,
  currentScenario,
  activityType,
  templateType,
}) {
  const [animationState, setAnimationState] = useState(null);
  const oneShotFollowUpRef = useRef(null);
  const lastProcessedMsgRef = useRef(0);

  const entity = entityFromActivity(activityType);
  const theme = entity ? getThemeForEntity(entity) : null;
  const hasVideo = !!(templateType === 'cat1' && theme?.videoPrefix);

  // Determine the "resting" state — what to show after TTS/reactions finish
  const restingState =
    currentStep === 'STEP_4_CELEBRATE' ? 'celebrating' :
    currentStep === 'STEP_5_CLOSING' || currentStep === 'ENDED' ? 'waving' :
    currentStep?.startsWith('STEP_3_') && currentRound >= 1 && currentScenario ? 'scenario' :
    'idle';

  // Resolve clip URL from animation state
  const resolveClipUrl = useCallback((state) => {
    if (!state || !hasVideo || !theme?.videoBasePath || !theme?.videoPrefix) return null;

    if (state === 'scenario') {
      if (!theme?.scenarioBasePath || !currentScenario) {
        return `${theme.videoBasePath}/${theme.videoPrefix}_idle.mp4`;
      }
      const slug = getScenarioSlug(activityType, currentScenario);
      if (!slug) {
        return `${theme.videoBasePath}/${theme.videoPrefix}_idle.mp4`;
      }
      return `${theme.scenarioBasePath}/scenario_${slug}.mp4`;
    }

    return `${theme.videoBasePath}/${theme.videoPrefix}_${state}.mp4`;
  }, [hasVideo, theme, currentScenario, activityType]);

  // 1. Game intro — waving once (8s) then idle, triggered at STEP_2.
  const hasPlayedWavingRef = useRef(false);
  useEffect(() => {
    if (!hasVideo) return;
    if (!currentStep?.startsWith('STEP_2_') || hasPlayedWavingRef.current) return;
    hasPlayedWavingRef.current = true;
    const startTimer = setTimeout(() => setAnimationState('waving'), 0);
    const idleTimer = setTimeout(() => setAnimationState('idle'), 8000);
    return () => { clearTimeout(startTimer); clearTimeout(idleTimer); };
  }, [currentStep, hasVideo]);

  // 2. AI response — set character emotion clip. TTS audio plays on top (overlapped).
  useEffect(() => {
    if (!hasVideo || !characterState || messageCount <= lastProcessedMsgRef.current) return;
    lastProcessedMsgRef.current = messageCount;
    const timer = setTimeout(() => {
      setAnimationState(characterState);
      // One-shot clips return to resting state after playing; loops keep going
      oneShotFollowUpRef.current = ONE_SHOT_STATES.has(characterState) ? restingState : null;
    }, 0);
    return () => clearTimeout(timer);
  }, [characterState, messageCount, hasVideo, restingState]);

  // 2b. New scenario introduced — override emotion clip with scenario world.
  const prevScenarioRef = useRef(null);
  useEffect(() => {
    if (!hasVideo || !currentScenario) return;
    if (!currentStep?.startsWith('STEP_3_') || currentRound < 1) return;
    if (currentScenario === prevScenarioRef.current) return;
    prevScenarioRef.current = currentScenario;
    const timer = setTimeout(() => {
      setAnimationState('scenario');
      oneShotFollowUpRef.current = null;
    }, 0);
    return () => clearTimeout(timer);
  }, [hasVideo, currentScenario, currentStep, currentRound]);

  // 3. When TTS ends (true→false), return to resting state (scenario or idle).
  const wasSpeakingRef = useRef(false);
  useEffect(() => {
    if (!hasVideo) return;
    if (isSpeaking) { wasSpeakingRef.current = true; return undefined; }
    if (!wasSpeakingRef.current) return undefined;
    wasSpeakingRef.current = false;
    const timer = setTimeout(() => {
      setAnimationState((prev) => {
        if (prev === 'waving' || prev === 'celebrating') return prev;
        return restingState;
      });
    }, 0);
    return () => clearTimeout(timer);
  }, [isSpeaking, hasVideo, restingState]);

  // Callback for when a one-shot video clip ends
  const onClipEnded = useCallback(() => {
    if (oneShotFollowUpRef.current) {
      setAnimationState(oneShotFollowUpRef.current);
      oneShotFollowUpRef.current = null;
    }
  }, []);

  const isOneShot = ONE_SHOT_STATES.has(animationState);
  const currentClipUrl = resolveClipUrl(animationState);
  return {
    animationState,
    currentClipUrl,
    isOneShot,
    onClipEnded,
  };
}
```

State machine summary:

| Step / event | Resulting `animationState` | Loops? |
|---|---|---|
| `STEP_2_*` first entry | `waving` (8 s) → then `idle` | one-shot then loop |
| `STEP_3_*` round entry with new scenario | `scenario` | loop |
| AI emotion response (one-shot states) | `excited`, `encouraging`, or `surprised` | one-shot, then `restingState` |
| AI emotion response (looping states) | `speaking`, `listening`, `thinking`, `idle` | loop |
| `isSpeaking` rises | (kept on current state, video ducks volume) | — |
| `isSpeaking` falls | back to `restingState` (unless waving/celebrating) | — |
| `STEP_4_CELEBRATE` | `celebrating` | loop |
| `STEP_5_CLOSING` / `ENDED` | `waving` | loop |

`ONE_SHOT_STATES = {excited, encouraging, surprised}`. Everything else is treated as a loop (`<video loop>`).

Resting state derivation (the post-TTS fallback):

```
STEP_4_CELEBRATE          → celebrating
STEP_5_CLOSING / ENDED    → waving
STEP_3_*  with currentRound>=1 and currentScenario → scenario
otherwise                 → idle
```

### 5.5 The Cat1 video gate

Source: `frontend/src/hooks/useCharacterAnimation.js:38`.

```javascript
const hasVideo = !!(templateType === 'cat1' && theme?.videoPrefix);
```

Two conditions:

1. `templateType === 'cat1'` — gating the entire system to Cat1 (commit `0d4a2c2`). Cat5 entities never play video, even if you accidentally put `videoBasePath` on a Cat5 entry in `gameThemes.js`.
2. `theme?.videoPrefix` truthy — guards against entities without a clip catalogue.

If either is false, every code path returns `null` for `currentClipUrl`, and `CharacterDisplay` renders the static-PNG variant instead.

### 5.6 `CharacterDisplay` and `DeviceScreen` integration

`CharacterDisplay` is the only widget that plays `<video>`. It uses a dual-slot crossfade so swapping clips doesn't show a blank frame:

Source: `frontend/src/widgets/CharacterDisplay.jsx:28-78` (load+play orchestration).

```javascript
useEffect(() => {
  if (!clipUrl) return;
  console.log('[CharacterDisplay] loading clip:', clipUrl, 'isOneShot:', isOneShot);

  const nextSlot = activeSlotRef.current === 'a' ? 'b' : 'a';
  const nextVideo = nextSlot === 'a' ? videoARef.current : videoBRef.current;
  const oldVideo = nextSlot === 'a' ? videoBRef.current : videoARef.current;

  if (!nextVideo) return;

  let activated = false;
  const activate = () => {
    if (activated) return;
    activated = true;
    if (oldVideo) oldVideo.pause();
    if (unlockedRef.current) nextVideo.muted = false;
    nextVideo.play().catch(/* fallback to muted retry */);
    activeSlotRef.current = nextSlot;
    setActiveSlot(nextSlot);
    setReadyToShow(true);
  };

  const onCanPlay = () => activate();
  const onLoadedData = () => activate();
  const onError = () => { /* log error */ };

  nextVideo.addEventListener('canplay', onCanPlay);
  nextVideo.addEventListener('loadeddata', onLoadedData);
  nextVideo.addEventListener('error', onError);
  nextVideo.src = clipUrl;
  nextVideo.loop = !isOneShot;
  nextVideo.load();

  return () => {
    nextVideo.removeEventListener('canplay', onCanPlay);
    nextVideo.removeEventListener('loadeddata', onLoadedData);
    nextVideo.removeEventListener('error', onError);
  };
}, [clipUrl, isOneShot]);
```

Volume management — Cat1 video has its own audio track that ducks during TTS playback:

```javascript
const VIDEO_VOLUME = 0.4;
const VIDEO_VOLUME_DUCKED = 0.1;

useEffect(() => {
  const volume = videoMuted ? 0 : isSpeaking ? VIDEO_VOLUME_DUCKED : VIDEO_VOLUME;
  if (videoARef.current) videoARef.current.volume = volume;
  if (videoBRef.current) videoBRef.current.volume = volume;
}, [isSpeaking, videoMuted]);
```

`DeviceScreen` decides whether to render the full-panel video or fall back to the regular widget. When `clipUrl` is non-null it overrides the backend's widget choice with `CharacterDisplay`:

Source: `frontend/src/components/DeviceScreen.jsx:101-118`.

```javascript
const frameKey = getFrameKey(screenFrame);
// In video mode, always render CharacterDisplay regardless of backend widget
// (celebrate/closing steps use badge_award, but we want the video to play)
const isVideoMode = !!clipUrl;
const WidgetComponent = isVideoMode ? CharacterDisplay : WIDGET_MAP[screenFrame.widget];
const params = screenFrame.widget_params || {};

// character_display has its own gentle-float; suppress all overlay animations
// except scene_transition (crossfade between rounds)
let overlayAnimation = screenFrame.animation;
if (isVideoMode && overlayAnimation !== 'scene_transition') {
  overlayAnimation = 'appear';
}

// In video mode, use a stable key so frame changes (celebrate → closing)
// don't remount the CharacterDisplay and reset its video playback state.
// Non-video widgets still use the full frameKey for proper transitions.
const containerKey = isVideoMode ? 'video-player' : frameKey;
```

Badge overlay during celebrate (Cat1):

Source: `frontend/src/components/DeviceScreen.jsx:148-169`.

```javascript
{/* Badge + IB concepts overlay on top of video during celebrate/closing */}
{isVideoMode && screenFrame.widget === 'badge_award' && (
  <div className="absolute bottom-3 left-3 right-3 z-10 flex flex-col gap-1.5 animate-badge-pop">
    <div className="flex items-center gap-2 bg-black/50 backdrop-blur-sm rounded-full pl-1.5 pr-3 py-1.5 shadow-lg self-start">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[var(--color-sunflower)] to-[var(--color-forest)] flex items-center justify-center border-2 border-white/60">
        <BadgeIcon className="w-4 h-4 text-white" />
      </div>
      <span className="text-white text-xs font-semibold truncate max-w-[8rem]">
        {params.title || 'Explorer'}
      </span>
    </div>
    {params.concepts?.length > 0 && (
      <div className="flex items-center gap-1.5 self-start">
        {params.concepts.map((concept) => (
          <span key={concept} className="px-2.5 py-1 bg-white/90 backdrop-blur-sm rounded-full text-[11px] font-semibold text-[var(--color-forest-dark)] shadow-sm border border-[var(--color-forest)]/20">
            {concept}
          </span>
        ))}
      </div>
    )}
  </div>
)}
```

Result: on `STEP_4_CELEBRATE`, the dog/cat/dinosaur celebrating clip plays full-panel and the role title + IB concepts float as a translucent overlay along the bottom.

### 5.7 Cat1 static asset paths

Beyond video, Cat1 also uses:

- **Entity icons** — `frontend/public/icons/{entity}.png` (e.g. `/icons/dog.png`). Used as the central icon in the `BadgeAward` fallback and as the `characterPng` placeholder while the first video loads.
- **Concept badges** — `frontend/public/badges/{concept}.png` (e.g. `/badges/perspective.png`). One per IB concept; rendered by `BadgeAward`'s `ConceptBadge` component with a CSS-gradient fallback if the PNG is missing.

The full `frontend/public/badges/` listing:

```
causation.png   change.png         connection.png   form.png
function.png    perspective.png    reflection.png   responsibility.png
```

These eight match the IB Primary Years Programme key concepts referenced by `ib_key_concept` and `concepts_earned` in the game `.md` frontmatter.

---

## 6. Configuration reference

### 6.1 `.env` (secrets — verbatim from `.env.example`)

```
# Option A: Vertex AI (service account)
GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
GOOGLE_CLOUD_PROJECT="your-project-id"
GOOGLE_CLOUD_LOCATION="us-central1"

# Option B: Gemini API key (AI Studio) — used when GOOGLE_CLOUD_PROJECT is empty
GEMINI_API_KEY="your-gemini-api-key"
OPENAI_API_KEY="your-openai-api-key"
OPENAI_BASE_URL="https://api.openai.com/v1"
LOG_LEVEL=INFO

# Imagen 3 image generation (uses same Google Cloud credentials above)
# Set IMAGEN_ENABLED=false to disable image generation (story still works without images)
```

Additionally — but not in `.env.example` — the synthesis LLM uses ALI Qwen via DashScope:

```
ALI_API_KEY="your-dashscope-api-key"
ALI_BASE_URL="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
```

### 6.2 `config.yaml` (verbatim)

Source: `backend/config.yaml`.

```yaml
gemini_model: "gemini-2.5-flash"
tts_model: "gemini-2.5-flash-tts"
openai_model: "gpt-5.2"
ali_model: "qwen3.5-plus"
imagen_model: "gemini-2.5-flash-image"
vision_timeout_ms: 15000
director_timeout_ms: 10000
director_max_tokens: 1000
script_timeout_ms: 60000
script_max_tokens: 4096
script_turn_timeout_ms: 5000
script_turn_max_tokens: 2048
turn_director_enabled: true
best_of_n: 1
max_retries: 3
db_path: "data/demo.db"
log_level: "DEBUG"
```

`imagen_enabled` is **not** in this file — its default is `True` in `config.py`. To disable, add `imagen_enabled: false` here, or set `IMAGEN_ENABLED=false` in `.env`.

### 6.3 `Settings` class (verbatim)

Source: `backend/config.py:24-62`.

```python
class Settings(BaseSettings):
    """Unified settings from environment variables and config.yaml."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Secrets — loaded from .env
    google_cloud_project: str = ""
    google_cloud_location: str = "us-central1"
    google_application_credentials: str = ""
    openai_api_key: str = ""
    openai_base_url: str = ""
    gemini_api_key: str = ""
    ali_api_key: str = ""
    ali_base_url: str = ""

    # App config — defaults from config.yaml, overridable by env vars
    gemini_model: str = str(_yaml_config.get("gemini_model", "gemini-2.5-flash"))
    openai_model: str = str(_yaml_config.get("openai_model", "gpt-5.2"))
    ali_model: str = str(_yaml_config.get("ali_model", "qwen3.5-plus"))
    ali_classifier_model: str = str(_yaml_config.get("ali_classifier_model", "qwen3.5-flash"))
    tts_model: str = str(_yaml_config.get("tts_model", "gemini-2.5-flash-tts"))
    director_timeout_ms: int = int(_yaml_config.get("director_timeout_ms", 200))
    director_max_tokens: int = int(_yaml_config.get("director_max_tokens", 150))
    script_timeout_ms: int = int(_yaml_config.get("script_timeout_ms", 600))
    script_max_tokens: int = int(_yaml_config.get("script_max_tokens", 600))
    script_turn_timeout_ms: int = int(_yaml_config.get("script_turn_timeout_ms", 5000))
    script_turn_max_tokens: int = int(_yaml_config.get("script_turn_max_tokens", 500))
    two_pass_enabled: bool = bool(_yaml_config.get("two_pass_enabled", False))
    planner_max_tokens: int = int(_yaml_config.get("planner_max_tokens", 400))
    planner_temperature: float = float(_yaml_config.get("planner_temperature", 0.3))
    speaker_temperature: float = float(_yaml_config.get("speaker_temperature", 0.7))
    turn_director_enabled: bool = bool(_yaml_config.get("turn_director_enabled", False))
    best_of_n: int = int(_yaml_config.get("best_of_n", 1))
    vision_timeout_ms: int = int(_yaml_config.get("vision_timeout_ms", 5000))
    max_retries: int = int(_yaml_config.get("max_retries", 3))
    db_path: str = str(_yaml_config.get("db_path", "data/demo.db"))
    log_level: str = str(_yaml_config.get("log_level", "INFO"))
    imagen_model: str = str(_yaml_config.get("imagen_model", "gemini-2.5-flash-image"))
    imagen_enabled: bool = bool(_yaml_config.get("imagen_enabled", True))
```

Override precedence: env var → `config.yaml` → hardcoded default.

### 6.4 AIGC-relevant settings table

| Setting | Default | Purpose | Source |
|---|---|---|---|
| `imagen_model` | `"gemini-2.5-flash-image"` | Imagen API model id | `config.yaml:5`, `config.py:61` |
| `imagen_enabled` | `True` | Master switch | `config.py:62` |
| `google_cloud_project` | `""` | Empty → API key auth; set → Vertex AI | `config.py:30` |
| `google_cloud_location` | `"us-central1"` | Informational; client uses `"global"` | `config.py:31` |
| `google_application_credentials` | `""` | Vertex AI service account JSON path | `config.py:32` |
| `gemini_api_key` | `""` | Used when `google_cloud_project` is empty | `config.py:35` |
| `ali_api_key` | `""` | Story-LLM key (DashScope) | `config.py:36` |
| `ali_base_url` | `""` | Story-LLM endpoint | `config.py:37` |
| `ali_model` | `"qwen3.5-plus"` | Story LLM model id | `config.yaml:4`, `config.py:42` |
| `script_timeout_ms` | `60000` | Story LLM request timeout | `config.yaml:9`, `config.py:47` |
| `script_max_tokens` | `4096` | Hard ceiling; per-format `max_tokens` is the practical limit | `config.yaml:10`, `config.py:48` |

### 6.5 Disabling AIGC

To disable image generation entirely:

```bash
# .env
IMAGEN_ENABLED=false
```

or:

```yaml
# config.yaml
imagen_enabled: false
```

What happens:

1. `generate_image()` returns `None` immediately on every call (`image_gen.py:125-127`).
2. The worker flips `scene_failed[i] = True` for every scene and `achievement_failed = True`.
3. `_deliver_scene` sees `scene.image_failed = True` and emits `image_status: "failed"`.
4. The frontend renders the placeholder + `ImageFailedBanner` overlay.

Story narration and audio are unaffected — only the picture is missing. This is the recommended setting for local development and CI when you don't want to burn quota.

---

## 7. Extension recipes

Each recipe assumes you have read sections 3–6.

### 7.1 Add a new Cat5 activity (with image generation)

Goal: a new entity, e.g. `acorn_shell_collection`, that uses `collaborative_story` to make a 3-scene story from collected items.

1. **Game definition.** Create `backend/games/<game_id>.md` modeled on `fluffy_expedition_dandelion.md`. Key frontmatter fields:
   - `activity_type: <game_id>`, `entity_name: <entity>`, `category: category_5`, `tier: T0|T1|T2`.
   - `creative_slots.observation_angle`, `collection_count: 3`, `role_title`, `naming_prompt`, `detail_question_template`.
   - `story_scaffold.synthesis_format: collaborative_story` (or `comparison_reveal` / `sorting_challenge`).
   - `collection_catalog.correct` and `collection_catalog.distractors` — each entry has `id`, `label`, `image: /icons/<id>.png`.
   - `step_instructions.{hook,transition,rounds[],celebrate,closing,synthesis,early_exit}` with the dialogue goals and constraints.
   - `screen_frames[]` and `celebration_frame` for widget orchestration.
2. **Test scenario.** Add a `backend/scenarios/<game_id>.yaml` that drives an end-to-end run for tests. Modeled on `backend/scenarios/fluffy_expedition_dandelion.yaml`.
3. **Static icons.** Drop PNGs at `frontend/public/icons/<id>.png` for every `collection_catalog` item (correct + distractors) and the entity itself. Refer to `docs/cat5-image-asset-list.md` for the existing prompt-style guidance for these icons.
4. **Theme entry.** In `frontend/src/widgets/gameThemes.js` add a new `<entity>:` block with `characterPng`, gradient/border/accent classes. **Omit** `videoBasePath`/`videoPrefix` — Cat5 has no video.
5. **Verify with no code changes.** No edits to `image_gen.py`, `synthesis.py`, or any agent are needed if the format already exists. The format registry (`get_format(...)`) reads the format `.md` lazily and the synthesis handler dispatches by format id — there's no Python-level glue you have to add.

If you're using `comparison_reveal` instead, also set `creative_slots.observation_angle` (e.g. `"pattern"`, `"texture"`) — this becomes `{obs_angle}` in the prompt and the invite template. For `sorting_challenge`, set `creative_slots.sorting_criterion` so `{sorting_suffix}` renders.

### 7.2 Add a new synthesis format

Goal: a new format, e.g. `sing_along_chant` with 4 scenes.

1. **Bump the schema ceiling.** `synthesis_formats/loader.py:55` has `scene_count: int = Field(ge=1, le=5)`. 4 is within range; if you need 6+, raise `le=6` (or higher) here. Larger scene counts also need a longer-budget aspect somewhere — you'll hit the `script_max_tokens` ceiling around 6–8 scenes depending on narration length.
2. **Write the format file.** Create `backend/synthesis_formats/sing_along_chant.md` with the same frontmatter shape as the existing formats. Required body sections: `# system_prompt`, `# user_prompt`, `# direction_template`. The user_prompt MUST produce JSON matching `StructuredStory` (a `scenes` array of `{narration, image_description, caption}`).
3. **Aspect ratio is currently hardcoded.** The `scene_aspect_ratio` / `achievement_aspect_ratio` fields in your format frontmatter are not read by the worker — both calls hardcode `aspect_ratio="16:9"` (`image_gen.py:307`, `image_gen.py:337`). If your new format truly needs a different ratio (e.g. portrait scenes for a 9:16 display), thread the format object into `_scene_image_worker` and replace the hardcoded literals with `fmt.scene_aspect_ratio` / `fmt.achievement_aspect_ratio`. Imagen 3 supports `"1:1"`, `"9:16"`, `"16:9"`, `"3:4"`, `"4:3"`.
4. **Wire up at the scaffold level.** Any game that wants to use the format sets `story_scaffold.synthesis_format: sing_along_chant`. No code change in `synthesis.py` is needed — `_resolve_format_id` reads from the scaffold and `get_format(id)` dispatches.
5. **Caveat on captions.** All current formats produce a `caption` field per scene. If your format omits captions, the worker still works — `_condense_caption` returns `None`, and `generate_image` skips the caption block entirely. No change to `image_gen.py`.
6. **Caveat on the achievement template.** The achievement description is **always** overwritten post-parse with the deterministic poster template, regardless of format. If you want format-specific achievement composition, that's the one place you'd need a Python-level change — extend `_build_achievement_prompt` to branch on format id and pass the format object in from `_generate_structured_output`.

### 7.3 Swap the image model

Goal: replace `gemini-2.5-flash-image` with a different Imagen variant or a third-party model.

- **For another Vertex / Gemini-family image model:** change `imagen_model` in `config.yaml`. The model name is passed straight through as `model=settings.imagen_model` in `generate_image`, and the SDK handles routing. Verify the new model supports the `response_modalities=["IMAGE"]` and `image_config=types.ImageConfig(aspect_ratio=...)` config options; `image_gen.py:163-166` is the only call site.
- **For a non-Google model:** you'll need to refactor `_get_client` and `generate_image` together. Imagen-specific assumptions in the current code:
  - `client.models.generate_content(...)` returns `parts[*].inline_data.data` for the image bytes (`_extract_image_bytes`).
  - Reference images are passed as `types.Part.from_bytes(data=..., mime_type="image/png")`.
  - Errors `genai_errors.ClientError` and `genai_errors.APIError` are the retry surface.
  - Aspect ratio is set via `types.GenerateContentConfig`/`types.ImageConfig`.
  Replacing the model means re-implementing `generate_image` against the new SDK, but the surrounding worker, futures, semaphore, and retry policy stay unchanged.
- **Do not bump the semaphore permit count blindly.** Imagen's per-project burst limit doesn't transfer to other vendors; new vendors may have wildly different policies. Stress-test before raising `Semaphore(1)` to `Semaphore(N)`.

### 7.4 Tune the watercolor style

The style prefix is the single global lever for the entire Cat5 image library. Source: `backend/image_gen.py:41`.

```python
_STYLE_PREFIX = "Soft watercolor children's storybook illustration. Gentle pastel tones, warm lighting."
```

To A/B a different style:

1. Edit the `_STYLE_PREFIX` constant.
2. Re-run a Cat5 session to verify the new style across the full pipeline (scene 1 → scene 3 → achievement).

Things to watch for:

- The reference-image chain biases toward continuity. Switching styles mid-tree is hard for the model; expect scene 1 to lean strongly on the prefix and scenes 2/3 to look more like scene 1.
- The caption-rendering reliability depends on the prefix evoking a hand-drawn aesthetic. "Photorealistic" prefixes tend to produce printed-text captions instead of hand-lettered, which sometimes fails the readability check.
- If you want per-format style overrides, add a `style_prefix:` field to the format `.md` frontmatter, surface it on `SynthesisFormat`, and pass it through `start_scene_images`. None of this is wired today.

### 7.5 Add a new Cat1 activity (with character video)

Goal: a new Cat1 entity, e.g. `kindness_practice_bunny`, with a full clip catalogue.

1. **Game definition.** Create `backend/games/<game_id>.md` modeled on `mood_changer_dog.md` or `dream_whisperer_cat.md`. Key fields:
   - `category: category_1`, `tier: T0|T1|T2`.
   - `creative_slots.game_mechanic: voice_acting` (or other Cat1 mechanic).
   - `creative_slots.round_scenarios: [...]` — list of scenario texts. These map 1:1 to `scenario_*.mp4` filenames (after slug conversion).
2. **Add prompt YAML for character clips.** Extend `tools/character_clip_prompts.yaml`:
   - Add `characters.<game_id>` with `prefix`, `base`, and the full state set: `idle`, `listening`, `thinking`, `speaking`, `excited`, `encouraging`, `surprised`, `waving`, `celebrating`.
   - Keep the `prefix` short and stable; it becomes the filename stem (`<prefix>_idle.mp4`, etc.).
3. **Generate / source 9 character clips.** Use the Veo CLI when generating in-repo:
   ```sh
   uv run python tools/generate_character_clips.py --character <game_id> --dry-run
   uv run python tools/generate_character_clips.py --character <game_id>
   ```
   Each clip is 16:9, 8 seconds in the current tool, looping where appropriate. Names use the YAML `prefix`:
   - `<prefix>_idle.mp4`, `<prefix>_listening.mp4`, `<prefix>_speaking.mp4`, `<prefix>_thinking.mp4`, `<prefix>_excited.mp4`, `<prefix>_encouraging.mp4`, `<prefix>_surprised.mp4`, `<prefix>_celebrating.mp4`, `<prefix>_waving.mp4`.
   - Drop them in `frontend/public/videos/character/<game_id>/` before runtime validation. The current generator constant writes to `frontend/public/video/character`, so move files or fix the tool path if needed.
4. **Add prompt YAML and generate / source up to 8 scenario clips.** Add `scenarios.<game_id>.clips` in `tools/character_clip_prompts.yaml`, one clip per `round_scenarios` entry, then run:
   ```sh
   uv run python tools/generate_character_clips.py --scenarios --character <game_id> --dry-run
   uv run python tools/generate_character_clips.py --scenarios --character <game_id>
   ```
   Names:
   - `scenario_<slug>.mp4` where `<slug>` is the value side of your `SCENARIO_SLUGS` mapping.
   - Drop them in `frontend/public/videos/scenario/<game_id>/`.
5. **Add the slug map.** Extend `SCENARIO_SLUGS` with a `<game_id>:` block mapping each `creative_slots.round_scenarios` string to the scenario filename slug:
   ```javascript
   const SCENARIO_SLUGS = {
     kindness_practice_bunny: {
       'sharing blocks': 'sharing_blocks',
       'helping a friend': 'helping_friend',
     },
   };
   ```
   Runtime resolves the second example to:
   `/videos/scenario/kindness_practice_bunny/scenario_helping_friend.mp4`.
6. **Add the theme entry.** Add a `GAME_THEMES` entry keyed by the entity returned from the activity id. `entityFromActivity(activityType)` uses the last underscore-separated token, so `kindness_practice_bunny` needs a `bunny` theme key:
   ```javascript
   bunny: {
     characterPng: `${BASE}/icons/bunny.png`,
     videoBasePath: `${BASE}/videos/character/kindness_practice_bunny`,
     videoPrefix: 'bunny',
     scenarioBasePath: `${BASE}/videos/scenario/kindness_practice_bunny`,
     particles: [
       { emoji: '🌼', count: 2, baseSize: 14 },
       { emoji: '💛', count: 1, baseSize: 12 },
     ],
     gradient: 'from-rose-50 to-rose-200',
     border: 'border-rose-300/40',
     accent: 'text-rose-800',
     accentBg: 'bg-rose-800/10',
     iconBg: 'bg-white ring-rose-200/60',
     decorations: ['🌼', '💛'],
   }
   ```
7. **Test the gating.** `useCharacterAnimation` checks `templateType === 'cat1' && theme?.videoPrefix`. Both must be true; the entity must be detected by `entityFromActivity(activityType)` (which takes the last `_`-separated part of `activityType` — so `kindness_practice_bunny` → `bunny`, which must match the theme key).
8. **Fallback states.** If a state has no clip, the resolved URL still points to a non-existent file; the `<video>` element will fail with `error`, but `useCharacterAnimation` already returns `null` from `resolveClipUrl` in some cases (e.g. unknown scenario → falls back to `<entity>_idle.mp4`). Make sure `_idle.mp4` always exists; it's the fallback for missing scenario slugs.

### 7.6 Disable AIGC for local dev

Add to `backend/.env`:

```
IMAGEN_ENABLED=false
```

Restart the backend. Verification:

- Trigger a Cat5 session end-to-end. Story narration plays normally; scene widgets show the gradient placeholder; the `ImageFailedBanner` appears in the top-right of every scene/achievement widget.
- Check backend logs: `Imagen disabled, skipping image generation` lines should appear at every Imagen call site.

To re-enable, remove the line and restart. No state cleanup is required between modes — `_scene_sessions` is in-memory only.

---

## 8. Failure modes & debugging

### 8.1 Symptom → cause → fix

| Symptom | Likely cause | Fix |
|---|---|---|
| Logs show `RESOURCE_EXHAUSTED` / `429` | Imagen burst limit | Confirm `_imagen_semaphore = asyncio.Semaphore(1)` is intact; check Vertex quota dashboard; if multiple sessions in parallel are common, request a quota increase rather than raising the permit count. |
| Character drifts visually across scenes | Reference chain broken (likely scene 1 failed, anchor missing) | Inspect `scene_failed[]` in the worker logs. If scene 1 failed, scene 2 becomes the anchor — the inconsistency will visibly start from there. |
| Achievement looks identical to scene 3 | The deterministic template is not running | Confirm `_build_achievement_prompt` is called in `_generate_structured_output` and that `story.achievement_description` is actually the deterministic value (log it). The LLM's value should be discarded. |
| Scene image times out | Imagen latency spike or upstream queue | Wait for the next turn delivery — `asyncio.shield` keeps the worker running; the resolved URL will appear on a subsequent retry. If timeouts are frequent, raise `_SCENE_IMAGE_WAIT_TIMEOUT_S` past 30 s but expect compounding effects with the semaphore. |
| Scene shows a blank gray placeholder | `image_status: "pending"` (worker still running) | Normal during the first few seconds. If it never resolves, check `_scene_sessions[session_id]` — `session.task.done()` and `task.exception()`. |
| Scene shows the amber failure banner | `image_status: "failed"` (worker confirmed failure) | Check Imagen logs upstream (auth failure? bad prompt? quota exhausted?). The PNG won't be on disk — that's the diagnostic signal. |
| Data URL too large / browser slow | `_downscale_to_jpeg` not running | Confirm `_process_generated_image` is called. The 768-max-dim/JPEG-85% pipeline cuts payload to ~150 KB; raw PNGs are ~1.3 MB. |
| Missing entity icon in `BadgeAward`/`FallbackTrophy` | `frontend/public/icons/<entity>.png` doesn't exist | Add the icon, or rely on the existing fallback (CSS gradient + 🏆 emoji). |
| Cat1 character clip fails to load | Wrong path or missing file | Check the resolved URL in the browser console. Path is `{videoBasePath}/{videoPrefix}_{state}.mp4`. Confirm the file exists at the public-folder root. |
| Newly generated Cat1 clips do not load | Generator wrote to `frontend/public/video/...` while runtime expects `frontend/public/videos/...` | Move the generated MP4s into the plural `videos` tree or patch `tools/generate_character_clips.py:33` in a dedicated tool fix. |
| Cat1 video not playing on celebrate | Video gate check failed | Verify `templateType === 'cat1'` arrives at the hook; verify `theme.videoPrefix` is set in `gameThemes.js`. |

### 8.2 Where to look

- **Backend logs.** Default `LOG_LEVEL=DEBUG` in `config.yaml` makes `image_gen.py` and `synthesis.py` very chatty. Lines to grep for: `Imagen generated image`, `Scene N image generation failed`, `Imagen waited Nms for semaphore`, `Imagen rate-limited, retrying`, `Achievement image generation failed`, `Structured story LLM response`.
- **Saved images on disk.** `backend/data/images/{session_id}/scene_*.png` and `achievement.png`. If the file exists, generation succeeded; if not, it failed. The full PNG (not the downscaled JPEG) is what the worker held in memory for the reference chain.
- **Browser network tab.** `/api/turn-speak` responses include the inline JPEG. The base64 string starts with `data:image/jpeg;base64,...`. If you see this, the frontend has the image — any rendering issue is on the React side.
- **`useConversation` state.** `screenFrame.widget_params.image_status` and `image_data_url` are passed straight from the backend.
- **Tester feedback flag UI.** Commit `db68c9c` added the tester quick-flag feature — testers can mark a moment with a screenshot, captured in the gallery panel (commit `019f63e`). Useful for tracking down "I saw a weird image yesterday" reports.

### 8.3 Useful one-liners

Inspect a session's generated images:

```sh
ls -lh backend/data/images/<session_id>/
```

Find the most recent session directory:

```sh
ls -td backend/data/images/*/ | head -1
```

See semaphore wait times in real time:

```sh
tail -f /var/log/wonderlens.log | grep "Imagen waited"
```

Disable AIGC quickly without editing files:

```sh
IMAGEN_ENABLED=false uv run uvicorn server:app --reload --port 8000
```

---

## 9. Test coverage

### 9.1 Concurrency test (verbatim)

Source: `backend/tests/test_image_gen_concurrency.py` (full file).

```python
"""Tests for the Imagen concurrency gate in ``image_gen.generate_image``.

Vertex Imagen has a per-project burst limit that the demo blew past whenever
a Cat5 ``comparison_reveal`` synthesis fired its single scene image and
achievement image back-to-back. The semaphore in ``image_gen`` collapses
both intra-session bursts and cross-session races into a serial queue;
these tests prove that gate actually serializes calls.
"""

import asyncio
import time
from typing import Any

import image_gen
import pytest


class _FakeImagenClient:
    """Stand-in for ``genai.Client`` that records concurrent in-flight calls."""

    def __init__(self, sleep_seconds: float) -> None:
        self.sleep_seconds = sleep_seconds
        self.in_flight = 0
        self.peak_in_flight = 0
        self.call_count = 0
        self.models = self  # client.models.generate_content → self.generate_content

    def generate_content(self, **_kwargs: Any) -> object:
        # Synchronous body — runs inside ``asyncio.to_thread`` so a real
        # blocking sleep is the right tool for measuring serialization.
        self.in_flight += 1
        self.peak_in_flight = max(self.peak_in_flight, self.in_flight)
        self.call_count += 1
        try:
            time.sleep(self.sleep_seconds)
        finally:
            self.in_flight -= 1
        return object()


@pytest.fixture()
def fake_client(monkeypatch: pytest.MonkeyPatch) -> _FakeImagenClient:
    """Patched ``image_gen`` env: fake client, fake bytes, fresh semaphore."""
    fake = _FakeImagenClient(sleep_seconds=0.2)
    monkeypatch.setattr(image_gen, "_get_client", lambda: fake)
    monkeypatch.setattr(image_gen, "_extract_image_bytes", lambda _resp: b"\x89PNGFAKE")
    monkeypatch.setattr(image_gen, "_imagen_semaphore", asyncio.Semaphore(1))
    monkeypatch.setattr(image_gen.get_settings(), "imagen_enabled", True)
    return fake


@pytest.mark.asyncio
async def test_concurrent_calls_are_serialized(fake_client: _FakeImagenClient) -> None:
    """Two concurrent ``generate_image`` calls must not overlap."""
    start = time.perf_counter()
    results = await asyncio.gather(
        image_gen.generate_image("scene one"),
        image_gen.generate_image("scene two"),
    )
    elapsed = time.perf_counter() - start

    assert all(r == b"\x89PNGFAKE" for r in results)
    assert fake_client.call_count == 2
    assert fake_client.peak_in_flight == 1, f"semaphore allowed {fake_client.peak_in_flight} concurrent Imagen calls"
    assert elapsed >= 0.35, f"calls finished in {elapsed:.3f}s — semaphore not gating"


@pytest.mark.asyncio
async def test_single_call_does_not_block(fake_client: _FakeImagenClient) -> None:
    """A lone caller should not pay any semaphore wait penalty."""
    start = time.perf_counter()
    result = await image_gen.generate_image("solo scene")
    elapsed = time.perf_counter() - start

    assert result == b"\x89PNGFAKE"
    assert fake_client.peak_in_flight == 1
    assert elapsed < 0.5
```

Pattern to replicate when adding tests:

- `monkeypatch` swaps `_get_client`, `_extract_image_bytes`, and `_imagen_semaphore` on the `image_gen` module. This isolates the test from real Vertex auth and from any leaked semaphore state across tests.
- Assertions on `peak_in_flight` and elapsed wall-clock time prove serialization without depending on Imagen-specific behavior.

### 9.2 Where to add tests

- **Synthesis dispatch.** Tests for `_resolve_format_id`, `_build_template_variables`, and `_build_achievement_prompt` belong in a `tests/test_synthesis*.py`. Mock the LLM and `start_scene_images`; assert that template variables are rendered correctly per format.
- **Format loader.** Tests for `loader.py` should cover: missing required body section → `ValueError`; missing frontmatter → `ValueError`; valid file → populated `SynthesisFormat`. Add a fixture under `tests/fixtures/synthesis_formats/` rather than mutating real format files.
- **Frontend render branches.** RTL tests for `StoryScene` and `AchievementImage` should cover the three `image_status` states. The `ImageFailedBanner` appears only on `failed` — assert with `getByRole('status')`.
- **Cat1 video gate.** `useCharacterAnimation` returns `currentClipUrl: null` when `templateType !== 'cat1'`. Add a unit test that toggles `templateType` between `'cat1'` and `'cat5'` and asserts the URL flips between a real path and `null`.

---

## 10. Recent history pointers

When you need the *why* behind a current design decision, dig into the design doc that originally shaped it.

| Commit | Subject | Original design doc |
|---|---|---|
| `8232359` | fix(synthesis): re-check live image session on celebrate frame | `docs/plans/2026-04-10-progressive-scene-image-delivery.md` |
| `b8d0c8e` | fix(image_gen): semaphore around Imagen calls to prevent 429 bursts | (no plan doc — direct fix; commit message has the rationale) |
| `db68c9c` | feat(feedback): tester flag capture + image failure banner | `docs/plans/2026-04-13-tester-feedback-collection.md` |
| `019f63e` | feat(feedback): read-only gallery panel for reviewers | `docs/plans/2026-04-14-feedback-gallery.md` |
| `b8aeef8` | refactor(synthesis): data-driven format registry (#10) | `docs/plans/2026-04-10-synthesis-format-registry.md` |
| `852f201` | feat: scene-by-scene story images, celebration redesign, content feedback (#9) | `docs/plans/2026-04-09-scene-images-achievement.md` |
| `d6db875` / `0d4a2c2` / `937121f` | character animation system; Cat1 video gate; rename `video` → `videos` | `docs/plans/2026-04-01-cat1-character-animation.md` |
| `1170c6f` | refactor(turn): decompose turn_handler into package | `docs/plans/2026-04-03-turn-handler-decomposition.md` |

---

## 11. Glossary

| Term | Definition |
|---|---|
| **AIGC** | AI-generated content. In this repo: live Imagen 3 images for Cat5; pre-rendered MP4 clips for Cat1. |
| **Anchor scene** | The first successfully generated scene image. Used as a reference for every subsequent scene to keep characters visually consistent. Set once per session; never replaced. |
| **Achievement image** | The celebration poster shown on `STEP_5_CELEBRATE`. Composed from a deterministic template (rotating props, locked composition), not from the LLM's free-text description. |
| **Caption** | Short ≤10-word string baked into the bottom of an image as hand-lettered text. Optional per scene; falls back to a condensed form of the narration if the LLM omits it. |
| **Character state** | A label like `idle`, `speaking`, `excited` that maps to a specific Cat1 video clip. Selected by `useCharacterAnimation`. |
| **Cat1 / Category 1** | In-Device Verbal activities. Three games: `mood_changer_dog`, `dream_whisperer_cat`, `time_machine_dinosaur`. Use pre-rendered MP4 clips, not Imagen. |
| **Cat5 / Category 5** | Out-of-Device Collection activities. Two games: `polka_dot_patrol`, `fluffy_expedition_dandelion`. Use live Imagen 3 generation during synthesis. |
| **Data URL** | A `data:image/jpeg;base64,…` string. Generated images are inlined into turn responses this way (no separate `/api/image/{id}` endpoint exists). |
| **Hook rule** | Convention that every game's first turn ends with an imaginative question. Defined in each game's `step_instructions.hook` block. |
| **IB concept** | International Baccalaureate Primary Years Programme key concept. Each game declares one or more in `concepts_earned`. Examples: `Form`, `Connection`, `Perspective`. |
| **Imagen 3** | Google's image-generation model, accessed via the Gemini API as `gemini-2.5-flash-image`. Single-permit semaphored in this repo to dodge per-project burst limits. |
| **Per-scene future** | An `asyncio.Future[str | None]` produced by `start_scene_images`. The worker resolves each future with the scene's data URL (or `None` on failure) the moment it lands. The synthesis handler awaits these one at a time as it delivers scenes to the frontend. |
| **Reference chain** | The (anchor, previous-scene) pair passed to Imagen on each scene generation to keep character identity stable across scenes. |
| **Resting state** | The Cat1 character animation state to fall back to after TTS or a one-shot reaction finishes. Derived from current step + scenario. |
| **Scenario** | A round-specific Cat1 setting like `"warm sunshine on belly"`. Mapped via `SCENARIO_SLUGS` to a video filename slug. |
| **Scene** | One element of `StructuredStory.scenes`. Carries `narration`, `image_description`, `caption`, and (post-generation) `image_data_url` / `image_failed`. |
| **Slug** | The filename-safe stem for a scenario clip. Derived from a `round_scenario` string via the per-game `SCENARIO_SLUGS` map. |
| **Structured story** | The Pydantic `StructuredStory` produced by the LLM during Cat5 synthesis. Contains the scene list and (after override) the achievement template description and caption. |
| **Synthesis format** | A markdown file under `backend/synthesis_formats/` that drives Cat5 image generation. Currently: `collaborative_story` (3 scenes), `comparison_reveal` (1 scene), `sorting_challenge` (1 scene, unused by current games). |
| **Tier** | Age band for the activity. `T0` = ages 2–4, `T1` = ages 4–6, `T2` = ages 6–8. Affects narration length, not image generation. |

---

> **For deeper context** see `docs/wonderlens_activity_demo_build_spec.md` (full agent design), `docs/game-pipeline-overview.md` (general pipeline mechanics), `docs/cat5-image-asset-list.md` (per-asset checklist for Cat5 static icons), `docs/tester-guide.md` (operator-facing UX), and the dated design docs under `docs/plans/` for any specific feature listed in [Section 10](#10-recent-history-pointers).
