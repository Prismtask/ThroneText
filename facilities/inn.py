# facilities/inn.py
from utils import advance_time, display_name
from character import player_max_hp
from resources.cities import CITIES
from city_dialogue import service_dialogue   # changed
import karma_dialogue
from gui.terminal import term

def inn_menu(player, city_id="solmere"):
    term.clear()
    service_dialogue(city_id, "inn", "enter")
    inn_line = karma_dialogue.service_line(player, "inn", city_id)
    if inn_line:
        term.print(f'  "{inn_line}"')
    city = CITIES.get(city_id, CITIES["solmere"])
    inn_config = city["inn"]

    # ── Wonderland: Mad Hatter's Tea Party (Phase 17) ───────────────────
    if city_id == "wonderland":
        _wonderland_inn_menu(player, city, inn_config)
        return

    term.print(f"=== THE WARM HEARTH INN - {city['name']} ===")
    while True:
        choice = term.menu([
            "Rest (Full Heal - 1 block)",
            "Sleep (Full Heal) - Night only",
            "Play tavern games...",
            "Back"
        ], prompt="What would you like to do?")
        if choice == 0:
            max_hp = player_max_hp(player)
            healed = max_hp - player["current_hp"]
            player["current_hp"] = max_hp
            # Heal allies too
            for ally in player.get("allies", []):
                ally["current_hp"] = ally["max_hp"]
            service_dialogue(city_id, "inn", "rest")
            advance_time(player, 30)
            if healed > 0:
                term.print(f"  Healed {healed} HP → {max_hp}/{max_hp}")
            else:
                term.print("  You were already at full health, but the rest feels nice.")
            term.print("  (1 block passes.)")
            term.pause("You feel refreshed. Press Continue...")
            break
        elif choice == 1:
            import time_blocks
            if time_blocks.get_day_phase(player) == "night":
                # Combat stress: settle falls, then let the party rest.
                from combat.party_stress import on_party_sleep
                for _stress_msg in on_party_sleep(player):
                    term.print(_stress_msg)
                player["current_hp"] = player_max_hp(player)
                # Heal allies too
                for ally in player.get("allies", []):
                    ally["current_hp"] = ally["max_hp"]
                service_dialogue(city_id, "inn", "sleep")
                time_blocks.end_day(player, slept=True)
                # Dream events (docs/dream_events_design.md) — one roll per sleep.
                from dreams import maybe_offer_dream
                maybe_offer_dream(player, "inn", term)
                term.pause("You wake up refreshed the next morning...")
                break
            else:
                service_dialogue(city_id, "inn", "early_sleep")
                term.pause()
        elif choice == 2:
            from facilities.casino_ui import tavern_games_menu
            tavern_games_menu(player, city_id)
        elif choice == 3 or choice == -1:
            service_dialogue(city_id, "inn", "leave")
            break
        else:
            term.print("Invalid choice.")
            advance_time(player, 15)


# ══════════════════════════════════════════════════════════════════════════════
# Wonderland Inn — Mad Hatter's Tea Party (Phase 17)
# ══════════════════════════════════════════════════════════════════════════════

_HEROINE_MENU_LABELS = {
    "alice":    "Talk to the girl in the blue dress (Alice)",
    "red_hood": "Talk to the huntress in the red hood (Red Hood)",
    "dorothy":  "Talk to the girl with the ruby slippers (Dorothy)",
}

_HEROINE_PERM_FLAGS = {
    "alice":    "wonderland_heroine_alice_permanent",
    "red_hood": "wonderland_heroine_redhood_permanent",
    "dorothy":  "wonderland_heroine_dorothy_permanent",
}

_HEROINE_FULL_DIALOGUE = {
    # ── Alice ──────────────────────────────────────────────────────────
    "alice": {
        "unmet": [
            'Alice sits at the far end of the table, teacup in hand. She doesn\'t seem',
            'to notice you until you\'re right beside her.',
            '',
            'Alice: "Oh! I\'m sorry — I was counting the sugar cubes. There are exactly',
            'forty-two, which is the answer to a question I haven\'t asked yet."',
        ],
        "who": [
            'Alice: "Alice. I followed a rabbit once, and then a cat, and then...',
            'I\'m not quite sure how I got *here*, specifically. The book',
            'shuffled its pages again. It does that."',
        ],
        "why": [
            'Alice: "There\'s a beast here — a Jabberwock. It\'s been writing its own',
            'story, and it\'s *terrible*. Run-on sentences everywhere. I tried',
            'to edit it, but it... didn\'t appreciate the feedback."',
        ],
        "join": [
            'Alice: "You\'re going into the Storybook Dungeon? Oh, please take me with',
            'you! I know the way — mostly. Sometimes the path is upside-down,',
            'but I\'ve learned to walk on ceilings."',
        ],
        "joined": 'Alice stands beside you, teacup still in hand. "Lead the way."',
        "declined": 'Alice: "Oh. Well... I\'ll be here. Counting sugar cubes. It\'s what I do."',
        "already_temp": 'Alice smiles. "I\'m already with you. Let\'s not keep the story waiting."',
        "already_permanent": 'Alice: "You came back! The story outside is so much more interesting than the one in here."',
    },

    # ── Red Hood ───────────────────────────────────────────────────────
    "red_hood": {
        "unmet": [
            'Red Hood sits with her back to the wall, a basket on the table. Her crimson',
            'hood is pulled low, but wolf ears twitch beneath it. She\'s sharpening a',
            'woodcutter\'s axe.',
            '',
            'Red Hood: "You\'re not from here. Good. The locals have a... particular sense',
            'of humour. The last person who asked me for directions turned left',
            'at the wrong mushroom and hasn\'t been seen since."',
        ],
        "who": [
            'Red Hood: "The forest is wherever the wolf is. And the wolf? He\'s here.',
            'Calls himself \'The Big Bad.\' Thinks he\'s clever because he ate',
            'the original ending to my story. I\'m here to write a new one."',
        ],
        "why": [
            'Red Hood: "Provisions. Healing herbs. A whetstone. And a very angry',
            'letter to my grandmother\'s estate lawyer. The usual."',
        ],
        "join": [
            'Red Hood: (She tests the axe\'s edge with her thumb, nods.)',
            '"Fine. You watch my back, I\'ll watch yours. But when we find',
            'the Wolf — he\'s mine."',
        ],
        "joined": 'Red Hood shoulders her axe. "Let\'s hunt."',
        "declined": 'Red Hood: "Suit yourself. The Wolf won\'t hunt itself... but I will."',
        "already_temp": 'Red Hood: "Already sharpened my axe. Let\'s go."',
        "already_permanent": 'Red Hood: "Back for more? Good. I was getting bored of sitting still."',
    },

    # ── Dorothy ────────────────────────────────────────────────────────
    "dorothy": {
        "unmet": [
            'Dorothy sits by the window, a pair of ruby slippers on the table before',
            'her. She\'s not wearing them — just looking at them, her expression distant.',
            'A small black dog sleeps at her feet.',
            '',
            'Dorothy: "They say these can take me home. Three clicks and I\'d be back in',
            'Kansas. But every time I try... I end up somewhere worse."',
            '',
            'She looks up at you. Her eyes are tired but not defeated.',
            '',
            '"Are you real? You don\'t look like the others. The ones she writes.',
            'You look like... someone who actually chooses where they\'re going."',
        ],
        "who": [
            'Dorothy: "The one with the pen. She wrote a witch for me to fight, and a',
            'wizard to disappoint me, and a road that never really ends. I\'ve',
            'walked it six times now. It changes, but it never... stops."',
        ],
        "why": [
            'Dorothy: "More than anything. But I think... I think I can\'t go home until',
            'I finish the story. And the story wants me to kill a witch."',
            '(She glances at the slippers.) "These won\'t work until I do."',
        ],
        "join": [
            'Dorothy: (She studies you for a long moment. The dog lifts its head.)',
            '"Toto says you\'re okay. And Toto\'s never wrong about people."',
            'She picks up the slippers — but puts them in her bag, not on her',
            'feet. "Lead the way. But if we see a witch... I\'m not running."',
        ],
        "joined": 'Dorothy tucks the slippers away. Toto wags his tail. "We\'re with you."',
        "declined": 'Dorothy: "I understand. I\'ll be here... staring at shoes."',
        "already_temp": 'Dorothy: "We\'re already walking together. Don\'t forget."',
        "already_permanent": 'Dorothy: "Back in Wonderland? It feels... smaller now. Like a story I\'ve already read."',
    },
}


def _wonderland_inn_menu(player, city, inn_config):
    """Mad Hatter's Tea Party — staged Wonderland guest room."""
    from combat.ally import (
        ensure_party_order, get_heroine_in_party,
        set_heroine_state,
    )
    import wonderland_guests as guests_mod

    city_id = "wonderland"

    # ── Restore saved temp heroines from previous Wonderland visit ──────
    # This handles the edge case where a save is loaded directly in Wonderland
    # without going through _enter_wonderland (which normally restores them).
    saved_temps = player.pop("wonderland_saved_temp_heroines", [])
    if saved_temps:
        for saved in saved_temps:
            hk = saved.get("_heroine_key")
            already_in_party = get_heroine_in_party(player, hk)
            if not already_in_party:
                if hk in _HEROINE_PERM_FLAGS and player.get(_HEROINE_PERM_FLAGS[hk]):
                    saved["_wonderland_temp"] = False
                    guests_mod.set_guest_state(player, hk, "resolved")
                else:
                    saved["_wonderland_temp"] = True
                    set_heroine_state(player, hk, "temp")
                    if guests_mod.get_guest_state(player, hk) not in ("late", "resolved"):
                        guests_mod.set_guest_state(player, hk, "accepted")
                player.setdefault("allies", []).append(saved)
                ensure_party_order(player)
                term.print(f"\n💫 {display_name(saved)} rematerializes beside you — your journey together resumes.")
        if saved_temps:
            term.pause()

    # ── Guest arrivals (Floor 10 / 20 / 30 gates) ──────────────────────
    scenes = guests_mod.on_inn_enter(player)
    for scene in scenes:
        _print_wonderland_guest_scene(scene, player)
    if scenes:
        term.pause()

    term.print(f"=== THE MAD HATTER'S TEA PARTY — {city['name']} ===")
    if guests_mod.menu_keys(player):
        term.print("The table is set for twenty-four. A few guest chairs are occupied.")
    else:
        term.print("The table is set for twenty-four. Every guest chair is empty.")
        term.print('"No guests for you yet," the Hatter says. "The Queen\'s chapter comes first."')
    term.print("")

    while True:
        menu_options = [
            "Rest (Full Heal - no time passes here)",
            "Sleep (Full Heal) - Always teatime here...",
        ]
        guest_keys = guests_mod.menu_keys(player)
        for hk in guest_keys:
            menu_options.append(_wonderland_guest_label(player, hk))
        menu_options.append("Ask the Hatter about the guests")
        menu_options.append("Back")

        choice = term.menu(menu_options, prompt="What would you like to do?")

        if choice == -1:
            service_dialogue(city_id, "inn", "leave")
            break

        if choice == 0:
            # Rest
            max_hp = player_max_hp(player)
            healed = max_hp - player["current_hp"]
            player["current_hp"] = max_hp
            for ally in player.get("allies", []):
                ally["current_hp"] = ally["max_hp"]
            service_dialogue(city_id, "inn", "rest")
            advance_time(player, 30)
            if healed > 0:
                term.print(f"  Healed {healed} HP → {max_hp}/{max_hp}")
            else:
                term.print("  You were already at full health, but the tea is lovely.")
            term.print("  (No time passes in the pocket.)")
            term.pause("The tea was excellent. Probably. Press Continue...")
            break

        elif choice == 1:
            # Sleep (Wonderland time pocket: the outside day is untouched)
            import time_blocks
            player["current_hp"] = player_max_hp(player)
            for ally in player.get("allies", []):
                ally["current_hp"] = ally["max_hp"]
            service_dialogue(city_id, "inn", "sleep")
            time_blocks.end_day(player, slept=True)
            term.pause("You dream of riddles without answers. You wake... eventually...")
            break

        elif 2 <= choice < 2 + len(guest_keys):
            hk = guest_keys[choice - 2]
            _heroine_interaction(player, hk, inn_config)

        elif choice == 2 + len(guest_keys):
            for line in guests_mod.hatter_hint(player):
                term.print(line)
            term.pause()

        elif choice == 3 + len(guest_keys):
            service_dialogue(city_id, "inn", "leave")
            break

        else:
            term.print("Invalid choice.")
            advance_time(player, 15)


def _print_wonderland_guest_scene(scene, player):
    """Print the one-time Hatter scenes for a guest arrival."""
    if scene == "three_guests":
        import wonderland_guests as guests_mod
        red_state = guests_mod.get_guest_state(player, "red_hood")
        term.print("The Hatter looks up as you enter. \"There you are.\"")
        term.print("\"Three guests came asking for you while the Queen was losing her head.\"")
        term.print("\"A huntress in red. A girl with silver shoes. A dreamer in blue.\"")
        term.print("\"They left before I could pour. Said they'll be back when the next chapter turns.\"")
        if red_state == "late":
            term.print("\"The huntress came back after the Wolf fell. She's waiting by the fireplace.\"")
        elif red_state == "resolved":
            term.print("\"The huntress has already found her ending. The other two are still waiting.\"")
        else:
            term.print("\"The huntress, though — she's been pacing by the fireplace. Wouldn't sit down.\"")
    elif scene == "red_hood_arrives":
        term.print("Red Hood is waiting by the fireplace, axe across her knees.")
    elif scene == "dorothy_arrives":
        term.print("A girl with silver slippers sits by the window. A small black dog sleeps at her feet.")
    elif scene == "alice_arrives":
        term.print("Alice sits at the far end of the table, counting sugar cubes.")


def _wonderland_guest_label(player, heroine_key):
    """Menu label for the guest's current stage."""
    import wonderland_guests as guests_mod
    base = _HEROINE_MENU_LABELS[heroine_key]
    state = guests_mod.get_guest_state(player, heroine_key)
    if state == "late":
        return base + " — unfinished story"
    ally = next((a for a in player.get("allies", [])
                 if a.get("_heroine_key") == heroine_key), None)
    if ally is not None and not ally.get("_wonderland_temp", True):
        return base + " ✓ (Permanent)"
    if ally is not None:
        return base + " ✓ (Traveling with you)"
    if player.get(_HEROINE_PERM_FLAGS.get(heroine_key, "")):
        return base
    return base


def _late_arc_interaction(player, heroine_key):
    """Close a skipped heroine's arc without replaying her boss."""
    import wonderland_guests as guests_mod

    lines = {
        "red_hood": [
            "Red Hood is by the fireplace. The crimson hood is folded in her lap.",
            '"I heard the Wolf fell. I wanted to be the one... but I\'m glad it\'s over."',
            '"Grandmother\'s axe is still out there. I want to finish what she started."',
        ],
        "dorothy": [
            "Dorothy sits by the window, turning the silver slippers over in her hands.",
            '"The Witch is gone. The slippers are quiet."',
            '"I could go home. But I think I want to see how your story ends first."',
        ],
        "alice": [
            "Alice is at the far end of the table, a cold cup of tea in front of her.",
            '"You wrote the ending without me. That\'s all right."',
            '"I\'ve been writing my own. I think it\'s ready for a second chapter."',
        ],
    }
    for line in lines.get(heroine_key, ["..."]):
        term.print(line)
    term.print("")
    choice = term.menu([
        f'"Finish her story." (Make {guests_mod.GUEST_NAMES[heroine_key]} permanent)',
        '"Not yet."',
    ], prompt="")
    if choice == 0:
        ok, msg = guests_mod.resolve_late_arc(player, heroine_key)
        term.print(msg)
        if ok:
            _sync_heroine_quest(player, heroine_key, "heroine_permanent")
    term.pause()


def _sync_heroine_quest(player, heroine_key, obj_type):
    """Start/advance a heroine's Journal arc after a tea-party state change."""
    from quests import update_quests
    for msg in update_quests(player, obj_type, heroine_key):
        term.print(msg)


def _heroine_interaction(player, heroine_key, inn_config):
    """Handle dialogue with a Wonderland heroine."""
    from combat.ally import (
        create_heroine_ally, get_heroine_in_party,
        get_heroine_state, set_heroine_state,
    )

    dialogue = _HEROINE_FULL_DIALOGUE.get(heroine_key, {})
    state = get_heroine_state(player, heroine_key)
    existing = get_heroine_in_party(player, heroine_key)

    term.clear()

    import wonderland_guests as guests_mod
    guest_state = guests_mod.get_guest_state(player, heroine_key)
    if guest_state == "late":
        _late_arc_interaction(player, heroine_key)
        return
    if guest_state == "away":
        term.print("The chair is empty. The Hatter says she has not arrived yet.")
        term.pause()
        return

    # ── Already permanent and in party ──────────────────────────────────
    if existing and not existing.get("_wonderland_temp", True):
        # ── Alice vorpal blade interaction (permanent) ─────────────────
        if heroine_key == "alice":
            has_vorpal_equipped = (
                existing.get("equipped", {}).get("weapon", {}).get("id")
                in ("vorpal_blade_rusted", "vorpal_blade")
            )
            has_blade_in_inv = any(
                item.get("id") == "vorpal_blade_rusted"
                for item in player.get("inventory", [])
            )

            if has_vorpal_equipped:
                weapon_name = existing["equipped"]["weapon"]["name"]
                if "???" in weapon_name:
                    term.print(f'Alice cradles the {weapon_name}. "It\'s getting stronger. I can feel it '
                               'stirring — especially near the deeper floors."')
                else:
                    term.print(f'Alice holds the {weapon_name} with quiet reverence. "Snicker-snack," '
                               'she murmurs. "The story is complete. But there are always new stories."')
                term.pause()
                return

            if has_blade_in_inv:
                term.print('Alice sees the blade in your pack. "You still have it? After everything?')
                term.print('I thought... after all we\'ve been through, you might have forgotten."')
                term.print("")
                sub = term.menu([
                    '"It was always meant for you." (Give ??? Blade)',
                    '"I\'m not ready to part with it yet."',
                ], prompt="")
                if sub == 0:
                    from combat.ally import equip_ally_item
                    blade_item = next(
                        (item for item in player.get("inventory", [])
                         if item.get("id") == "vorpal_blade_rusted"), None
                    )
                    if blade_item:
                        result = equip_ally_item(existing, blade_item, player)
                        term.print(result)
                    term.pause()
                    return
                else:
                    term.print('Alice smiles. "Stories wait. I\'ve learned that much."')
                    term.pause()
                    return

        # ── Red Hood axe interaction (permanent) ─────────────────────
        if heroine_key == "red_hood":
            has_axe_equipped = (
                existing.get("equipped", {}).get("weapon", {}).get("id")
                in ("woodcutters_broken_axe", "grandmothers_axe")
            )
            has_axe_in_inv = any(
                item.get("id") == "woodcutters_broken_axe"
                for item in player.get("inventory", [])
            )

            if has_axe_equipped:
                weapon_name = existing["equipped"]["weapon"]["name"]
                if "Broken" in weapon_name:
                    term.print(f'Red Hood runs a thumb along the {weapon_name}. "The Woodcutter '
                               'said it would wake up when the Wolf died. The Wolf is dead. '
                               'But it still feels... incomplete."')
                else:
                    term.print(f'Red Hood holds the {weapon_name} with quiet reverence. '
                               '"Grandmother\'s Axe. She used it to chop firewood. The Wolf '
                               'never knew what hit him."')
                term.pause()
                return

            if has_axe_in_inv:
                term.print('Red Hood sees the axe handle sticking out of your pack. She goes still.')
                term.print('"All this time. All this time you had it, and you didn\'t say anything."')
                term.print("")
                sub = term.menu([
                    '"It belongs with you." (Give Broken Axe)',
                    '"I\'m still not sure it\'s safe."',
                ], prompt="")
                if sub == 0:
                    from combat.ally import equip_ally_item
                    axe_item = next(
                        (item for item in player.get("inventory", [])
                         if item.get("id") == "woodcutters_broken_axe"), None
                    )
                    if axe_item:
                        result = equip_ally_item(existing, axe_item, player)
                        term.print(result)
                    term.pause()
                    return
                else:
                    term.print('Red Hood nods slowly. "Safety is a lie the Wolf taught me. '
                               'Take your time. I\'ve waited this long."')
                    term.pause()
                    return

        # ── Dorothy slippers interaction (permanent) ──────────────────
        if heroine_key == "dorothy":
            has_slippers_equipped = (
                existing.get("equipped", {}).get("accessory1", {}).get("id")
                in ("silver_slippers", "ruby_slippers")
            )
            has_slippers_in_inv = any(
                item.get("id") == "silver_slippers"
                for item in player.get("inventory", [])
            )

            if has_slippers_equipped:
                slipper_name = existing["equipped"]["accessory1"]["name"]
                if "Silver" in slipper_name:
                    term.print(f'Dorothy looks down at the {slipper_name}. "They\'re beautiful. '
                               'Quieter than I expected. The Witch of the East had them first, '
                               'you know. They felt... heavier then."')
                else:
                    term.print(f'Dorothy clicks her heels once — just once. The {slipper_name} '
                               'flash. "There\'s no place like home," she whispers. "And home '
                               'is wherever the story ends."')
                term.pause()
                return

            if has_slippers_in_inv:
                term.print('Dorothy sees the silver glint in your pack. Her hand goes to her chest.')
                term.print('"Are those...? They look like my slippers. But silver. Like the ones '
                           'from before Technicolor. From before everything got... loud."')
                term.print("")
                sub = term.menu([
                    '"The Wizard sent these. For you." (Give Silver Slippers)',
                    '"Let me hold onto them a little longer."',
                ], prompt="")
                if sub == 0:
                    from combat.ally import equip_ally_item
                    slippers_item = next(
                        (item for item in player.get("inventory", [])
                         if item.get("id") == "silver_slippers"), None
                    )
                    if slippers_item:
                        result = equip_ally_item(existing, slippers_item, player)
                        term.print(result)
                    term.pause()
                    return
                else:
                    term.print('Dorothy nods. "They\'ve waited this long. What\'s a little more time '
                               'to a pair of shoes that can cross worlds?"')
                    term.pause()
                    return

        term.print(dialogue.get("already_permanent", f"{heroine_key.title()} is already your permanent ally."))
        term.pause()
        return

    # ── Already temp and in party ───────────────────────────────────────
    if existing and existing.get("_wonderland_temp"):
        # ── Alice + ??? Blade special interaction ────────────────────
        if heroine_key == "alice":
            from combat.ally_skills import swap_alice_to_vorpal_skills

            # Check if Alice already has the vorpal blade equipped
            has_vorpal_equipped = (
                existing.get("equipped", {}).get("weapon", {}).get("id")
                in ("vorpal_blade_rusted", "vorpal_blade")
            )

            # Check if player has the blade in inventory
            has_blade_in_inv = any(
                item.get("id") == "vorpal_blade_rusted"
                for item in player.get("inventory", [])
            )

            if has_vorpal_equipped:
                term.print('Alice holds the blade up. "It still hums. Like it\'s waiting for something."')
                term.print("")
                # Check if upgrade is possible
                if (player.get("wl_godmother_spoken") and
                    player.get("wl_boss_defeated_jabberwock") and
                    not player.get("wl_godmother_blade_upgraded")):
                    term.print('"Perhaps the Godmother at the Temple can help us finish what we started."')
                term.pause()
                return

            if has_blade_in_inv:
                term.print('Alice looks at you curiously. "You have something. I can feel it — ')
                term.print('like a half-remembered poem. What is it?"')
                term.print("")

                sub = term.menu([
                    '"This blade... I think it was meant for you." (Give ??? Blade)',
                    '"Just a rusty old sword. Never mind."',
                ], prompt="")

                if sub == 0:
                    # Give the blade to Alice
                    term.print("")
                    term.print('Alice takes the rusted blade. Her fingers trace the faded inscription.')
                    term.print('"Vorpal..." she whispers. The blade shimmers faintly, as if waking.')
                    term.print('"I remember. I remember the poem. The Jabberwock. The beamish boy."')
                    term.print('She looks at you with new determination. "Let\'s finish the story."')
                    term.print("")

                    # Equip vorpal_blade_rusted on Alice
                    from combat.ally import equip_ally_item
                    blade_item = next(
                        (item for item in player.get("inventory", [])
                         if item.get("id") == "vorpal_blade_rusted"), None
                    )
                    if blade_item:
                        result = equip_ally_item(existing, blade_item, player)
                        term.print(result)
                    term.pause()
                    return
                else:
                    term.print('Alice nods slowly. "If you say so. But... keep it close. Some stories '
                               'don\'t like being ignored."')
                    term.pause()
                    return

            # Player spoke to godmother but blade not in inventory (given away/lost?)
            if player.get("wl_godmother_spoken"):
                term.print('"The Godmother gave you something, didn\'t she? I can feel its echo."')
                term.print('Alice tilts her head. "If you still have it... bring it to me."')
                term.pause()
                return

        # ── Red Hood + Woodcutter's Axe special interaction ──────────
        if heroine_key == "red_hood":
            has_axe_equipped = (
                existing.get("equipped", {}).get("weapon", {}).get("id")
                in ("woodcutters_broken_axe", "grandmothers_axe")
            )

            has_axe_in_inv = any(
                item.get("id") == "woodcutters_broken_axe"
                for item in player.get("inventory", [])
            )

            if has_axe_equipped:
                weapon_name = existing["equipped"]["weapon"]["name"]
                if "Broken" in weapon_name:
                    term.print(f'Red Hood tests the {weapon_name}\'s edge. "It\'s not what it was. '
                               'But it remembers."')
                else:
                    term.print(f'Red Hood swings the {weapon_name} in a slow arc. '
                               '"Grandmother would be proud. The Wolf won\'t come back this time."')
                term.pause()
                return

            if has_axe_in_inv:
                term.print('Red Hood\'s eyes widen. She reaches toward your pack before stopping herself.')
                term.print('"That axe. I\'d know its weight anywhere. That\'s... that\'s the Woodcutter\'s. '
                           'The one that saved me."')
                term.print("")

                sub = term.menu([
                    '"He wanted you to have it." (Give Broken Axe)',
                    '"Not yet. It\'s not ready."',
                ], prompt="")

                if sub == 0:
                    term.print("")
                    term.print('Red Hood takes the broken axe. Her knuckles go white around the haft.')
                    term.print('"He gave this to you? The Woodcutter? I thought he was just... '
                               'a story they told me. Like the happy ending they promised."')
                    term.print('She looks up, and there\'s something feral in her eyes — '
                               'but it\'s not anger. It\'s hope.')
                    term.print('"Let\'s find the Wolf. I want to show him what this axe still remembers."')
                    term.print("")

                    from combat.ally import equip_ally_item
                    axe_item = next(
                        (item for item in player.get("inventory", [])
                         if item.get("id") == "woodcutters_broken_axe"), None
                    )
                    if axe_item:
                        result = equip_ally_item(existing, axe_item, player)
                        term.print(result)
                    term.pause()
                    return
                else:
                    term.print('Red Hood exhales slowly. "When it\'s ready. I\'ve learned patience. '
                               'The Wolf taught me that — the hard way."')
                    term.pause()
                    return

            if player.get("wl_woodcutter_spoken"):
                term.print('"The Woodcutter," Red Hood says quietly. "He\'s here, isn\'t he? I can '
                           'smell the pine sap and whetstone. If he gave you something... don\'t keep it from me."')
                term.pause()
                return

        # ── Dorothy + Silver Slippers special interaction ────────────
        if heroine_key == "dorothy":
            has_slippers_equipped = (
                existing.get("equipped", {}).get("accessory1", {}).get("id")
                in ("silver_slippers", "ruby_slippers")
            )
            has_slippers_in_inv = any(
                item.get("id") == "silver_slippers"
                for item in player.get("inventory", [])
            )

            if has_slippers_equipped:
                slipper_name = existing["equipped"]["accessory1"]["name"]
                if "Silver" in slipper_name:
                    term.print(f'Dorothy taps the {slipper_name} together. "They hum. Like '
                               'a storm that hasn\'t decided where to land."')
                else:
                    term.print(f'Dorothy gazes at the {slipper_name}. "They\'re real now. '
                               'Not just a story prop. They\'re MINE."')
                term.pause()
                return

            if has_slippers_in_inv:
                term.print('Dorothy\'s eyes fix on your pack. Toto whines softly.')
                term.print('"Those aren\'t mine," she says slowly. "My slippers are — were — '
                           'red. But those feel the same. The same hum. The same storm."')
                term.print("")
                sub = term.menu([
                    '"They\'re yours now." (Give Silver Slippers)',
                    '"Let me keep them safe for now."',
                ], prompt="")
                if sub == 0:
                    term.print("")
                    term.print('Dorothy takes the silver slippers. They gleam against her palms '
                               'like captured starlight.')
                    term.print('"The Wizard," she breathes. "The real Wizard — not the humbug — '
                               'he sent these? I thought I\'d never see him again. I thought '
                               'he was just... another story that ended."')
                    term.print('She slips them on. A warm wind circles her ankles. '
                               '"They\'re not home. But they\'re the road there. Let\'s walk it."')
                    term.print("")
                    from combat.ally import equip_ally_item
                    slippers_item = next(
                        (item for item in player.get("inventory", [])
                         if item.get("id") == "silver_slippers"), None
                    )
                    if slippers_item:
                        result = equip_ally_item(existing, slippers_item, player)
                        term.print(result)
                    term.pause()
                    return
                else:
                    term.print('Dorothy strokes Toto\'s ears. "Okay. The road\'s still there '
                               'tomorrow. It always is."')
                    term.pause()
                    return

            if player.get("wl_wizard_spoken"):
                term.print('"The Wizard," Dorothy says. "He\'s here, isn\'t he? I can feel '
                           'his... presence. Like ozone before a storm. If he gave you '
                           'something — please. Don\'t keep me in Kansas."')
                term.pause()
                return

        # Standard already-temp message for non-heroine or without item
        term.print(dialogue.get("already_temp", f"{heroine_key.title()} is already traveling with you."))
        term.pause()
        return

    # ── UNMET → INTRO ──────────────────────────────────────────────────
    if state == "unmet":
        for line in dialogue.get("unmet", ["..."]) :
            term.print(line)
        term.print("")

        # First conversation options
        sub = term.menu([
            '"Who are you?"',
            '"Why are you here?"',
            '"Not now." (Step away)',
        ], prompt="")
        if sub == 0:
            for line in dialogue.get("who", ["..."]):
                term.print(line)
        elif sub == 1:
            for line in dialogue.get("why", ["..."]):
                term.print(line)
        elif sub == 2 or sub == -1:
            term.print(dialogue.get("declined", "..."))
            term.pause()
            return

        # Transition to INTRO
        set_heroine_state(player, heroine_key, "intro")
        _sync_heroine_quest(player, heroine_key, "heroine_met")
        term.print("")
        term.pause("Press Enter...")

    # ── INTRO → "Join me" option ───────────────────────────────────────
    if state == "intro":
        for line in dialogue.get("unmet", ["..."]):
            term.print(line)
        term.print("")

        sub = term.menu([
            '"Who are you?"',
            '"Why are you here?"',
            '"Would you like to travel with me?"',
            '"Not now." (Step away)',
        ], prompt="")

        if sub == 0:
            for line in dialogue.get("who", ["..."]):
                term.print(line)
            term.pause()
        elif sub == 1:
            for line in dialogue.get("why", ["..."]):
                term.print(line)
            term.pause()
        elif sub == 2:
            # Join!
            for line in dialogue.get("join", ["..."]):
                term.print(line)
            term.print("")

            # Create and add heroine ally
            current_floor = player.get("saved_dungeon_floor", 1)
            ally = create_heroine_ally(player, heroine_key, floor=current_floor)
            if ally:
                player.setdefault("allies", []).append(ally)
                # Ensure party_order
                from combat.ally import ensure_party_order
                ensure_party_order(player)
                set_heroine_state(player, heroine_key, "temp")
                guests_mod.set_guest_state(player, heroine_key, "accepted")
                _sync_heroine_quest(player, heroine_key, "heroine_recruited")
                term.print(dialogue.get("joined", f"{heroine_key.title()} joins your party!"))
            else:
                term.print("(Something went wrong... the page is blank.)")
            term.pause()
        elif sub == 3 or sub == -1:
            set_heroine_state(player, heroine_key, "declined")
            _sync_heroine_quest(player, heroine_key, "heroine_met")
            term.print(dialogue.get("declined", "..."))
            term.pause()

    # ── DECLINED → can ask again ───────────────────────────────────────
    elif state == "declined":
        for line in dialogue.get("unmet", ["..."]):
            term.print(line)
        term.print("")

        sub = term.menu([
            '"Change your mind? Want to join me?"',
            '"Not now." (Step away)',
        ], prompt="")

        if sub == 0:
            for line in dialogue.get("join", ["..."]):
                term.print(line)
            term.print("")

            current_floor = player.get("saved_dungeon_floor", 1)
            ally = create_heroine_ally(player, heroine_key, floor=current_floor)
            if ally:
                player.setdefault("allies", []).append(ally)
                from combat.ally import ensure_party_order
                ensure_party_order(player)
                set_heroine_state(player, heroine_key, "temp")
                guests_mod.set_guest_state(player, heroine_key, "accepted")
                _sync_heroine_quest(player, heroine_key, "heroine_recruited")
                term.print(dialogue.get("joined", f"{heroine_key.title()} joins your party!"))
            else:
                term.print("(Something went wrong... the page is blank.)")
            term.pause()
        elif sub == 1 or sub == -1:
            term.print(dialogue.get("declined", "..."))
            term.pause()

    # ── Already temp (shouldn't hit this due to check above, but safety) ─
    elif state == "temp":
        term.print(dialogue.get("already_temp", f"{heroine_key.title()} is already traveling with you."))
        term.pause()

    # ── Already permanent (shouldn't hit this either) ──────────────────
    elif state == "permanent":
        # If they're not in the party, offer to re-recruit them
        if not existing:
            term.print(dialogue.get("already_permanent",
                       f"{heroine_key.title()} is your permanent ally, but not currently in your party."))
            term.print("")
            sub = term.menu([
                '"Rejoin me." (Add to party)',
                '"Not right now." (Step away)',
            ], prompt="")
            if sub == 0:
                from combat.ally import ensure_party_order, _HEROINE_TEMPLATE_KEYS
                current_floor = player.get("saved_dungeon_floor", 1)
                ally = create_heroine_ally(player, heroine_key, floor=current_floor)
                if ally:
                    ally["_wonderland_temp"] = False  # already permanent
                    # Merge any house-record progress (affection/exp/rings) so
                    # a heroine who was returned home never rejoins as a blank copy.
                    template_key = _HEROINE_TEMPLATE_KEYS.get(heroine_key)
                    for house in player.get("houses", {}).values():
                        for g in house.get("monster_girls", []):
                            if g.get("key") == template_key:
                                ally["affection"] = g.get("affection", ally["affection"])
                                ally["affection_cap"] = g.get("affection_cap", ally["affection_cap"])
                                ally["engaged"] = g.get("engaged", False)
                                ally["married"] = g.get("married", False)
                                if g.get("ring_stat_bonus"):
                                    ally["ring_stat_bonus"] = dict(g["ring_stat_bonus"])
                                ally["nickname"] = g.get("nickname", ally.get("nickname", ""))
                                ally["exp"] = g.get("exp", 0)
                                break
                    player.setdefault("allies", []).append(ally)
                    ensure_party_order(player)
                    term.print(dialogue.get("joined", f"{heroine_key.title()} rejoins your party!"))
                else:
                    term.print("(Something went wrong... the page is blank.)")
                term.pause()
            else:
                term.print(f'{heroine_key.title()} nods. "I\'ll be here."')
                term.pause()
        else:
            term.print(dialogue.get("already_permanent", f"{heroine_key.title()} is your permanent ally."))
            term.pause()