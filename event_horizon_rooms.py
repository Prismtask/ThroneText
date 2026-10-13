"""event_horizon_rooms.py — room handlers for the Event Horizon run loop.

Phase 2 pieces: room generation (combat / shop / mote event / fountain /
trials), the flask "who drinks?" flow, trial + boon card choice, the
mote-priced rift shop, milestone grants (high flask / deep boon / trophies),
and the post-room menu.

I/O goes through the shared terminal helpers (``_tprint`` / ``_tpause`` /
``_tmenu``), which route to the GUI facility bridge when one is active —
terminal shows text menus, the GUI shows the same choices as buttons.

All state changes live in ``player["event_horizon"]`` (see event_horizon.py).
"""

import random

from utils import _tprint, _tmenu, _term, display_name
from character import player_max_hp
from resources.items import ITEMS, build_item

# Rift shop wares: FLASKS ONLY (playtest 2026-10-06 — random consumables were
# dead weight once deep fights run minutes long). Three distinct kinds per
# stall; the grade scales with room progress via the flask tier cap, and the
# price scales by grade.
EH_SHOP_FLASK_WARES = 3


def _shop_flask_price(tier, player=None):
    """Ware price by grade; The Devil's drawback taxes the stall (+20%)."""
    import event_horizon as eh
    price = 20 + 20 * int(tier)
    if player is not None:
        price = max(1, int(price * eh.joker_shop_multiplier(player)))
    return price


# ═══════════════════════════════════════════════════════════════════════════
# Room generation
# ═══════════════════════════════════════════════════════════════════════════

def generate_room(player):
    """Roll the next room, or the pending trial if one is due.

    Trials sit BETWEEN numbered rooms and do not count as progress
    (docs §4.1): after clearing e.g. r10, the next room is a trial, then r11.
    """
    import event_horizon as eh

    state = eh.ensure_eh_state(player)
    last = int(state.get("room", 0))

    if (last >= eh.EH_TRIAL_MIN_ROOM
            and last % eh.EH_TRIAL_EVERY == 0
            and int(state.get("trial_done_for", 0)) < last):
        positive = (last % eh.EH_POSITIVE_TRIAL_EVERY == 0)
        return {"type": "trial_pos" if positive else "trial_neg", "for_room": last}

    number = last + 1
    roll = random.random()
    if roll < 0.70:
        pack = 2 + min(3, number // 12)
        count = random.randint(max(2, pack - 1), pack)
        from dungeon import get_random_enemy_key  # lazy — avoid import cycle
        level, band_lo = eh.enemy_band_for_room(player, number)
        enemies = [get_random_enemy_key(level, boss=False, region=None,
                                        player=player, band_lo=band_lo)
                   for _ in range(count)]
        return {"type": "combat", "number": number, "enemies": enemies}
    if roll < 0.82:
        return {"type": "shop", "number": number}
    if roll < 0.92:
        return {"type": "event", "number": number}
    return {"type": "fountain", "number": number}


def generate_rush_room(player):
    """Next Boss Rush room (docs §6.4) — the head of the echo queue.

    Room numbers advance 1..N as echoes fall, so payout/best_room/flask
    tiering all behave like a normal run.
    """
    import event_horizon as eh

    state = eh.ensure_eh_state(player)
    queue = list(state.get("rush_queue") or [])
    if not queue:
        # Stale state (crashed between last kill and completion) — the
        # dungeon loop treats this as "rush done" and pays out.
        return {"type": "rush_done", "number": int(state.get("room", 0)) + 1}
    total = int(state.get("rush_total", len(queue)) or len(queue))
    boss = eh.rush_boss_by_id(queue[0]) or {"id": queue[0], "name": queue[0],
                                           "keys": [queue[0]]}
    number = total - len(queue) + 1
    return {"type": "boss_rush", "number": number, "boss": boss, "total": total}


def room_title(room):
    rtype = room.get("type")
    if rtype == "combat":
        return f"ROOM {room['number']} — Rift Combat"
    if rtype == "shop":
        return f"ROOM {room['number']} — Rift Merchant"
    if rtype == "event":
        return f"ROOM {room['number']} — Mote Storm"
    if rtype == "fountain":
        return f"ROOM {room['number']} — Still Pool"
    if rtype == "trial_pos":
        return f"TRIAL — a deep boon after room {room.get('for_room', '?')}"
    if rtype == "trial_neg":
        return f"TRIAL — the Horizon demands a toll after room {room.get('for_room', '?')}"
    if rtype == "boss_rush":
        boss = room.get("boss") or {}
        return (f"BOSS RUSH {room.get('number', '?')}/{room.get('total', '?')} — "
                f"the echo of {boss.get('name', '?')}")
    return "ROOM — ???"


# ═══════════════════════════════════════════════════════════════════════════
# Room play
# ═══════════════════════════════════════════════════════════════════════════

def play_room(player, room, combat_override=None, superboss_override=None):
    """Resolve one room. Returns "cleared" | "fled" | "dead" | "timeout"."""
    rtype = room.get("type")
    if rtype == "combat":
        return _play_combat(player, room, combat_override)
    if rtype == "boss_rush":
        return _play_boss_rush(player, room, superboss_override)
    if rtype == "trial_pos":
        return handle_trial_room(player, room)
    if rtype == "trial_neg":
        return handle_trial_room(player, room)
    if rtype == "shop":
        handle_eh_shop(player)
        return "cleared"
    if rtype == "event":
        return handle_eh_event(player)
    if rtype == "fountain":
        return handle_eh_fountain(player)
    return "cleared"


def _catch_breath(player):
    """Post-fight HP recovery (city-loop parity; Death's toll halves it).

    Shared by rift combat rooms and Boss Rush fights.
    """
    from combat.stats import player_con_mod

    heal = random.randint(1, 5) + player_con_mod(player)
    heal = int(heal * (player.get("_eh_joker_healing_mult") or 1))
    player["current_hp"] = min(player["current_hp"] + heal, player_max_hp(player))
    _tprint(f"You catch your breath and recover {heal} HP.")
    for ally in player.get("allies", []):
        if ally.get("current_hp", 0) > 0:
            ally_heal = random.randint(1, 3) + ally["attributes"].get("Constitution", 0)
            ally["current_hp"] = min(ally["current_hp"] + ally_heal, ally["max_hp"])


def _play_combat(player, room, combat_override):
    import event_horizon as eh

    state = eh.ensure_eh_state(player)
    level = eh.enemy_level_for_room(player, room["number"])
    if combat_override:
        result = combat_override(player, room["enemies"], floor=level,
                                 room_num=room["number"], total_rooms=None)
    else:
        from combat.combat_engine import combat as _combat
        result = _combat(player, room["enemies"], floor=level,
                         room_num=room["number"], total_rooms=None)

    if result != "victory":
        return result

    # Motes (no XP / no drops / no per-kill gold in the Event Horizon)
    gain = 6 + int(room["number"]) // 2
    gain = eh.apply_mote_multiplier(player, gain)
    state["motes"] = int(state.get("motes", 0)) + gain
    _tprint(f"\n  ◎ {gain} Horizon Motes scatter from the fading foes.")

    _catch_breath(player)
    return "cleared"


def _play_boss_rush(player, room, superboss_override):
    """One Boss Rush fight (docs §6.4). Flee is blocked — the fight restarts.

    Terminal mode calls the boss combat function directly; the GUI injects
    ``superboss_override(spec, None)`` which shows the shared CombatScreen.
    Rush scaling itself lives in ``event_horizon.apply_enemy_scaling`` (the
    ``rush_mode`` branch), so both paths scale identically.
    """
    import event_horizon as eh

    boss = room["boss"]
    spec = {"rush": True, "boss_id": boss["id"],
            "index": int(room["number"]), "total": int(room["total"])}

    while True:
        if superboss_override:
            result = superboss_override(spec, None)
        else:
            result = eh.rush_boss_combat(boss)(player)
        if result == "fled":
            _tprint("There is no running from the echoes.")
            _tprint("The fight resumes where it left off...")
            continue
        break

    if result != "victory":
        return result

    # Pure linear progress (locked 2026-10-12): no motes, no cards, no flask,
    # no system healing — between echoes only HP and skill buffs persist.
    # Interval healing comes from the player's own bag (the post-room menu's
    # “Inventory / Stats” option).
    return "cleared"


# ═══════════════════════════════════════════════════════════════════════════
# Flask flow
# ═══════════════════════════════════════════════════════════════════════════

def _actor_labels(player):
    labels = []
    actors = [player] + list(player.get("allies", []))
    for actor in actors:
        if actor is player:
            labels.append(f"You ({player.get('name', 'the bearer')})")
        else:
            tag = "" if actor.get("current_hp", 0) > 0 else "  [fallen]"
            labels.append(f"{display_name(actor)}{tag}")
    return actors, labels


def _flask_hint(player, actor):
    """Compact reminder of the flasks this actor already drank (all types)."""
    import event_horizon as eh
    state = eh.ensure_eh_state(player)
    recs = (state.get("actor_flasks") or {}).get(eh.actor_key(actor, player)) or []
    if not recs:
        return ""
    counts = {}
    for rec in recs:
        name = rec.get("name", "?")
        counts[name] = counts.get(name, 0) + 1
    parts = [f"{n}\u00d7{c}" if c > 1 else n for n, c in counts.items()]
    return "  \u2014  " + ", ".join(parts)


def _choose_flask_drinker(player, flask):
    """Mandatory 'who drinks?' pick + apply + log (shared by drops + shop)."""
    import event_horizon as eh

    actors, labels = _actor_labels(player)
    # Remind the player what each actor already carries (per-archetype tally).
    labels = [f"{lab}{_flask_hint(player, actor)}"
              for lab, actor in zip(labels, actors)]
    prompt = f"{flask['label']} — who drinks?"
    idx = _tmenu(labels, prompt=prompt)
    while idx < 0 or idx >= len(actors):
        _tprint("Someone must drink the flask — choose.")
        idx = _tmenu(labels, prompt=prompt)

    actor = actors[idx]
    eh.apply_flask(player, actor, flask)
    who = "You" if actor is player else display_name(actor)
    verb = "drink" if actor is player else "drinks"
    _tprint(f"  {who} {verb} the {flask['label']}.")
    _tprint("  (Permanent for this run — visible in the status HUD and Inventory.)")
    return actor


def offer_flask(player, forced_tier=None, banner=None):
    """Offer one flask; the player picks exactly one actor to drink it."""
    import event_horizon as eh

    state = eh.ensure_eh_state(player)
    room = max(1, int(state.get("room", 1)))
    flask = eh.roll_flask(room, tier=forced_tier)
    if banner:
        _tprint(f"\n◆ {banner}")
    # Announce the flask in the log — previously the drinker menu appeared
    # with no line saying a flask had been received (playtest confusion).
    _tprint(f"\n◆ The Horizon offers a flask: {flask['label']}")
    _tprint("   One actor drinks it — the effect lasts for the rest of the run.")
    _choose_flask_drinker(player, flask)


# ═══════════════════════════════════════════════════════════════════════════
# Trials + deep boons (card choice: terminal text menus / GUI buttons)
# ═══════════════════════════════════════════════════════════════════════════

def handle_trial_room(player, room):
    import event_horizon as eh

    state = eh.ensure_eh_state(player)
    positive = room.get("type") == "trial_pos"
    for_room = int(room.get("for_room", state.get("room", 0)))

    if positive:
        _tprint("\n◆ A deep boon surfaces from the distortion — a gift with no price.")
        prompt = "Choose a boon (mandatory):"
    else:
        _tprint("\n◆ The Horizon demands a toll. Your enemies must carry a burden —")
        _tprint("  (Every card persists for the rest of the run; harder cards add more Entropy.)")
        prompt = "Choose the card your enemies will carry (mandatory):"

    cards = eh.roll_trial_cards(player, positive=positive)
    if not cards:
        # Deck exhausted (playtest 2026-10-07): every kind maxed at T3.
        if positive:
            _tprint("  The deck of boons is spent — the Horizon has no gift left to give.")
        else:
            _tprint("  The deck is spent — the Horizon shows you an empty hand.")
            _tprint("  No burden remains to impose; the toll passes over you.")
        motes = eh.apply_mote_multiplier(player, 10 + for_room // 5)
        state["motes"] = int(state.get("motes", 0)) + motes
        _tprint(f"  ◎ The trial still grants {motes} Horizon Motes.")
        state["trial_done_for"] = for_room
        return "cleared"
    labels = [eh.format_card_label(c) for c in cards]
    idx = _tmenu(labels, prompt=prompt)
    while idx < 0 or idx >= len(cards):
        _tprint("The trial is mandatory — a card must be chosen.")
        idx = _tmenu(labels, prompt=prompt)

    card = cards[idx]
    if positive:
        _tprint(eh.apply_positive_card(player, card))
    else:
        _tprint(eh.apply_negative_card(player, card))

    motes = eh.apply_mote_multiplier(player, 10 + for_room // 5)
    state["motes"] = int(state.get("motes", 0)) + motes
    _tprint(f"  ◎ The trial grants {motes} Horizon Motes.")
    state["trial_done_for"] = for_room
    return "cleared"


def handle_boon(player):
    """Milestone deep boon — pick 1 of 3 positive team cards (mandatory)."""
    import event_horizon as eh

    _tprint("\n◆ DEEP BOON — the distortion offers a lasting gift to the whole party.")
    cards = eh.roll_trial_cards(player, positive=True)
    if not cards:
        _tprint("  The deck of blessings is spent — the Horizon relents.")
        return
    labels = [eh.format_card_label(c) for c in cards]
    prompt = "Choose a deep boon (mandatory):"
    idx = _tmenu(labels, prompt=prompt)
    while idx < 0 or idx >= len(cards):
        _tprint("The boon must be claimed — a card must be chosen.")
        idx = _tmenu(labels, prompt=prompt)
    _tprint(eh.apply_positive_card(player, cards[idx]))


def offer_joker(player):
    """rn+25: the Joker deals 2 arcana — keep one (or refuse).

    Hand model (docs/joker_cards_proposal.md): draws come from the unowned
    pool; at the hand cap a keep requires throwing an owned arcana, which
    returns to the deck. The World closes the deal permanently. Off-deck:
    no Entropy, no payout weight (playtest 2026-10-07).
    """
    import event_horizon as eh

    if eh.has_owned_joker(player, "joker_world"):
        _tprint("\n◆ The Joker tips his hat — the deal is done. "
                "No further cards will be dealt this run.")
        return
    faces = eh.deal_joker_faces(player)
    if not faces:
        _tprint("\n◆ The Joker shuffles — then puts the deck away. "
                "Every face has been shown.")
        return
    _tprint("\n" + "◆" * 25)
    _tprint("  ♠ THE JOKER — a spread of the Arcana.")
    options = [f"Keep {f['name']} — {f['desc']}" for f in faces]
    options.append("Refuse the deal")
    idx = _tmenu(options, prompt="The Joker waits.")
    if idx < 0 or idx >= len(faces):
        _tprint("  You wave the spread away. The Joker bows, unoffended.")
        return
    face = faces[idx]
    replace = None
    if eh.joker_hand_full(player):
        owned = eh.owned_jokers(player)
        throw_options = [f"Throw {r['name']} — {r.get('desc', '')}"
                         for r in owned]
        throw_options.append("Cancel")
        t_idx = _tmenu(throw_options,
                       prompt=(f"Your hand is full — throw an arcana "
                               f"to take {face['name']}."))
        if t_idx < 0 or t_idx >= len(owned):
            _tprint("  You keep your hand as it is.")
            return
        replace = owned[t_idx]
    _tprint(eh.apply_joker(player, face, replace=replace))


# ═══════════════════════════════════════════════════════════════════════════
# Shop (motes only)
# ═══════════════════════════════════════════════════════════════════════════

def handle_eh_shop(player):
    import event_horizon as eh

    state = eh.ensure_eh_state(player)
    room = int(state.get("room", 0))

    _tprint("\n" + "=" * 50)
    _tprint("🏺 A rift-merchant unfolds a stall out of folded space.")
    _tprint('"Motes, motes — the only coin the Horizon honors."')
    _tprint("=" * 50)

    # Every shop visit includes one free flask (docs §3.1)
    offer_flask(player, banner='The merchant uncorks a flask. "On the house, crawler."')

    # Wares: three distinct flask kinds at the depth's grade (scales with
    # room progress via the tier cap; price scales by grade).
    tier_cap = eh.flask_tier_max(room)
    kinds = random.sample(list(eh.FLASK_ARCHETYPES.keys()),
                          k=min(EH_SHOP_FLASK_WARES, len(eh.FLASK_ARCHETYPES)))
    stock = []
    for kind in kinds:
        tier = random.randint(max(1, tier_cap - 1), tier_cap)
        stock.append({"flask": eh.roll_flask(room, tier=tier, kind=kind),
                      "price": _shop_flask_price(tier, player), "sold": False})
    # One ware per visit is discounted (playtest 2026-10-07) — 40% off.
    if stock:
        sale = random.choice(stock)
        sale["full_price"] = sale["price"]
        sale["price"] = max(1, int(sale["full_price"] * 0.6))
        sale["sale"] = True
    tune_price = 50 + room
    tune_available = True

    while True:
        options = []
        for entry in stock:
            if not entry["sold"]:
                options.append(("buy", entry))
        if tune_available:
            options.append(("tune", {"price": tune_price}))
        labels = []
        for kind, entry in options:
            if kind == "buy":
                label = f"{entry['flask']['label']} — {entry['price']} ◎"
                if entry.get("sale"):
                    label += f"  (SALE −40%, was {entry['full_price']} ◎)"
                labels.append(label)
            else:
                labels.append(f"Tune-Up (one actor: +1 all attributes, this run) — {entry['price']} ◎")
        labels.append("Leave")

        idx = _tmenu(labels, prompt=f"Horizon Motes: {state.get('motes', 0)} ◎ — what will it be?")
        if idx < 0 or idx >= len(options):
            _tprint('"May the Horizon spit you out somewhere kind."')
            return

        kind, entry = options[idx]
        if int(state.get("motes", 0)) < entry["price"]:
            _tprint("  Not enough motes.")
            continue

        if kind == "buy":
            flask = entry["flask"]
            state["motes"] = int(state["motes"]) - entry["price"]
            entry["sold"] = True
            _tprint(f"  Bought the {flask['label']} for {entry['price']} ◎.")
            _choose_flask_drinker(player, flask)
        else:
            actor = _pick_actor(player, f"Tune-Up ({entry['price']} ◎) — who grows?")
            if actor is None:
                continue
            actor.setdefault("active_buffs", []).append({
                "type": "stat", "stat": "all", "value": 1,
                "remaining": 9999, "permanent": True,
                "source": eh.EH_SOURCE, "label": "Tune-Up",
            })
            state["motes"] = int(state["motes"]) - entry["price"]
            tune_available = False
            who = "You" if actor is player else display_name(actor)
            _tprint(f"  {who} is tuned up: +1 all attributes (this run).")


def _pick_actor(player, prompt):
    actors, labels = _actor_labels(player)
    idx = _tmenu(labels, prompt=prompt)
    while idx < 0 or idx >= len(actors):
        _tprint("Choose someone.")
        idx = _tmenu(labels, prompt=prompt)
    return actors[idx]


# ═══════════════════════════════════════════════════════════════════════════
# Events / fountain
# ═══════════════════════════════════════════════════════════════════════════

def handle_eh_event(player):
    import event_horizon as eh

    state = eh.ensure_eh_state(player)
    room = int(state.get("room", 0))
    gain = random.randint(3, 8) + room // 10
    gain = eh.apply_mote_multiplier(player, gain)
    state["motes"] = int(state.get("motes", 0)) + gain
    _tprint("\n◆ A storm of drifting motes hums through the chamber.")
    _tprint(f"  You cup your hands and catch {gain} Horizon Motes.")
    return "cleared"


def handle_eh_fountain(player):
    _tprint("\n◆ A still pool floats midair, untouched by the distortion.")
    total = 0
    for actor in [player] + list(player.get("allies", [])):
        if actor.get("current_hp", 0) <= 0:
            continue
        mx = player_max_hp(actor) if actor is player else actor.get("max_hp", 1)
        before = actor["current_hp"]
        actor["current_hp"] = min(mx, before + max(1, int(mx * 0.20)))
        total += actor["current_hp"] - before
    _tprint(f"  The party drinks deep and recovers {total} HP in total.")
    return "cleared"


# ═══════════════════════════════════════════════════════════════════════════
# Milestones + trophies
# ═══════════════════════════════════════════════════════════════════════════

def grant_trophy(player, item_id):
    """Give a trophy item to the player. Returns True if it entered inventory."""
    item = build_item(item_id)
    if not item:
        _tprint(f"  [ERROR] Unknown trophy item: {item_id}")
        return False
    from inventory_ui import prompt_acquire_item
    if prompt_acquire_item(player, item):
        return True
    _tprint(f"  (Your bag is full — the {item.get('name', item_id)} waits in the distortion.)")
    return False


def grant_milestone(player, event):
    """Grant one milestone event (docs §10.3). Queues trophies if the bag is full."""
    import event_horizon as eh

    kind = event.get("kind")
    if kind == "high_flask":
        offer_flask(player, forced_tier=random.randint(6, 7),
                    banner="A milestone flask crystallizes out of the distortion.")
    elif kind == "boon":
        handle_boon(player)
    elif kind in ("trophy", "beating_root"):
        item_id = event.get("item_id") or "beating_root"
        if grant_trophy(player, item_id):
            if eh.claim_milestone(player, event):
                _tprint(f"  ★ Trophy claimed: {ITEMS.get(item_id, {}).get('name', item_id)}")
        else:
            state = eh.ensure_eh_state(player)
            queue = state.setdefault("pending_trophies", [])
            if item_id not in queue:
                queue.append(item_id)


def retry_pending_trophies(player):
    """Retry trophies that couldn't be picked up (bag was full) each room."""
    import event_horizon as eh

    state = eh.ensure_eh_state(player)
    queue = state.get("pending_trophies") or []
    while queue:
        item_id = queue[0]
        if not grant_trophy(player, item_id):
            break
        queue.pop(0)


# ═══════════════════════════════════════════════════════════════════════════
# Post-room menu
# ═══════════════════════════════════════════════════════════════════════════

def post_room_choice(player):
    """Return 'continue' | 'suspend' | 'abandon'. Inventory opens inline (GUI)."""
    t = _term()
    if t:
        while True:
            choice = t.menu(
                ["Continue", "Inventory / Stats", "Save and quit", "Abandon the run"],
                prompt="The distortion waits. What now?", allow_cancel=False)
            if choice == 1:
                t.open_inventory()
                continue
            if choice == 0:
                return "continue"
            if choice == 2:
                return "suspend"
            confirm = t.menu(
                ["Yes — collapse the run", "No — keep descending"],
                prompt="Abandon the run? All progress, motes, cards and flask buffs are lost.",
                allow_cancel=False)
            if confirm == 0:
                return "abandon"

    while True:
        print("\n[Enter] to continue  [I]nventory/Stats  [S]ave and quit  [A]bandon the run")
        cmd = input().strip().lower()
        if cmd == "":
            return "continue"
        if cmd == "i":
            print("Inventory management is only available in GUI mode. Please use the launcher.")
            continue
        if cmd == "s":
            return "suspend"
        if cmd == "a":
            confirm = input("Abandon the run? All progress is lost. [y/N] ").strip().lower()
            if confirm in ("y", "yes"):
                return "abandon"
            continue
