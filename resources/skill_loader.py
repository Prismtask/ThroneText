# resources/skill_loader.py – Skill Data Loader
"""Loads and caches skill definitions from the skill_book YAML."""
import os
import yaml


def _resolve_yaml_path() -> str:
    """Return the absolute path to the skill_list.yaml file."""
    # This file lives inside resources/; the YAML lives in skill_book/ subfolder.
    return os.path.join(os.path.dirname(__file__), "skill_book", "skill_list.yaml")


def _resolve_innate_yaml_path() -> str:
    """Return the absolute path to the innate_skills.yaml file."""
    return os.path.join(os.path.dirname(__file__), "skill_book", "innate_skills.yaml")


class SkillLoader:
    """Loads and caches passive / class skill data from the project YAML."""

    _instance = None
    _skill_data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        path = _resolve_yaml_path()
        with open(path, "r", encoding="utf-8") as f:
            self._skill_data = yaml.safe_load(f)

    @property
    def passive_skills(self) -> dict:
        """Return the passive skills dictionary keyed by class name."""
        return self._skill_data["passive_skills"]

    @property
    def class_skills(self) -> dict:
        """Return the class skills dictionary keyed by class name, then skill ID."""
        return self._skill_data["class_skills"]
    
    @property
    def race_passives(self) -> dict:
        """Return the race-based passive skills dictionary."""
        return self._skill_data.get("race_passives", {})
    
    @property
    def learnable_skills(self) -> dict:
        """Return the learnable skills dictionary (offensive, defensive, support)."""
        return self._skill_data.get("learnable_skills", {})

    def get_class_skill_map(self, class_name: str) -> dict:
        """Return the skill definition dict for a given class name."""
        return self._skill_data["class_skills"].get(class_name, {})

    def get_passive_skill(self, class_name: str) -> dict | None:
        """Return the passive skill dict for a given class name, or None."""
        return self._skill_data["passive_skills"].get(class_name)
    
    def get_race_passive(self, race: str) -> dict | None:
        """Return the passive skill dict for a given race, or None."""
        return self._skill_data.get("race_passives", {}).get(race)
    
    def get_learnable_skill(self, skill_id: str) -> dict | None:
        """Return a learnable skill definition by ID."""
        learnable = self._skill_data.get("learnable_skills", {})
        for category_skills in learnable.values():
            if skill_id in category_skills:
                return category_skills[skill_id]
        return None


# Convenience module-level accessors – keeps the same API as the old inline loading.

_LOADER = SkillLoader()
PASSIVE_SKILLS = _LOADER.passive_skills
CLASS_SKILLS = _LOADER.class_skills
RACE_PASSIVES = _LOADER.race_passives
LEARNABLE_SKILLS = _LOADER.learnable_skills


def get_class_skill_map(class_name: str) -> dict:
    return _LOADER.get_class_skill_map(class_name)


def get_passive_skill(class_name: str) -> dict | None:
    return _LOADER.get_passive_skill(class_name)


def get_race_passive(race: str) -> dict | None:
    return _LOADER.get_race_passive(race)


def get_learnable_skill(skill_id: str) -> dict | None:
    return _LOADER.get_learnable_skill(skill_id)
