from combat.combat_io import c_print, c_input, c_clear
"""Wedding accessory special effect engine.

Wedding items are Unique accessories gifted by married monster girls.
Their 'special' field triggers unique effects. If the married girl is in the
active party, the effect is amplified (Bonded).

State used during combat (stored on player dict):
  wedding_combat_active     bool   – True while in combat
  wedding_combat_floor      int    – floor number from combat() call
  wedding_combat_room      int    – room number from combat() call
  wedding_first_attack_done bool   – set after first player attack
  wedding_bark_shield_used_floor int – last floor bark_shield triggered
  wedding_bark_shield_room_count int – rooms since last bark_shield refresh (bonded)
  wedding_keening_wail_used bool   – keening wail triggered this combat
  wedding_shadow_cloak_used bool   – shadow_cloak bonded used this combat
  wedding_homeward_used     bool   – homeward_locket low-HP heal used this combat
  wedding_cosmic_gravity_used bool – cosmic_gravity buff steal used this combat
  wedding_crimson_feast_cha_buff bool – whether +2 CHA buff is active
"""

import random

from utils import display_name

# ── Core lookups ───────────────────────────────────────────────────────────

def get_active_wedding_item(player):
    """Return the equipped wedding accessory dict, or None."""
    for slot in ("accessory1", "accessory2", "accessory3"):
        item = player.get("equipped", {}).get(slot)
        if item and item.get("id", "").startswith("wedding_"):
            return item
    return None


def get_wedding_girl_key(item):
    """Extract the girl key from a wedding item ID."""
    return item["id"].replace("wedding_", "")


def is_bonded(player, item):
    """Return True if the married girl is in the active party."""
    girl_key = get_wedding_girl_key(item)
    for ally in player.get("allies", []):
        if ally.get("key") == girl_key:
            return True
    return False


# ── Combat lifecycle helpers ───────────────────────────────────────────────

def begin_wedding_combat(player, floor=None, room_num=None):
    """Call once at the start of combat()."""
    player["wedding_combat_active"] = True
    player["wedding_combat_floor"] = floor
    player["wedding_combat_room"] = room_num
    player["wedding_first_attack_done"] = False
    player["wedding_keening_wail_used"] = False
    player["wedding_shadow_cloak_used"] = False
    player["wedding_homeward_used"] = False
    player["wedding_cosmic_gravity_used"] = False


def end_wedding_combat(player):
    """Call once at the end of combat (victory, flee, or dead)."""
    player["wedding_combat_active"] = False
    player.pop("wedding_first_attack_done", None)
    player.pop("wedding_keening_wail_used", None)
    player.pop("wedding_shadow_cloak_used", None)
    player.pop("wedding_homeward_used", None)
    player.pop("wedding_cosmic_gravity_used", None)
    player.pop("wedding_overclock_proc", None)
    player.pop("wedding_grave_reign_stacks", None)
    player.pop("wedding_crimson_feast_cha_buff", None)


# ── Single-effect helpers (called by the main hooks below) ─────────────────

def _active(player):
    item = get_active_wedding_item(player)
    if not item:
        return None, None
    special = item.get("special")
    bonded = is_bonded(player, item)
    return special, bonded


def _is_boss(target):
    return bool(target.get("key") and target.get("name", "").startswith("Empowered ") or target.get("boss", False))


def _msg(text):
    c_print(f"  ♥ {text}")


# ── Combat Start ───────────────────────────────────────────────────────────

def apply_wedding_combat_start(player, enemies):
    """Call once after enemies are generated at combat start."""
    special, bonded = _active(player)
    if not special:
        return

    # tailwind (bonded): Party +1 initiative
    if special == "tailwind" and bonded:
        player.setdefault("active_buffs", []).append({
            "type": "wedding_initiative", "value": 1, "remaining": 1,
            "source": "tailwind_bonded"
        })
        _msg("Windweaver Pinion — your party's reflexes sharpen! (+1 initiative)")

    # rabbit_time (base or bonded): party gains +2/+3 initiative on every roll
    # (read by combat_engine.roll_initiative via apply_wedding_initiative_bonus)
    if special == "rabbit_time":
        _msg(f"Rabbit's Pocket Watch — your party moves a beat ahead! (+{3 if bonded else 2} initiative)")

    # shadow_cloak (bonded): 2-turn invisible (enemies target allies first)
    if special == "shadow_cloak" and bonded:
        player.setdefault("active_buffs", []).append({
            "type": "evasion", "value": 0.50, "remaining": 2,
            "source": "shadow_cloak_bonded"
        })
        _msg("Shadowthread Ring — you fade into the darkness! (+50% dodge, 2 turns)")

    # blizzard_song (bonded): enemies take 5 water damage at start
    if special == "blizzard_song" and bonded:
        from combat.weapon.chance_and_choice import apply_chance_and_choice
        _cac_state = {"rolled": False, "mult": 1.0}   # one flip per invocation
        for e in enemies:
            _bliz = apply_chance_and_choice(player, 5, _cac_state)
            e["hp"] = max(0, e["hp"] - _bliz)
            _msg(f"Blizzard Veil — {e['name']} is lashed by freezing winds! (-{_bliz} HP)")

    # tidal_blessing (bonded): enemies take 5 water damage at start
    if special == "tidal_blessing" and bonded:
        from combat.weapon.chance_and_choice import apply_chance_and_choice
        _cac_state = {"rolled": False, "mult": 1.0}   # one flip per invocation
        for e in enemies:
            _tid = apply_chance_and_choice(player, 5, _cac_state)
            e["hp"] = max(0, e["hp"] - _tid)
            _msg(f"Tidecaller Ring — a tidal wave crashes into {e['name']}! (-{_tid} HP)")

    # matriarchs_embrace (bonded): allies regenerate 2 HP per turn
    if special == "matriarchs_embrace" and bonded:
        for ally in player.get("allies", []):
            if ally.get("current_hp", 0) > 0:
                ally.setdefault("active_buffs", []).append({
                    "type": "hot", "value": 2, "remaining": 99,
                    "source": "matriarchs_embrace"
                })
        _msg("Matriarch's Favor — your allies are bathed in dark vitality. (+2 HP/turn)")

    # cosmic_gravity (base or bonded): +8% or +12% all stats when married girl in party
    if special == "cosmic_gravity":
        val = 0.12 if bonded else 0.08
        player.setdefault("active_buffs", []).append({
            "type": "wedding_stats", "value": val, "remaining": 99,
            "source": "cosmic_gravity"
        })
        _msg(f"Galaxy Heart — cosmic gravity surges! (+{int(val*100)}% to all stats)")

    # headless_oath: immune to fear and dread
    if special == "headless_oath":
        # Clear any existing fear/dread and add immunity buffs
        player["dreaded"] = False
        player["active_debuffs"] = [d for d in player.get("active_debuffs", []) if d.get("type") not in ("dread", "fear")]
        player.setdefault("active_buffs", []).append({
            "type": "fear_immunity", "remaining": 99, "source": "headless_oath"
        })
        _msg("Headless Rider's Seal — no fear can touch your oath-bound heart.")

    # oni_rage (bonded): when below 50% HP, gain +2 CON +2 STR
    if special == "oni_rage" and bonded:
        hp_ratio = player.get("current_hp", 1) / max(1, player.get("max_hp", 1))
        if hp_ratio < 0.50:
            player.setdefault("active_buffs", []).append({
                "stat": "Strength", "value": 2, "remaining": 99, "source": "oni_rage"
            })
            player.setdefault("active_buffs", []).append({
                "stat": "Constitution", "value": 2, "remaining": 99, "source": "oni_rage"
            })
            _msg("Oni Horn Ring — hellfire surges through your veins! (+2 STR, +2 CON)")

    # infernal_crown (base or bonded): +15% fire and dark damage
    if special == "infernal_crown":
        # Handled via elemental_dmg on the item itself, which is already wired.
        # The bonded extra (burn 10 + dread on melee attacker) is handled in on_damage_taken.
        pass

    # grave_reign: enemies take 3 dark damage at combat start; bonded 5
    if special == "grave_reign":
        dmg = 5 if bonded else 3
        from combat.weapon.chance_and_choice import apply_chance_and_choice
        _cac_state = {"rolled": False, "mult": 1.0}   # one flip per invocation
        dmg = apply_chance_and_choice(player, dmg, _cac_state)
        for e in enemies:
            e["hp"] = max(0, e["hp"] - dmg)
        _msg(f"Deathward Crown — the chill of the grave sweeps the battlefield! (-{dmg} HP all enemies)")

    # auto_guard (bonded): +3 CON for 3 turns at combat start
    if special == "auto_guard" and bonded:
        player.setdefault("active_buffs", []).append({
            "stat": "Constitution", "value": 3, "remaining": 3, "source": "auto_guard"
        })
        _msg("Precision Core — defensive protocols engaged! (+3 CON, 3 turns)")


# ── End of Round ───────────────────────────────────────────────────────────

def apply_wedding_end_of_round(player):
    """Call once per round after buffs/debuffs tick."""
    special, bonded = _active(player)
    if not special:
        return

    # bloom_regen: regenerate 3 HP at end of every turn; bonded 5 HP + cure 1 poison
    if special == "bloom_regen":
        heal = 5 if bonded else 3
        from character import player_max_hp
        old_hp = player.get("current_hp", 0)
        max_hp = player_max_hp(player)
        player["current_hp"] = min(old_hp + heal, max_hp)
        actual = player["current_hp"] - old_hp
        if actual > 0:
            _msg(f"Pollenheart Locket blooms — you regenerate {actual} HP.")
        if bonded:
            # Cure 1 poison stack
            poisons = [d for d in player.get("active_debuffs", []) if d.get("type") == "poison"]
            if poisons:
                player["active_debuffs"].remove(poisons[0])
                _msg("Pollenheart Locket — the blossom cleanses a poison stack.")

    # auto_guard: regenerate 2 HP at end of turn; bonded 3 HP
    if special == "auto_guard":
        heal = 3 if bonded else 2
        from character import player_max_hp
        old_hp = player.get("current_hp", 0)
        max_hp = player_max_hp(player)
        player["current_hp"] = min(old_hp + heal, max_hp)
        actual = player["current_hp"] - old_hp
        if actual > 0:
            _msg(f"Precision Core — auto-repair restores {actual} HP.")

    # seraph_light: heal 4 HP at end of turn; bonded 6 HP + cleanse 1 debuff
    if special == "seraph_light":
        heal = 6 if bonded else 4
        from character import player_max_hp
        old_hp = player.get("current_hp", 0)
        max_hp = player_max_hp(player)
        player["current_hp"] = min(old_hp + heal, max_hp)
        actual = player["current_hp"] - old_hp
        if actual > 0:
            _msg(f"Seraph's Feather — divine light restores {actual} HP.")
        if bonded and player.get("active_debuffs"):
            from combat.status_effects import is_cleansable
            idx = next((i for i, d in enumerate(player["active_debuffs"]) if is_cleansable(d)), None)
            if idx is not None:
                cleansed = player["active_debuffs"].pop(idx)
                _msg(f"Seraph's Feather — a {cleansed.get('type', 'debuff')} is cleansed!")


# ── Attack Bonus (flat damage before elemental) ────────────────────────────

def apply_wedding_attack_bonus(player, target, base_dmg, is_first_attack):
    """Return flat bonus damage to add to the player's attack."""
    from combat.status_effects import check_status_resisted
    special, bonded = _active(player)
    if not special:
        return 0

    bonus = 0

    # stampede: first attack +5 flat; bonded +5 and 25% stun
    if special == "stampede" and is_first_attack:
        bonus += 5
        if bonded and random.random() < 0.25 and not check_status_resisted(target):
            target["stunned"] = True
            _msg("Thunderhoof Brooch — the stampede stuns the target!")

    # huntsman_oath: first attack +30% damage; bonded +45%
    if special == "huntsman_oath" and is_first_attack:
        pct = 0.45 if bonded else 0.30
        bonus += max(1, int(base_dmg * pct))

    # champion_charge: first attack +8, +15% accuracy; bonded +12 and ignore 50% armor
    if special == "champion_charge" and is_first_attack:
        bonus += 12 if bonded else 8
        if bonded and "con_mod" in target:
            target["champion_charge_armor_ignore"] = target["con_mod"] // 2

    # bull_rush: above 70% HP +4; bonded above 50% +6
    if special == "bull_rush":
        threshold = 0.50 if bonded else 0.70
        hp_ratio = player.get("current_hp", 1) / max(1, player.get("max_hp", 1))
        if hp_ratio >= threshold:
            bonus += 6 if bonded else 4

    # war_sister: +3 with 2+ allies; bonded +5 and +1 STR to all allies
    if special == "war_sister":
        allies = [a for a in player.get("allies", []) if a.get("current_hp", 0) > 0]
        if len(allies) >= 2:
            bonus += 5 if bonded else 3
            if bonded:
                for a in allies:
                    a.setdefault("active_buffs", []).append({
                        "stat": "Strength", "value": 1, "remaining": 3, "source": "war_sister"
                    })
                _msg("Warband of the Sister — your allies stand stronger! (+1 STR)")

    # oni_rage: below 50% HP +5; bonded also +2 STR/CON (handled in combat_start)
    if special == "oni_rage":
        hp_ratio = player.get("current_hp", 1) / max(1, player.get("max_hp", 1))
        if hp_ratio < 0.50:
            bonus += 5

    # arena_glory: +5 vs bosses; bonded +8 and -2 damage from bosses
    if special == "arena_glory" and _is_boss(target):
        bonus += 8 if bonded else 5

    # dragon_judgment: +10% vs flying (beast/fey/dragonkin); bonded +15% and ignore 30% res
    if special == "dragon_judgment":
        from resources.enemies import ENEMIES
        key = target.get("key")
        if key:
            race = ENEMIES.get(key, {}).get("race", "")
            if race in ("Beast", "Fey", "Dragonkin"):
                # Approximate +10%/+15% as flat bonus relative to base damage
                bonus += int(base_dmg * (0.15 if bonded else 0.10))

    # riddle_solved: +8 if enemy hasn't acted; bonded +12 and silence 1 turn
    if special == "riddle_solved":
        if not target.get("has_acted", False):
            bonus += 12 if bonded else 8
            if bonded and not check_status_resisted(target):
                target["stunned"] = True  # Silence approximated as stun for 1 turn
                _msg("Riddlelock Band — the answer strikes before the question! (Silenced)")

    # valkyrie_ride: +10% at full HP; bonded allies +5%
    if special == "valkyrie_ride":
        if player.get("current_hp", 0) >= player.get("max_hp", 1):
            bonus += int(base_dmg * 0.10)
            if bonded:
                for a in player.get("allies", []):
                    if a.get("current_hp", 0) > 0:
                        a.setdefault("active_buffs", []).append({
                            "stat": "Strength", "value": 1, "remaining": 2, "source": "valkyrie_ride"
                        })
                _msg("Commander's Ring — your valor inspires the party! (+5% damage)")

    # starfire_breath: bonus = 20% CHA (35% bonded)
    if special == "starfire_breath":
        from combat.stats import get_effective_attribute
        cha = get_effective_attribute(player, "Charisma")
        pct = 0.35 if bonded else 0.20
        bonus += max(1, int(cha * pct))

    # overclock: first attack +10; bonded +15 and ignore 25% armor
    if special == "overclock" and is_first_attack:
        bonus += 15 if bonded else 10
        if bonded and "con_mod" in target:
            target["overclock_armor_ignore"] = max(0, target["con_mod"] // 4)

    # blood_fury: below 50% HP +6; bonded below 70% +8 and +2 STR/+2 CON
    if special == "blood_fury":
        threshold = 0.70 if bonded else 0.50
        hp_ratio = player.get("current_hp", 1) / max(1, player.get("max_hp", 1))
        if hp_ratio < threshold:
            bonus += 8 if bonded else 6
            if bonded:
                player.setdefault("active_buffs", []).append({
                    "stat": "Strength", "value": 2, "remaining": 3, "source": "blood_fury"
                })
                player.setdefault("active_buffs", []).append({
                    "stat": "Constitution", "value": 2, "remaining": 3, "source": "blood_fury"
                })
                _msg("War-Sister's Bond — battle-fury surges! (+2 STR, +2 CON, 3 turns)")

    # dragon_heart: +10% fire bonus damage; bonded +15% fire + burn
    if special == "dragon_heart":
        pct = 0.15 if bonded else 0.10
        bonus += max(1, int(base_dmg * pct))

    # seraph_light: +5% damage per alive ally; bonded +8% and heal allies 2 HP
    if special == "seraph_light":
        alive_allies = len([a for a in player.get("allies", []) if a.get("current_hp", 0) > 0])
        pct = (0.08 if bonded else 0.05) * alive_allies
        bonus += max(0, int(base_dmg * pct))
        if bonded and alive_allies > 0:
            for a in player.get("allies", []):
                if a.get("current_hp", 0) > 0:
                    a["current_hp"] = min(a["current_hp"] + 2, a.get("max_hp", a["current_hp"]))
            _msg("Seraph's Feather — your radiance restores allies! (+2 HP each)")

    # infernal_vow: +8% fire and dark damage; bonded +12%
    if special == "infernal_vow":
        pct = 0.12 if bonded else 0.08
        bonus += max(1, int(base_dmg * pct))

    return bonus


# ── On Hit (status procs) ──────────────────────────────────────────────────

def _find_burn(entity):
    """Return the entity's active burn debuff dict, or None."""
    return next((d for d in entity.get("active_debuffs", []) if d.get("type") == "burn"), None)


def apply_wedding_on_hit(player, target, enemies, damage_dealt):
    """Call after a successful player attack lands."""
    from combat.status_effects import check_status_resisted
    special, bonded = _active(player)
    if not special:
        return

    # moth_dust: 20% blind 2 turns; bonded 3 turns and -1 DEX
    if special == "moth_dust" and random.random() < 0.20 and not check_status_resisted(target):
        dur = 3 if bonded else 2
        target.setdefault("active_debuffs", []).append({
            "type": "blind", "remaining": dur
        })
        target["blinded"] = True
        _msg(f"Moondust Pendant — {target['name']} is blinded! ({dur} turns)")
        if bonded:
            target["dex_mod"] = max(0, target.get("dex_mod", 0) - 1)
            _msg(f"Moondust Pendant — {target['name']}'s Dexterity fades! (-1 DEX)")

    # coil_bind: 25% slow 2 turns; bonded slowed enemies +2 damage taken
    if special == "coil_bind" and random.random() < 0.25:
        from combat.status_effects import apply_slow_to_enemy
        apply_slow_to_enemy(target, duration=2)
        _msg(f"Coiled Serpent Ring — {target['name']} is slowed!")
        if bonded:
            target.setdefault("coil_bind_vulnerable", 2)
            _msg(f"Coiled Serpent Ring — {target['name']} is constricted! (+2 damage taken)")

    # frost_aura: 20% freeze 1 turn; bonded 35% freeze, frozen +20% next hit
    if special == "frost_aura":
        chance = 0.35 if bonded else 0.20
        if random.random() < chance and not check_status_resisted(target):
            target["frozen"] = True
            target["freeze_duration"] = 1
            _msg(f"Frostbloom Charm — {target['name']} freezes solid!")
            if bonded:
                target["frost_aura_vulnerable"] = True

    # flame_dance: 30% burn 3 turns (5/turn); bonded 8/turn and spread
    if special == "flame_dance" and random.random() < 0.30:
        from combat.status_effects import apply_burn, damage_to_burn_tier, get_burn_tier_name
        burn_dmg = 8 if bonded else 5
        b_tier = damage_to_burn_tier(burn_dmg)
        apply_burn(target, b_tier, 3)
        _msg(f"Emberwaltz Ring — {target['name']} is set ablaze! ({get_burn_tier_name(b_tier)})")
        if bonded and enemies:
            adjacent = [e for e in enemies if e is not target and e.get("hp", 0) > 0]
            if adjacent:
                spread = random.choice(adjacent)
                apply_burn(spread, b_tier, 3)
                _msg(f"Emberwaltz Ring — flames spread to {spread['name']}!")

    # dream_drain: 20% dread 2 turns; bonded dreaded enemies 40% miss
    if special == "dream_drain" and random.random() < 0.20 and not check_status_resisted(target):
        from combat.status_effects import apply_dread
        apply_dread(player, duration=2)  # Wait, dread applies to PLAYER, not enemy
        # Actually dread is a player debuff. The design says "inflict dread for 2 turns"
        # But dread is currently a player-only debuff. Let's apply it to the enemy via a custom flag.
        # For now, apply a fear debuff to the enemy instead.
        target.setdefault("active_debuffs", []).append({
            "type": "fear", "value": 0.25, "remaining": 2
        })
        _msg(f"Dreamcatcher Ring — {target['name']} is filled with dread!")
        if bonded:
            target["dream_drain_miss"] = 0.40

    # silk_bind: 25% -2 DEX for 3 turns; bonded also -20% dodge
    if special == "silk_bind" and random.random() < 0.25 and not check_status_resisted(target):
        target["dex_mod"] = max(0, target.get("dex_mod", 0) - 2)
        target.setdefault("silk_bind_stacks", []).append({"remaining": 3})
        _msg(f"Silkspinner Band — webs bind {target['name']}! (-2 DEX, 3 turns)")
        if bonded:
            target.setdefault("silk_bind_dodge_penalty", 0.20)

    # siren_song: 20% charm (stun 1 turn); bonded 2 turns and -2 WIS
    if special == "siren_song" and random.random() < 0.20 and not check_status_resisted(target):
        dur = 2 if bonded else 1
        target["stunned"] = True
        _msg(f"Coral Crown Ring — {target['name']} is charmed! ({dur} turn(s))")
        if bonded:
            target.setdefault("wis_mod", 0)
            target["wis_mod"] = max(0, target["wis_mod"] - 2)
            _msg(f"Coral Crown Ring — {target['name']}'s will breaks! (-2 WIS)")

    # whip_crack: 25% -3 armor for 3 turns; bonded also -2 DEX
    if special == "whip_crack" and random.random() < 0.25 and not check_status_resisted(target):
        target.setdefault("active_debuffs", []).append({
            "type": "sunder", "value": 3, "remaining": 3
        })
        _msg(f"Whipmaster's Coil — {target['name']}'s armor cracks! (-3 armor, 3 turns)")
        if bonded:
            target["dex_mod"] = max(0, target.get("dex_mod", 0) - 2)
            _msg(f"Whipmaster's Coil — {target['name']} is hobbled! (-2 DEX)")

    # abyssal_grasp: 30% -3 DEX for 3 turns (tentacle bind); bonded also slow + 3 water/turn
    if special == "abyssal_grasp" and random.random() < 0.30 and not check_status_resisted(target):
        target["dex_mod"] = max(0, target.get("dex_mod", 0) - 3)
        target.setdefault("abyssal_bind_turns", 3)
        _msg(f"Abyssal Coil — tentacles bind {target['name']}! (-3 DEX, 3 turns)")
        if bonded:
            from combat.status_effects import apply_slow_to_enemy
            apply_slow_to_enemy(target, duration=3)
            target.setdefault("active_debuffs", []).append({
                "type": "poison", "damage": 3, "remaining": 3  # water damage approximated as poison
            })
            _msg(f"Abyssal Coil — {target['name']} is drowning in tentacles! (slowed, 3 water/turn)")

    # dusk_weave: 25% blind 2 turns; bonded 35% blind + slow
    if special == "dusk_weave" and random.random() < (0.35 if bonded else 0.25) and not check_status_resisted(target):
        dur = 3 if bonded else 2
        target.setdefault("active_debuffs", []).append({
            "type": "blind", "remaining": dur
        })
        target["blinded"] = True
        _msg(f"Twilight Shroud — shadows blind {target['name']}! ({dur} turns)")
        if bonded:
            from combat.status_effects import apply_slow_to_enemy
            apply_slow_to_enemy(target, duration=2)
            _msg(f"Twilight Shroud — {target['name']} is slowed by the dusk!")

    # stone_gaze: 20% petrify (-3 STR/DEX for 3 turns); bonded 15% chance to stun instead
    if special == "stone_gaze" and random.random() < 0.20 and not check_status_resisted(target):
        if bonded and random.random() < 0.15:
            target["stunned"] = True
            _msg(f"Gorgon's Veil Ring — {target['name']} is fully petrified! (Stunned)")
        else:
            target.setdefault("str_mod", 0)
            target["str_mod"] = max(0, target.get("str_mod", 0) - 3)
            target["dex_mod"] = max(0, target.get("dex_mod", 0) - 3)
            target.setdefault("stone_gaze_turns", 3)
            _msg(f"Gorgon's Veil Ring — {target['name']} begins to petrify! (-3 STR, -3 DEX, 3 turns)")

    # lich_grasp: 25% curse -2 all stats for 3 turns; bonded also 5 dark/turn and no heal
    if special == "lich_grasp" and random.random() < 0.25 and not check_status_resisted(target):
        target.setdefault("active_debuffs", []).append({
            "type": "curse", "penalty": 2, "remaining": 3, "stats": ["Strength", "Constitution", "Dexterity", "Wisdom", "Charisma", "Learning"]
        })
        _msg(f"Phylactery Bond — {target['name']} is cursed! (-2 all stats, 3 turns)")
        if bonded:
            target.setdefault("active_debuffs", []).append({
                "type": "poison", "damage": 5, "remaining": 3  # dark damage approximated
            })
            target["lich_grasp_no_heal"] = True
            _msg(f"Phylactery Bond — the curse withers {target['name']}'s soul! (5 dark/turn, no heal)")

    # brood_swarm: 25% +6 damage and poison 3 turns (4/turn); bonded poison 8/turn and -2 DEX
    if special == "brood_swarm" and target.pop("wedding_brood_swarm_proc", False):
        from combat.status_effects import apply_poison
        poison_dmg = 8 if bonded else 4
        apply_poison(target, poison_dmg, 3)
        # Bonus damage is applied in attack_bonus (+6)
        _msg(f"Broodmother's Web — spiderlings swarm {target['name']}! (+6 damage, {poison_dmg}/turn)")
        if bonded:
            target["dex_mod"] = max(0, target.get("dex_mod", 0) - 2)
            _msg(f"Broodmother's Web — spiderlings gnaw at {target['name']}'s agility! (-2 DEX)")

    # legendary_flame: burn 3 turns (6/turn); bonded 10/turn and spreads to all.
    #
    # The bonded spread is a pure seed (2026-10-12): it only lights enemies that
    # aren't already burning, and a spread-seeded burn never counts as a prior
    # application — the first direct strike on a seeded enemy just fans the
    # flame, the next one intensifies it. Without this, one AoE (which fires
    # this hook once per enemy) applied Blaze twice to every target — spread +
    # direct hit — instantly escalating whole packs to Inferno via the burn
    # system's same-tier reapplication rule.
    if special == "legendary_flame":
        from combat.status_effects import apply_burn, damage_to_burn_tier, get_burn_tier_name
        burn_dmg = 10 if bonded else 6
        b_tier = damage_to_burn_tier(burn_dmg)

        existing = _find_burn(target)
        if existing is not None and existing.pop("sunfire_seed", False):
            # Seeded by the band's own spread: this strike is the burn's first
            # real application, so it feeds the flame instead of intensifying
            # it (no resist roll — the burn is already lit).
            existing["remaining"] = 3
            _msg(f"Sunfire Band — {target['name']} is engulfed in legendary flame! "
                 f"({get_burn_tier_name(existing.get('tier', b_tier))})")
        else:
            result = apply_burn(target, b_tier, 3)
            burn = _find_burn(target)
            tier = burn.get("tier", b_tier) if burn else b_tier
            if result == "intensified":
                _msg(f"Sunfire Band — {target['name']}'s flames intensify into {get_burn_tier_name(tier)}!")
            elif result == "upgraded":
                _msg(f"Sunfire Band — {target['name']}'s flames surge to {get_burn_tier_name(tier)}!")
            elif result == "resisted":
                _msg(f"Sunfire Band — {target['name']} resists the legendary flame!")
            elif result == "refreshed":
                _msg(f"Sunfire Band — the legendary flame on {target['name']} burns on. "
                     f"({get_burn_tier_name(tier)})")
            elif result is not None:
                _msg(f"Sunfire Band — {target['name']} is engulfed in legendary flame! "
                     f"({get_burn_tier_name(tier)})")

        if bonded:
            spread_names = []
            for e in enemies:
                if e is target or e.get("hp", 0) <= 0:
                    continue
                if _find_burn(e) is not None:
                    continue  # never re-ignite: the spread must not feed escalation
                if apply_burn(e, b_tier, 3) == "applied":
                    _find_burn(e)["sunfire_seed"] = True
                    spread_names.append(e["name"])
            if spread_names:
                _msg(f"Sunfire Band — the flame spreads to {', '.join(spread_names)}!")

    # starfire_breath (bonded): attacks burn for 3 turns — designed in the
    # original spec but never implemented until 2026-10-04 (the blurb
    # advertised it regardless; now the effect is real).
    if special == "starfire_breath" and bonded:
        from combat.status_effects import apply_burn, damage_to_burn_tier, get_burn_tier_name
        b_tier = damage_to_burn_tier(6)
        apply_burn(target, b_tier, 3)
        _msg(f"Stardust Crown — {target['name']} is bathed in starfire! ({get_burn_tier_name(b_tier)})")

    # infernal_crown: +15% fire/dark damage (handled by elemental stats), melee burn 5
    # The melee burn is handled in on_damage_taken (retribution).

    # overclock (bonded): 30% chance to refresh a skill cooldown
    if special == "overclock" and bonded and random.random() < 0.30:
        player["wedding_overclock_proc"] = True
        _msg("Gearheart Pendant — the gears align! (Skill cooldown refreshed)")

    # dragon_heart: on hit 30% burn 3 turns (6/turn); bonded 10/turn and spread
    if special == "dragon_heart" and random.random() < 0.30:
        from combat.status_effects import apply_burn, damage_to_burn_tier, get_burn_tier_name
        burn_dmg = 10 if bonded else 6
        b_tier = damage_to_burn_tier(burn_dmg)
        apply_burn(target, b_tier, 3)
        _msg(f"Eternal Ember — {target['name']} is seared by dragonfire! ({get_burn_tier_name(b_tier)})")
        if bonded and enemies:
            others = [e for e in enemies if e is not target and e.get("hp", 0) > 0]
            if others:
                spread = random.choice(others)
                apply_burn(spread, b_tier, 3)
                _msg(f"Eternal Ember — flames spread to {spread['name']}!")

    # infernal_vow: on hit 25% burn 3 turns (5/turn); bonded 35% burn 8/turn + dread
    if special == "infernal_vow" and random.random() < (0.35 if bonded else 0.25):
        from combat.status_effects import apply_burn, damage_to_burn_tier, get_burn_tier_name
        burn_dmg = 8 if bonded else 5
        b_tier = damage_to_burn_tier(burn_dmg)
        apply_burn(target, b_tier, 3)
        _msg(f"Infernal Vow Band — hellfire sears {target['name']}! ({get_burn_tier_name(b_tier)})")
        if bonded and not check_status_resisted(target):
            target.setdefault("active_debuffs", []).append({
                "type": "fear", "value": 0.25, "remaining": 1
            })
            _msg(f"Infernal Vow Band — {target['name']} is stricken with dread!")

    # cosmic_gravity (bonded): once per combat steal 1 random buff on first hit
    if special == "cosmic_gravity" and bonded and not player.get("wedding_cosmic_gravity_used") and not check_status_resisted(target):
        player["wedding_cosmic_gravity_used"] = True
        if target.get("active_buffs"):
            stolen = random.choice(target["active_buffs"])
            player.setdefault("active_buffs", []).append(stolen.copy())
            target["active_buffs"].remove(stolen)
            _msg(f"Galaxy Heart — you absorb {target['name']}'s cosmic power!")

    # blood_drain: heal 15% damage dealt; bonded 25% and excess becomes HoT
    if special == "blood_drain" and damage_dealt > 0:
        from character import player_max_hp
        pct = 0.25 if bonded else 0.15
        heal = int(damage_dealt * pct)
        old_hp = player.get("current_hp", 0)
        max_hp = player_max_hp(player)
        player["current_hp"] = min(old_hp + heal, max_hp)
        actual = player["current_hp"] - old_hp
        if actual > 0:
            _msg(f"Sanguine Kiss Ring — you drain {actual} HP from the wound.")
        excess = heal - actual
        if bonded and excess > 0:
            player.setdefault("active_buffs", []).append({
                "type": "hot", "value": excess, "remaining": 3, "source": "blood_drain"
            })
            _msg(f"Sanguine Kiss Ring — excess life becomes a blood ward! (+{excess} HP/turn, 3 turns)")

    # tidal_blessing: heal 15% damage dealt; bonded 25% + start wave
    if special == "tidal_blessing" and damage_dealt > 0:
        from character import player_max_hp
        pct = 0.25 if bonded else 0.15
        heal = int(damage_dealt * pct)
        old_hp = player.get("current_hp", 0)
        max_hp = player_max_hp(player)
        player["current_hp"] = min(old_hp + heal, max_hp)
        actual = player["current_hp"] - old_hp
        if actual > 0:
            _msg(f"Tidecaller Ring — tidal waters restore {actual} HP.")

    # crimson_feast: heal 15% max HP on defeat; bonded 25% and +2 CHA for 3 turns
    if special == "crimson_feast" and target.get("hp", 0) <= 0:
        from character import player_max_hp
        max_hp = player_max_hp(player)
        heal = int(max_hp * (0.25 if bonded else 0.15))
        old_hp = player.get("current_hp", 0)
        player["current_hp"] = min(old_hp + heal, max_hp)
        actual = player["current_hp"] - old_hp
        if actual > 0:
            _msg(f"Crimson Sigil — the feast restores {actual} HP!")
        if bonded and not player.get("wedding_crimson_feast_cha_buff"):
            player["wedding_crimson_feast_cha_buff"] = True
            player.setdefault("active_buffs", []).append({
                "stat": "Charisma", "value": 2, "remaining": 3, "source": "crimson_feast"
            })
            _msg("Crimson Sigil — your presence grows more commanding! (+2 CHA, 3 turns)")


# ── Attack Bonus (called before on_hit) ────────────────────────────────────

def apply_wedding_attack_bonus_procs(player, target, base_dmg, is_first_attack):
    """Return extra flat damage to add before elemental calculations."""
    special, bonded = _active(player)
    if not special:
        return 0
    bonus = apply_wedding_attack_bonus(player, target, base_dmg, is_first_attack)
    # brood_swarm bonus damage (+6)
    if special == "brood_swarm" and random.random() < 0.25:
        bonus += 6
        target["wedding_brood_swarm_proc"] = True
        _msg(f"Broodmother's Web — spiderlings bite {target['name']} for 6 extra damage!")
    return bonus


# ── On Kill ────────────────────────────────────────────────────────────────

def apply_wedding_on_kill(player, target, enemies):
    """Call when the player defeats an enemy."""
    special, bonded = _active(player)
    if not special:
        return

    # headless_oath (bonded): allies heal 10 HP
    if special == "headless_oath" and bonded:
        for ally in player.get("allies", []):
            if ally.get("current_hp", 0) > 0:
                ally["current_hp"] = min(ally["current_hp"] + 10, ally.get("max_hp", ally["current_hp"]))
                _msg(f"Headless Rider's Seal — {display_name(ally)} is healed by your oath! (+10 HP)")

    # grave_reign: on kill heal 15% max HP; bonded 25% and gain +1 all stats (stacks 3x)
    if special == "grave_reign":
        from character import player_max_hp
        max_hp = player_max_hp(player)
        heal_pct = 0.25 if bonded else 0.15
        heal = int(max_hp * heal_pct)
        old_hp = player.get("current_hp", 0)
        player["current_hp"] = min(old_hp + heal, max_hp)
        actual = player["current_hp"] - old_hp
        if actual > 0:
            _msg(f"Deathward Crown — the grave yields {actual} HP!")
        if bonded:
            stacks = player.get("wedding_grave_reign_stacks", 0)
            if stacks < 3:
                player["wedding_grave_reign_stacks"] = stacks + 1
                for stat in ("Strength", "Constitution", "Dexterity", "Wisdom", "Charisma", "Learning"):
                    player.setdefault("active_buffs", []).append({
                        "stat": stat, "value": 1, "remaining": 99, "source": "grave_reign"
                    })
                _msg(f"Deathward Crown — the grave empowers you! (+1 all stats, stack {stacks+1}/3)")


# ── Dodge ────────────────────────────────────────────────────────────────────

def apply_wedding_dodge_bonus(player):
    """Return extra dodge chance (0.0–1.0)."""
    special, bonded = _active(player)
    if not special:
        return 0.0

    if special == "tailwind":
        return 0.08
    if special == "spectral_dodge":
        return 0.10
    if special == "neko_shadow":
        return 0.12
    if special == "shadow_cloak":
        return 0.12
    if special == "dusk_weave":
        return 0.12 if bonded else 0.08
    if special == "star_waltz":
        return 0.15 if bonded else 0.10
    return 0.0


def apply_wedding_on_dodge(player, enemy):
    """Call when the player successfully dodges an attack."""
    special, bonded = _active(player)
    if not special:
        return

    # spectral_dodge (bonded): heal 5 HP on dodge
    if special == "spectral_dodge" and bonded:
        from character import player_max_hp
        old_hp = player.get("current_hp", 0)
        max_hp = player_max_hp(player)
        player["current_hp"] = min(old_hp + 5, max_hp)
        actual = player["current_hp"] - old_hp
        if actual > 0:
            _msg(f"Ectoplasm Veil — you slip through reality and heal {actual} HP.")

    # neko_shadow (bonded): counter-attack for 50% normal damage
    if special == "neko_shadow" and bonded:
        from combat.stats import get_effective_attribute
        p_str = get_effective_attribute(player, "Strength")
        counter_dmg = max(1, int((random.randint(4, 10) + p_str) * 0.5))
        from combat.weapon.chance_and_choice import apply_chance_and_choice
        counter_dmg = apply_chance_and_choice(player, counter_dmg)
        enemy["hp"] = max(0, enemy["hp"] - counter_dmg)
        from combat.helpers import format_damage_msg
        _msg(format_damage_msg(player['name'], enemy['name'], counter_dmg, skill_name="Nekomata Bell"))

    # star_waltz: counter-attack for 50% weapon damage; bonded 60% and +2 DEX for 2 turns
    if special == "star_waltz":
        from combat.stats import get_effective_attribute
        p_str = get_effective_attribute(player, "Strength")
        pct = 0.60 if bonded else 0.50
        counter_dmg = max(1, int((random.randint(4, 10) + p_str) * pct))
        from combat.weapon.chance_and_choice import apply_chance_and_choice
        counter_dmg = apply_chance_and_choice(player, counter_dmg)
        enemy["hp"] = max(0, enemy["hp"] - counter_dmg)
        from combat.helpers import format_damage_msg
        _msg(format_damage_msg(player['name'], enemy['name'], counter_dmg, skill_name="Constellation Waltz Ring"))
        if bonded:
            player.setdefault("active_buffs", []).append({
                "stat": "Dexterity", "value": 2, "remaining": 2, "source": "star_waltz"
            })
            _msg("Constellation Waltz Ring — your steps quicken! (+2 DEX, 2 turns)")


# ── Damage Taken ───────────────────────────────────────────────────────────

def apply_wedding_damage_reduction(player, damage, is_elemental=False, element=None):
    """Return reduced damage amount (before applying to HP)."""
    special, bonded = _active(player)
    if not special:
        return damage

    # stone_endurance: -2 flat; bonded -4 and immune to stun
    if special == "stone_endurance":
        reduction = 4 if bonded else 2
        damage = max(0, damage - reduction)

    # auto_guard: -3 flat; bonded -5
    if special == "auto_guard":
        reduction = 5 if bonded else 3
        damage = max(0, damage - reduction)

    # stone_ward: -2 physical; bonded -4 physical and immune to stun
    if special == "stone_ward" and element == "physical":
        reduction = 4 if bonded else 2
        damage = max(0, damage - reduction)
        if bonded:
            player["stun_immune"] = True

    # bark_shield: once per floor survive fatal blow with 1 HP + defense buff
    # This is handled in on_damage_taken_fatal below, not here.

    # slime_absorb: absorb 15% elemental as healing; bonded 25% and share 10%
    if special == "slime_absorb" and is_elemental and damage > 0:
        pct = 0.25 if bonded else 0.15
        absorb = int(damage * pct)
        damage = max(0, damage - absorb)
        from character import player_max_hp
        old_hp = player.get("current_hp", 0)
        max_hp = player_max_hp(player)
        player["current_hp"] = min(old_hp + absorb, max_hp)
        actual = player["current_hp"] - old_hp
        if actual > 0:
            _msg(f"Gelatinous Heart — you absorb {actual} elemental damage as healing!")
        if bonded and actual > 0:
            girl_key = get_wedding_girl_key(get_active_wedding_item(player))
            for ally in player.get("allies", []):
                if ally.get("key") == girl_key and ally.get("current_hp", 0) > 0:
                    share = int(actual * 0.10)
                    ally["current_hp"] = min(ally["current_hp"] + share, ally.get("max_hp", ally["current_hp"]))
                    _msg(f"Gelatinous Heart — you share {share} healing with {display_name(ally)}.")

    # infernal_crown (bonded): melee attackers take 10 burn damage
    # Handled in on_damage_taken_after_hit for retribution.

    return damage


def apply_wedding_on_damage_taken(player, enemy, damage, outcome):
    """Call after the enemy has hit the player (but before HP check)."""
    from combat.status_effects import check_status_resisted
    special, bonded = _active(player)
    if not special:
        return

    # pharaohs_curse: enemies that attack you take 4 damage; bonded 8 and -10% accuracy
    if special == "pharaohs_curse" and damage > 0:
        ret = 8 if bonded else 4
        from combat.weapon.chance_and_choice import apply_chance_and_choice
        ret = apply_chance_and_choice(player, ret)
        enemy["hp"] = max(0, enemy["hp"] - ret)
        _msg(f"Pharaoh's Band — {enemy['name']} suffers {ret} retribution damage!")
        if bonded:
            enemy.setdefault("pharaohs_curse_acc", 0.10)

    # infernal_crown: melee attackers take 5 burn; bonded 10 and 1-turn dread
    if special == "infernal_crown" and damage > 0:
        burn = 10 if bonded else 5
        from combat.status_effects import apply_burn, damage_to_burn_tier, get_burn_tier_name
        b_tier = damage_to_burn_tier(burn)
        apply_burn(enemy, b_tier, 2)
        _msg(f"Infernal Throne Seal — {enemy['name']} is scorched by hellfire! ({get_burn_tier_name(b_tier)})")
        if bonded and not check_status_resisted(enemy):
            enemy.setdefault("active_debuffs", []).append({
                "type": "fear", "value": 0.25, "remaining": 1
            })
            _msg(f"Infernal Throne Seal — {enemy['name']} is filled with dread!")

    # infernal_vow: attackers take 5 fire retribution; bonded 10
    if special == "infernal_vow" and damage > 0:
        ret = 10 if bonded else 5
        from combat.weapon.chance_and_choice import apply_chance_and_choice
        ret = apply_chance_and_choice(player, ret)
        enemy["hp"] = max(0, enemy["hp"] - ret)
        _msg(f"Infernal Vow Band — {enemy['name']} is scorched by retribution! (-{ret} HP)")

    # keening_wail: when HP < 25%, enemies take 10-20 damage, 30% fear; bonded 15-30 at 35%
    if special == "keening_wail" and not player.get("wedding_keening_wail_used"):
        threshold = 0.35 if bonded else 0.25
        hp_ratio = player.get("current_hp", 1) / max(1, player.get("max_hp", 1))
        if hp_ratio < threshold:
            player["wedding_keening_wail_used"] = True
            dmg_range = (15, 30) if bonded else (10, 20)
            wail_dmg = random.randint(*dmg_range)
            from combat.weapon.chance_and_choice import apply_chance_and_choice
            wail_dmg = apply_chance_and_choice(player, wail_dmg)
            # Apply to all enemies
            from combat.combat_engine import prune_dead
            # We can't easily access the enemies list here, so we'll apply to the attacker
            enemy["hp"] = max(0, enemy["hp"] - wail_dmg)
            from combat.helpers import format_damage_msg
            _msg(format_damage_msg(player['name'], enemy['name'], wail_dmg, skill_name="Keening Wail"))
            if random.random() < 0.30 and not check_status_resisted(enemy):
                enemy.setdefault("active_debuffs", []).append({
                    "type": "fear", "value": 0.30, "remaining": 1
                })
                _msg(f"Wailing Spirit Locket — {enemy['name']} is stricken with fear!")

    # homeward_locket: once per combat, below 35% HP — hearth-light heal
    if special == "homeward_locket" and not player.get("wedding_homeward_used"):
        from character import player_max_hp
        max_hp = player_max_hp(player)
        hp_ratio = player.get("current_hp", 1) / max(1, max_hp)
        if hp_ratio < 0.35:
            player["wedding_homeward_used"] = True
            healed = max(1, int(max_hp * (0.30 if bonded else 0.20)))
            old_hp = player.get("current_hp", 0)
            player["current_hp"] = min(old_hp + healed, max_hp)
            _msg(f"Homeward Locket — a hearth-light steadies you. (+{player['current_hp'] - old_hp} HP)")
            if bonded:
                for a in player.get("allies", []):
                    if a.get("current_hp", 0) > 0:
                        a_heal = max(1, int(a.get("max_hp", 1) * 0.05))
                        a["current_hp"] = min(a["current_hp"] + a_heal, a.get("max_hp", a["current_hp"]))
                _msg("Homeward Locket — the warmth spreads to your whole party! (+5% HP each)")

    # foxfire_trick: 20% when attacked to miss + 5 fire; bonded 35% and blind 1 turn
    if special == "foxfire_trick" and damage > 0:
        chance = 0.35 if bonded else 0.20
        if random.random() < chance:
            # The attack already hit, so we can't make it miss. Instead, reduce damage to 0 and return fire.
            # But this function is called after damage is applied. We should handle it in enemy_ai.py before damage.
            pass


# ── Fatal Blow Survival (called before applying damage) ────────────────────

def apply_wedding_fatal_blow_survival(player, damage):
    """Return modified damage. If fatal blow is prevented, returns 0 and applies effects."""
    special, bonded = _active(player)
    if not special or special != "bark_shield":
        return damage

    # Check if this blow would be fatal
    current_hp = player.get("current_hp", 0)
    if current_hp - damage > 0:
        return damage

    # Once per floor
    used_floor = player.get("wedding_bark_shield_used_floor", -1)
    current_floor = player.get("wedding_combat_floor", -1)
    if used_floor == current_floor and not bonded:
        return damage

    # Bonded: refresh every 5 rooms
    if bonded:
        room_count = player.get("wedding_bark_shield_room_count", 0)
        if used_floor == current_floor and room_count < 5:
            return damage
        # Reset counter
        player["wedding_bark_shield_room_count"] = 0

    player["wedding_bark_shield_used_floor"] = current_floor
    # Survive with 1 HP
    player["current_hp"] = 1
    player.setdefault("active_buffs", []).append({
        "type": "defense", "value": 3, "remaining": 4, "source": "bark_shield"
    })
    _msg("Barkskin Band — the tree's gift preserves your life! (1 HP, +3 defense, 4 turns)")
    return 0  # Damage prevented


# ── Skill Cooldown Skip ────────────────────────────────────────────────────

def apply_wedding_skill_cooldown_skip(player, skill_id):
    """Return True if the skill cooldown should NOT be set."""
    special, bonded = _active(player)
    if not special:
        return False

    if special == "tinkerers_inspiration":
        chance = 0.40 if bonded else 0.20
        if random.random() < chance:
            _msg("Clockwork Bond Ring — the gears align, and your skill is ready again!")
            return True
        return False

    if special == "overclock" and player.pop("wedding_overclock_proc", False):
        _msg("Gearheart Pendant — overclock refreshes your skill!")
        return True

    return False


# ── Max HP Bonus ────────────────────────────────────────────────────────────

def apply_wedding_max_hp_bonus(player):
    """Return flat bonus max HP."""
    special, bonded = _active(player)
    if not special:
        return 0
    if special == "matriarchs_embrace":
        # +10% max HP
        from character import player_max_hp
        base = player_max_hp(player)
        return int(base * 0.10)
    if special == "stone_ward":
        from character import player_max_hp
        base = player_max_hp(player)
        pct = 0.12 if bonded else 0.08
        return int(base * pct)
    return 0


# ── Capture Bonus ──────────────────────────────────────────────────────────

def apply_wedding_capture_bonus(player):
    """Return bonus capture success percentage points (additive)."""
    special, bonded = _active(player)
    if not special or special != "regal_presence":
        return 0
    return 15


def apply_wedding_capture_affection_bonus(player):
    """Return bonus starting affection for captured monster girls."""
    special, bonded = _active(player)
    if not special or special != "regal_presence":
        return 0
    return 10 if bonded else 0


# ── Combat End Rewards ─────────────────────────────────────────────────────

def apply_wedding_combat_end(player, victory):
    """Call after combat ends (victory, flee, or death)."""
    if not victory:
        end_wedding_combat(player)
        return

    special, bonded = _active(player)
    if not special:
        end_wedding_combat(player)
        return

    # goblin_luck: 25% chance for 5-15 bonus gold; bonded 50%
    if special == "goblin_luck":
        chance = 0.50 if bonded else 0.25
        if random.random() < chance:
            gold = random.randint(5, 15)
            player["gold"] = player.get("gold", 0) + gold
            _msg(f"Lucky Copper Ring — you find {gold} bonus gold among the loot!")

    # mimic_jackpot: 20% duplicate random consumable; bonded also 10% gift item
    if special == "mimic_jackpot":
        if random.random() < 0.20:
            consumables = [itm for itm in player.get("inventory", []) if itm.get("type") in ("consumable", "utility")]
            if consumables:
                dup = random.choice(consumables).copy()
                dup.pop("id", None)  # Remove ID to avoid issues
                from inventory import add_item_to_inventory
                if add_item_to_inventory(player, dup):
                    _msg(f"Mimic's Tooth — your {dup['name']} somehow duplicated!")
            else:
                _msg("Mimic's Tooth — nothing to duplicate right now.")
        if bonded and random.random() < 0.10:
            from resources.items import build_item, ITEMS
            gift_ids = [k for k, v in ITEMS.items() if v.get("type") == "gift"]
            if gift_ids:
                gift = build_item(random.choice(gift_ids), "common")
                from inventory import add_item_to_inventory
                if add_item_to_inventory(player, gift):
                    _msg(f"Mimic's Tooth — you found a hidden {gift['name']}!")

    end_wedding_combat(player)


# ── Enemy Accuracy Penalty (applied in enemy AI) ───────────────────────────

def apply_wedding_enemy_accuracy_penalty(player):
    """Return extra dodge chance from enemy accuracy reduction."""
    special, bonded = _active(player)
    if not special:
        return 0.0
    if special == "shadow_cloak":
        return 0.12
    if special == "pharaohs_curse" and bonded:
        return 0.10
    return 0.0


# ── When Enemy Attacks (pre-damage) ────────────────────────────────────────

def apply_wedding_enemy_attack_pre_damage(player, enemy):
    """Return True if the attack should miss entirely (foxfire_trick, etc.)."""
    special, bonded = _active(player)
    if not special:
        return False

    # foxfire_trick: 20% chance when attacked to create clone (miss + 5 fire); bonded 35% and blind
    if special == "foxfire_trick":
        chance = 0.35 if bonded else 0.20
        if random.random() < chance:
            from combat.weapon.chance_and_choice import apply_chance_and_choice
            fox_dmg = apply_chance_and_choice(player, 5)
            enemy["hp"] = max(0, enemy["hp"] - fox_dmg)
            _msg(f"Foxfire Band — a foxfire clone takes the blow! {enemy['name']} burns for {fox_dmg} damage!")
            if bonded:
                from combat.status_effects import check_status_resisted
                if not check_status_resisted(enemy):
                    enemy.setdefault("active_debuffs", []).append({
                        "type": "blind", "remaining": 1
                    })
                    enemy["blinded"] = True
                    _msg(f"Foxfire Band — {enemy['name']} is blinded by the foxfire!")
            return True
    return False


# ── Inititiative Bonus (applied to roll) ───────────────────────────────────

def apply_wedding_initiative_bonus(player):
    """Return the party's flat initiative bonus from the active wedding item."""
    special, bonded = _active(player)
    if not special:
        return 0
    # rabbit_time — the whole party rolls a beat sooner (read by
    # combat_engine.roll_initiative on every round's roll)
    if special == "rabbit_time":
        return 3 if bonded else 2
    # tailwind bonded is handled as a combat-start buff, not here
    return 0


# ── Soulbound check ────────────────────────────────────────────────────────

def is_wedding_item_soulbound(item):
    """Return True if the item is a soulbound wedding accessory."""
    return bool(item and item.get("id", "").startswith("wedding_"))


# ── Stat multiplier from cosmic_gravity ────────────────────────────────────

def apply_wedding_stat_multiplier(player, attr_name, base_value):
    """Return modified stat value after wedding percentage bonuses."""
    special, bonded = _active(player)
    if not special or special != "cosmic_gravity":
        return base_value
    # Only active when married girl is in party (is_bonded handles this for base effect)
    # But the base effect (+8%) also requires the girl to be in party
    # is_bonded already checks this, so if special is active, the girl is in party
    pct = 0.12 if bonded else 0.08
    return int(base_value * (1 + pct))


# ── Effect blurbs (round-1 combat reminder) ────────────────────────────────
# One-line, honest summaries of each special's ACTIVE effect, used by the
# round-1 reminder line in combat_engine. The bonded text states the upgraded
# version. Mirrors docs/wedding_item_design.md; the extra roster covers items
# added after the original 46. If a special is missing here, the reminder is
# skipped rather than advertising an effect we cannot describe.

_WEDDING_BLURBS = {
    # ── Tier 1 (early companions) ──
    "goblin_luck": ("25% chance of 5–15 bonus gold after each victory",
                    "50% chance of 5–15 bonus gold after each victory"),
    "tailwind": ("+8% dodge",
                 "+8% dodge; the party gains +1 initiative at combat start"),
    "bloom_regen": ("regenerate 3 HP at the end of each round",
                    "regenerate 5 HP and cleanse a poison stack each round"),
    "tinkerers_inspiration": ("20% chance for skills to skip their cooldown",
                              "40% chance for skills to skip their cooldown"),
    "bark_shield": ("once per floor, survive a fatal blow at 1 HP (+3 damage reduction, 4 turns)",
                    "the survival trigger refreshes every 5 rooms"),
    "spectral_dodge": ("+10% dodge",
                       "+10% dodge; dodging heals you 5 HP"),
    "stampede": ("first attack each combat deals +5 damage",
                 "first attack deals +5 and has a 25% chance to stun for 1 turn"),
    "moth_dust": ("attacks have a 20% chance to blind for 2 turns",
                  "blinds last 3 turns and reduce enemy DEX by 1"),
    "slime_absorb": ("absorb 15% of elemental damage taken as healing",
                     "absorb 25% and share 10% of the healing with the married girl"),
    "coil_bind": ("attacks have a 25% chance to slow for 2 turns",
                  "slowed enemies take +2 damage from all sources"),
    "regal_presence": ("+15% capture chance",
                       "+15% capture chance; captured girls start with +10 affection"),
    "mimic_jackpot": ("20% chance after combat to duplicate a consumable",
                      "also a 10% chance to find a random gift item"),
    "shadow_cloak": ("enemies suffer −12% accuracy against you",
                     "start combat with 2 turns invisible — enemies target allies first"),
    "frost_aura": ("attacks have a 20% chance to freeze for 1 turn",
                   "freeze chance 35%; frozen enemies take +20% from the next hit"),

    # ── Tier 2 (mid-game companions) ──
    "bull_rush": ("+4 damage while above 70% HP",
                  "+6 damage while above 50% HP"),
    "stone_endurance": ("take 2 less damage from all sources",
                        "take 4 less damage and become immune to stun"),
    "blood_drain": ("heal 15% of damage dealt",
                    "heal 25%; excess healing becomes a 3-turn heal-over-time"),
    "blizzard_song": ("+3 ice damage per attack; 20% chance to slow for 2 turns",
                      "slowed enemies have a 15% chance to freeze instead"),
    "war_sister": ("+3 damage while 2 or more allies are in the party",
                   "+5 damage and +1 STR to all allies"),
    "keening_wail": ("below 25% HP: all enemies take 10–20 damage (30% fear chance)",
                     "triggers below 35% HP; 15–30 damage"),
    "neko_shadow": ("+12% dodge",
                    "dodging counter-attacks for 50% of a normal hit"),
    "silk_bind": ("attacks have a 25% chance to reduce enemy DEX by 2 for 3 turns",
                  "webbed enemies also lose 20% dodge"),
    "pharaohs_curse": ("attackers take 4 retaliation damage",
                       "retaliation becomes 8; attackers suffer −10% accuracy"),
    "oni_rage": ("+5 damage while below 50% HP",
                 "below 50% HP: also +2 STR and +2 CON"),
    "flame_dance": ("30% chance to inflict Burn for 3 turns",
                    "Burn becomes Blaze and spreads to a second enemy"),
    "dream_drain": ("20% chance to inflict dread for 2 turns",
                    "dreaded enemies miss 40% of attacks instead of 25%"),
    "headless_oath": ("immune to fear and dread",
                      "defeating an enemy heals all allies 10 HP"),
    "foxfire_trick": ("20% chance when attacked: a foxfire clone blocks it and burns the attacker for 5",
                      "35% chance, and it blinds the attacker for 1 turn"),
    "siren_song": ("attacks have a 20% chance to charm (stun) for 1 turn",
                   "charm lasts 2 turns and reduces enemy WIS by 2"),
    "crimson_feast": ("defeating an enemy heals 15% of max HP",
                      "heals 25% and grants +2 CHA for 3 turns"),
    "whip_crack": ("25% chance to reduce enemy armor by 3 for 3 turns",
                   "vulnerable enemies also lose 2 DEX"),
    "arena_glory": ("+5 damage against bosses",
                    "+8 against bosses and −2 damage taken from them"),

    # ── Tier 3 (late-game & legendary companions) ──
    "matriarchs_embrace": ("+10% max HP",
                           "allies gain +5% max HP and regenerate 2 HP/turn"),
    "champion_charge": ("first attack deals +8 damage and gains +15% accuracy",
                        "first attack deals +12 and ignores 50% armor"),
    "infernal_crown": ("+15% fire and dark damage; melee attackers catch Burn",
                       "their Burn becomes Blaze and inflicts 1-turn dread"),
    "abyssal_grasp": ("30% chance to reduce enemy DEX by 3 for 3 turns",
                      "bound enemies are slowed and take 3 water damage per turn"),
    "stone_gaze": ("20% chance to petrify (−3 STR/DEX for 3 turns)",
                   "petrified enemies have a 15% chance to be stunned instead"),
    "legendary_flame": ("attacks leave a 3-turn Burn",
                        "Burn becomes Blaze and spreads to all enemies"),
    "tidal_blessing": ("heal 15% of damage dealt",
                       "heal 25%; at combat start all enemies take 5 water damage"),
    "dragon_judgment": ("+10% damage vs beasts, fey, dragons, and fliers",
                        "+15% damage and ignores 30% of their elemental resistance"),
    "riddle_solved": ("+8 damage to enemies that haven't acted yet",
                      "+12 damage and silences the target for 1 turn"),
    "lich_grasp": ("25% chance to curse (−2 to all enemy stats for 3 turns)",
                   "cursed enemies take 5 dark/turn and cannot heal"),
    "valkyrie_ride": ("+10% damage while at full HP",
                      "allies also gain +5% damage while you're at full HP"),
    "starfire_breath": ("attacks deal bonus damage equal to 20% of your CHA",
                        "35% of your CHA, and attacks inflict a 3-turn Burn"),
    "brood_swarm": ("25% chance: spiderlings deal +6 and poison for 3 turns (4/turn)",
                    "poison becomes 8/turn and stings −2 DEX"),
    "cosmic_gravity": ("+8% to all stats while the married girl is in the party",
                       "+12% to all stats; steal 1 enemy buff on your first hit"),

    # ── Extra roster (later additions beyond the original 46) ──
    "overclock": ("first attack deals +10 damage",
                  "first attack +15 and ignores 25% armor; 30% chance to refresh a skill cooldown"),
    "blood_fury": ("+6 damage while below 50% HP",
                   "below 70% HP: +8 damage, +2 STR and +2 CON"),
    "dusk_weave": ("+8% dodge; 25% chance to blind for 2 turns",
                   "+12% dodge; 35% chance to blind for 3 turns and slow"),
    "star_waltz": ("+10% dodge; dodging counters for 50%",
                   "+15% dodge; counters for 60% and grants +2 DEX for 2 turns"),
    "auto_guard": ("regenerate 2 HP each round; take 3 less damage",
                   "regenerate 3 HP; take 5 less and gain +3 CON for 3 turns at start"),
    "seraph_light": ("+5% damage per living ally; heal 4 HP each round",
                     "+8% per ally; heal 6 and cleanse a debuff each round"),
    "stone_ward": ("take 2 less physical damage",
                   "take 4 less physical damage and become immune to stun"),
    "dragon_heart": ("+10% fire damage; 30% chance to inflict Burn for 3 turns",
                     "+15% fire; Burn becomes Blaze and spreads"),
    "infernal_vow": ("+8% fire and dark damage; 25% chance to inflict Burn",
                     "+12%; 35% chance to inflict Blaze and dread"),
    "grave_reign": ("at combat start, all enemies take 3 dark damage",
                    "all enemies take 5 dark damage"),
    "palettes_palette": ("no effect unless Palette is in the active party",
                         "exhibit strokes unlock early and hit harder"),

    # ── Wonderland heroines (2026-10-14) ──
    "homeward_locket": ("below 35% HP: a hearth-light restores 20% max HP (once per combat)",
                        "restores 30% max HP and shares 5% with every living ally"),
    "rabbit_time": ("your party gains +2 initiative on every round's roll",
                    "your party gains +3 initiative on every round's roll"),
    "huntsman_oath": ("first attack each combat deals +30% damage",
                      "first attack deals +45% damage"),
}


def wedding_special_blurb(special, bonded=False):
    """Human-readable effect of a wedding special, or "" if unknown.

    Unknown specials return "" — callers should skip the reminder rather
    than advertise an effect that cannot be described (2026-10-04).
    """
    entry = _WEDDING_BLURBS.get(special)
    if not entry:
        return ""
    return entry[1] if bonded else entry[0]
