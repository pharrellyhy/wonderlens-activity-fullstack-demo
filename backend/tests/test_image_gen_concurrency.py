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
    """Two concurrent ``generate_image`` calls must not overlap.

    With a 200 ms fake API call and a single-permit semaphore, two
    ``gather``ed calls should take >= ~400 ms wall clock. Without the
    semaphore they'd both finish in ~200 ms.
    """
    start = time.perf_counter()
    results = await asyncio.gather(
        image_gen.generate_image("scene one"),
        image_gen.generate_image("scene two"),
    )
    elapsed = time.perf_counter() - start

    assert all(r == b"\x89PNGFAKE" for r in results)
    assert fake_client.call_count == 2
    assert fake_client.peak_in_flight == 1, f"semaphore allowed {fake_client.peak_in_flight} concurrent Imagen calls"
    # Allow generous slack for slow CI; the key signal is "more than one
    # call's worth of latency", not exact timing.
    assert elapsed >= 0.35, f"calls finished in {elapsed:.3f}s — semaphore not gating"


@pytest.mark.asyncio
async def test_single_call_does_not_block(fake_client: _FakeImagenClient) -> None:
    """A lone caller should not pay any semaphore wait penalty."""
    start = time.perf_counter()
    result = await image_gen.generate_image("solo scene")
    elapsed = time.perf_counter() - start

    assert result == b"\x89PNGFAKE"
    assert fake_client.peak_in_flight == 1
    # Single call should be roughly the fake sleep duration, with a
    # comfortable upper bound for scheduler jitter.
    assert elapsed < 0.5
