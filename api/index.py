from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
RUNTIME_DATA_DIR = Path("/tmp/weekendgo-data")


def _prepare_runtime_database(name: str) -> str:
    RUNTIME_DATA_DIR.mkdir(parents=True, exist_ok=True)
    source = BACKEND_DIR / "data" / name
    target = RUNTIME_DATA_DIR / name
    if source.exists() and not target.exists():
        shutil.copyfile(source, target)
    return str(target)


os.environ.setdefault("FLASK_DEBUG", "false")
os.environ.setdefault("WEEKENDGO_DATABASE_PATH", _prepare_runtime_database("meituan_v2.db"))
os.environ.setdefault("WEEKENDGO_MEMORY_DATABASE_PATH", _prepare_runtime_database("memories.db"))

sys.path.insert(0, str(BACKEND_DIR))

from app import create_app  # noqa: E402


app = create_app()
