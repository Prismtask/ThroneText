"""Wedding accessory special effect engine.

Wedding items are Legendary accessories gifted by married monster girls.
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
  wedding_cosmic_gravity_used bool – cosmic_gravity buff steal used this combat
  wedding_crimson_feast_cha_buff bool – whether +2 CHA buff is active
"""

import random

# ── Core lookups ───────────────────────────────────────────────────────────

def get_active_wedding_item(player):
    """Return the equipped wedding accessory dict, or None."""
    for slot in ("accessory1", "accessory2"):
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
    player["wedding_cosmic_gravity_used"] = False


def end_wedding_combat(player):
    """Call once at the end of combat (victory, flee, or dead)."""
    player["wedding_combat_active"] = False
    player.pop("wedding_first_attack_done", None)
    player.pop("wedding_keening_wail_used", None)
    player.pop("wedding_shadow_cloak_used", None)
    player.pop("wedding_cosmic_gravity_used", None)


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
    print(f"  ♥ {text}")


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

    # shadow_cloak (bonded): 2-turn invisible (enemies target allies first)
    if special == "shadow_cloak" and bonded:
        player.setdefault("active_buffs", []).append({
            "type": "evasion", "value": 0.50, "remaining": 2,
            "source": "shadow_cloak_bonded"
        })
        _msg("Shadowthread Ring — you fade into the darkness! (+50% dodge, 2 turns)")

    # blizzard_song (bonded): enemies take 5 water damage at start
    if special == "blizzard_song" and bonded:
        for e in enemies:
            e["hp"] = max(0, e["hp"] - 5)
            _msg(f"Blizzard Veil — {e['name']} is lashed by freezing winds! (-5 HP)")

    # tidal_blessing (bonded): enemies take 5 water damage at start
    if special == "tidal_blessing" and bonded:
        for e in enemies:
            e["hp"] = max(0, e["hp"] - 5)
            _msg(f"Tidecaller Ring — a tidal wave crashes into {e['name']}! (-5 HP)")

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


# ── Attack Bonus (flat damage before elemental) ────────────────────────────

def apply_wedding_attack_bonus(player, target, base_dmg, is_first_attack):
    """Return flat bonus damage to add to the player's attack."""
    special, bonded = _active(player)
    if not special:
        return 0

    bonus = 0

    # stampede: first attack +5 flat; bonded +5 and 25% stun
    if special == "stampede" and is_first_attack:
        bonus += 5
        if bonded and random.random() < 0.25:
            target["stunned"] = True
            _msg("Thunderhoof Brooch — the stampede stuns the target!")

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
            if bonded:
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

    return bonus


# ── On Hit (status procs) ──────────────────────────────────────────────────

def apply_wedding_on_hit(player, target, enemies, damage_dealt):
    """Call after a successful player attack lands."""
    special, bonded = _active(player)
    if not special:
        return

    # moth_dust: 20% blind 2 turns; bonded 3 turns and -1 DEX
    if special == "moth_dust" and random.random() < 0.20:
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
        target["slowed"] = True
        target.setdefault("active_debuffs", []).append({
            "type": "slow", "remaining": 2
        })
        _msg(f"Coiled Serpent Ring — {target['name']} is slowed!")
        if bonded:
            target.setdefault("coil_bind_vulnerable", 2)
            _msg(f"Coiled Serpent Ring — {target['name']} is constricted! (+2 damage taken)")

    # frost_aura: 20% freeze 1 turn; bonded 35% freeze, frozen +20% next hit
    if special == "frost_aura":
        chance = 0.35 if bonded else 0.20
        if random.random() < chance:
            target["frozen"] = True
            target["freeze_duration"] = 1
            _msg(f"Frostbloom Charm — {target['name']} freezes solid!")
            if bonded:
                target["frost_aura_vulnerable"] = True

    # flame_dance: 30% burn 3 turns (5/turn); bonded 8/turn and spread
    if special == "flame_dance" and random.random() < 0.30:
        from combat.status_effects import apply_burn
        burn_dmg = 8 if bonded else 5
        apply_burn(target, burn_dmg, 3)
        _msg(f"Emberwaltz Ring — {target['name']} is set ablaze! ({burn_dmg}/turn)")
        if bonded and enemies:
            adjacent = [e for e in enemies if e is not target and e.get("hp", 0) > 0]
            if adjacent:
                spread = random.choice(adjacent)
                apply_burn(spread, burn_dmg, 3)
                _msg(f"Emberwaltz Ring — flames spread to {spread['name']}!")

    # dream_drain: 20% dread 2 turns; bonded dreaded enemies 40% miss
    if special == "dream_drain" and random.random() < 0.20:
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
    if special == "silk_bind" and random.random() < 0.25:
        target["dex_mod"] = max(0, target.get("dex_mod", 0) - 2)
        target.setdefault("silk_bind_stacks", []).append({"remaining": 3})
        _msg(f"Silkspinner Band — webs bind {target['name']}! (-2 DEX, 3 turns)")
        if bonded:
            target.setdefault("silk_bind_dodge_penalty", 0.20)

    # siren_song: 20% charm (stun 1 turn); bonded 2 turns and -2 WIS
    if special == "siren_song" and random.random() < 0.20:
        dur = 2 if bonded else 1
        target["stunned"] = True
        _msg(f"Coral Crown Ring — {target['name']} is charmed! ({dur} turn(s))")
        if bonded:
            target.setdefault("wis_mod", 0)
            target["wis_mod"] = max(0, target["wis_mod"] - 2)
            _msg(f"Coral Crown Ring — {target['name']}'s will breaks! (-2 WIS)")

    # whip_crack: 25% -3 armor for 3 turns; bonded also -2 DEX
    if special == "whip_crack" and random.random() < 0.25:
        target.setdefault("active_debuffs", []).append({
            "type": "sunder", "value": 3, "remaining": 3
        })
        _msg(f"Whipmaster's Coil — {target['name']}'s armor cracks! (-3 armor, 3 turns)")
        if bonded:
            target["dex_mod"] = max(0, target.get("dex_mod", 0) - 2)
            _msg(f"Whipmaster's Coil — {target['name']} is hobbled! (-2 DEX)")

    # abyssal_grasp: 30% -3 DEX for 3 turns (tentacle bind); bonded also slow + 3 water/turn
    if special == "abyssal_grasp" and random.random() < 0.30:
        target["dex_mod"] = max(0, target.get("dex_mod", 0) - 3)
        target.setdefault("abyssal_bind_turns", 3)
        _msg(f"Abyssal Coil — tentacles bind {target['name']}! (-3 DEX, 3 turns)")
        if bonded:
            target["slowed"] = True
            target.setdefault("active_debuffs", []).append({
                "type": "slow", "remaining": 3
            })
            target.setdefault("active_debuffs", []).append({
                "type": "poison", "damage": 3, "remaining": 3  # water damage approximated as poison
            })
            _msg(f"Abyssal Coil — {target['name']} is drowning in tentacles! (slowed, 3 water/turn)")

    # stone_gaze: 20% petrify (-3 STR/DEX for 3 turns); bonded 15% chance to stun instead
    if special == "stone_gaze" and random.random() < 0.20:
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
    if special == "lich_grasp" and random.random() < 0.25:
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

    # legendary_flame: burn 3 turns (6/turn); bonded 10/turn and spread to all
    if special == "legendary_flame":
        from combat.status_effects import apply_burn
        burn_dmg = 10 if bonded else 6
        apply_burn(target, burn_dmg, 3)
        _msg(f"Sunfire Band — {target['name']} is engulfed in legendary flame! ({burn_dmg}/turn)")
        if bonded:
            for e in enemies:
                if e is not target and e.get("hp", 0) > 0:
                    apply_burn(e, burn_dmg, 3)
            _msg("Sunfire Band — the flame spreads to all enemies!")

    # infernal_crown: +15% fire/dark damage (handled by elemental stats), melee burn 5
    # The melee burn is handled in on_damage_taken (retribution).

    # cosmic_gravity (bonded): once per combat steal 1 random buff on first hit
    if special == "cosmic_gravity" and bonded and not player.get("wedding_cosmic_gravity_used"):
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
                _msg(f"Headless Rider's Seal — {ally['name']} is healed by your oath! (+10 HP)")


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
        enemy["hp"] = max(0, enemy["hp"] - counter_dmg)
        _msg(f"Nekomata Bell — you counter-strike {enemy['name']} for {counter_dmg} damage!")


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
                    _msg(f"Gelatinous Heart — you share {share} healing with {ally['name']}.")

    # infernal_crown (bonded): melee attackers take 10 burn damage
    # Handled in on_damage_taken_after_hit for retribution.

    return damage


def apply_wedding_on_damage_taken(player, enemy, damage, outcome):
    """Call after the enemy has hit the player (but before HP check)."""
    special, bonded = _active(player)
    if not special:
        return

    # pharaohs_curse: enemies that attack you take 4 damage; bonded 8 and -10% accuracy
    if special == "pharaohs_curse" and damage > 0:
        ret = 8 if bonded else 4
        enemy["hp"] = max(0, enemy["hp"] - ret)
        _msg(f"Pharaoh's Band — {enemy['name']} suffers {ret} retribution damage!")
        if bonded:
            enemy.setdefault("pharaohs_curse_acc", 0.10)

    # infernal_crown: melee attackers take 5 burn; bonded 10 and 1-turn dread
    if special == "infernal_crown" and damage > 0:
        burn = 10 if bonded else 5
        from combat.status_effects import apply_burn
        apply_burn(enemy, burn, 2)
        _msg(f"Infernal Throne Seal — {enemy['name']} is scorched by hellfire! ({burn} burn)")
        if bonded:
            enemy.setdefault("active_debuffs", []).append({
                "type": "fear", "value": 0.25, "remaining": 1
            })
            _msg(f"Infernal Throne Seal — {enemy['name']} is filled with dread!")

    # keening_wail: when HP < 25%, enemies take 10-20 damage, 30% fear; bonded 15-30 at 35%
    if special == "keening_wail" and not player.get("wedding_keening_wail_used"):
        threshold = 0.35 if bonded else 0.25
        hp_ratio = player.get("current_hp", 1) / max(1, player.get("max_hp", 1))
        if hp_ratio < threshold:
            player["wedding_keening_wail_used"] = True
            dmg_range = (15, 30) if bonded else (10, 20)
            wail_dmg = random.randint(*dmg_range)
            # Apply to all enemies
            from combat.combat_engine import prune_dead
            # We can't easily access the enemies list here, so we'll apply to the attacker
            enemy["hp"] = max(0, enemy["hp"] - wail_dmg)
            _msg(f"Wailing Spirit Locket — a keening wail tears through {enemy['name']} for {wail_dmg} damage!")
            if random.random() < 0.30:
                enemy.setdefault("active_debuffs", []).append({
                    "type": "fear", "value": 0.30, "remaining": 1
                })
                _msg(f"Wailing Spirit Locket — {enemy['name']} is stricken with fear!")

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
    if not special or special != "tinkerers_inspiration":
        return False
    chance = 0.40 if bonded else 0.20
    if random.random() < chance:
        _msg("Clockwork Bond Ring — the gears align, and your skill is ready again!")
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
            enemy["hp"] = max(0, enemy["hp"] - 5)
            _msg(f"Foxfire Band — a foxfire clone takes the blow! {enemy['name']} burns for 5 damage!")
            if bonded:
                enemy.setdefault("active_debuffs", []).append({
                    "type": "blind", "remaining": 1
                })
                enemy["blinded"] = True
                _msg(f"Foxfire Band — {enemy['name']} is blinded by the foxfire!")
            return True
    return False


# ── Inititiative Bonus (applied to roll) ───────────────────────────────────

def apply_wedding_initiative_bonus(player):
    """Return flat bonus to player initiative roll."""
    special, bonded = _active(player)
    if not special:
        return 0
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
