import os
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"
TEST_DIR = PROJECT_DIR / "test"

sys.path.insert(0, str(SRC_DIR))


def load_env_file(env_path: Path, *, override: bool = False) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if override:
            os.environ[key] = value
        else:
            os.environ.setdefault(key, value)


load_env_file(SRC_DIR / ".env")
load_env_file(TEST_DIR / ".env", override=True)
