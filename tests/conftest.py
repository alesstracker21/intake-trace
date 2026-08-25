from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"
PROPOSALS = ROOT / "tests" / "fixtures" / "proposals"


@pytest.fixture
def sample_text():
    def loader(name: str) -> str:
        return (SAMPLES / name).read_text(encoding="utf-8")

    return loader


@pytest.fixture
def sample_json():
    def loader(name: str) -> dict:
        return json.loads((SAMPLES / name).read_text(encoding="utf-8"))

    return loader


@pytest.fixture
def proposal_json():
    def loader(number: int) -> dict:
        return json.loads((PROPOSALS / f"int-synth-{number:03d}.json").read_text(encoding="utf-8"))

    return loader
