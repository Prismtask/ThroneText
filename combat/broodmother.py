import random
from utils import clear_screen
from combat.generic import enemy_stats, print_superboss_header, superboss_combat_loop
from combat.status_effects import apply_poison

def combat_broodmother(player, floor=None):
    boss_key = "broodmother_vileheart"
    boss = enemy_stats(boss_key, player)
    boss["max_hp"] = boss["hp"]
    enemies = [boss]

    print("\n" + "=" * 60)
    print("The air grows thick with the stench of rot and venom.")
    print("Hundreds of tiny legs skitter in the darkness above and below.")
    print("A monstrous, bloated silhouette rises — crowned with thrashing")
    print("limbs and dripping fangs. Countless spider eyes gleam with")
    print("pure, instinctual hunger.")
    print(f"\nBroodmother Vileheart — HP: {boss['hp']}")
    print("=" * 60)
    input("\nPress Enter to face the Broodmother...")

    context = {
        "boss_escaped_data": None,
        "minion_phase_active": False,
        "minion_timer": 0,
        "boss_enraged_turns": 0
    }

    def _broodmother_poison(enemy, pl, enemy_dmg):
        if enemy_dmg > 0 and random.random() < 0.5:
            status = apply_poison(pl, 4, 3)
            if status == "applied": return f"You are poisoned by the {enemy['name']}!"
            return f"The {enemy['name']} re-infects you!"
        return None

    def pre_player_hook(ctx, elist):
        if not ctx["minion_phase_active"] and ctx["boss_escaped_data"] is None:
            for e in elist[:]:
                if e.get("key") == "broodmother_vileheart" and e["hp"] <= int(e["max_hp"] * 0.75):
                    print(f"\n[GIMMICK] {e['name']} screeches and retreats into the shadows!")
                    print("Three Vileheart Spiderlings drop from the ceiling!")
                    ctx["boss_escaped_data"] = e
                    elist.remove(e)
                    for _ in range(3):
                        m_stats = enemy_stats("vileheart_spiderling", player)
                        m_stats["key"] = "vileheart_spiderling"
                        m_stats["max_hp"] = m_stats["hp"]
                        elist.append(m_stats)
                    ctx["minion_phase_active"] = True
                    ctx["minion_timer"] = 3
                    break

    def enemy_turn_hook(enemy, ctx, pl, p_con, defending):
        is_boss = (enemy.get("key") == "broodmother_vileheart")
        is_enraged = (is_boss and ctx["boss_enraged_turns"] > 0)
        
        actions = 2 if is_enraged else 1
        extra, armor_mult, temp_str = None, 1.0, 0

        if is_boss:
            r = random.random()
            if r < 0.4:
                def poison_strike(e, p, dmg):
                    if dmg > 0:
                        apply_poison(p, 6 if is_enraged else 4, 3)
                        return f"🧪 Vileheart toxins seep into your veins! (Poisoned)"
                    return None
                extra = poison_strike
            elif r < 0.7:
                # Heavy Trample: +3 STR and ignores 30% armor
                temp_str = 3
                armor_mult = 0.7
        else:
            extra = _broodmother_poison # Spiderling poison

        return actions, False, extra, armor_mult, temp_str

    def post_round_hook(ctx, elist):
        if ctx["minion_phase_active"]:
            spiderlings_alive = any(e.get("key") == "vileheart_spiderling" for e in elist)
            if not spiderlings_alive:
                print("\n[GIMMICK] You slaughtered all spiderlings!")
                print("Broodmother Vileheart descends again, enraged by your defiance.")
                elist.append(ctx["boss_escaped_data"])
                ctx["boss_escaped_data"] = None
                ctx["minion_phase_active"] = False
            else:
                ctx["minion_timer"] -= 1
                if ctx["minion_timer"] <= 0:
                    print("\n[GIMMICK] Time's up! The remaining spiderlings retreat.")
                    print("Broodmother Vileheart ambushes you, ENRAGED with double actions for 3 turns!")
                    elist[:] = [e for e in elist if e.get("key") != "vileheart_spiderling"]
                    ctx["boss_enraged_turns"] = 3
                    elist.append(ctx["boss_escaped_data"])
                    ctx["boss_escaped_data"] = None
                    ctx["minion_phase_active"] = False

        if ctx["boss_enraged_turns"] > 0:
            ctx["boss_enraged_turns"] -= 1

    return superboss_combat_loop(
        player, enemies, floor, "Broodmother Vileheart", context,
        pre_player_hook=pre_player_hook,
        enemy_turn_hook=enemy_turn_hook,
        post_round_hook=post_round_hook
    )