"""Checks for the frontend fallback data used by PhotoSelector."""

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FALLBACK_MODULE = REPO_ROOT / "frontend" / "src" / "components" / "photoSelectorFallbacks.js"


def _load_fallback_categories() -> list[dict]:
    # Node.js ESM cannot resolve extensionless imports or Vite's import.meta.env,
    # so we register a custom loader that intercepts the basePath dependency with
    # a minimal stub.
    loader_code = """
export function resolve(specifier, context, next) {
  if (specifier.endsWith('/basePath')) {
    const url = new URL(specifier + '.js', context.parentURL).href;
    return { url, shortCircuit: true };
  }
  return next(specifier, context);
}
export function load(url, context, next) {
  if (url.endsWith('/basePath.js')) {
    return {
      format: 'module',
      source: 'export function asset(p) { return p; } export default "";',
      shortCircuit: true,
    };
  }
  return next(url, context);
}
"""
    script = f"""
import {{ register }} from 'node:module';
register('data:text/javascript,' + encodeURIComponent({json.dumps(loader_code)}));
const {{ FALLBACK_CATEGORIES }} = await import({json.dumps(FALLBACK_MODULE.as_uri())});
console.log(JSON.stringify(FALLBACK_CATEGORIES));
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_fallback_categories_match_current_demo_summaries() -> None:
    categories = _load_fallback_categories()
    photos_by_id = {photo["id"]: photo for category in categories for photo in category["photos"]}

    cat_summary = photos_by_id["cat"]["summary"]
    assert cat_summary["tier"] == "T0"
    assert cat_summary["ib_key_concept"] == "Reflection"
    assert cat_summary["game_mechanic"] == "storytelling_chain"

    dinosaur_summary = photos_by_id["dinosaur"]["summary"]
    assert dinosaur_summary["tier"] == "T0"
    assert dinosaur_summary["game_mechanic"] == "voice_acting"
    assert dinosaur_summary["role_title"] == "Time Traveler"

    dandelion_previews = {item["label"] for item in photos_by_id["dandelion"]["summary"]["collectible_previews"]}
    assert "Soft petal" in dandelion_previews
    assert "Woolly caterpillar" in dandelion_previews
