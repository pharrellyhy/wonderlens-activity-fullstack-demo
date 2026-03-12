## Recipe Assembler — Validation and Merge Rules

The Recipe Assembler merges the Script Agent's VoiceScript and the Visual Agent's ScreenScript into
a single unified JSON recipe. It validates the combined output against schema and content rules,
then applies retry or fallback logic on failure.

---

## Merge Rules

1. **Round alignment**: Each VoiceScript round must pair with exactly one ScreenScript frame.
   If counts differ, pad the shorter output with defaults (blank frame or silent round).

2. **Hook merge**: VoiceScript `hook_line` pairs with ScreenScript hook frame (always frame index 0).

3. **Transition merge**: VoiceScript `transition_line` is injected between hook and round 1.
   No dedicated screen frame — it shares the hook frame.

4. **Closing merge**: VoiceScript `closing_speech` pairs with the ScreenScript closing frame
   (always last frame). `tomorrow_hook` is appended to the closing turn.

5. **SFX cues**: Each round's `sfx_cue` from VoiceScript is placed in the merged round object.
   The Visual Agent does not set SFX — only the Script Agent does.

6. **Field precedence**: If both agents produce conflicting metadata, the Director Agent's
   Composition Plan is the tie-breaker.

---

## Validation Checklist

| #  | Check                              | Severity | On Failure                                    |
|----|-------------------------------------|----------|-----------------------------------------------|
| 1  | Recipe has hook_line                | CRITICAL | Retry from Script Agent                       |
| 2  | hook_line contains no question marks| CRITICAL | Retry from Script Agent                       |
| 3  | Round count matches Director plan   | CRITICAL | Retry from Script Agent                       |
| 4  | Round count within tier bounds      | CRITICAL | Clamp to tier max and warn                    |
| 5  | Every round has all branch paths    | CRITICAL | Retry from Script Agent                       |
| 6  | closing_speech exists               | CRITICAL | Retry from Script Agent                       |
| 7  | T0 closing has no IB concept names  | WARNING  | Strip concept names, log warning              |
| 8  | T1 closing names exactly 1 concept  | WARNING  | Log warning, do not retry                     |
| 9  | T2 closing names up to 3 concepts   | WARNING  | Log warning, do not retry                     |
| 10 | Every round has a paired screen frame | WARNING | Pad with default photo_display frame          |
| 11 | All animations are in allowed list  | WARNING  | Replace with gentle_pulse                     |
| 12 | All SFX cues are in allowed list    | WARNING  | Replace with null                             |
| 13 | Sentence count per turn within tier | WARNING  | Truncate to tier max_sentences                |
| 14 | Words per sentence within tier range| WARNING  | Log warning, do not retry                     |
| 15 | tomorrow_hook exists                | WARNING  | Insert default: "See you next time!"          |

---

## Retry and Fallback Logic

1. **First failure (CRITICAL)**: Re-run the failing agent with the same inputs. Include the
   validation error message in the retry prompt so the agent can self-correct.

2. **Second failure (CRITICAL)**: Re-run with a simplified prompt — reduce round count by 1
   (minimum 2 rounds) and relax creative constraints.

3. **Third failure (CRITICAL)**: Abandon agent pipeline. Load the pre-built fallback recipe from
   `backend/fallbacks/` matching the activity name and tier. Log the failure for review.

4. **WARNING failures**: Never trigger a retry. Apply the automatic fix described in the
   "On Failure" column and log the warning.

Maximum total latency budget: 3 retries x ~600ms = ~1800ms before fallback.

---

## Allowed SFX Cues

The following are the only valid SFX cue values. Any other value must be replaced with `null`.

| SFX Cue                   | When to Use                              |
|----------------------------|------------------------------------------|
| wonder_chime               | Hook / first reaction                    |
| excitement_rising          | Building toward mission or reveal        |
| photo_shutter_click        | Child submits a photo                    |
| slot_fill_chime            | Collection slot fills                    |
| mission_accepted           | Role assignment / mission start          |
| mission_complete_fanfare   | All collection slots filled              |
| celebration_fanfare        | General celebration moment               |
| badge_awarded              | Badge / role title awarded               |
| scene_woosh                | Scene transition between rounds          |
| game_start_chime           | Game or activity begins                  |

---

## Output Schema

The final merged recipe must conform to this structure:

```json
{
  "session_id": "<uuid>",
  "activity_name": "<string>",
  "entity": "<string>",
  "tier": "<T0|T1|T2>",
  "round_count": <int>,
  "hook": {
    "voice": "<hook_line>",
    "screen": { "widget": "...", "animation": "...", "description": "..." },
    "sfx": "wonder_chime"
  },
  "transition": {
    "voice": "<transition_line>"
  },
  "rounds": [
    {
      "voice": {
        "prompt": "...",
        "correct_responses": ["..."],
        "on_correct": "...",
        "on_incorrect": "...",
        "on_silence": "...",
        "hint": "..."
      },
      "screen": { "widget": "...", "animation": "...", "description": "..." },
      "sfx": "..."
    }
  ],
  "closing": {
    "voice": "<closing_speech>",
    "tomorrow_hook": "<tomorrow_hook>",
    "screen": { "widget": "badge_award", "animation": "badge_reveal", "description": "..." },
    "sfx": "badge_awarded"
  }
}
```
