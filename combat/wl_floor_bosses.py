"""
combat/wl_floor_bosses.py — Wonderland Floor Boss AI Patterns (Phase 19)

Each of the 20 regular floor bosses (every even floor that isn't a multiple
of 10) has a unique combat AI function. These bosses are encountered in
room 10 of their respective floors.

Floor → Boss mapping:
    F2:   White Rabbit          F4:   Cheshire Cat
    F6:   Card Knight           F8:   Dormouse Captain
    F12:  Peter Pan             F14:  Tick-Tock Crocodile
    F16:  Pirate Captain James  F18:  Tin Woodsman Captain
    F22:  Mr. Hyde              F24:  Professor Moriarty
    F26:  Dracula's Bride       F28:  Phantom of the Opera
    F32:  Captain Hook          F34:  The Red Queen
    F36:  The Scarecrow King    F38:  Bandersnatch Alpha
    F42:  The Wizard of Oz      F44:  Headless Horseman
    F46:  The Snow Queen        F48:  The Nothing
"""

import random
from combat.combat_io import c_print, c_input, c_clear
from combat.status_effects import (
    apply_bleed, apply_blind, apply_curse,
    apply_dread, apply_freeze, apply_silence,
    apply_weaken, apply_drain,
    apply_burn, apply_poison,
)
from combat.elemental import ELEMENTS, calculate_elemental_damage


# ── Inline helpers for effects not in status_effects ──────────────

def _apply_confusion(player, duration=2):
    """Apply confusion to a player."""
    for debuff in player.get("active_debuffs", []):
        if debuff.get("type") == "confusion":
            debuff["remaining"] = max(debuff.get("remaining", 0), duration)
            return "refreshed"
    player.setdefault("active_debuffs", []).append(
        {"type": "confusion", "value": 0.30, "remaining": duration}
    )
    return "applied"


def _apply_fear(player, duration=2, value=0.25):
    """Apply fear to a player."""
    for debuff in player.get("active_debuffs", []):
        if debuff.get("type") == "fear":
            debuff["remaining"] = max(debuff.get("remaining", 0), duration)
            return "refreshed"
    player.setdefault("active_debuffs", []).append(
        {"type": "fear", "value": value, "remaining": duration}
    )
    return "applied"


def _apply_sleep(player, duration=2):
    """Apply sleep to a player (skip turns)."""
    player["asleep"] = True
    player["sleep_duration"] = duration
    return "applied"


def _apply_stun(player, duration=1):
    """Apply stun to a player (skip 1 turn)."""
    player["stunned"] = True
    return "applied"


def _apply_vulnerable(player, duration=2, value=0.25):
    """Apply vulnerable debuff."""
    for debuff in player.get("active_debuffs", []):
        if debuff.get("type") == "vulnerable":
            debuff["remaining"] = max(debuff.get("remaining", 0), duration)
            return "refreshed"
    player.setdefault("active_debuffs", []).append(
        {"type": "vulnerable", "value": value, "remaining": duration}
    )
    return "applied"


# ═══════════════════════════════════════════════════════════════════════
# AI Helper — extra logic injector for enemy_ai
# ═══════════════════════════════════════════════════════════════════════

def _wl_boss_extra_logic(enemy, player, dmg, boss_ai_fn):
    """Wrap a floor boss AI as an extra_logic callback for enemy_ai."""
    return boss_ai_fn(enemy, player, dmg)


# ═══════════════════════════════════════════════════════════════════════
# F2: White Rabbit — "I'm Late!"
# ═══════════════════════════════════════════════════════════════════════

def white_rabbit_ai(enemy, player, dmg):
    """High speed, flees at low HP. Panicked movements cause self-buffs."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # If below 25% HP, try to flee
    if hp_pct < 0.25 and random.random() < 0.50:
        c_print(f"\n  The {enemy['name']} glances at its watch in horror!"
                 f"\n  'I'm late, I'm late!' — it vanishes down a rabbit hole!")
        enemy["hp"] = 0
        return "The White Rabbit has fled the battle!"

    # Panicked haste: buffs own speed when threatened
    if hp_pct < 0.60 and random.random() < 0.35:
        enemy["dex_mod"] = enemy.get("dex_mod", 0) + 2
        c_print(f"\n  The {enemy['name']} moves in a panicked blur — its speed increases!")

    # Time Warp: small chance to act twice
    if random.random() < 0.15:
        enemy["_wl_extra_action"] = True

    return None


# ═══════════════════════════════════════════════════════════════════════
# F4: Cheshire Cat — "We're All Mad Here"
# ═══════════════════════════════════════════════════════════════════════

def cheshire_cat_ai(enemy, player, dmg):
    """Phases in and out, applying confusion. Hard to pin down."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Phase shift: chance to evade attacks entirely
    if random.random() < 0.25:
        enemy["_wl_phased"] = True
        c_print(f"\n  The {enemy['name']}'s body fades, leaving only its grin."
                 f"\n  'You can't hit what isn't all there.'")

    # Confusing grin
    if dmg > 0 and random.random() < 0.30:
        result = _apply_confusion(player, duration=2)
        if result == "applied":
            return (f"The {enemy['name']}'s grin twists reality — "
                    f"{player['name']} is confused for 2 turns!")

    # Vanishes at low HP — but it was never really there
    if hp_pct < 0.15 and random.random() < 0.40:
        c_print(f"\n  The grin lingers for a moment. Then it, too, fades."
                 f"\n  'We're all mad here. I'm mad. You're mad.'")
        enemy["hp"] = 0
        return "The Cheshire Cat has vanished — or was it ever here?"

    return None


# ═══════════════════════════════════════════════════════════════════════
# F6: Card Knight — "By Order of the Queen!"
# ═══════════════════════════════════════════════════════════════════════

def card_knight_ai(enemy, player, dmg):
    """Summons card soldier minions. Tanky with shield stance."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Summon card soldiers (once)
    if not enemy.get("_wl_summoned") and hp_pct < 0.70:
        enemy["_wl_summoned"] = True
        c_print(f"\n  The {enemy['name']} raises its blade!"
                 f"\n  'To arms! Soldiers of the Queen — form ranks!'")
        # Summon 2 card soldiers
        enemy["_wl_minions"] = [
            {"name": "Card Soldier", "hp": 12, "max_hp": 12,
             "str_mod": 2, "con_mod": 2, "dex_mod": 1,
             "elemental_res": {}, "elemental_dmg": {},
             "active_debuffs": [], "active_buffs": [],
             "key": "wl_card_soldier_2", "level": 6},
            {"name": "Card Soldier", "hp": 12, "max_hp": 12,
             "str_mod": 2, "con_mod": 2, "dex_mod": 1,
             "elemental_res": {}, "elemental_dmg": {},
             "active_debuffs": [], "active_buffs": [],
             "key": "wl_card_soldier_2", "level": 6},
        ]
        c_print("  Two Card Soldiers march onto the field!")

    # Shield stance: reduces incoming damage
    if hp_pct < 0.40 and random.random() < 0.30:
        if not any(b.get("type") == "defense" for b in enemy.get("active_buffs", [])):
            enemy.setdefault("active_buffs", []).append(
                {"type": "defense", "value": 3, "remaining": 3, "name": "Card Shield"}
            )
            c_print(f"\n  The {enemy['name']} assumes a defensive stance with its card-shield!")

    # Bleed on hit
    if dmg > 0 and random.random() < 0.25:
        apply_bleed(player, damage=max(2, dmg // 4), duration=3)
        return f"The {enemy['name']}'s paper-thin blade draws blood!"

    return None


# ═══════════════════════════════════════════════════════════════════════
# F8: Dormouse Captain — "Tea Party Offensive"
# ═══════════════════════════════════════════════════════════════════════

def dormouse_captain_ai(enemy, player, dmg):
    """Sleep-inducing AoE attacks and tea-themed abilities."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Scalding Tea — AoE fire damage
    if random.random() < 0.25:
        dmg_val = random.randint(4, 10) + enemy.get("wis_mod", 2)
        c_print(f"\n  The {enemy['name']} hurls a pot of scalding tea!"
                 f"\n  It deals {dmg_val} fire damage!")
        # Apply as extra damage through element system
        player["current_hp"] -= max(0, dmg_val - player.get("con_mod", 0) // 2)
        return "The scalding tea burns!"

    # Sleep-inducing murmur
    if random.random() < 0.30:
        result = _apply_sleep(player, duration=2)
        if result == "applied":
            return (f"The {enemy['name']} murmurs about treacle and buttered toast..."
                    f"\n  {player['name']} grows drowsy!")

    # Dormouse Rage — at low HP, wakes up angry
    if hp_pct < 0.30 and not enemy.get("_wl_enraged"):
        enemy["_wl_enraged"] = True
        enemy["str_mod"] = enemy.get("str_mod", 0) + 4
        c_print(f"\n  The {enemy['name']} snaps awake — and it is FURIOUS!"
                 f"\n  Its strength surges!")

    return None


# ═══════════════════════════════════════════════════════════════════════
# F12: Peter Pan — "Never Grow Up"
# ═══════════════════════════════════════════════════════════════════════

def peter_pan_ai(enemy, player, dmg):
    """Never ages — heals per turn. Flight gives high evasion."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Eternal Youth: heal per turn
    heal = max(1, enemy["max_hp"] // 15)
    enemy["hp"] = min(enemy["max_hp"], enemy["hp"] + heal)
    if random.random() < 0.40:
        c_print(f"\n  The {enemy['name']} laughs — 'I'll never grow up!'"
                 f"\n  He recovers {heal} HP from eternal youth.")

    # Pixie Dust Diversion: blinds
    if random.random() < 0.25:
        result = apply_blind(player, duration=1)
        if result == "applied":
            return (f"The {enemy['name']} throws pixie dust in {player['name']}'s eyes!"
                    f"\n  {player['name']} is blinded!")

    # Crow's Call: summon shadow (once)
    if hp_pct < 0.50 and not enemy.get("_wl_crowed"):
        enemy["_wl_crowed"] = True
        c_print(f"\n  The {enemy['name']} crows triumphantly!"
                 f"\n  His shadow detaches and joins the fight!")
        enemy["_wl_minions"] = [
            {"name": "Peter's Shadow", "hp": 15, "max_hp": 15,
             "str_mod": 3, "con_mod": 2, "dex_mod": 5,
             "elemental_res": {"light": 0.5, "dark": 1.5},
             "elemental_dmg": {"dark": 1.3},
             "active_debuffs": [], "active_buffs": [],
             "key": "_wl_shadow", "level": 12},
        ]

    return None


# ═══════════════════════════════════════════════════════════════════════
# F14: Tick-Tock Crocodile — "The Clock is Ticking"
# ═══════════════════════════════════════════════════════════════════════

def ticktock_croc_ai(enemy, player, dmg):
    """Swallow attack, ticking countdown telegraph."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Ticking Countdown — warns of big attack
    count = enemy.get("_wl_tick", 0) + 1
    enemy["_wl_tick"] = count

    if count >= 3:
        enemy["_wl_tick"] = 0
        big_dmg = random.randint(10, 18) + enemy.get("str_mod", 0)
        c_print(f"\n  The clock inside the {enemy['name']} STRIKES!"
                 f"\n  It deals {big_dmg} thunder damage!")
        player["current_hp"] -= max(0, big_dmg - player.get("con_mod", 0) // 2)
        return "The tick-tock crescendo hits with a deafening CLANG!"
    else:
        ticks_left = 3 - count
        c_print(f"\n  Tick... ({ticks_left} turns until the clock strikes)")

    # Swallow: devour attempt
    if random.random() < 0.15:
        dmg_val = random.randint(8, 14) + enemy.get("str_mod", 0)
        c_print(f"\n  The {enemy['name']} tries to swallow {player['name']} whole!"
                 f"\n  It deals {dmg_val} damage!")
        player["current_hp"] -= max(0, dmg_val - player.get("con_mod", 0) // 2)
        _apply_fear(player, duration=1)
        return "The crocodile's jaws snap shut!"

    return None


# ═══════════════════════════════════════════════════════════════════════
# F16: Pirate Captain James — "Dead Men Tell No Tales"
# ═══════════════════════════════════════════════════════════════════════

def pirate_captain_james_ai(enemy, player, dmg):
    """Ghost pirate — summons crew, curse chance."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Summon ghost crew (once)
    if not enemy.get("_wl_summoned") and hp_pct < 0.70:
        enemy["_wl_summoned"] = True
        c_print(f"\n  The {enemy['name']} raises his spectral cutlass!"
                 f"\n  'Avast, ye souls! To me, me hearties!'")
        enemy["_wl_minions"] = [
            {"name": "Pirate Shade", "hp": 18, "max_hp": 18,
             "str_mod": 3, "con_mod": 2, "dex_mod": 3,
             "elemental_res": {"light": 0.7, "dark": 1.3},
             "elemental_dmg": {"dark": 1.2},
             "active_debuffs": [], "active_buffs": [],
             "key": "wl_pirate_shade", "level": 14},
        ]
        c_print("  A spectral crewmate rises from the depths!")

    # Ghostly curse
    if dmg > 0 and random.random() < 0.25:
        result = apply_curse(player)
        if result == "applied":
            return (f"The {enemy['name']}'s cursed blade withers {player['name']}'s spirit!"
                    f"\n  All attributes reduced!")

    # Ethereal: chance to phase through attacks
    if hp_pct < 0.30:
        enemy["_wl_phased"] = True
        if random.random() < 0.40:
            c_print(f"\n  The {enemy['name']} becomes translucent — your attacks pass through!")

    return None


# ═══════════════════════════════════════════════════════════════════════
# F18: Tin Woodsman Captain — "If I Only Had a Heart"
# ═══════════════════════════════════════════════════════════════════════

def tin_woodsman_capt_ai(enemy, player, dmg):
    """Axe cleave, self-buff. Gains power from allies' buffs."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Rusted Resilience: self-buff
    if random.random() < 0.30:
        enemy["str_mod"] = enemy.get("str_mod", 0) + 1
        enemy.setdefault("active_buffs", []).append(
            {"type": "strength_up", "value": 2, "remaining": 3, "name": "Heart's Resolve"}
        )
        c_print(f"\n  The {enemy['name']} clangs its chest — 'I may be hollow,"
                 f"\n  but I still STAND!' Its strength grows.")

    # Axe Cleave: hits harder
    if random.random() < 0.20:
        extra = enemy.get("str_mod", 0)
        apply_bleed(player, damage=max(2, extra), duration=3)
        return (f"The {enemy['name']}'s axe cleaves deep!"
                f"\n  {player['name']} bleeds from the wound!")

    # Oil Can: heal at low HP (once)
    if hp_pct < 0.25 and not enemy.get("_wl_oiled"):
        enemy["_wl_oiled"] = True
        heal = enemy["max_hp"] // 4
        enemy["hp"] = min(enemy["max_hp"], enemy["hp"] + heal)
        c_print(f"\n  The {enemy['name']} produces a small oil can..."
                 f"\n  It oils its joints and recovers {heal} HP!")

    return None


# ═══════════════════════════════════════════════════════════════════════
# F22: Mr. Hyde — "The Transformation"
# ═══════════════════════════════════════════════════════════════════════

def mr_hyde_ai(enemy, player, dmg):
    """Transforms mid-fight — becomes stronger at low HP."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Hyde Transformation: at 50% HP, transforms
    if hp_pct < 0.50 and not enemy.get("_wl_transformed"):
        enemy["_wl_transformed"] = True
        enemy["name"] = "Mr. Hyde (Unleashed)"
        enemy["str_mod"] = enemy.get("str_mod", 0) + 5
        enemy["max_hp"] = int(enemy["max_hp"] * 1.2)
        enemy["hp"] = enemy["max_hp"]
        c_print(f"\n  The doctor's form twists and swells!"
                 f"\n  'NOW you shall see what I truly am!'"
                 f"\n  Mr. Hyde is UNLEASHED! His HP and strength surge!")

    # Savage strike: high damage, self-damaging
    if enemy.get("_wl_transformed") and random.random() < 0.25:
        bonus = random.randint(4, 10)
        c_print(f"\n  Hyde lunges with savage fury dealing {bonus} bonus damage!")
        player["current_hp"] -= bonus
        # Self-damage from reckless attack
        self_dmg = bonus // 2
        enemy["hp"] -= self_dmg
        c_print(f"  But the reckless assault costs him {self_dmg} HP.")
        return "Hyde's savage strike connects!"

    return None


# ═══════════════════════════════════════════════════════════════════════
# F24: Professor Moriarty — "The Napoleon of Crime"
# ═══════════════════════════════════════════════════════════════════════

def professor_moriarty_ai(enemy, player, dmg):
    """Counters last-used skill. Analytical, predictive combat."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Counter-Strategy: analyze and weaken
    if random.random() < 0.30:
        c_print(f"\n  The {enemy['name']} studies your stance with cold precision..."
                 f"\n  'I have calculated every variable. You have already lost.'")
        # Debuff based on what he "analyzed"
        result = apply_weaken(player, str_penalty=2, duration=3)
        if result == "applied":
            return (f"Moriarty's analysis exposes your weaknesses!"
                    f"\n  {player['name']}'s strength is reduced!")

    # Calculated Strike: high accuracy, ignores some defense
    if random.random() < 0.20:
        bonus = enemy.get("ler_mod", 3)
        c_print(f"\n  Moriarty strikes with mathematical precision!"
                 f"\n  His attack pierces defenses! (+{bonus} damage)")
        player["current_hp"] -= bonus
        return "A calculated strike finds its mark!"

    # Criminal Network: summon henchman once
    if hp_pct < 0.40 and not enemy.get("_wl_summoned"):
        enemy["_wl_summoned"] = True
        c_print(f"\n  Moriarty snaps his fingers. 'A contingency, of course.'")
        enemy["_wl_minions"] = [
            {"name": "Hired Thug", "hp": 22, "max_hp": 22,
             "str_mod": 4, "con_mod": 3, "dex_mod": 2,
             "elemental_res": {}, "elemental_dmg": {},
             "active_debuffs": [], "active_buffs": [],
             "key": "_wl_thug", "level": 22},
        ]
        c_print("  A hired thug emerges from the shadows!")

    return None


# ═══════════════════════════════════════════════════════════════════════
# F26: Dracula's Bride — "Eternal Embrace"
# ═══════════════════════════════════════════════════════════════════════

def dracula_bride_ai(enemy, player, dmg):
    """Life drain, bat swarm summon, seductive charm."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Vampiric Drain
    if dmg > 0 and random.random() < 0.30:
        drained = apply_drain(player, enemy, drain_amount=max(2, dmg // 2))
        if drained > 0:
            return (f"The {enemy['name']} sinks her fangs into {player['name']}!"
                    f"\n  She drains {drained} HP!")

    # Bat Swarm: AoE damage
    if random.random() < 0.20:
        swarm = random.randint(6, 12)
        c_print(f"\n  The {enemy['name']} disperses into a swarm of bats!"
                 f"\n  The bats deal {swarm} damage!")
        player["current_hp"] -= max(0, swarm - player.get("con_mod", 0) // 2)
        apply_blind(player, duration=1)
        return "The bat swarm obscures your vision!"

    # Seductive Charm: confusion/debuff
    if random.random() < 0.20:
        result = _apply_confusion(player, duration=2)
        if result == "applied":
            return (f"The {enemy['name']}'s gaze is hypnotic..."
                    f"\n  {player['name']} is confused!")

    return None


# ═══════════════════════════════════════════════════════════════════════
# F28: Phantom of the Opera — "Music of the Night"
# ═══════════════════════════════════════════════════════════════════════

def phantom_opera_ai(enemy, player, dmg):
    """Invisible until attacking. Musical cues telegraph attacks."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Vanishes / phases
    if not enemy.get("_wl_visible"):
        enemy["_wl_visible"] = True
        c_print(f"\n  A haunting chord echoes through the darkness..."
                 f"\n  The {enemy['name']} materializes from shadow!")

    if random.random() < 0.25:
        enemy["_wl_visible"] = False
        c_print(f"\n  The {enemy['name']} wraps himself in shadow and silence."
                 f"\n  He becomes invisible!")

    # Dissonant Chord: thunder damage
    if random.random() < 0.20:
        chord = random.randint(8, 16) + enemy.get("cha_mod", 2)
        c_print(f"\n  The {enemy['name']} strikes a DISSONANT CHORD!"
                 f"\n  The sound wave deals {chord} thunder damage!")
        player["current_hp"] -= max(0, chord - player.get("con_mod", 0) // 2)
        apply_dread(player, duration=2)
        return "The terrible music shakes your soul!"

    # Chandelier Drop (once, at low HP)
    if hp_pct < 0.30 and not enemy.get("_wl_chandelier"):
        enemy["_wl_chandelier"] = True
        crash = random.randint(15, 25)
        c_print(f"\n  The chandelier CRASHES down!"
                 f"\n  It deals {crash} physical damage!")
        player["current_hp"] -= max(0, crash - player.get("con_mod", 0))
        return "The chandelier shatters around you!"

    return None


# ═══════════════════════════════════════════════════════════════════════
# F32: Captain Hook — "Bad Form!"
# ═══════════════════════════════════════════════════════════════════════

def captain_hook_ai(enemy, player, dmg):
    """Rapier & hook combo. Bleed on crit. Croc phobia."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Hook and Rapier combo
    if random.random() < 0.25:
        extra = random.randint(3, 8)
        apply_bleed(player, damage=max(2, extra), duration=3)
        c_print(f"\n  Hook slashes with both hook and rapier!"
                 f"\n  A flurry of strikes deals +{extra} damage!")
        player["current_hp"] -= extra
        return "Hook's twin blades draw blood!"

    # Crocodile Phobia — at half HP, Hook panics
    if hp_pct < 0.50 and not enemy.get("_wl_croc_phobia"):
        enemy["_wl_croc_phobia"] = True
        enemy["str_mod"] = enemy.get("str_mod", 0) - 2
        enemy["dex_mod"] = enemy.get("dex_mod", 0) + 2
        c_print(f"\n  Hook hears an imagined ticking... his face goes pale."
                 f"\n  'Not the crocodile! NOT THE CROCODILE!'"
                 f"\n  He fights more erratically — less power, more speed.")

    # "Bad form!" — counterattack
    if dmg > 0 and random.random() < 0.20:
        counter = random.randint(3, 6)
        c_print(f"\n  'Bad form, you cad!' Hook counters for {counter} damage!")
        player["current_hp"] -= counter
        return "Hook's riposte is swift!"

    return None


# ═══════════════════════════════════════════════════════════════════════
# F34: The Red Queen — "Off With Their Head!"
# ═══════════════════════════════════════════════════════════════════════

def red_queen_ai(enemy, player, dmg):
    """Speed chess — action economy. Tyrannical commands."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # "Off with their head!" — Execution attempt
    if random.random() < 0.15:
        execute = random.randint(10, 20)
        c_print(f"\n  'OFF WITH THEIR HEAD!' the Red Queen shrieks!"
                 f"\n  The executioner's axe deals {execute} damage!")
        player["current_hp"] -= max(0, execute - player.get("con_mod", 0) // 2)
        _apply_fear(player, duration=1)
        return "The Queen's decree is absolute!"

    # Speed Chess — extra action
    if random.random() < 0.30:
        enemy["_wl_extra_action"] = True
        c_print(f"\n  The Red Queen moves several pieces at once!"
                 f"\n  She'll act again immediately!")

    # "Painting the Roses Red" — buff allies/minions
    if enemy.get("_wl_minions"):
        for m in enemy["_wl_minions"]:
            m["str_mod"] = m.get("str_mod", 0) + 1
        c_print(f"\n  'Paint them RED!' The Queen's soldiers surge with fury!")

    return None


# ═══════════════════════════════════════════════════════════════════════
# F36: The Scarecrow King — "If I Only Had a Brain"
# ═══════════════════════════════════════════════════════════════════════

def scarecrow_king_ai(enemy, player, dmg):
    """Learns and adapts to your patterns. Gets smarter each turn."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Adaptive Learning: gains stats as the fight progresses
    learn_count = enemy.get("_wl_learned", 0) + 1
    enemy["_wl_learned"] = learn_count

    if learn_count % 3 == 0:
        enemy["ler_mod"] = enemy.get("ler_mod", 0) + 2
        enemy["wis_mod"] = enemy.get("wis_mod", 0) + 1
        c_print(f"\n  The Scarecrow King tilts its stuffed head..."
                 f"\n  'Ah, I see! I SEE! The pattern is clear!'"
                 f"\n  Its Learning and Wisdom increase!")

    # "If I only had a brain" — defense adaptation
    if learn_count >= 5 and not enemy.get("_wl_brain"):
        enemy["_wl_brain"] = True
        enemy["max_hp"] = int(enemy["max_hp"] * 1.3)
        enemy["hp"] = enemy["max_hp"]
        enemy["ler_mod"] = enemy.get("ler_mod", 0) + 4
        c_print(f"\n  'I... I UNDERSTAND!'"
                 f"\n  The Scarecrow King has found its brain!"
                 f"\n  Its HP and intellect surge dramatically!")

    # Straw Barrage: multi-hit
    if random.random() < 0.20:
        hits = random.randint(2, 4)
        total = 0
        for _ in range(hits):
            total += random.randint(2, 5)
        c_print(f"\n  The Scarecrow unleashes a straw barrage — {hits} hits for {total} damage!")
        player["current_hp"] -= max(0, total - player.get("con_mod", 0) // 2)
        return "The straw storm cuts deep!"

    return None


# ═══════════════════════════════════════════════════════════════════════
# F38: Bandersnatch Alpha — "Frumious Rage"
# ═══════════════════════════════════════════════════════════════════════

def bandersnatch_alpha_ai(enemy, player, dmg):
    """Frumious rage — gets stronger as HP drops. Berserker."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Frumious Rage: scales with missing HP
    missing_pct = 1.0 - hp_pct
    rage_bonus = int(missing_pct * 8)
    if rage_bonus > 0:
        enemy["str_mod"] = enemy.get("_wl_base_str", enemy.get("str_mod", 0)) + rage_bonus
        enemy.setdefault("_wl_base_str", enemy.get("str_mod", 0) - rage_bonus)

    if rage_bonus >= 3 and random.random() < 0.30:
        c_print(f"\n  The Bandersnatch's eyes glow with FRUMIOUS RAGE!"
                 f"\n  Its strength surges! (+{rage_bonus})")

    # Whiffling Charge: high damage, self-recoil
    if random.random() < 0.20:
        charge = random.randint(10, 18) + enemy.get("str_mod", 0)
        recoil = charge // 3
        enemy["hp"] -= recoil
        c_print(f"\n  The Bandersnatch charges with a whiffling roar!"
                 f"\n  It deals {charge} damage but takes {recoil} recoil!")
        player["current_hp"] -= max(0, charge - player.get("con_mod", 0) // 2)
        return "The frumious charge connects!"

    # Burble: AoE fear
    if random.random() < 0.15:
        c_print(f"\n  The Bandersnatch lets out a horrible BURBLE!"
                 f"\n  The sound fills you with dread!")
        _apply_fear(player, duration=2)
        apply_dread(player, duration=2)
        return "The burble shakes your courage!"

    return None


# ═══════════════════════════════════════════════════════════════════════
# F42: The Wizard of Oz — "Pay No Attention..."
# ═══════════════════════════════════════════════════════════════════════

def wizard_of_oz_ai(enemy, player, dmg):
    """Illusion-based. Summons fake copies, hides real self."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # "Pay no attention to the man behind the curtain!"
    if not enemy.get("_wl_illusion_active") and random.random() < 0.35:
        enemy["_wl_illusion_active"] = True
        c_print(f"\n  'I AM THE GREAT AND POWERFUL OZ!'"
                 f"\n  The Wizard conjures terrifying illusions!")
        # Summon illusion copies
        enemy["_wl_minions"] = [
            {"name": "Oz's Illusion", "hp": 20, "max_hp": 20,
             "str_mod": 4, "con_mod": 3, "dex_mod": 3,
             "elemental_res": {}, "elemental_dmg": {"light": 1.3},
             "active_debuffs": [], "active_buffs": [],
             "key": "_wl_illusion", "level": 40, "_wl_illusion": True},
        ]
        c_print("  A terrifying illusion manifests!")

    # Smoke and Mirrors: evade
    if random.random() < 0.25:
        enemy["_wl_phased"] = True
        c_print(f"\n  Smoke fills the chamber! The Wizard vanishes!"
                 f"\n  'You dare to reveal the truth?'")

    # Fireball: spectacle attack
    if random.random() < 0.20:
        fire = random.randint(8, 16) + enemy.get("ler_mod", 3)
        c_print(f"\n  The Wizard hurls a massive FIREBALL!"
                 f"\n  It deals {fire} fire damage!")
        player["current_hp"] -= max(0, fire - player.get("con_mod", 0) // 2)
        apply_burn(player, tier=1, duration=3)
        return "The flames of Oz burn bright!"

    # Reveal weakness (once, at low HP)
    if hp_pct < 0.25 and not enemy.get("_wl_revealed"):
        enemy["_wl_revealed"] = True
        enemy["con_mod"] = max(0, enemy.get("con_mod", 0) - 3)
        c_print(f"\n  The curtain falls! The Wizard is just a man..."
                 f"\n  'I... I'm just a humbug.' His defenses crumble!")

    return None


# ═══════════════════════════════════════════════════════════════════════
# F44: Headless Horseman — "The Wild Ride"
# ═══════════════════════════════════════════════════════════════════════

def headless_horseman_ai(enemy, player, dmg):
    """Throws explosive pumpkins. Cannot be crit (no head)."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # No head to strike — immune to critical hits
    if not enemy.get("_wl_headless_immune"):
        enemy["_wl_headless_immune"] = True
        # Represented by high defense behavior, not literal crit immunity in generic combat

    # Explosive Pumpkin: fire AoE
    if random.random() < 0.25:
        pumpkin = random.randint(10, 18) + enemy.get("str_mod", 0)
        c_print(f"\n  The Headless Horseman hurls a FLAMING PUMPKIN!"
                 f"\n  It explodes for {pumpkin} fire damage!")
        player["current_hp"] -= max(0, pumpkin - player.get("con_mod", 0) // 2)
        apply_burn(player, damage=4, duration=3)
        return "The pumpkin EXPLODES in a shower of fire!"

    # Spectral Charge: trample
    if random.random() < 0.20:
        charge = random.randint(8, 14) + enemy.get("str_mod", 0)
        c_print(f"\n  The Horseman's steed charges through you!"
                 f"\n  The spectral trample deals {charge} damage!")
        player["current_hp"] -= max(0, charge - player.get("con_mod", 0) // 2)
        apply_dread(player, duration=2)
        return "The ghostly steed passes through — leaving only cold dread!"

    # Dullahan's Wail: fear AoE at low HP
    if hp_pct < 0.30 and not enemy.get("_wl_wailed"):
        enemy["_wl_wailed"] = True
        c_print(f"\n  The Horseman raises his arms and lets out a SOUL-PIERCING WAIL!")
        _apply_fear(player, duration=3)
        apply_dread(player, duration=3)
        return "The Dullahan's death-cry fills you with terror!"

    return None


# ═══════════════════════════════════════════════════════════════════════
# F46: The Snow Queen — "Frozen Heart"
# ═══════════════════════════════════════════════════════════════════════

def snow_queen_ai(enemy, player, dmg):
    """Ice magic. Freezes party members. Shatter combo."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Icy Grasp: freeze attempt
    freeze_timer = enemy.get("_wl_freeze_timer", 0) + 1
    enemy["_wl_freeze_timer"] = freeze_timer

    if freeze_timer >= 3 and random.random() < 0.40:
        enemy["_wl_freeze_timer"] = 0
        result = apply_freeze(player, duration=2)
        if result == "applied":
            c_print(f"\n  The Snow Queen extends her hand..."
                     f"\n  'Let the cold embrace you.'"
                     f"\n  {player['name']} is FROZEN SOLID!")
            # Shatter combo: if frozen, next attack deals bonus
            enemy["_wl_shatter_ready"] = True
            return "The ice claims you!"

    # Shatter: bonus damage to frozen target
    if enemy.get("_wl_shatter_ready"):
        enemy["_wl_shatter_ready"] = False
        shatter = random.randint(15, 25)
        c_print(f"\n  The Snow Queen's voice is ice: 'SHATTER.'"
                 f"\n  The ice around you EXPLODES for {shatter} damage!")
        player["current_hp"] -= max(0, shatter - player.get("con_mod", 0) // 2)
        return "The ice shatters — taking flesh with it!"

    # Blizzard: AoE cold damage
    if random.random() < 0.20:
        blizzard = random.randint(6, 12) + enemy.get("wis_mod", 2)
        c_print(f"\n  A BLIZZARD howls through the chamber!"
                 f"\n  The biting cold deals {blizzard} damage!")
        player["current_hp"] -= max(0, blizzard - player.get("con_mod", 0) // 2)
        return "The eternal winter bites deep!"

    return None


# ═══════════════════════════════════════════════════════════════════════
# F48: The Nothing — "The Story Ends"
# ═══════════════════════════════════════════════════════════════════════

def the_nothing_ai(enemy, player, dmg):
    """Consumes buffs. Grows larger. Final pre-Mary Sue challenge."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Consume buffs: strips player buffs
    if player.get("active_buffs") and random.random() < 0.30:
        stripped = player["active_buffs"][:2]  # Remove first 2 buffs
        player["active_buffs"] = player["active_buffs"][2:]
        c_print(f"\n  The Nothing REACHES into your soul..."
                 f"\n  It consumes your buffs — they are... gone."
                 f"\n  '{len(stripped)} blessing(s) erased.'")

    # Growing Void: gets bigger
    if not enemy.get("_wl_grown"):
        enemy["_wl_grown"] = True
        enemy["max_hp"] = int(enemy["max_hp"] * 1.5)
        enemy["hp"] = enemy["max_hp"]
        enemy["str_mod"] = enemy.get("str_mod", 0) + 3
        c_print(f"\n  The Nothing EXPANDS..."
                 f"\n  'I am the space between words. The silence after the last page.'"
                 f"\n  Its form grows — HP and power increase!")

    # Void Touch: pure damage
    if random.random() < 0.25:
        void_dmg = random.randint(10, 20) + enemy.get("str_mod", 0)
        c_print(f"\n  The Nothing touches you — and for a moment, you cease to exist."
                 f"\n  It deals {void_dmg} damage!")
        player["current_hp"] -= max(0, void_dmg - player.get("con_mod", 0) // 2)
        apply_dread(player, duration=3)
        return "The void's touch is absolute oblivion!"

    # Empty Echo: silence
    if random.random() < 0.20:
        result = apply_silence(player, duration=3)
        if result == "applied":
            return (f"The Nothing whispers — and all sound dies."
                    f"\n  {player['name']} is silenced for 3 turns!")

    return None


# ═══════════════════════════════════════════════════════════════════════
# F41–48 Regular Enemies — AI Patterns
# ═══════════════════════════════════════════════════════════════════════
# The regular enemies in F41-48 (non-boss) use their race-based AI from
# enemy_ai.py's get_race_extra_logic(). However, the "Author's Draft" theme
# gives them a shared mechanic: Mary Sue's abandoned experiments are
# unstable and may glitch.

def authors_draft_glitch(enemy, player, dmg):
    """Shared AI for F41-48 regular enemies — unstable storybook creations."""
    hp_pct = enemy["hp"] / enemy["max_hp"]

    # Glitch: random effect when attacking
    glitch_roll = random.random()

    if glitch_roll < 0.10:
        # Beneficial glitch for enemy
        enemy["hp"] = min(enemy["max_hp"], enemy["hp"] + random.randint(3, 8))
        c_print(f"\n  * The {enemy['name']} glitches — reality rewrites to heal it!")
    elif glitch_roll < 0.20:
        # Harmful glitch for enemy
        enemy["hp"] -= random.randint(3, 8)
        c_print(f"\n  * The {enemy['name']} glitches — its form destabilizes!")
    elif glitch_roll < 0.25:
        # Narrative skip: enemy vanishes
        if hp_pct < 0.40:
            c_print(f"\n  * The {enemy['name']} glitches..."
                     f"\n  'This story was abandoned.' — it fades from existence!")
            enemy["hp"] = 0
            return "The abandoned character fades away..."

    return None


# ═══════════════════════════════════════════════════════════════════════
# Dispatch Map
# ═══════════════════════════════════════════════════════════════════════

WL_FLOOR_BOSS_MAP = {
    2:  ("White Rabbit",         "wl_white_rabbit",      white_rabbit_ai),
    4:  ("Cheshire Cat",         "wl_cheshire",           cheshire_cat_ai),
    6:  ("Card Knight",          "wl_card_knight",        card_knight_ai),
    8:  ("Dormouse Captain",     "wl_dormouse_capt",      dormouse_captain_ai),
    12: ("Peter Pan",            "wl_peter_pan",          peter_pan_ai),
    14: ("Tick-Tock Crocodile",  "wl_croc_ticktock_boss", ticktock_croc_ai),
    16: ("Pirate Captain James", "wl_pirate_captain",     pirate_captain_james_ai),
    18: ("Tin Woodsman Captain", "wl_tin_woodsman_capt",  tin_woodsman_capt_ai),
    22: ("Mr. Hyde",             "wl_hyde_boss",          mr_hyde_ai),
    24: ("Professor Moriarty",   "wl_moriarty",           professor_moriarty_ai),
    26: ("Dracula's Bride",      "wl_dracula_bride",      dracula_bride_ai),
    28: ("Phantom of the Opera", "wl_phantom",            phantom_opera_ai),
    32: ("Captain Hook",         "wl_captain_hook",       captain_hook_ai),
    34: ("The Red Queen",        "wl_red_queen",          red_queen_ai),
    36: ("The Scarecrow King",   "wl_scarecrow_king",     scarecrow_king_ai),
    38: ("Bandersnatch Alpha",   "wl_bandersnatch_alpha", bandersnatch_alpha_ai),
    42: ("The Wizard of Oz",     "wl_wizard_oz",          wizard_of_oz_ai),
    44: ("Headless Horseman",    "wl_headless_horseman",  headless_horseman_ai),
    46: ("The Snow Queen",       "wl_snow_queen",         snow_queen_ai),
    48: ("The Nothing",          "wl_the_nothing",        the_nothing_ai),
}


def get_wl_floor_boss(floor):
    """Return (boss_name, enemy_key, ai_function) or None."""
    return WL_FLOOR_BOSS_MAP.get(floor)


def is_wl_boss_floor(floor):
    """Check if a floor is a wonderland floor boss floor."""
    return floor in WL_FLOOR_BOSS_MAP
