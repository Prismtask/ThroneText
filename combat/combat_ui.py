# combat_ui.py – HUD and status formatting
from utils import clear_screen, format_time
from combat.status_effects import format_player_status_line
from combat.action_menu import get_action_menu
from combat.abyss_fang import is_abyssal_tempo_active, get_abyss_fang_cooldown_display
from combat.captain_cutlass import get_captain_cutlass_cooldown_display
from combat.ally import format_ally_status_line, _ally_action_menu
from combat.ally_skills import get_all_ally_skills
from combat.skills import get_all_unlocked_skills
from combat.combat_io import c_print, c_input, c_clear


def format_enemy_status_line(enemy, extra=""):
    statuses = []
    if enemy.get("slowed"):
        statuses.append("Slowed")
    if enemy.get("stunned"):
        statuses.append("Stunned")
    if enemy.get("blinded"):
        statuses.append("Blinded")
    if enemy.get("frozen"):
        statuses.append("Frozen")
    if enemy.get("confused"):
        statuses.append("Confused")
    if any(d["type"] == "burn" for d in enemy.get("active_debuffs", [])):
        burn_debuff = next((d for d in enemy.get("active_debuffs", []) if d["type"] == "burn"), None)
        if burn_debuff:
            from combat.status_effects import get_burn_tier_name
            tier_name = get_burn_tier_name(burn_debuff.get("tier", 2))
            statuses.append(tier_name)
    if enemy.get("expose_stacks", 0) > 0:
        statuses.append(f"Exposed×{enemy['expose_stacks']}")
    status_str = f" ({', '.join(statuses)})" if statuses else ""
    return f"{enemy['name']} - HP: {enemy['hp']}{status_str}{extra}"


def print_pre_initiative_enemies(enemies):
    """Print a simple enemy list before initiative is rolled."""
    c_print("ENEMIES:")
    for idx, e in enumerate(enemies):
        mg_symbol = "♀" if e.get("monster_girl") else ""
        c_print(f"  [{idx+1}] {e['name']} ({e['hp']}/{e['max_hp']}) {mg_symbol}")


def _hp_bar(current, max_hp, width=12):
    """Return a simple ASCII HP bar."""
    if max_hp <= 0:
        return "[            ]"
    ratio = current / max_hp
    filled = int(ratio * width)
    filled = max(0, min(width, filled))
    empty = width - filled
    bar = "#" * filled + "." * empty
    return f"[{bar}]"


def _center_text(text, width):
    """Center text within a given width, truncating if necessary."""
    if len(text) >= width:
        return text[:width]
    pad = width - len(text)
    left = pad // 2
    right = pad - left
    return " " * left + text + " " * right


def _get_entity_buff_tags(entity):
    """Return a short buff/debuff tag string for any entity (player, ally, enemy)."""
    statuses = []
    # Flag-based debuffs
    if entity.get("stunned"):
        statuses.append("STN")
    if entity.get("slowed"):
        statuses.append("SLW")
    if entity.get("blinded"):
        statuses.append("BLD")
    if entity.get("frozen"):
        statuses.append("FRZ")
    if entity.get("silenced"):
        statuses.append("SIL")
    if entity.get("dreaded"):
        statuses.append("DRD")
    if entity.get("cursed"):
        statuses.append("CRS")
    if entity.get("confused"):
        statuses.append("CNF")
    if entity.get("hunters_mark"):
        statuses.append("MRK")
    if entity.get("parrot_target"):
        statuses.append("🦜TGT")

    # Debuff types from active_debuffs
    debuff_map = {
        "poison": "PSN",
        "bleed": "BLE",
        "slow": "SLW",
        "weaken": "WKN",
        "silence": "SIL",
        "dread": "DRD",
        "blind": "BLD",
        "curse": "CRS",
        "fear": "FER",
        "vulnerable": "VUL",
        "confusion": "CNF",
        "elemental_weakness": "ELW",
    }
    for d in entity.get("active_debuffs", []):
        if d["type"] == "burn":
            # Burn uses tier-specific tags
            from combat.status_effects import get_burn_tier_tag
            tag = get_burn_tier_tag(d.get("tier", 2))
        else:
            tag = debuff_map.get(d["type"])
        if tag and tag not in statuses:
            statuses.append(tag)

    # Tarnished Jade pin stacks
    tj_pins = entity.get("tarnished_jade_pins", 0)
    if tj_pins > 0:
        statuses.append(f"PIN×{tj_pins}")

    # Expose stacks (enemy only)
    expose = entity.get("expose_stacks", 0)
    if expose > 0:
        statuses.append(f"EXP×{expose}")

    # Buffs from active_buffs
    for b in entity.get("active_buffs", []):
        btype = b.get("type")
        if btype == "hot":
            tag = "REG"
        elif btype == "defense":
            tag = "DEF"
        elif btype == "defense_pct":
            tag = f"DEF{int(b.get('value', 0) * 100)}%"
        elif btype == "blessing":
            tag = "BLS"
        elif btype == "evasion":
            tag = f"DGE{int(b.get('value', 0) * 100)}%"
        elif btype == "damage_boost":
            tag = f"DMG+{int(b.get('value', 0) * 100)}%"
        elif btype == "well_rested":
            tag = "RST"
        elif btype == "arcane_ward":
            tag = "MYS"
        elif btype == "arcane_blessing":
            tag = "ARC"
        elif btype == "crit_chance":
            tag = f"CRT+{int(b.get('value', 0) * 100)}%"
        elif btype == "fear_immunity":
            tag = "FER-IMN"
        elif b.get("stat"):
            stat = b["stat"]
            if stat == "all":
                tag = "ALL+"
            else:
                tag = f"+{stat[:3].upper()}"
        else:
            continue
        if tag not in statuses:
            statuses.append(tag)

    # Elemental tag removed — now displayed separately via _get_entity_elem_tags()

    # ── Custom tags (injected by boss scripts, e.g. Chrysalis aspect stacks) ──
    for tag in entity.get("_custom_tags", []):
        if tag not in statuses:
            statuses.append(tag)

    return f" [{' '.join(statuses)}]" if statuses else ""


# ── Elemental tags (displayed beside entity name) ─────────────────────────

def _get_entity_elem_tags(entity, is_enemy=False):
    """Return compact elemental tags for display beside the entity name.

    ⚔  = best attack element    (highest elemental_dmg > 1.1)
    🛡↑ = strongest resistance   (highest elemental_res > 1.2)
    🛡↓ = biggest weakness       (lowest elemental_res < 0.85)

    All three are shown for every entity when applicable.
    Returns a short string like "⚔FIR 🛡DAR↑ 🛡LIG↓" or "" if neutral.
    """
    parts = []

    # Attack: best damage element
    e_dmg = entity.get("elemental_dmg", {})
    best_dmg_el = None
    best_dmg_val = 1.1
    for el, val in e_dmg.items():
        if val > best_dmg_val:
            best_dmg_val = val
            best_dmg_el = el
    if best_dmg_el:
        parts.append(f"⚔{best_dmg_el[:3].upper()}")

    # Defence: both strongest resistance AND biggest weakness
    e_res = entity.get("elemental_res", {})
    best_res_el = None
    best_res_val = 1.2
    worst_res_el = None
    worst_res_val = 0.85

    for el, val in e_res.items():
        if val > best_res_val:
            best_res_val = val
            best_res_el = el
        if val < worst_res_val:
            worst_res_val = val
            worst_res_el = el

    if best_res_el:
        parts.append(f"🛡{best_res_el[:3].upper()}↑")
    if worst_res_el:
        parts.append(f"🛡{worst_res_el[:3].upper()}↓")

    return " ".join(parts) if parts else ""


# ── Skill elemental tag ────────────────────────────────────────────────────

# Element → display color codes (for terminal ANSI)
_ELEMENT_COLORS = {
    "fire":     "\033[91m",   # red
    "water":    "\033[94m",   # blue
    "thunder":  "\033[93m",   # yellow/gold
    "wind":     "\033[96m",   # cyan/teal
    "earth":    "\033[92m",   # green
    "light":    "\033[97m",   # white
    "dark":     "\033[95m",   # purple/magenta
    "physical": "\033[90m",   # gray
    "magical":  "\033[35m",   # magenta
}
_RESET = "\033[0m"


def format_skill_elemental_tag(skill_def):
    """Return a colored elemental tag string for a skill, or '' if none/neutral."""
    element = skill_def.get("elemental")
    if not element:
        return ""
    color = _ELEMENT_COLORS.get(element, "")
    tag = f"[{element.upper()}]"
    if color:
        return f" {color}{tag}{_RESET}"
    return f" {tag}"


def _wrap_menu_lines(menu_str, max_width=66):
    """Split menu string into lines that fit within max_width."""
    if len(menu_str) <= max_width:
        return [menu_str]
    parts = menu_str.split('  ')
    lines = []
    current = ""
    for part in parts:
        if not current:
            current = part
        elif len(current) + 2 + len(part) <= max_width:
            current += "  " + part
        else:
            lines.append(current)
            current = part
    if current:
        lines.append(current)
    return lines


def format_combat_hud_data(player, enemies, active_ally=None, header=""):
    """Return a dict with all HUD data for GUI rendering.

    Keys:
        party:       list of dicts with name, hp, max_hp, is_active, buff_tags, is_player, is_front, is_back
        enemies:     list of dicts with name, hp, max_hp, index, monster_girl, buff_tags
        header:      str (e.g. '>> ABYSSAL TEMPO ACTIVE <<')
        action_menu: list of (key, label) tuples
        cooldowns:   list of cooldown message strings
        active_ally: the ally whose turn it is (or None for player)
    """
    from combat.ally import (get_active_allies, get_reserve_allies,
                             get_all_active_allies_including_defeated,
                             get_all_reserve_allies_including_defeated,
                             ensure_party_order)
    ensure_party_order(player)
    active_allies = get_all_active_allies_including_defeated(player)
    reserve_allies = get_all_reserve_allies_including_defeated(player)

    _max_hp = 15 + player["attributes"]["Constitution"] * 3 + player.get("level_hp_bonus", 0)

    if not header and is_abyssal_tempo_active(player):
        header = ">> ABYSSAL TEMPO ACTIVE <<"

    # Party data
    party_data = []

    # Player (always front)
    party_data.append({
        "name": player["name"],
        "hp": player["current_hp"],
        "max_hp": _max_hp,
        "is_active": active_ally is None,
        "buff_tags": _get_entity_buff_tags(player),
        "elem_tags": _get_entity_elem_tags(player, is_enemy=False),
        "is_player": True,
        "is_front": True,
        "is_back": False,
    })

    # Front-row allies (only active combatants — capped at 3, so max 4 rows including player)
    for ally in active_allies:
        party_data.append({
            "name": ally["name"],
            "hp": ally.get("current_hp", 0),
            "max_hp": ally.get("max_hp", 1),
            "is_active": ally is active_ally,
            "buff_tags": _get_entity_buff_tags(ally),
            "elem_tags": _get_entity_elem_tags(ally, is_enemy=False),
            "is_player": False,
            "is_front": True,
            "is_back": False,
        })

    # Back-row allies are NOT shown in the main party panel to keep the HUD compact.
    # They are only visible during ally-switch mode (reserve_party replaces enemies).

    # Enemy data — only include alive, uncaptured enemies (empty if in switch mode)
    enemy_data = []
    reserve_party = []
    switch_mode = player.get("_ally_switch_mode", False)

    if switch_mode:
        # In ally switch mode: show backup party instead of enemies
        reserve_living = get_reserve_allies(player)
        for idx, ally in enumerate(reserve_living):
            reserve_party.append({
                "name": ally["name"],
                "hp": ally.get("current_hp", 0),
                "max_hp": ally.get("max_hp", 1),
                "index": idx,
                "buff_tags": _get_entity_buff_tags(ally),
                "elem_tags": _get_entity_elem_tags(ally, is_enemy=False),
            })
    else:
        for idx, e in enumerate(enemies):
            if e.get("hp", 0) <= 0 or e.get("captured"):
                continue
            enemy_data.append({
                "name": e["name"],
                "hp": e["hp"],
                "max_hp": e["max_hp"],
                "index": idx,
                "monster_girl": e.get("monster_girl", False),
                "buff_tags": _get_entity_buff_tags(e),
                "elem_tags": _get_entity_elem_tags(e, is_enemy=True),
            })

    # Action menu
    if active_ally is not None:
        menu_str, valid_actions, _disabled = _ally_action_menu(active_ally, player, enemies)
    else:
        menu_str, valid_actions, _disabled = get_action_menu(player, enemies)

    # Parse menu string into (key, label) pairs
    action_menu = []
    for part in menu_str.split("  "):
        part = part.strip()
        if part.startswith("[") and "]" in part:
            key = part[1:part.index("]")]
            label = part[part.index("]") + 1:]
            action_menu.append((key, label))

    # Cooldown messages
    cooldowns = []
    if active_ally is None:
        cd_msg = get_abyss_fang_cooldown_display(player)
        if cd_msg:
            cooldowns.append(cd_msg)
        cd_msg2 = get_captain_cutlass_cooldown_display(player)
        if cd_msg2:
            cooldowns.append(cd_msg2)
        skill_cds = player.get('skill_cooldowns', {})
        if skill_cds:
            unlocked = get_all_unlocked_skills(player)
            for sid, sdef in unlocked:
                cd = skill_cds.get(sid, 0)
                if cd > 0:
                    cooldowns.append(f"({sdef['name']} recharging: {cd} turn(s))")
    else:
        skill_cds = active_ally.get('skill_cooldowns', {})
        if skill_cds:
            all_skills = get_all_ally_skills(active_ally)
            for sid, sdef in all_skills:
                cd = skill_cds.get(sid, 0)
                if cd > 0:
                    cooldowns.append(f"({sdef['name']} recharging: {cd} turn(s))")

    return {
        "party": party_data,
        "enemies": enemy_data,
        "header": header,
        "action_menu": action_menu,
        "cooldowns": cooldowns,
        "active_ally": active_ally,
        "switch_mode": switch_mode,
        "reserve_party": reserve_party,
    }


def print_combat_hud(player, enemies, active_ally=None, header=""):
    """Print the main combat HUD with a perfectly aligned party vs enemies layout.
    Shows FRONT (active combat) and BACK (reserve) party members."""
    from combat.ally import (get_active_allies, get_reserve_allies,
                             get_all_active_allies_including_defeated,
                             get_all_reserve_allies_including_defeated,
                             ensure_party_order)
    ensure_party_order(player)
    active_allies = get_all_active_allies_including_defeated(player)
    reserve_allies = get_all_reserve_allies_including_defeated(player)
    active_living = get_active_allies(player)
    reserve_living = get_reserve_allies(player)

    # Determine header context
    if not header:
        if is_abyssal_tempo_active(player):
            header = ">> ABYSSAL TEMPO ACTIVE <<"

    # 1. Top Border (Total inner width = 68 characters)
    c_print("+" + "-" * 68 + "+")
    if header:
        c_print("|" + _center_text(header, 68) + "|")
        c_print("+" + "-" * 32 + "+" + "-" * 35 + "+")

    # 2. Column Headers
    left_header = " YOUR PARTY"
    right_header = " ENEMIES"
    c_print(f"| {left_header:<30} | {right_header:<33} |")
    c_print(f"| {'-' * 30} | {'-' * 33} |")

    # 3. Gather Party Rows
    party_rows = []
    _max_hp = 15 + player["attributes"]["Constitution"] * 3 + player.get("level_hp_bonus", 0)
    player_active = " >" if active_ally is None else ""

    # Player — always in front
    player_hp_str = f"{player['current_hp']}/{_max_hp}"
    player_elem = _get_entity_elem_tags(player, is_enemy=False)
    player_name_line = f"* You{player_active:<2} {player_hp_str:>12}"
    if player_elem:
        player_name_line += f"  {player_elem}"
    party_rows.append(player_name_line)
    party_rows.append(_get_entity_buff_tags(player))

    # ── FRONT row (active combatants) ─────────────────────────────────────
    if active_allies:
        party_rows.append("  ── FRONT ──")
        party_rows.append("")
        for ally in active_allies:
            is_active = (ally is active_ally)
            ally_line = format_ally_status_line(ally, idx=None, is_active=is_active)
            ally_elem = _get_entity_elem_tags(ally, is_enemy=False)
            if ally_elem:
                ally_line += f"  {ally_elem}"
            party_rows.append(ally_line)
            party_rows.append(_get_entity_buff_tags(ally))

    # ── BACK row (reserve) ────────────────────────────────────────────────
    if reserve_allies:
        party_rows.append("  ── BACK ──")
        party_rows.append("")
        for ally in reserve_allies:
            ally_line = format_ally_status_line(ally, idx=None, is_active=False)
            ally_elem = _get_entity_elem_tags(ally, is_enemy=False)
            if ally_elem:
                ally_line += f"  {ally_elem}"
            party_rows.append(ally_line)
            party_rows.append(_get_entity_buff_tags(ally))

    # 4. Gather Enemy Rows (2 rows per entity)
    enemy_rows = []
    for idx, e in enumerate(enemies):
        name = e['name'][:12]
        hp_str = f"{e['hp']}/{e['max_hp']}"
        mg_symbol = " ♀" if e.get("monster_girl") else ""
        enemy_line = f"[{idx+1}] {name:<12} {hp_str:>8}{mg_symbol}"
        enemy_elem = _get_entity_elem_tags(e, is_enemy=True)
        if enemy_elem:
            enemy_line += f"  {enemy_elem}"
        enemy_rows.append(enemy_line)
        enemy_rows.append(_get_entity_buff_tags(e))

    # 5. Pad both sides to the same height
    max_rows = max(len(party_rows), len(enemy_rows), 4)
    while len(party_rows) < max_rows:
        party_rows.append("")
    while len(enemy_rows) < max_rows:
        enemy_rows.append("")

    # 6. Print Side-by-Side Content Columns
    for pl, el in zip(party_rows, enemy_rows):
        safe_pl = pl[:30]
        safe_el = el[:33]
        c_print(f"| {safe_pl:<30} | {safe_el:<33} |")

    # 7. Bottom Frame Actions
    c_print("+" + "-" * 68 + "+")

    # Action menu
    if active_ally is not None:
        menu_str, _, _disabled = _ally_action_menu(active_ally, player, enemies)
    else:
        menu_str, _, _disabled = get_action_menu(player, enemies)
    for line in _wrap_menu_lines(menu_str):
        c_print(f"|  {line:<66}|")

    # Cooldown message (player only)
    if active_ally is None:
        cd_msg = get_abyss_fang_cooldown_display(player)
        if cd_msg:
            c_print(f"|  {cd_msg:<66}|")

        cd_msg2 = get_captain_cutlass_cooldown_display(player)
        if cd_msg2:
            c_print(f"|  {cd_msg2:<66}|")

        # Skill cooldown messages
        skill_cds = player.get('skill_cooldowns', {})
        if skill_cds:
            unlocked = get_all_unlocked_skills(player)
            for sid, sdef in unlocked:
                cd = skill_cds.get(sid, 0)
                if cd > 0:
                    cd_msg = f"({sdef['name']} recharging: {cd} turn(s))"
                    c_print(f"|  {cd_msg:<66}|")
    else:
        # Ally skill cooldown messages
        skill_cds = active_ally.get('skill_cooldowns', {})
        if skill_cds:
            all_skills = get_all_ally_skills(active_ally)
            for sid, sdef in all_skills:
                cd = skill_cds.get(sid, 0)
                if cd > 0:
                    cd_msg = f"({sdef['name']} recharging: {cd} turn(s))"
                    c_print(f"|  {cd_msg:<66}|")

    # Pandemonium: Display active floor curse
    curse = player.get("pandemonium_curse")
    if curse:
        c_print("|" + " " * 68 + "|")
        curse_line = f"  {curse['icon']}  PANDEMONIUM CURSE: {curse['name']} — {curse['desc_full']}"
        c_print(f"| {curse_line:<67}|")

    c_print("+" + "-" * 68 + "+")


def print_superboss_header(player, floor, boss_name, extra_gimmick_line=""):
    time_str = format_time(player)
    if floor is not None:
        c_print(f" Floor {floor} - Superboss: {boss_name} | Time: {time_str}")
    else:
        c_print(f" Superboss: {boss_name} | Time: {time_str}")
    if extra_gimmick_line:
        c_print(extra_gimmick_line)
    status_line = format_player_status_line(player)
    tempo_str = " [Abyssal Tempo]" if is_abyssal_tempo_active(player) else ""
    c_print(f"\n{player['name']}: {player['current_hp']} {status_line}{tempo_str}".rstrip())


def print_player_mini_hud(player, enemies):
    """Inline HUD used during player turn in superboss loop - uses central action menu."""
    print_combat_hud(player, enemies)


def print_turn_order(turn_order, current_idx=None):
    """Print a compact turn order bar."""
    entries = []
    for i, c in enumerate(turn_order):
        marker = ">" if i == current_idx else " "
        label = c.get("label", "?")
        entries.append(f"{marker}{label}")
    c_print(f"  Turn Order: {' -> '.join(entries)}")


def print_round_header(round_num, floor=None, room_num=None, total_rooms=None, time_str=None):
    """Print a clean round header."""
    parts = [f">> ROUND {round_num}"]
    if floor is not None and room_num is not None and total_rooms is not None:
        parts.append(f"Floor {floor} | Room {room_num}/{total_rooms}")
    if time_str:
        parts.append(f"Time: {time_str}")
    c_print("  " + " | ".join(parts))
    c_print("  " + "-" * 66)
