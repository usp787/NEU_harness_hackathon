"""Select a benchmark without mixing its database, questions or results."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# A dataset lives in one directory, one database and one results directory.
# Keeping the three in a single table is what stops a run reading milk-tea
# questions against the saas database and reporting the number as real.
_DATASETS = {
    # name        data dir                database      results subdir
    "saas":     (ROOT / "data",            "harness",    None),
    "milk_tea": (ROOT / "data" / "milk_tea", "milk_tea", "milk_tea"),
    # Five industries condensed into 25 prefixed tables, 30 questions. Lives
    # at the repo root rather than under data/ because that is where the
    # mixed-dataset branch put it. It has no curated glossary of its own, so
    # HARNESS_KNOWLEDGE=curated gives the harness arm nothing -- see
    # glossary.active_glossary(). Run it discovered.
    "mixed":    (ROOT / "mixed",           "mixed",      "mixed"),
}


def name() -> str:
    value = os.getenv("HARNESS_DATASET", "saas").strip().lower()
    if value not in _DATASETS:
        raise ValueError(f"Unknown HARNESS_DATASET: {value!r} "
                         f"(known: {', '.join(sorted(_DATASETS))})")
    return value


def data_dir() -> Path:
    return _DATASETS[name()][0]


def results_dir() -> Path:
    subdir = _DATASETS[name()][2]
    return ROOT / "eval" / "out" if subdir is None else ROOT / "eval" / "out" / subdir


def database_name() -> str:
    return _DATASETS[name()][1]
