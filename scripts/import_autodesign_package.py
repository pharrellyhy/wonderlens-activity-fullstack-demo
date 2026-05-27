"""Import autodesign activity packages into demo game files."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from autodesign_importer import AutodesignImportError, import_autodesign_package


def main() -> None:
    parser = argparse.ArgumentParser(description="Import autodesign demo packages into fullstack demo assets.")
    parser.add_argument("packages", nargs="+", type=Path, help="Package directories to import")
    parser.add_argument(
        "--games-dir",
        type=Path,
        default=ROOT / "backend" / "games",
        help="Destination backend games directory",
    )
    parser.add_argument(
        "--activity-assets-dir",
        type=Path,
        default=ROOT / "frontend" / "public" / "activity-assets",
        help="Destination frontend activity-assets directory",
    )
    parser.add_argument("--source-commit", required=True, help="Pinned upstream autodesign fixture commit")
    args = parser.parse_args()

    for package_dir in args.packages:
        try:
            result = import_autodesign_package(
                package_dir=package_dir,
                games_dir=args.games_dir,
                activity_assets_dir=args.activity_assets_dir,
                source_commit=args.source_commit,
            )
        except AutodesignImportError as exc:
            print(f"{package_dir}: ERROR {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

        if result.game_path:
            print(f"{package_dir}: {result.status} -> {result.game_path}")
        else:
            reasons = "; ".join(result.unsupported_reasons)
            print(f"{package_dir}: {result.status} skipped ({reasons})")


if __name__ == "__main__":
    main()
