"""Load demo game definitions from MD files at module import time.

Scans backend/games/ for markdown files with YAML frontmatter. Files without
frontmatter (e.g. *_prod.md design docs) are silently skipped.
"""

from pathlib import Path

try:
    from .entity_registry import EntityConfig, _populate_registry
    from .game_parser import parse_game_file
    from .logger import setup_logger
    from .schemas.recipe import InstructionRecipe
except ImportError:
    from entity_registry import EntityConfig, _populate_registry
    from game_parser import parse_game_file
    from logger import setup_logger
    from schemas.recipe import InstructionRecipe

logger = setup_logger(__name__)

_GAMES_DIR = Path(__file__).parent / "games"

_entity_configs: dict[str, EntityConfig] = {}
_instruction_recipes: dict[str, InstructionRecipe] = {}


def _load_demo_games() -> None:
    """Scan games/ for MD files with YAML frontmatter, parse and register."""
    _entity_configs.clear()
    _instruction_recipes.clear()
    failures: list[str] = []

    for md_path in sorted(_GAMES_DIR.glob("*.md")):
        text = md_path.read_text()
        if not text.startswith("---"):
            continue
        try:
            entity_config, recipe = parse_game_file(md_path)
            _entity_configs[entity_config.activity_type] = entity_config
            _instruction_recipes[entity_config.activity_type] = recipe
            logger.debug(f"Loaded game: {entity_config.activity_type} from {md_path.name}")
        except Exception as exc:
            logger.exception(f"Failed to parse game file: {md_path.name}")
            failures.append(f"{md_path.name}: {exc}")

    if failures:
        failure_list = "\n".join(f"  - {failure}" for failure in failures)
        raise RuntimeError(f"Failed to load demo game definitions:\n{failure_list}")


_load_demo_games()
_populate_registry(list(_entity_configs.values()))

logger.info(f"Loaded {len(_entity_configs)} demo games from {_GAMES_DIR}")


def get_demo_entities() -> list[EntityConfig]:
    """Return all demo entity configs loaded from game MD files."""
    return list(_entity_configs.values())


def get_demo_recipe(activity_type: str) -> InstructionRecipe | None:
    """Return the instruction recipe for a demo entity, or None if not found."""
    return _instruction_recipes.get(activity_type)
