# Batch Game Setup: Convert prod.md + Generate Entity Icons

## Context

We have 12 `*_prod.md` game design documents in `backend/games/` that are rich markdown design docs but lack YAML frontmatter — so the game loader ignores them. To make these games playable in the demo (especially via deep link from the upstream app), each needs:
1. A structured game `.md` file with valid YAML frontmatter
2. A character entity icon PNG in `frontend/public/icons/`

We build two reusable CLI tools that leverage Gemini to automate both tasks.

## Tool 1: `scripts/convert_game.py`

Converts a `*_prod.md` design doc into a loadable game `.md` with YAML frontmatter using Gemini 2.0 Flash in JSON mode.

### Flow

1. Read prod.md file
2. Detect category (Cat1 vs Cat5) via regex on "Activity Category" field
3. Load a reference game file (same category) as a few-shot example
4. Build prompt with: reference YAML, prod.md content, Pydantic JSON schema
5. Call Gemini in JSON mode with the appropriate Pydantic output model
6. Deserialize JSON → Pydantic model → validate
7. Serialize to YAML, wrap in `---` delimiters, append original markdown below
8. Validate via `game_parser.parse_game_file()`
9. Write output file (or print in dry-run mode)

### CLI Interface

```
uv run python scripts/convert_game.py backend/games/bicycle_cat1_prod.md
uv run python scripts/convert_game.py backend/games/bicycle_cat1_prod.md --dry-run
uv run python scripts/convert_game.py --all
uv run python scripts/convert_game.py --all --dry-run
```

## Tool 2: `scripts/generate_icon.py`

Generates character entity icon PNGs via Gemini Imagen, matching existing kawaii illustration style.

### CLI Interface

```
uv run python scripts/generate_icon.py bicycle
uv run python scripts/generate_icon.py bicycle --style-ref frontend/public/icons/dog.png
uv run python scripts/generate_icon.py --all
```

## Prod Files to Convert (12)

**Cat1 (6):** bicycle, city_library, green_apple, playground, stop_sign, sunflower
**Cat5 (6):** crayons, eye, firefighter, lion, piano, raincoat

## Verification

1. Dry-run output produces valid YAML with all fields populated
2. Output files pass `game_parser.parse_game_file()` without errors
3. Backend loads new entities via `GET /api/entities`
4. Icons are ~256x256 PNGs with transparent backgrounds, kawaii style
5. Lint: `uv run ruff check scripts/` and `uv run ruff format scripts/`
