import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"


class BackendImportCompatibilityTests(unittest.TestCase):
    def test_backend_server_imports_from_repo_root(self) -> None:
        result = subprocess.run(  # noqa: PLW1510
            [sys.executable, "-c", "import backend.server; print('ok')"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("ok", result.stdout)

    def test_server_imports_from_backend_directory(self) -> None:
        result = subprocess.run(  # noqa: PLW1510
            [sys.executable, "-c", "import server; print('ok')"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
