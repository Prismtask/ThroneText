"""Bestiary ledger tests (Guild Hall discovery journal)."""

from bestiary import (
    classify_enemy,
    get_discovered_cards,
    get_enemy_card,
    record_capture,
    record_defeat,
)


def test_defeat_and_capture_are_tracked():
    player = {"dungeon_region": "forest"}

    assert record_defeat(player, "goblin_girl") is True
    assert record_defeat(player, "goblin_girl") is True
    assert record_capture(player, "goblin_girl") is True

    entry = player["bestiary"]["goblin_girl"]
    assert entry["defeated"] == 2
    assert entry["captured"] == 1
    assert entry["regions"] == ["forest"]

    cards = get_discovered_cards(player)
    assert len(cards) == 1
    assert cards[0]["name"] == "Goblin Girl"
    assert cards[0]["type"] == "Monster Girl"
    assert cards[0]["dungeons"] == ["Forest"]
    assert "capture net" in cards[0]["description"]


def test_enemy_instance_is_logged_once():
    player = {"dungeon_region": "mountain"}
    enemy = {"key": "iron_golem", "hp": 0, "captured": False}

    assert record_defeat(player, enemy) is True
    assert record_defeat(player, enemy) is False
    assert player["bestiary"]["iron_golem"]["defeated"] == 1


def test_unknown_and_internal_enemies_are_ignored():
    player = {}
    assert record_defeat(player, "training_dummy") is False
    assert record_defeat(player, "not_a_real_enemy") is False
    assert player.get("bestiary", {}) == {}


def test_enemy_card_includes_required_fields():
    card = get_enemy_card("broodmother_vileheart")

    assert card["name"] == "Broodmother Vileheart"
    assert card["race"] == "Beast"
    assert card["level"] == 24
    assert card["type"] == "Superboss"
    assert set(card["attributes"]) >= {"Strength", "Constitution", "Dexterity"}
    assert card["elemental_res"]
    assert card["description"]


def test_type_classification_priority():
    assert classify_enemy({"super_boss": True, "boss": True}) == "Superboss"
    assert classify_enemy({"boss": True, "monster_girl": True}) == "Boss"
    assert classify_enemy({"monster_girl": True}) == "Monster Girl"
    assert classify_enemy({}) == "Common"
