"""Paths shared by the thesis data tools."""

import json
import os
from pathlib import Path


DATA_ROOT = Path(os.environ.get("MAGISTERKA_DATA_ROOT", Path(__file__).resolve().parents[1])).resolve()
RAW = DATA_ROOT / "raw"
METADATA = DATA_ROOT / "metadata"
PROCESSED = DATA_ROOT / "processed"
EVENTS = PROCESSED / "events"
LEGACY = DATA_ROOT / "archive" / "previous_scope"


def load_study_scope():
    with (METADATA / "study_scope.json").open(encoding="utf-8") as stream:
        return json.load(stream)
