"""resources/family_scenes.py — loader for resources/family_scenes.yaml.

All Shared Night, child-bond, and birth text now lives in
``resources/family_scenes.yaml`` so it can be tuned without touching Python.
This module keeps the stable constants/helper API used by the UI and tests.
"""
import os

import yaml

_YAML_PATH = os.path.join(os.path.dirname(__file__), "family_scenes.yaml")
with open(_YAML_PATH, encoding="utf-8") as _handle:
    _DATA = yaml.safe_load(_handle) or {}

ACTION_PROMPTS = _DATA.get("action_prompts", {}) or {}
ACTION_LINES = _DATA.get("action_lines", {}) or {}
MOOD_LINES = _DATA.get("mood_lines", {}) or {}
MATCH_LINES = _DATA.get("match_lines", []) or []
COMPATIBLE_LINES = _DATA.get("compatible_lines", []) or []
MISS_LINES = _DATA.get("miss_lines", []) or []
RANDOM_BEATS = _DATA.get("random_beats", []) or []
ENDING_LINES = _DATA.get("ending_lines", {}) or {}
ENDING_TITLES = _DATA.get("ending_titles", {}) or {}
WRITTEN_ACTION_LINES = _DATA.get("written_action_lines", {}) or {}
WRITTEN_ENDING_LINES = _DATA.get("written_ending_lines", {}) or {}
WRITTEN_GIRL_ACTION_LINES = _DATA.get("written_girl_action_lines", {}) or {}
WRITTEN_GIRL_ENDING_LINES = _DATA.get("written_girl_ending_lines", {}) or {}
GIRL_ACTION_LINES = _DATA.get("girl_action_lines", {}) or {}
GIRL_MOOD_LINES = _DATA.get("girl_mood_lines", {}) or {}
GIRL_ENDING_LINES = _DATA.get("girl_ending_lines", {}) or {}
CHILD_TALK_LOW = _DATA.get("child_talk_low", []) or []
CHILD_TALK_MID = _DATA.get("child_talk_mid", []) or []
CHILD_TALK_HIGH = _DATA.get("child_talk_high", []) or []
CHILD_GIFT_LOVE = _DATA.get("child_gift_love", []) or []
CHILD_GIFT_HATE = _DATA.get("child_gift_hate", []) or []
CHILD_RACE_TALK = _DATA.get("child_race_talk", {}) or {}
CHILD_RACE_GIFT = _DATA.get("child_race_gift", {}) or {}
GIRL_CHILD_TALK = _DATA.get("girl_child_talk", {}) or {}
GIRL_CHILD_GIFT = _DATA.get("girl_child_gift", {}) or {}
BIRTH_LINES = _DATA.get("birth_lines", []) or []
BIRTH_NAME_PROMPT = _DATA.get("birth_name_prompt", "What will you name the child?")
STAGE_LABELS = _DATA.get("stage_labels", {}) or {}


def action_lines_for(girl_key, action):
    override = (GIRL_ACTION_LINES.get(girl_key) or {}).get(action)
    generic = ACTION_LINES.get(action, ACTION_LINES.get("tender", []))
    return list(override) + list(generic) if override else generic


def mood_line_for(girl_key, tone):
    override = (GIRL_MOOD_LINES.get(girl_key) or {}).get(tone)
    return override or MOOD_LINES.get(tone, MOOD_LINES.get("tender", []))


def ending_lines_for(girl_key, ending):
    override = (GIRL_ENDING_LINES.get(girl_key) or {}).get(ending)
    return override or ENDING_LINES.get(ending, ENDING_LINES.get("rest", []))


def written_action_lines_for(girl_key, action):
    override = (WRITTEN_GIRL_ACTION_LINES.get(girl_key) or {}).get(action)
    return override or WRITTEN_ACTION_LINES.get(
        action, WRITTEN_ACTION_LINES.get("tender", []))


def written_ending_lines_for(girl_key, ending):
    override = (WRITTEN_GIRL_ENDING_LINES.get(girl_key) or {}).get(ending)
    return override or WRITTEN_ENDING_LINES.get(
        ending, WRITTEN_ENDING_LINES.get("rest", []))


def child_talk_lines(tier, race=None, mother_key=None):
    override = (GIRL_CHILD_TALK.get(mother_key) or {}).get(tier)
    if override:
        return list(override)
    race_pool = (CHILD_RACE_TALK.get(race) or {}).get(tier)
    if race_pool:
        return list(race_pool)
    return {
        "low": CHILD_TALK_LOW,
        "mid": CHILD_TALK_MID,
        "high": CHILD_TALK_HIGH,
        "max": CHILD_TALK_HIGH,
    }.get(tier, CHILD_TALK_LOW)


def child_gift_lines(positive, race=None, mother_key=None):
    key = "love" if positive else "hate"
    override = (GIRL_CHILD_GIFT.get(mother_key) or {}).get(key)
    if override:
        return list(override)
    race_pool = (CHILD_RACE_GIFT.get(race) or {}).get(key)
    if race_pool:
        return list(race_pool)
    return CHILD_GIFT_LOVE if positive else CHILD_GIFT_HATE
