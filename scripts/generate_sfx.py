"""Generate synthesized WAV sound effects for the 10 WonderLens SFX cues.

Each cue gets 3 variations (v1, v2, v3) with different musical character:
different keys, rhythms, timbres, and tempos so they feel distinct.
"""

import math
import os
import struct
import wave

SAMPLE_RATE = 44100
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "sfx")


def write_wav(filename: str, samples: list[float], sample_rate: int = SAMPLE_RATE) -> None:
    path = os.path.join(OUTPUT_DIR, filename)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        data = b""
        for sample in samples:
            clamped = max(-1.0, min(1.0, sample))
            data += struct.pack("<h", int(clamped * 32767))
        wf.writeframes(data)
    print(f"  {filename} ({len(samples) / sample_rate:.2f}s)")


def sine(freq: float, duration: float, volume: float = 0.5) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    return [volume * math.sin(2 * math.pi * freq * i / SAMPLE_RATE) for i in range(n)]


def triangle(freq: float, duration: float, volume: float = 0.5) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    result = []
    for i in range(n):
        phase = (freq * i / SAMPLE_RATE) % 1.0
        val = 4 * abs(phase - 0.5) - 1
        result.append(volume * val)
    return result


def bell_tone(freq: float, duration: float, volume: float = 0.4) -> list[float]:
    """Bell-like tone using inharmonic partials."""
    partials = [1.0, 2.76, 5.4, 8.93]
    amps = [1.0, 0.5, 0.3, 0.12]
    decays = [1.5, 3.0, 5.0, 7.0]
    n = int(SAMPLE_RATE * duration)
    result = [0.0] * n
    for partial, amp, decay in zip(partials, amps, decays):
        for i in range(n):
            t = i / SAMPLE_RATE
            result[i] += volume * amp * math.exp(-decay * t) * math.sin(2 * math.pi * freq * partial * t)
    peak = max(abs(s) for s in result) or 1.0
    if peak > 1.0:
        result = [s / peak * volume for s in result]
    return result


def pluck(freq: float, duration: float, volume: float = 0.4) -> list[float]:
    """Plucked string using Karplus-Strong-like synthesis."""
    result = sine(freq, duration, volume)
    # Add harmonics with fast decay
    for h in [2, 3, 5]:
        harm = envelope_decay(sine(freq * h, duration, volume * 0.3 / h), 6.0 * h)
        for i in range(min(len(result), len(harm))):
            result[i] += harm[i]
    result = envelope_decay(result, 2.5)
    peak = max(abs(s) for s in result) or 1.0
    if peak > 1.0:
        result = [s / peak * volume for s in result]
    return result


def fade_in(samples: list[float], duration: float = 0.01) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    for i in range(min(n, len(samples))):
        samples[i] *= i / n
    return samples


def fade_out(samples: list[float], duration: float = 0.05) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    length = len(samples)
    for i in range(min(n, length)):
        samples[length - 1 - i] *= i / n
    return samples


def mix(*tracks: list[float]) -> list[float]:
    max_len = max(len(t) for t in tracks)
    result = [0.0] * max_len
    for t in tracks:
        for i, s in enumerate(t):
            result[i] += s
    peak = max(abs(s) for s in result) or 1.0
    if peak > 1.0:
        result = [s / peak for s in result]
    return result


def pad_start(samples: list[float], duration: float) -> list[float]:
    return [0.0] * int(SAMPLE_RATE * duration) + samples


def envelope_decay(samples: list[float], decay: float = 2.0) -> list[float]:
    for i in range(len(samples)):
        t = i / SAMPLE_RATE
        samples[i] *= math.exp(-decay * t)
    return samples


def noise(duration: float, volume: float = 0.3, seed: int = 42) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    result = []
    for _ in range(n):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        result.append(volume * (seed / 0x7FFFFFFF * 2 - 1))
    return result


def vibrato(samples: list[float], rate: float = 5.0, depth: float = 0.02) -> list[float]:
    n = len(samples)
    result = [0.0] * n
    for i in range(n):
        t = i / SAMPLE_RATE
        offset = depth * SAMPLE_RATE * math.sin(2 * math.pi * rate * t)
        idx = i + offset
        i0 = int(idx) % n
        i1 = (i0 + 1) % n
        frac = idx - int(idx)
        result[i] = samples[i0] * (1 - frac) + samples[i1] * frac
    return result


# ── wonder_chime ──────────────────────────────────────────────


def wonder_chime_v1() -> None:
    """Ascending C major chime with shimmer."""
    freqs = [523.25, 659.25, 783.99, 1046.50]
    parts = []
    for j, f in enumerate(freqs):
        note = fade_in(fade_out(envelope_decay(sine(f, 0.35, 0.45), 1.8), 0.08))
        shimmer = fade_out(envelope_decay(sine(f * 3, 0.25, 0.08), 3.0), 0.05)
        parts.append(pad_start(mix(note, shimmer), j * 0.12))
    write_wav("wonder_chime_v1.wav", fade_out(mix(*parts), 0.1))


def wonder_chime_v2() -> None:
    """Pentatonic bell tones — D5 F#5 A5 D6, slower spacing."""
    freqs = [587.33, 739.99, 880.0, 1174.66]
    parts = []
    for j, f in enumerate(freqs):
        note = fade_out(bell_tone(f, 0.5, 0.35), 0.12)
        parts.append(pad_start(note, j * 0.16))
    write_wav("wonder_chime_v2.wav", fade_out(mix(*parts), 0.15))


def wonder_chime_v3() -> None:
    """Gentle wind-chime style — randomish intervals, triangle wave."""
    freqs = [698.46, 880.0, 1046.50, 783.99, 1174.66]
    parts = []
    for j, f in enumerate(freqs):
        note = fade_out(envelope_decay(triangle(f, 0.25, 0.3), 2.5), 0.06)
        shimmer = fade_out(envelope_decay(sine(f * 2, 0.15, 0.06), 4.0), 0.04)
        parts.append(pad_start(mix(note, shimmer), j * 0.1))
    write_wav("wonder_chime_v3.wav", fade_out(mix(*parts), 0.1))


# ── scene_woosh ───────────────────────────────────────────────


def scene_woosh_v1() -> None:
    """Rising frequency sweep with noise."""
    duration = 0.5
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 200 + 600 * progress
        vol = math.sin(math.pi * progress) * 0.3
        samples.append(vol * math.sin(2 * math.pi * freq * t))
    swept_noise = noise(duration, 0.25)
    for i in range(len(swept_noise)):
        progress = i / len(swept_noise)
        swept_noise[i] *= math.sin(math.pi * progress)
    write_wav("scene_woosh_v1.wav", fade_in(fade_out(mix(samples, swept_noise), 0.05), 0.02))


def scene_woosh_v2() -> None:
    """Falling whoosh — high to low, faster."""
    duration = 0.4
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 800 - 500 * progress
        vol = math.sin(math.pi * progress) * 0.3
        samples.append(vol * math.sin(2 * math.pi * freq * t))
    n_buf = noise(duration, 0.3, seed=77)
    for i in range(len(n_buf)):
        progress = i / len(n_buf)
        n_buf[i] *= math.sin(math.pi * progress)
    write_wav("scene_woosh_v2.wav", fade_in(fade_out(mix(samples, n_buf), 0.04), 0.01))


def scene_woosh_v3() -> None:
    """Double whoosh — up then down, gentle."""
    duration = 0.6
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 300 + 400 * math.sin(math.pi * progress)
        vol = math.sin(math.pi * progress) * 0.25
        samples.append(vol * math.sin(2 * math.pi * freq * t))
    n_buf = noise(duration, 0.2, seed=99)
    for i in range(len(n_buf)):
        progress = i / len(n_buf)
        n_buf[i] *= math.sin(math.pi * progress) * 0.8
    write_wav("scene_woosh_v3.wav", fade_in(fade_out(mix(samples, n_buf), 0.06), 0.02))


# ── celebration_fanfare ───────────────────────────────────────


def celebration_fanfare_v1() -> None:
    """C major chord then high C."""
    chord_c = fade_out(envelope_decay(sine(523.25, 0.4, 0.3), 1.5), 0.1)
    chord_e = fade_out(envelope_decay(sine(659.25, 0.4, 0.25), 1.5), 0.1)
    chord_g = fade_out(envelope_decay(sine(783.99, 0.4, 0.25), 1.5), 0.1)
    high_c = fade_out(envelope_decay(sine(1046.50, 0.5, 0.4), 1.2), 0.15)
    chord = mix(chord_c, chord_e, chord_g)
    write_wav("celebration_fanfare_v1.wav", fade_out(mix(chord, pad_start(high_c, 0.3)), 0.1))


def celebration_fanfare_v2() -> None:
    """G major fanfare — brighter, trumpet-like with harmonics."""
    g4 = fade_out(envelope_decay(sine(392.0, 0.25, 0.25), 1.5), 0.06)
    g4h = fade_out(envelope_decay(sine(784.0, 0.2, 0.1), 2.5), 0.05)
    b4 = fade_out(envelope_decay(sine(493.88, 0.25, 0.25), 1.5), 0.06)
    d5 = fade_out(envelope_decay(sine(587.33, 0.25, 0.25), 1.5), 0.06)
    g5 = fade_out(envelope_decay(sine(783.99, 0.5, 0.35), 1.0), 0.12)
    g5h = fade_out(envelope_decay(sine(1568.0, 0.3, 0.08), 2.0), 0.08)
    write_wav(
        "celebration_fanfare_v2.wav",
        fade_out(
            mix(
                mix(g4, g4h),
                pad_start(b4, 0.15),
                pad_start(d5, 0.3),
                pad_start(mix(g5, g5h), 0.45),
            ),
            0.12,
        ),
    )


def celebration_fanfare_v3() -> None:
    """Eb major fanfare — warm, slower, with vibrato on final note."""
    eb4 = fade_out(envelope_decay(sine(311.13, 0.3, 0.3), 1.2), 0.08)
    g4 = fade_out(envelope_decay(sine(392.0, 0.3, 0.28), 1.2), 0.08)
    bb4 = fade_out(envelope_decay(sine(466.16, 0.3, 0.28), 1.2), 0.08)
    eb5 = vibrato(fade_out(envelope_decay(sine(622.25, 0.6, 0.4), 0.8), 0.15), rate=4.5, depth=0.015)
    write_wav(
        "celebration_fanfare_v3.wav",
        fade_out(
            mix(
                eb4,
                pad_start(g4, 0.18),
                pad_start(bb4, 0.36),
                pad_start(eb5, 0.5),
            ),
            0.12,
        ),
    )


# ── photo_shutter_click ──────────────────────────────────────


def photo_shutter_click_v1() -> None:
    """Mechanical click with resonant tone."""
    click = noise(0.03, 0.7)
    click = fade_in(fade_out(click, 0.015), 0.002)
    tone = fade_out(envelope_decay(sine(1200, 0.05, 0.15), 20.0), 0.02)
    write_wav("photo_shutter_click_v1.wav", mix(click, pad_start(tone, 0.02)))


def photo_shutter_click_v2() -> None:
    """Softer digital shutter — two quick clicks."""
    click1 = fade_in(fade_out(noise(0.02, 0.5, seed=55), 0.01), 0.001)
    click2 = fade_in(fade_out(noise(0.015, 0.4, seed=88), 0.008), 0.001)
    tone = fade_out(envelope_decay(sine(2400, 0.03, 0.08), 25.0), 0.01)
    write_wav("photo_shutter_click_v2.wav", mix(click1, pad_start(click2, 0.04), pad_start(tone, 0.03)))


def photo_shutter_click_v3() -> None:
    """Film camera style — longer mechanical sound with winding."""
    click = fade_in(fade_out(noise(0.04, 0.6, seed=31), 0.02), 0.003)
    wind = fade_out(noise(0.08, 0.15, seed=67), 0.03)
    for i in range(len(wind)):
        t = i / SAMPLE_RATE
        wind[i] *= 0.5 + 0.5 * math.sin(2 * math.pi * 60 * t)
    tone = fade_out(envelope_decay(sine(900, 0.06, 0.1), 18.0), 0.02)
    write_wav("photo_shutter_click_v3.wav", mix(click, pad_start(tone, 0.02), pad_start(wind, 0.05)))


# ── slot_fill_chime ───────────────────────────────────────────


def slot_fill_chime_v1() -> None:
    """Two-note ascending ding (A5 → E6)."""
    note1 = fade_out(envelope_decay(sine(880, 0.15, 0.4), 3.0), 0.05)
    note2 = fade_out(envelope_decay(sine(1318.5, 0.2, 0.4), 2.5), 0.08)
    write_wav("slot_fill_chime_v1.wav", mix(note1, pad_start(note2, 0.1)))


def slot_fill_chime_v2() -> None:
    """Bell-tone ding (C6 → G6) — rounder sound."""
    note1 = fade_out(bell_tone(1046.50, 0.2, 0.35), 0.06)
    note2 = fade_out(bell_tone(1567.98, 0.25, 0.35), 0.08)
    write_wav("slot_fill_chime_v2.wav", mix(note1, pad_start(note2, 0.12)))


def slot_fill_chime_v3() -> None:
    """Plucked string pop (D5 → A5) — playful."""
    note1 = fade_out(pluck(587.33, 0.15, 0.4), 0.04)
    note2 = fade_out(pluck(880.0, 0.2, 0.4), 0.06)
    write_wav("slot_fill_chime_v3.wav", mix(note1, pad_start(note2, 0.08)))


# ── mission_accepted ─────────────────────────────────────────


def mission_accepted_v1() -> None:
    """Two-note ascending (A4 → E5) with harmonics."""
    note1 = fade_out(envelope_decay(sine(440, 0.2, 0.35), 2.0), 0.05)
    harm1 = fade_out(envelope_decay(sine(880, 0.15, 0.1), 3.0), 0.05)
    note2 = fade_out(envelope_decay(sine(660, 0.3, 0.4), 1.5), 0.1)
    harm2 = fade_out(envelope_decay(sine(1320, 0.2, 0.1), 3.0), 0.08)
    write_wav("mission_accepted_v1.wav", mix(mix(note1, harm1), pad_start(mix(note2, harm2), 0.18)))


def mission_accepted_v2() -> None:
    """Three-note motif (C4 → E4 → G4) — march-like."""
    c4 = fade_out(envelope_decay(sine(261.63, 0.15, 0.3), 2.5), 0.04)
    e4 = fade_out(envelope_decay(sine(329.63, 0.15, 0.3), 2.5), 0.04)
    g4 = fade_out(envelope_decay(sine(392.0, 0.3, 0.4), 1.5), 0.1)
    g4h = fade_out(envelope_decay(sine(784.0, 0.2, 0.1), 3.0), 0.06)
    write_wav("mission_accepted_v2.wav", mix(c4, pad_start(e4, 0.12), pad_start(mix(g4, g4h), 0.24)))


def mission_accepted_v3() -> None:
    """Bell confirmation (F5 → C6) — gentle authority."""
    note1 = fade_out(bell_tone(698.46, 0.25, 0.3), 0.08)
    note2 = fade_out(bell_tone(1046.50, 0.35, 0.35), 0.1)
    write_wav("mission_accepted_v3.wav", mix(note1, pad_start(note2, 0.2)))


# ── mission_complete_fanfare ─────────────────────────────────


def mission_complete_fanfare_v1() -> None:
    """C major arpeggio into chord."""
    notes = [(523.25, 0.15, 0.3), (659.25, 0.15, 0.3), (783.99, 0.15, 0.3), (1046.50, 0.4, 0.4)]
    parts = []
    offset = 0.0
    for freq, dur, vol in notes:
        note = fade_out(envelope_decay(sine(freq, dur, vol), 1.0), 0.05)
        parts.append(pad_start(note, offset))
        offset += 0.12
    final = mix(
        fade_out(envelope_decay(sine(523.25, 0.4, 0.2), 1.0), 0.1),
        fade_out(envelope_decay(sine(659.25, 0.4, 0.2), 1.0), 0.1),
        fade_out(envelope_decay(sine(783.99, 0.4, 0.2), 1.0), 0.1),
        fade_out(envelope_decay(sine(1046.50, 0.4, 0.25), 1.0), 0.1),
    )
    parts.append(pad_start(final, offset))
    write_wav("mission_complete_fanfare_v1.wav", fade_out(mix(*parts), 0.15))


def mission_complete_fanfare_v2() -> None:
    """D major triumphant — faster arpeggio, bell-tone finale."""
    notes = [(587.33, 0.1, 0.3), (739.99, 0.1, 0.3), (880.0, 0.1, 0.3), (1174.66, 0.12, 0.35)]
    parts = []
    offset = 0.0
    for freq, dur, vol in notes:
        note = fade_out(envelope_decay(sine(freq, dur, vol), 1.5), 0.03)
        parts.append(pad_start(note, offset))
        offset += 0.08
    finale = fade_out(bell_tone(1174.66, 0.6, 0.4), 0.15)
    parts.append(pad_start(finale, offset))
    write_wav("mission_complete_fanfare_v2.wav", fade_out(mix(*parts), 0.15))


def mission_complete_fanfare_v3() -> None:
    """F major warm completion — plucked arpeggio, sustained chord."""
    f4 = fade_out(pluck(349.23, 0.15, 0.3), 0.04)
    a4 = fade_out(pluck(440.0, 0.15, 0.3), 0.04)
    c5 = fade_out(pluck(523.25, 0.15, 0.3), 0.04)
    f5 = fade_out(pluck(698.46, 0.15, 0.35), 0.04)
    chord = mix(
        fade_out(envelope_decay(sine(349.23, 0.5, 0.2), 0.8), 0.12),
        fade_out(envelope_decay(sine(440.0, 0.5, 0.2), 0.8), 0.12),
        fade_out(envelope_decay(sine(523.25, 0.5, 0.2), 0.8), 0.12),
        fade_out(envelope_decay(sine(698.46, 0.5, 0.25), 0.8), 0.12),
    )
    write_wav(
        "mission_complete_fanfare_v3.wav",
        fade_out(
            mix(
                f4,
                pad_start(a4, 0.1),
                pad_start(c5, 0.2),
                pad_start(f5, 0.3),
                pad_start(chord, 0.4),
            ),
            0.15,
        ),
    )


# ── badge_awarded ─────────────────────────────────────────────


def badge_awarded_v1() -> None:
    """Shimmering ascending sparkle (C major)."""
    base = [523.25, 659.25, 783.99, 1046.50, 1318.5]
    parts = []
    for j, f in enumerate(base):
        note = fade_out(envelope_decay(sine(f, 0.2, 0.3), 2.5), 0.06)
        sparkle = fade_out(envelope_decay(sine(f * 2.5, 0.12, 0.08), 5.0), 0.03)
        parts.append(pad_start(mix(note, sparkle), j * 0.08))
    write_wav("badge_awarded_v1.wav", fade_out(mix(*parts), 0.1))


def badge_awarded_v2() -> None:
    """Bell cascade (Eb major) — richer, deeper."""
    base = [311.13, 392.0, 466.16, 622.25, 783.99]
    parts = []
    for j, f in enumerate(base):
        note = fade_out(bell_tone(f, 0.3, 0.3), 0.08)
        parts.append(pad_start(note, j * 0.1))
    # Add final shimmer
    shimmer = fade_out(envelope_decay(sine(1567.98, 0.3, 0.1), 3.0), 0.08)
    parts.append(pad_start(shimmer, 0.45))
    write_wav("badge_awarded_v2.wav", fade_out(mix(*parts), 0.12))


def badge_awarded_v3() -> None:
    """Sparkle burst — quick ascending then chord bloom."""
    burst = [880.0, 1108.73, 1318.5, 1760.0]
    parts = []
    for j, f in enumerate(burst):
        note = fade_out(envelope_decay(sine(f, 0.1, 0.3), 4.0), 0.03)
        sparkle = fade_out(envelope_decay(sine(f * 3, 0.06, 0.06), 8.0), 0.02)
        parts.append(pad_start(mix(note, sparkle), j * 0.05))
    # Bloom chord
    bloom = mix(
        fade_out(envelope_decay(sine(523.25, 0.5, 0.2), 1.0), 0.12),
        fade_out(envelope_decay(sine(659.25, 0.5, 0.2), 1.0), 0.12),
        fade_out(envelope_decay(sine(783.99, 0.5, 0.15), 1.0), 0.12),
        fade_out(envelope_decay(sine(1046.50, 0.5, 0.15), 1.0), 0.12),
    )
    parts.append(pad_start(bloom, 0.2))
    write_wav("badge_awarded_v3.wav", fade_out(mix(*parts), 0.12))


# ── excitement_rising ─────────────────────────────────────────


def excitement_rising_v1() -> None:
    """Rising pitch sweep with pulsing."""
    duration = 0.8
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 300 + 900 * (progress**1.5)
        vol = 0.15 + 0.3 * progress
        pulse = 0.7 + 0.3 * math.sin(2 * math.pi * 8 * t)
        samples.append(vol * pulse * math.sin(2 * math.pi * freq * t))
    write_wav("excitement_rising_v1.wav", fade_in(fade_out(samples, 0.05), 0.02))


def excitement_rising_v2() -> None:
    """Staircase rise — discrete frequency steps with tremolo."""
    steps = [330, 440, 554, 660, 880, 1046]
    step_dur = 0.12
    parts = []
    for j, freq in enumerate(steps):
        n = int(SAMPLE_RATE * step_dur)
        step_samples = []
        for i in range(n):
            t = i / SAMPLE_RATE
            vol = (0.2 + 0.05 * j) * (0.7 + 0.3 * math.sin(2 * math.pi * 12 * t))
            step_samples.append(vol * math.sin(2 * math.pi * freq * t))
        step_samples = fade_in(fade_out(step_samples, 0.02), 0.005)
        parts.append(pad_start(step_samples, j * step_dur * 0.9))
    write_wav("excitement_rising_v2.wav", fade_out(mix(*parts), 0.05))


def excitement_rising_v3() -> None:
    """Wobble rise — triangle wave with increasing vibrato rate."""
    duration = 0.7
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        base_freq = 250 + 800 * progress
        vib_rate = 4 + 12 * progress
        freq = base_freq + 30 * math.sin(2 * math.pi * vib_rate * t)
        vol = 0.15 + 0.25 * progress
        phase = (freq * t) % 1.0
        val = 4 * abs(phase - 0.5) - 1
        samples.append(vol * val)
    write_wav("excitement_rising_v3.wav", fade_in(fade_out(samples, 0.05), 0.02))


# ── game_start_chime ──────────────────────────────────────────


def game_start_chime_v1() -> None:
    """Three quick notes (G4 C5 E5) then chord."""
    g4 = fade_out(envelope_decay(sine(392.0, 0.12, 0.35), 4.0), 0.03)
    c5 = fade_out(envelope_decay(sine(523.25, 0.12, 0.35), 4.0), 0.03)
    e5 = fade_out(envelope_decay(sine(659.25, 0.12, 0.35), 4.0), 0.03)
    chord = mix(
        fade_out(envelope_decay(sine(523.25, 0.35, 0.25), 1.5), 0.1),
        fade_out(envelope_decay(sine(659.25, 0.35, 0.25), 1.5), 0.1),
        fade_out(envelope_decay(sine(783.99, 0.35, 0.25), 1.5), 0.1),
    )
    write_wav(
        "game_start_chime_v1.wav",
        fade_out(
            mix(
                g4,
                pad_start(c5, 0.1),
                pad_start(e5, 0.2),
                pad_start(chord, 0.3),
            ),
            0.1,
        ),
    )


def game_start_chime_v2() -> None:
    """Bouncy start — plucked notes (E4 A4 C#5 E5)."""
    e4 = fade_out(pluck(329.63, 0.12, 0.35), 0.03)
    a4 = fade_out(pluck(440.0, 0.12, 0.35), 0.03)
    cs5 = fade_out(pluck(554.37, 0.12, 0.35), 0.03)
    e5 = fade_out(pluck(659.25, 0.3, 0.4), 0.08)
    write_wav(
        "game_start_chime_v2.wav",
        fade_out(
            mix(
                e4,
                pad_start(a4, 0.08),
                pad_start(cs5, 0.16),
                pad_start(e5, 0.24),
            ),
            0.1,
        ),
    )


def game_start_chime_v3() -> None:
    """Bell countdown — three bell tones then sparkle."""
    b1 = fade_out(bell_tone(523.25, 0.2, 0.3), 0.05)
    b2 = fade_out(bell_tone(659.25, 0.2, 0.3), 0.05)
    b3 = fade_out(bell_tone(783.99, 0.2, 0.35), 0.05)
    sparkle = mix(
        fade_out(envelope_decay(sine(1046.50, 0.3, 0.2), 2.0), 0.08),
        fade_out(envelope_decay(sine(1318.5, 0.25, 0.15), 2.5), 0.07),
        fade_out(envelope_decay(sine(1567.98, 0.2, 0.1), 3.0), 0.06),
    )
    write_wav(
        "game_start_chime_v3.wav",
        fade_out(
            mix(
                b1,
                pad_start(b2, 0.15),
                pad_start(b3, 0.3),
                pad_start(sparkle, 0.42),
            ),
            0.1,
        ),
    )


# ── main ──────────────────────────────────────────────────────

ALL_GENERATORS = [
    wonder_chime_v1,
    wonder_chime_v2,
    wonder_chime_v3,
    scene_woosh_v1,
    scene_woosh_v2,
    scene_woosh_v3,
    celebration_fanfare_v1,
    celebration_fanfare_v2,
    celebration_fanfare_v3,
    photo_shutter_click_v1,
    photo_shutter_click_v2,
    photo_shutter_click_v3,
    slot_fill_chime_v1,
    slot_fill_chime_v2,
    slot_fill_chime_v3,
    mission_accepted_v1,
    mission_accepted_v2,
    mission_accepted_v3,
    mission_complete_fanfare_v1,
    mission_complete_fanfare_v2,
    mission_complete_fanfare_v3,
    badge_awarded_v1,
    badge_awarded_v2,
    badge_awarded_v3,
    excitement_rising_v1,
    excitement_rising_v2,
    excitement_rising_v3,
    game_start_chime_v1,
    game_start_chime_v2,
    game_start_chime_v3,
]


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Generating 30 SFX files (3 variations x 10 cues)...")
    for gen in ALL_GENERATORS:
        gen()
    print("Done!")


if __name__ == "__main__":
    main()
