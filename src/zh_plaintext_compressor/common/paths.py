from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
FINAL_DATA_DIR = DATA_DIR / "final"
DOCS_DIR = ROOT / "docs"
SCRIPTS_DIR = ROOT / "scripts"
SRC_DIR = ROOT / "src"
EXPERIMENTS_DIR = ROOT / "experiments"


def ensure_experiment_subdirs(run_dir: Path) -> Path:
    for subdir in ("logs", "checkpoints", "predictions", "metrics", "samples"):
        (run_dir / subdir).mkdir(parents=True, exist_ok=True)
    return run_dir

