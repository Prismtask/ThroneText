"""heroine_quests/__init__.py — heroine quest modules.

Each module owns the rules and actions for one heroine's quest. Callers
(house, dungeon, city events, …) only launch the quest; per-player progress
always lives in the save data. Quest content + tuning lives in the heroine's
YAML entry (e.g. ``heroines.yaml`` → ``sylvana.quest``).
"""

__all__ = ["sylvana_mirror"]
