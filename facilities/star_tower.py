"""Skylume's Star Tower — the Stellar Archive (Archivist Quillan Voss).

Registered as the "star_tower" city service for Skylume
(see city.py SERVICE_HANDLERS and resources/city_maps.py).

Flow
────
- Entering records the visit_service quest hook.
- Until MQ1's audience is done, the tower runs the meeting scene: Lumen
  greets you, Voss explains the Field Studies, the Stellar Field Kit is
  granted, and MQ1 completes (rewards + starts the next study).
- Afterwards, the archive menu offers the Resonance Ledger, your active
  Field Studies, some flavor — and claiming the kit if your bag was full.
"""

import quests
from gui.terminal import term
from resources.quests import QUESTS, RESONANCE_GRADES, GRADE_REQUIREMENTS

FIELD_KIT_FLAG = "stellar_field_kit"


# ── Service entry ─────────────────────────────────────────────────────────────

def star_tower_service(player, city_id):
    """Service entry point (called with (player, city_id) by the city UI)."""
    # Quest hook: entering the service records visit_service objectives.
    for msg in quests.update_quests(player, "visit_service", "star_tower"):
        if msg:
            term.print(msg)

    state = quests.ensure_quest_state(player)
    if not state["flags"].get("met_voss"):
        _meet_the_archivist(player)
        return

    _archive_menu(player)


# ── First audience (MQ1 completion) ──────────────────────────────────────────

def _meet_the_archivist(player):
    """Lumen greets you; Voss sets up the Field Studies and hands over the kit."""
    # If the letter never found them (they walked here first), catch up now.
    catch_up = []
    if quests.quest_state(player, "mq_archivist_01") is None:
        from facilities.archivist_intro import grant_archivist_intro
        catch_up = grant_archivist_intro(player)

    term.clear()
    term.print("═" * 64)
    term.print("  THE STAR TOWER — THE STELLAR ARCHIVE")
    term.print("═" * 64)
    if catch_up:
        for msg in catch_up:
            term.print(msg)
        term.print("(A late star-moth dissolves into your Journal.)")
        term.print("")
    term.print("Warm lamplight. Shelves spiral up past the reach of the stairs.")
    term.print("")
    term.print("A moth the size of a teacup drops from the rafters and hovers in")
    term.print("front of your face — glowing faintly, entirely unafraid.")
    term.pause("Continue")

    term.print("")
    term.print('"You came!" (Her voice is a small, bright hum.) "He said you')
    term.print(' might. Don\'t tell him I told you he\'s been recalibrating the')
    term.print(' door-ward for a week."')
    term.pause("Continue")

    term.print("")
    term.print("She leads you up the spiral to a desk buried in ledgers. The")
    term.print("Archivist looks up — composed, precise, unsurprised.")
    term.print("")
    term.print('VOSS: "Field agent. You came." (a pause) "Good. My instruments')
    term.print(" read bonds from a distance, but they cannot test them. When a")
    term.print(" mortal and a monster girl fight as one, the bond leaves an")
    term.print(' echo. I call it resonance."')
    term.pause("Continue")

    term.print("")
    term.print('VOSS: "Command Resonance has limits — how many voices one handler')
    term.print(" can hold in concert. The Archive rates it in grades: Pitch,")
    term.print(" Timbre, Cadence, and onward. Mine sits at Pitch. One voice.")
    term.print(' Hers."')
    term.print("")
    term.print("(The moth, perched on the ledger, radiates quiet smugness.)")
    term.pause("Continue")

    term.print("")
    term.print('VOSS: "You already walk beside monster girls. You can gather the')
    term.print(" readings I cannot. Field Study One: build a household, and bring")
    term.print(" one girl home. The first clear note — that will tell me whether")
    term.print(' the scale can grow."')
    term.pause("Continue")

    term.print("")
    term.print('VOSS: "Take this. Capture nets are a Black Market commodity;')
    term.print(' consider this one a research loan."')
    for line in _give_field_kit(player):
        term.print(line)
    term.print("")
    term.print('VOSS: "...and this. A resonance blank — a sphere of clouded glass,')
    term.print(' fallen apart. It records the ledger as you grow, and it will come')
    term.print(' together as your household does. Do try not to drop it."')
    for line in quests.grant_resonance_orb(player):
        term.print(line)
    term.print("")
    term.print('LUMEN: "He means: go make a friend. He\'s very bad at saying it.')
    term.print(' Come back when it works — the readings go in the big book!"')
    term.pause("Continue")

    # Complete MQ1: marks the talk_npc objective, grants rewards, starts MQ2.
    messages = quests.update_quests(player, "talk_npc", "archivist_voss")
    term.print("")
    for msg in messages:
        term.print(msg)
    if messages:
        term.print("(Your Journal has been updated.)")
    term.pause("Continue")


# ── Archive menu (after the audience) ────────────────────────────────────────

def _archive_menu(player):
    while True:
        state = quests.ensure_quest_state(player)
        term.clear()
        term.print("═" * 64)
        term.print("  THE STAR TOWER — THE STELLAR ARCHIVE")
        term.print("═" * 64)
        term.print("Voss writes. Lumen keeps everything else running.")
        term.print("")

        options = ["The Resonance Ledger", "Your Field Studies", "Ask about the Archive"]
        if not state["flags"].get(FIELD_KIT_FLAG):
            options.append("Claim the Stellar Field Kit")
        options.append("Leave")

        choice = term.menu(options, prompt="What will you do?", allow_cancel=True)
        if choice == -1:
            return
        label = options[choice]

        if label == "The Resonance Ledger":
            _resonance_ledger(player)
        elif label == "Your Field Studies":
            _field_studies(player)
        elif label == "Ask about the Archive":
            _about_archive(player)
        elif label == "Claim the Stellar Field Kit":
            for line in _give_field_kit(player):
                term.print(line)
            term.pause()
        else:  # Leave
            term.print("Lumen waves from the rafters as you go.")
            return


def _resonance_ledger(player):
    tier = quests.get_resonance_tier(player)
    grade = quests.get_player_grade(player)
    term.print("")
    term.print("--- The Resonance Ledger ---")
    term.print(f'  Current grade : {grade["name"]}   '
               f'({grade["front"]} front / {grade["bench"]} bench)')
    nxt = RESONANCE_GRADES.get(tier + 1)
    if nxt:
        term.print(f'  Next grade    : {nxt["name"]}   '
                   f'({nxt["front"]} front / {nxt["bench"]} bench)')
        req = GRADE_REQUIREMENTS.get(tier + 1, "")
        if req:
            term.print(f'  Requirement   : {req}')
        term.print("  'Grades are earned through the Field Studies,' Voss says.")
        term.print("  'The ceiling is not where tradition claims it is.'")
    else:
        term.print("  'Crescendo. The full swell.' (He almost smiles.)")
    term.pause()


def _field_studies(player):
    state = quests.ensure_quest_state(player)
    term.print("")
    term.print("--- Field Studies ---")
    found = False
    for quest_id, entry in state["active"].items():
        quest = QUESTS.get(quest_id)
        if not quest or quest.get("giver") != "archivist_voss":
            continue
        found = True
        term.print(f'  {quest["name"]}')
        for stage in quest.get("stages", []):
            for obj in stage.get("objectives", []):
                key = f'{obj["type"]}:{obj["target"]}'
                mark = "✓" if entry["objectives"].get(key) else "☐"
                term.print(f'    {mark} {obj["label"]}')
    if not found:
        term.print("  Voss has no studies for you at the moment.")
    term.pause()


def _about_archive(player):
    term.print("")
    term.print('VOSS: "The Stellar Archive keeps the echoes of bonds — long after')
    term.print(' the people in them are gone, the harmony remains. Somewhere in')
    term.print(' these shelves is the limit of what one handler can hold."')
    term.print('LUMEN: "And somewhere in here is his lunch. It\'s been four days."')
    term.pause()


# ── Stellar Field Kit ────────────────────────────────────────────────────────

def _give_field_kit(player):
    """Grant the Stellar Field Kit (starter Capture Net) once. Returns lines."""
    state = quests.ensure_quest_state(player)
    if state["flags"].get(FIELD_KIT_FLAG):
        return []

    from resources.items import build_item
    from inventory import add_item_to_inventory

    net = build_item("capture_net", rarity="common")
    if not add_item_to_inventory(player, net):
        return ["Voss sets the field kit aside — your bag is full. "
                "(Ask for it again when you have room.)"]

    state["flags"][FIELD_KIT_FLAG] = True
    return ["📦 Stellar Field Kit received: Capture Net"]
