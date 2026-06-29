import random
from utils import clear_screen
from combat.stats import enemy_stats, compute_player_stats
from combat.player_actions import handle_player_turn
from combat.combat_ui import format_enemy_status_line, print_superboss_header, print_combat_hud
from combat.superboss_common import superboss_triple_action_loop, superboss_combat_loop
from combat.status_effects import apply_poison, apply_curse
from resources.items import build_item

def combat_slitcurrent(player, floor=None):
    boss_key = "dream_devouring_slitcurrent"
    boss = enemy_stats(boss_key, player)
    boss["max_hp"] = boss["hp"]
    enemies = [boss]

    print("\n" + "=" * 60)
    print("Reality frays at the edges. Whispers that are not your own...")
    print(f"\nDream-Devouring Slitcurrent — HP: {boss['hp']}")
    print("=" * 60)
    input("\nPress Enter to face the Dream-Devourer...")

    context = {
        "devour_focus_stacks": 0,
        "floatsam_spawned": False,
        "turn_counter": 0,
        "boss_stun_turns": 0,
        "failure_timer": 0,
        "boss_buff_turns": 0,
        "massive_attack_triggered": False,
        "player_stunned": False,
        "skip_player_turn": False
    }

    def on_kill_hook(target, elist, ctx):
        if target.get("key") == "dream_floatsam":
            ctx["devour_focus_stacks"] += 1
            print(f"[GIMMICK] Slitcurrent devours the remains! Devour Focus +1 ({ctx['devour_focus_stacks']}/3)")
            ctx["failure_timer"] = 0 
            if ctx["devour_focus_stacks"] >= 3:
                print("\n[GIMMICK] NIGHTMARE OVERLOAD! Slitcurrent is stunned for 2 turns and takes +40% damage!")
                ctx["boss_stun_turns"] = 3
                b = next((e for e in elist if e.get("key") == boss_key), None)
                if b: b["stunned"] = True
                ctx["devour_focus_stacks"] = 0

    def pre_player_hook(ctx, elist):
        b = next((e for e in elist if e.get("key") == boss_key), None)
        
        # Floatsam Spawn
        if b and not ctx["floatsam_spawned"] and b["hp"] <= b["max_hp"] * 0.8:
            print("\n[GIMMICK] Slitcurrent shrieks and spawns 3 Dream Floatsam from the abyss!")
            for _ in range(3):
                m_stats = enemy_stats("dream_floatsam", player)
                m_stats["key"] = "dream_floatsam"
                m_stats["max_hp"] = m_stats["hp"]
                elist.append(m_stats)
            ctx["floatsam_spawned"] = True
            ctx["failure_timer"] = 0

        floatsam_alive = any(e.get("key") == "dream_floatsam" for e in elist)

        # Failure Timer
        if floatsam_alive and not ctx["massive_attack_triggered"] and ctx["devour_focus_stacks"] < 3:
            ctx["failure_timer"] += 1
            if ctx["failure_timer"] >= 5:
                print("\n[GIMMICK] The Floatsam fester too long! Slitcurrent explodes in rage!")
                massive_dmg = max(5, random.randint(15, 25) + b["str_mod"] - player.get("attributes", {}).get("Constitution", 0))
                player["current_hp"] -= massive_dmg
                print(f"Slitcurrent unleashes DREAM SURGE for {massive_dmg} damage!")
                if player["current_hp"] <= 0: return "dead"
                
                ctx["devour_focus_stacks"] = 0
                ctx["boss_buff_turns"] = 2
                print("Slitcurrent gains TEMPORARY ALL-STATS BUFF for 2 turns!")
                ctx["massive_attack_triggered"] = True
        elif not floatsam_alive:
            ctx["failure_timer"] = 0
            ctx["massive_attack_triggered"] = False

        # Apply Temporary Boss Buff
        if ctx["boss_buff_turns"] > 0:
            if b: b["temp_str_bonus"] = 5
            ctx["boss_buff_turns"] -= 1
            if ctx["boss_buff_turns"] == 0 and b:
                b.pop("temp_str_bonus", None)
                print("Slitcurrent's rage subsides.")
        else:
            if b: b.pop("temp_str_bonus", None)

        # Player Stun Logic
        if ctx["player_stunned"]:
            print("\nYou are STUNNED from the Nightmarish Tide and cannot act this turn!")
            input("Press Enter to yield your turn...")
            ctx["player_stunned"] = False
            ctx["skip_player_turn"] = True
            ctx["turn_counter"] += 1

    def custom_hud_hook(ctx, elist):
        b = next((e for e in elist if e.get("key") == boss_key), None)
        if b:
            print(f"  Slitcurrent: Devour {ctx['devour_focus_stacks']}/3", end="")
            if ctx["boss_stun_turns"] > 0:
                print(f" | Stunned: {ctx['boss_stun_turns']} turns left", end="")
            print()
        print_combat_hud(player, elist, header="Superboss: Dream-Devouring Slitcurrent")

    def player_action_override(ctx):
        action = input("Choose: ").strip().lower()
        ctx["turn_counter"] += 1
        return action

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending, **kwargs):
        if enemy.get("key") == boss_key and ctx["boss_stun_turns"] > 0:
            print(f"The {enemy['name']} is stunned and cannot act! ({ctx['boss_stun_turns']} turns remain)")
            ctx["boss_stun_turns"] -= 1
            if ctx["boss_stun_turns"] == 0: enemy["stunned"] = False
            return 0, True, None, 1.0, 0  # Skip attack entirely

        temp_str = enemy.get("temp_str_bonus", 0)
        
        # Nightmarish Tide
        if enemy.get("key") == boss_key and ctx["turn_counter"] % 3 == 0:
            print("\n🌊 The abyss churns – NIGHTMARISH TIDE!")
            tide_dmg = max(5, random.randint(12, 20) + enemy["str_mod"] + temp_str - p_con)
            pl["current_hp"] -= tide_dmg
            print(f"Slitcurrent washes over you for {tide_dmg} damage!")
            pl["stunned"] = True
            print("You are STUNNED and will lose your next turn!")
            ctx["player_stunned"] = True
            if pl["current_hp"] <= 0: return "dead"
            return 0, True, None, 1.0, 0

        floatsam_alive = any(e.get("key") == "dream_floatsam" for e in enemies) # from closure scope
        is_empowered = floatsam_alive and enemy.get("key") == boss_key
        
        if is_empowered:
            print(f"⚠️ {enemy['name']} channels abyssal power through its floatsam! (Empowered)")
            temp_str += 2  # Offset to simulate Empowered's higher base damage roll in standard attack handler

        extra = None
        if enemy.get("key") == boss_key and random.random() < 0.4:
            def devourer_ailment(e, p, dmg):
                if random.random() < 0.5:
                    apply_poison(p, 5, 3)
                    return f"Nightmarish venom from {e['name']}!"
                else:
                    if apply_curse(p) == "applied": return f"A dream curse grips you from the {e['name']}!"
                return None
            extra = devourer_ailment

        return 1, False, extra, 1.0, temp_str
    
    result = superboss_combat_loop(
        player, enemies, floor, "Dream-Devouring Slitcurrent", context,
        pre_player_hook=pre_player_hook,
        custom_hud_hook=custom_hud_hook,
        on_kill_hook=on_kill_hook,
        player_action_override=player_action_override,
        enemy_turn_hook=enemy_turn_hook
    )

    if result == "victory":
        print("\n" + "~" * 55)
        print("As the Dream-Devourer dissolves, a blade crystallises")
        print("from the void where its heart once beat. It hums with")
        print("an eerie, hungry resonance — as if the abyss itself")
        print("has been shaped into an edge.")
        print("\n  ✦ You obtained: ABYSS FANG (Legendary) ✦")
        print("~" * 55)
        abyss_fang = build_item("abyss_fang", "legendary")
        from inventory import add_item_to_inventory
        if not add_item_to_inventory(player, abyss_fang):
            player.setdefault("inventory", []).append(abyss_fang)
            print("  (Your bag is full, but you force the Abyss Fang in anyway!)")
        input("\nPress Enter to continue...")

    return result