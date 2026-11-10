import importlib
import os

import pytest

from combat.stats import player_str_mod
import save_load


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
