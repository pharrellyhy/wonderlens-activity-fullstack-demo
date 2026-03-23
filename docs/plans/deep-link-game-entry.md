# Deep Link Direct Game Entry

## Context

A separate upstream web app has a multi-turn conversation with a child about an entity (e.g., dinosaur). After the conversation, it redirects to our WonderLens demo URL with parameters to start the game directly — skipping game selection (PhotoSelector) and game summary (GameDetailView). The game's STEP_1_HOOK should be shortened to briefly acknowledge the upstream conversation before moving to STEP_2.

**Handoff data from upstream:** entity name, tier, and structured conversation context (`[{role, text}, ...]`).

**URL format:** `https://our-demo.com/?entity=dinosaur&tier=T0&context=/handoff/conversation.json`

The upstream app saves the conversation context as a JSON file (array of `{role, text}` objects) to a location served by the frontend (e.g., `/handoff/conversation.json`), and passes its path via the `context` URL parameter. The frontend fetches this file before starting the session.

---

## Phasing

### Phase 1 (this plan): Known entities
- Upstream passes entity name (e.g., "dinosaur") → we look up the matching game in our registry
- Supports all 5 demo entities: dinosaur, dog, cat, ladybug, dandelion
- Unknown entities return a friendly error suggesting available entities

### Phase 2 (future): Unknown entities with dynamic game generation
- Algorithm to pick the best game template (Cat 1 or Cat 5) for any entity
- Dynamic creative slots generation adapted to the entity
- Dynamic collection catalog generation for Cat 5 (LLM-powered)
- Essentially: `mood_changer_elephant`, `polka_dot_patrol_butterfly`, etc.

---

## Phase 1 — Implementation Steps

### Step 1: Schema — Add deep link fields to SessionStateModel

**File:** `backend/schemas/session_state.py`

Add two fields to `SessionStateModel`:

```python
deep_linked: bool = False
upstream_conversation: list[dict] = Field(default_factory=list)
```

Both have defaults so existing code is unaffected.

---

### Step 2: Entity Registry — Add `lookup_by_entity_name()`

**File:** `backend/entity_registry.py`

New public function that searches `ENTITY_REGISTRY` by `entity_name` (case-insensitive), falls back to `_KEYWORD_MAP` for keyword-based lookup. Returns `EntityConfig | None`.

```python
def lookup_by_entity_name(entity_name: str) -> EntityConfig | None:
    name_lower = entity_name.lower().strip()
    for entity in ENTITY_REGISTRY:
        if entity.entity_name.lower() == name_lower:
            return entity
    activity_type = _KEYWORD_MAP.get(name_lower)
    if activity_type:
        return _BY_ACTIVITY_TYPE.get(activity_type)
    return None
```

---

### Step 3: Backend — New `POST /api/start-deep-link` endpoint

**File:** `backend/server.py`

New Pydantic request model:

```python
class DeepLinkStartRequest(BaseModel):
    entity: str
    tier: str = "T0"
    conversation_context: list[dict] = []
```

New endpoint logic:
1. Call `lookup_by_entity_name(request.entity)` to get `EntityConfig`
2. If not found, return 400 with `{"error": "Unknown entity", "available_entities": [...]}` listing available entity names (Phase 2 will handle unknown entities dynamically)
3. Resolve `activity_type` from entity config
4. Load instruction recipe via `load_instruction_recipe(activity_type)` (reuse existing)
5. Call `recipe_to_session_state(recipe, session_id, tier, entity_config.demo_filename)` (reuse existing)
6. Set `state.deep_linked = True` and `state.upstream_conversation = request.conversation_context`
7. Generate Cat 5 round items if applicable (reuse existing pattern from lines 169-170)
8. Generate hook turn via `ScriptAgent` (which will see the `deep_linked` flag)
9. Return same response shape as `/api/start` plus `photo_url` from entity's `icon_src`

The endpoint mirrors the demo-entity path in `start_session` (lines 164-219) but accepts JSON instead of multipart form data and uses entity name lookup instead of filename matching.

---

### Step 4: Script Agent — Shortened hook for deep-linked sessions

**File:** `backend/agents/script_agent.py`

Two changes in the system prompt / step instruction building:

**A. Upstream context in system prompt:**
When `state.deep_linked` and `state.upstream_conversation` is non-empty, append an "Upstream Conversation Context" section after the existing conversation state section. Format each turn as `Child: ...` or `Upstream AI: ...`.

**B. Deep link override for STEP_1_HOOK:**
When `state.deep_linked` and step is `STEP_1_HOOK`, append a "Deep Link Override" instruction block after loading the base hook instructions:

```
### DEEP LINK OVERRIDE (takes priority over normal hook rules):
This child was just talking with another AI about {entity_name}. They already know the entity.
Your hook must be SHORTENED:
1. One brief sentence acknowledging what they were just discussing (reference a specific detail from the upstream conversation).
2. Immediately transition to the game invitation — frame it as "Would you like to...?" using invitational language.
3. Do NOT do the full observation + wonder sequence. The child is already engaged.
4. Maximum 2 sentences total regardless of tier.
```

This layers the override on top of existing instructions without modifying the base step instruction files.

---

### Step 5: Frontend API client — Add `startDeepLinkSession()`

**File:** `frontend/src/utils/api.js`

New export function:

```js
export async function startDeepLinkSession(entity, tier, conversationContext) {
  const res = await fetch('/api/start-deep-link', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ entity, tier, conversation_context: conversationContext }),
  });
  if (!res.ok) throw new Error(`Deep link start failed: ${res.status}`);
  return res.json();
}
```

---

### Step 6: useConversation — Add `startDeepLink()` method

**File:** `frontend/src/hooks/useConversation.js`

New function mirroring `start()` (lines 73-122) but:
- Calls `startDeepLinkSession(entity, tier, conversationContext)` instead of `startSession(photo, tier)`
- Sets `photoUrl` directly from the response's `photo_url` field (no `URL.createObjectURL` needed)
- All other state updates (sessionId, sessionState, screenFrame, messages, loading, error) identical to `start()`

Export `startDeepLink` alongside existing `start`.

---

### Step 7: useSessionOrchestration — Add `startDeepLinkSession()` wrapper

**File:** `frontend/src/hooks/useSessionOrchestration.js`

New function that:
1. Calls `unlockSfx()` (browser autoplay policy)
2. Delegates to `conversation.startDeepLink(entity, tier, conversationContext)`

Export `startDeepLinkSession` alongside existing `startSession`.

---

### Step 8: App.jsx — URL param parsing and auto-start

**File:** `frontend/src/App.jsx`

Add a `useEffect` that runs once on mount:
1. Parse `window.location.search` for `entity` (required), `tier` (optional, default "T0"), `context` (optional, path to a JSON file)
2. If `entity` param exists:
   - If `context` is provided, fetch the JSON file at that path → parse → array of `{role, text}` (try/catch for fetch or parse failure)
   - Call `startDeepLinkSession(entity, tier, conversationContext)`
   - After session starts, call `window.history.replaceState({}, '', '/')` to clear URL params (prevent re-trigger on refresh)
3. The existing `showPhotoSelector` logic (`!sessionId && !loading && !showRetry`) already prevents rendering when `loading` is true, so PhotoSelector is never shown during deep link auto-start

---

## Key Files

| File | Change |
|------|--------|
| `backend/schemas/session_state.py` | Add `deep_linked`, `upstream_conversation` fields |
| `backend/entity_registry.py` | Add `lookup_by_entity_name()` |
| `backend/server.py` | New `POST /api/start-deep-link` endpoint + request model |
| `backend/agents/script_agent.py` | Upstream context in prompt, hook override |
| `frontend/src/utils/api.js` | New `startDeepLinkSession()` |
| `frontend/src/hooks/useConversation.js` | New `startDeepLink()` method |
| `frontend/src/hooks/useSessionOrchestration.js` | New wrapper |
| `frontend/src/App.jsx` | URL param parsing + auto-start on mount |

---

## Reused Existing Code

| Function/Utility | File | Reused In |
|------------------|------|-----------|
| `load_instruction_recipe()` | `backend/recipe_loader.py` | Step 3 — load recipe by activity_type |
| `recipe_to_session_state()` | `backend/recipe_loader.py` | Step 3 — build session state from recipe |
| `generate_round_items()` | `backend/entity_registry.py` | Step 3 — Cat 5 round items |
| `ScriptAgent` + `_generate_with_retry()` | `backend/agents/script_agent.py`, `backend/turn_handler.py` | Step 3 — generate hook turn |
| `get_screen_frame()` | `backend/state_machine.py` | Step 3 — build hook frame |
| `_build_turn_response()` | `backend/server.py` | Step 3 — format response |
| `_session_state_dict()` | `backend/server.py` | Step 3 — serialize state |

---

## Edge Cases

- **Unknown entity (Phase 1):** Return 400 with list of available entity names. Phase 2 will handle this with dynamic game generation.
- **Empty/missing context:** Set `deep_linked=true` but generate normal-length hook (no upstream references)
- **Context file not found:** Frontend catches fetch error, proceeds without context
- **Browser refresh:** URL params cleared after start via `replaceState`, so refresh returns to PhotoSelector
- **CORS:** Upstream app domain must be added to `allow_origins` in `server.py` for production deployment

---

## Verification

1. Start backend (`uv run uvicorn server:app --reload --port 8000`) + frontend (`npm run dev`)
2. Save a test context JSON file:
   ```
   echo '[{"role":"child","text":"I see a big dinosaur!"},{"role":"ai","text":"What do you notice about it?"},{"role":"child","text":"It has spikes on its back!"}]' > frontend/public/handoff/conversation.json
   ```
3. Navigate to `http://localhost:5173/?entity=dinosaur&tier=T0&context=/handoff/conversation.json`
4. Verify: PhotoSelector and GameDetailView are **never shown**
5. Verify: First AI message is a **shortened hook** (1-2 sentences) referencing the upstream conversation
6. Verify: Game proceeds normally through STEP_2 → STEP_3
7. Verify: `?entity=elephant` returns a clear error with available entities
8. Verify: Browser refresh after start returns to PhotoSelector (URL params cleared)
9. Run `uv run ruff check .` and `uv run ruff format .` on backend

---

## Phase 2 Outline (Future)

### Goal
Support unknown entities by dynamically generating game variants.

### Key challenges
1. **Template selection algorithm:** Given an unknown entity, pick the best game template (Cat 1 or Cat 5). Options: LLM-based selection, heuristic rules, or hybrid.
2. **Dynamic creative slots:** Generate entity-adapted creative slots (metaphor, round scenarios, escalation axis for Cat 1; collection criterion, synthesis type for Cat 5).
3. **Dynamic collection catalog (Cat 5):** Generate correct items + distractors for the entity via LLM. E.g., for `polka_dot_patrol_butterfly`: correct = spotted butterfly wings, distractor = plain wings, moth wings, etc.
4. **Photo/icon handling:** Unknown entities won't have demo photos in our system. Options: use a generic placeholder, accept a photo URL from upstream, or generate an icon.

### Approach sketch
- Extend `/api/start-deep-link` to detect unknown entities and route to a "dynamic generation" path
- Use Gemini (Director Agent or new dedicated agent) to: pick template → generate creative slots → generate collection catalog
- Cache generated game configs to avoid re-generating for the same entity
- Latency will be higher (~1-2s for LLM calls) compared to Phase 1 (~500ms for known entities)
