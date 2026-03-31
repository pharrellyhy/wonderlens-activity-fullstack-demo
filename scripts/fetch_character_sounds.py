"""Fetch, trim, and convert character/environment sounds from Freesound API.

Downloads HQ preview MP3s, trims to target duration, converts to mono WAV,
and saves as {cue_id}_v{1,2,3}.wav in the correct activity directory.

Usage:
    python scripts/fetch_character_sounds.py
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

API_TOKEN = "wQrOpgTOzBLUrd4lUs8m5CaM5lNGvM7DPJEYpx49"
BASE_URL = "https://freesound.org/apiv2"
OUTPUT_BASE = Path(__file__).parent.parent / "frontend" / "public" / "sfx" / "character"

# Target: 3 variations per cue, each trimmed to this max duration
MAX_DURATION = 1.5  # seconds
VARIATIONS = 3
SAMPLE_RATE = 22050

# Search queries per cue ID — tuned for child-friendly, fun, short sounds
# Format: (cue_id, search_query, max_duration_filter, min_results_needed)
SOUND_MAP: dict[str, list[tuple[str, str, float]]] = {
    "mood_changer_dog": [
        ("dog_bark_happy", "dog bark happy excited small", 4.0),
        ("dog_bark_curious", "dog bark single short", 4.0),
        ("dog_pant_content", "dog panting happy", 8.0),
        ("dog_whimper_sad", "dog whimper whine sad", 6.0),
        ("dog_yip_playful", "dog yip yelp small playful", 4.0),
        ("dog_growl_dramatic", "dog growl playful", 5.0),
        ("dog_sniff_curious", "dog sniff sniffing", 5.0),
        ("dog_howl_dramatic", "dog howl howling", 8.0),
        ("dog_tail_thump", "dog tail wag thump", 8.0),
        ("dog_shake_excitement", "dog shake body", 6.0),
        ("env_birds_chirp", "bird chirp single short", 4.0),
        ("env_breeze_gentle", "gentle breeze wind soft", 10.0),
        ("env_leaves_rustle", "leaves rustling wind", 8.0),
        ("env_sunshine_warm", "warm ambient tone gentle chime", 6.0),
        ("env_rain_soft", "rain gentle soft light", 10.0),
        ("env_thunder_distant", "thunder distant rumble soft", 10.0),
    ],
    "dream_whisperer_cat": [
        ("cat_purr_soft", "cat purring soft", 10.0),
        ("cat_meow_curious", "cat meow single short", 4.0),
        ("cat_meow_happy", "cat meow cute kitten", 4.0),
        ("cat_hiss_surprised", "cat hiss short", 4.0),
        ("cat_chirp_excited", "cat chirp trill", 5.0),
        ("cat_yawn_sleepy", "cat yawn", 5.0),
        ("cat_paw_knead", "cat purr knead", 8.0),
        ("env_fireplace_crackle", "fireplace crackling fire", 10.0),
        ("env_rain_window", "rain window indoor", 10.0),
        ("env_clock_tick", "clock ticking wall", 8.0),
        ("env_blanket_rustle", "fabric rustle cloth", 5.0),
        ("env_wind_chime", "wind chime gentle", 8.0),
    ],
    "time_machine_dinosaur": [
        ("dino_roar_friendly", "dinosaur roar creature monster", 6.0),
        ("dino_stomp_heavy", "heavy footstep stomp giant", 5.0),
        ("dino_growl_playful", "creature growl monster short", 5.0),
        ("dino_chirp_small", "bird chirp creature small animal", 4.0),
        ("dino_rumble_deep", "rumble deep bass low", 6.0),
        ("dino_chomp_munching", "chomp bite crunch eating", 4.0),
        ("env_jungle_ambience", "jungle tropical birds insects", 10.0),
        ("env_volcano_rumble", "volcano rumble lava", 10.0),
        ("env_waterfall_distant", "waterfall distant water", 10.0),
        ("env_prehistoric_wind", "wind howling eerie", 10.0),
        ("env_time_whoosh", "whoosh magic time travel", 5.0),
    ],
    "polka_dot_patrol": [
        ("nature_birds_chirp", "bird chirp singing nature", 6.0),
        ("nature_breeze_gentle", "breeze gentle wind outdoor", 10.0),
        ("nature_leaves_rustle", "leaves rustling tree", 8.0),
        ("nature_cricket_chirp", "cricket chirping insect", 8.0),
        ("discovery_sparkle", "sparkle magic chime twinkle", 5.0),
        ("discovery_gasp", "gasp wow surprise child", 4.0),
    ],
    "fluffy_expedition_dandelion": [
        ("nature_wind_soft", "wind soft gentle breeze", 10.0),
        ("nature_dandelion_puff", "blow puff air soft whoosh", 5.0),
        ("nature_grass_rustle", "grass rustling field", 8.0),
        ("nature_bees_buzz", "bee buzzing gentle", 8.0),
        ("discovery_sparkle", "sparkle magic twinkle chime", 5.0),
        ("discovery_oooh", "wow oooh surprise amazed", 4.0),
    ],
}


def search_sounds(query: str, max_duration: float, page_size: int = 10) -> list[dict]:
    """Search Freesound API for matching sounds."""
    params = urllib.parse.urlencode({
        "query": query,
        "filter": f"duration:[0.1 TO {max_duration}]",
        "sort": "rating_desc",
        "page_size": str(page_size),
        "fields": "id,name,duration,previews,tags,avg_rating,num_ratings",
        "token": API_TOKEN,
    })
    url = f"{BASE_URL}/search/text/?{params}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return data.get("results", [])
    except Exception as e:
        print(f"    Search failed: {e}")
        return []


def download_preview(sound: dict, output_path: Path) -> bool:
    """Download the HQ MP3 preview of a sound."""
    preview_url = sound.get("previews", {}).get("preview-hq-mp3")
    if not preview_url:
        return False
    try:
        urllib.request.urlretrieve(preview_url, str(output_path))
        return True
    except Exception as e:
        print(f"    Download failed: {e}")
        return False


def convert_and_trim(input_mp3: Path, output_wav: Path, max_duration: float = MAX_DURATION) -> bool:
    """Convert MP3 to mono WAV, trim to max_duration, normalize volume."""
    try:
        cmd = [
            "ffmpeg", "-y", "-i", str(input_mp3),
            "-ac", "1",                         # mono
            "-ar", str(SAMPLE_RATE),            # sample rate
            "-t", str(max_duration),            # trim duration
            "-filter:a", "loudnorm=I=-16:TP=-1.5:LRA=11",  # normalize loudness
            "-sample_fmt", "s16",               # 16-bit
            str(output_wav),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"    Convert failed: {e}")
        return False


def process_cue(activity: str, cue_id: str, query: str, max_dur: float) -> int:
    """Search, download, and process variations for one cue."""
    activity_dir = OUTPUT_BASE / activity
    activity_dir.mkdir(parents=True, exist_ok=True)

    # Check if already processed (all 3 variations exist and are not placeholder sine tones)
    existing = [activity_dir / f"{cue_id}_v{v}.wav" for v in range(1, VARIATIONS + 1)]
    if all(f.exists() and f.stat().st_size > 5000 for f in existing):
        print(f"  [{cue_id}] Already has real assets, skipping")
        return 3

    results = search_sounds(query, max_dur, page_size=VARIATIONS * 3)
    if not results:
        print(f"  [{cue_id}] No results found for '{query}'")
        return 0

    count = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, sound in enumerate(results):
            if count >= VARIATIONS:
                break

            tmp_mp3 = Path(tmpdir) / f"{cue_id}_{i}.mp3"
            if not download_preview(sound, tmp_mp3):
                continue

            variant = count + 1
            out_wav = activity_dir / f"{cue_id}_v{variant}.wav"

            # Vary the trim start slightly for each variation
            trim_offset = i * 0.15  # stagger start by 150ms per variant
            actual_dur = min(MAX_DURATION, sound["duration"] - trim_offset)
            if actual_dur < 0.2:
                trim_offset = 0
                actual_dur = min(MAX_DURATION, sound["duration"])

            # Use ffmpeg with start offset for variation
            try:
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{trim_offset:.2f}",
                    "-i", str(tmp_mp3),
                    "-ac", "1",
                    "-ar", str(SAMPLE_RATE),
                    "-t", f"{actual_dur:.2f}",
                    "-filter:a", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-sample_fmt", "s16",
                    str(out_wav),
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and out_wav.exists() and out_wav.stat().st_size > 100:
                    count += 1
                    print(f"    v{variant}: {sound['name'][:50]} ({sound['duration']:.1f}s) -> {out_wav.name}")
            except Exception as e:
                print(f"    Convert error: {e}")

    # If we didn't get enough from different sounds, duplicate with pitch shift
    while count < VARIATIONS:
        count += 1
        src = activity_dir / f"{cue_id}_v1.wav"
        dst = activity_dir / f"{cue_id}_v{count}.wav"
        if src.exists() and not dst.exists():
            pitch_shift = 1.0 + (count - 1) * 0.08  # slight pitch variation
            try:
                cmd = [
                    "ffmpeg", "-y", "-i", str(src),
                    "-filter:a", f"asetrate={SAMPLE_RATE}*{pitch_shift},aresample={SAMPLE_RATE}",
                    str(dst),
                ]
                subprocess.run(cmd, capture_output=True, timeout=15)
                print(f"    v{count}: pitch-shifted from v1")
            except Exception:
                pass

    return count


def main() -> None:
    total = 0
    failed = []

    for activity, cues in SOUND_MAP.items():
        print(f"\n{'='*60}")
        print(f"Activity: {activity}")
        print(f"{'='*60}")

        for cue_id, query, max_dur in cues:
            print(f"\n  [{cue_id}] Searching: '{query}'")
            count = process_cue(activity, cue_id, query, max_dur)
            if count > 0:
                total += count
            else:
                failed.append(f"{activity}/{cue_id}")

            # Rate limit: Freesound allows ~2 req/sec
            time.sleep(0.6)

    print(f"\n{'='*60}")
    print(f"Done! Processed {total} sound files.")
    if failed:
        print(f"Failed ({len(failed)}): {', '.join(failed)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
