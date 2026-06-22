# sylvana.py – Queen of Mirrors Sylvana super boss encounter
import random
from utils import clear_screen
from combat.stats import enemy_stats, compute_player_stats
from combat.player_actions import handle_player_turn
from combat.combat_ui import format_enemy_status_line, print_superboss_header, print_combat_hud
from combat.superboss_common import superboss_triple_action_loop, superboss_combat_loop
from character import player_max_hp
from combat.status_effects import (
    apply_poison, apply_curse,
    tick_enemy_debuffs, tick_player_debuffs, tick_player_buffs,
    cure_curse, apply_weaken, format_player_status_line, apply_silence, apply_blind
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scramble_name(name):
    """Return the name with random letters uppercased – marks the fake copy."""
    chars = list(name)
    indices = random.sample(range(len(chars)), k=max(2, len(chars) // 3))
    for i in indices:
        if chars[i].isalpha():
            chars[i] = chars[i].upper() if chars[i].islower() else chars[i].lower()
    # Guarantee at least one upper-case letter is present so it's visible
    while not any(c.isupper() for c in chars if c.isalpha()):
        idx = random.choice([i for i, c in enumerate(chars) if c.isalpha()])
        chars[idx] = chars[idx].upper()
    return "".join(chars)


def _make_fake_copy(boss):
    """Create a mirror illusion with identical stats but a scrambled name."""
    fake = dict(boss)
    fake["key"] = "sylvana_mirror_copy"
    fake["name"] = _scramble_name(boss["name"])
    fake["is_fake"] = True
    fake["hp"] = boss["hp"]
    fake["max_hp"] = boss["max_hp"]
    return fake


def _is_sylvana(e):
    return e.get("key") == "queen_of_mirrors_sylvana"

def _nullify_player_buff(player):
    """
    Null ability – remove one random active buff from the player.
    Returns a message string, or None if no buffs to remove.
    """
    buffs = player.get("active_buffs", [])
    eligible = [b for b in buffs if b.get("type") != "blessing"]
    if not eligible:
        return None
    target_buff = random.choice(eligible)
    buffs.remove(target_buff)
    label = target_buff.get("stat") or target_buff.get("type") or "buff"
    return f"✨ Sylvana's Null shatters your {label}! The enchantment unravels."

def _illusory_veil(boss, player):
    """
    25% chance per turn:
      – Blind the player
      – Give the boss a temporary defense_buff (stored on the enemy dict).
    Returns a message, or None.
    """
    if random.random() >= 0.25:
        return None
    apply_blind(player, duration=2)
    boss["veil_defense"] = boss.get("veil_defense", 0) + 3
    return (
        "🪞 Illusory Veil! Sylvana blurs into fractured reflections – "
        "you are Blinded and her form becomes harder to hit! (+3 defense)"
    )


# ---------------------------------------------------------------------------
# Main combat function
# ---------------------------------------------------------------------------

def combat_sylvana(player, floor=None):
    boss_key = "queen_of_mirrors_sylvana"
    boss = enemy_stats(boss_key, player)
    boss["max_hp"] = boss["hp"]
    enemies = [boss]

    print("\n" + "=" * 55)
    print("A thousand reflections shatter apart and reassemble —")
    print("Queen of Mirrors Sylvana steps forward, smiling coldly.")
    print(f"{boss['name']} — HP: {boss['hp']}")
    print("=" * 55)
    input("Press Enter to face the Queen of Mirrors...")

    context = {
        "mirror_phase_triggered": False,
        "boss_extra_actions": 0,
        "final_form": False,
        "reflection_turn_counter": 0,
        "split_active": False,
        "extra_actions_granted_this_round": False
    }

    def on_kill_hook(target, elist, ctx):
        """Fallback — if something else kills a clone."""
        if target.get("is_fake"):
            # Rage is already triggered by on_player_hit_hook,
            # so just print a message and clear the split flag.
            print(f"\n🪞 The mirror copy of {target['name']} shatters!")
            ctx["split_active"] = False
        else:
            ctx["split_active"] = False

    def _trigger_mirror_rage(ctx, is_kill=False):
        """Centralized rage trigger for hitting/killing clones."""
        print("\n🪞 That was just a mirror! Sylvana laughs as you strike the illusion.")
        if ctx["final_form"]:
            print("Her rage surges — TRIPLE ACTIONS for 2 turns!")
        else:
            print("Her rage crystalises — DOUBLE ACTIONS for 2 turns!")
        ctx["boss_extra_actions"] += 2
        ctx["extra_actions_granted_this_round"] = True

    def on_player_hit_hook(target, elist, ctx):
        """NEW: Trigger on any hit against a clone (main fix)."""
        if target.get("is_fake"):
            _trigger_mirror_rage(ctx, is_kill=False)

    def pre_player_hook(ctx, elist):
        b = next((e for e in elist if not e.get("is_fake")), None)
        if not b: return

        if not ctx["final_form"] and b["hp"] <= int(b["max_hp"] * 0.30):
            ctx["final_form"] = True
            print("\n" + "!" * 55)
            print("[FINAL FORM] Sylvana screams. Every surface erupts into mirrors!")
            print("Her reflection multiplies endlessly — she is EVERYWHERE NOW.")
            print("Double actions become permanent. Reflections spawn every 3 turns.")
            print("!" * 55)
            input("Press Enter...")

        should_spawn = False
        if not ctx["mirror_phase_triggered"] and b["hp"] <= int(b["max_hp"] * 0.65):
            should_spawn = True
            ctx["mirror_phase_triggered"] = True

        if ctx["final_form"] and not ctx["split_active"]:
            ctx["reflection_turn_counter"] += 1
            if ctx["reflection_turn_counter"] >= 3:
                should_spawn = True
                ctx["reflection_turn_counter"] = 0

        if should_spawn:
            num_fakes = 2 if ctx["final_form"] else 1
            for _ in range(num_fakes):
                elist.append(_make_fake_copy(b))
            random.shuffle(elist)
            ctx["split_active"] = True
            fake_label = "two illusory copies" if num_fakes == 2 else "an illusory copy"
            print(f"\n🪞 [GIMMICK] Mirror Reflection! Sylvana fractures into {fake_label}!")
            print("One of them is the REAL Sylvana. The copies bear subtly wrong names.")
            input("Press Enter...")

    def custom_hud_hook(ctx, elist):
        clear_screen()
        if ctx["final_form"] and ctx["boss_extra_actions"] > 0:
            action_status = f"⚡ TRIPLE ACTION ({ctx['boss_extra_actions']} turn(s) left)"
        elif ctx["final_form"]:
            action_status = "⚡ PERMANENT DOUBLE ACTION"
        elif ctx["boss_extra_actions"] > 0:
            action_status = f"⚡ DOUBLE ACTION PENALTY ({ctx['boss_extra_actions']} turn(s) left)"
        else:
            action_status = "Normal actions"

        print(f"  {action_status}")
        print_combat_hud(player, elist, header="Superboss: Queen of Mirrors Sylvana")

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending):
        if enemy.get("is_fake"):
            block = p_con + (5 if defending else 0)
            fake_dmg = max(0, random.randint(2, 6) + enemy["str_mod"] - block)
            pl["current_hp"] -= fake_dmg
            if fake_dmg > 0:
                print(f"\n🪞 {enemy['name']} flickers and strikes you for {fake_dmg} damage!")
                if apply_blind(pl, duration=2) == "applied": print("The illusion's touch blinds you!")
                else: print("The illusion refreshes your blindness!")
            else:
                print(f"\n🪞 {enemy['name']} flickers through you — you block the illusion!")
            print(f"The copy shatters after attacking!")
            enemy["hp"] = 0
            if pl["current_hp"] <= 0: return "dead"
            return 0, True, None, 1.0, 0  # Handled manually, skip standard loop

        # Real Sylvana Logic
        if ctx["final_form"] and ctx["boss_extra_actions"] > 0: actions = 3
        elif ctx["final_form"] or ctx["boss_extra_actions"] > 0: actions = 2
        else: actions = 1

        veil_msg = _illusory_veil(enemy, pl)
        if veil_msg: print(veil_msg)

        if random.random() < 0.70:
            null_msg = _nullify_player_buff(pl)
            if null_msg: print(null_msg)

        # Invert veil defense into negative temp_str so the base loop calculates block properly
        veil_def = enemy.pop("veil_defense", 0)
        temp_str = -veil_def 

        def sylvana_extra(e, p, dmg):
            if dmg > 0 and random.random() < 0.25:
                from combat.status_effects import apply_silence
                if apply_silence(p, duration=2) == "applied":
                    return "Sylvana's fey magic seals your pack shut for 2 turns!"
            return None

        return actions, False, sylvana_extra, 1.0, temp_str

    def post_round_hook(ctx, elist):
        if ctx["boss_extra_actions"] > 0 and not ctx["extra_actions_granted_this_round"]:
            ctx["boss_extra_actions"] -= 1
            if ctx["boss_extra_actions"] == 0:
                print("\n✨ Sylvana's extra fury subsides...")
        ctx["extra_actions_granted_this_round"] = False

        if ctx["split_active"] and not any(e.get("is_fake") for e in elist):
            ctx["split_active"] = False

    result = superboss_combat_loop(
    player, enemies, floor, "Queen of Mirrors Sylvana", context,
    pre_player_hook=pre_player_hook,
    custom_hud_hook=custom_hud_hook,
    on_kill_hook=on_kill_hook,
    on_player_hit_hook=on_player_hit_hook,
    enemy_turn_hook=enemy_turn_hook,
    post_round_hook=post_round_hook
    )

    if result == "victory":
        print("\n✨ The mirrors all shatter at once. Sylvana dissipates into shards of light.")
        
    return result