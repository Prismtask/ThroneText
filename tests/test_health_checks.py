import importlib
import os

import pytest

from character import allocate_points
from combat.stats import player_str_mod
from resources.races_classes import ATTRIBUTES
import save_load


def test_allocate_points_preserves_partial_allocation(monkeypatch):
    answers = iter(["2"] + [""] * (len(ATTRIBUTES) * 2) + ["n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    base_attrs = {attr: 0 for attr in ATTRIBUTES}
    result = allocate_points(base_attrs)

    assert result["Strength"] == 2


def test_player_mod_helpers_use_effective_values():
    player = {
        "attributes": {"Strength": 5},
        "active_buffs": [{"type": "blessing", "stat": "Strength", "value": 3}],
    }

    assert player_str_mod(player) == 8


def test_save_directory_uses_module_relative_path(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    reloaded = importlib.reload(save_load)

    filename = reloaded.get_filename(7)
    expected_dir = os.path.join(os.path.dirname(reloaded.__file__), "savefile")

    assert os.path.dirname(filename) == expected_dir
