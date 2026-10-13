"""Vesper Erebus, the Horizon Watcher — first contact scene (docs §6.1).

Plays ONCE after the party exits a dungeon with ``max_floor >= 20``
(``eh_intro_seen`` unset). Uses the same NPC UI as Archivist Voss's Star
Tower scene (``gui.terminal`` bridge: paced lines + button/text menus),
launched from CityScreen as a FacilityScreen.

The site **arrival scene** (:func:`event_horizon_arrival_service`) also lives
here; its greeting is context-aware — first arrival, rotating idle lines for
repeat visits, and a one-time line the first time each 25-room milestone is
reached (``plan_vesper_greeting``).

Appearance: a man in a robe whose head is a black hole; he speaks normally,
but his voice echoes. He explains the space-time distortion and reveals the
site on the world map.
"""

from gui.terminal import term


def event_horizon_intro_service(player, city_id=None):
    """FacilityScreen entry point. No-op once seen."""
    if player.get("eh_intro_seen"):
        return

    term.clear()
    term.print("═" * 64)
    term.print("  A TEAR IN THE SKY")
    term.print("═" * 64)
    term.print("The road home bends. For a heartbeat the horizon peels open —")
    term.print("a seam of black glass hanging over the far country, drinking")
    term.print("the light.")
    term.print("")
    term.print("A figure waits at the roadside, as if he has always been there.")
    term.print("A robe, worn plain. Where a head should be: a sphere of")
    term.print("absolute dark, its edge burning faintly — and every word he")
    term.print("speaks arrives twice, the second time from somewhere much")
    term.print("further away.")
    term.pause("Step closer")

    term.print("")
    term.print('VESPER: "Easy. I am not the thing that is wrong here."')
    term.print('VESPER: "...though I am close enough to it that the map blurs."')
    term.print("")
    term.print("He does not turn, but the dark of him tilts toward you —")
    term.print("the way a listener does.")
    term.print('VESPER: "That lightless seam up there? A distortion. Space')
    term.print('folded wrong, and folding worse. I have watched it for a')
    term.print('while now. It is not a door. It is a throat."')
    term.pause("Continue")

    while True:
        choice = term.menu(
            ["Ask about the distortion",
             "Ask who he is",
             "Ask what it wants",
             'Say you will find it ("I will go there.")'],
            prompt="Vesper waits.",
            allow_cancel=False,
        )
        if choice == 0:
            term.print("")
            term.print('VESPER: "Inside, there are rooms. More rooms than there')
            term.print('are reasons for them. Space there is a wheel that keeps')
            term.print('turning — and it pays in weight: gold for depth, power')
            term.print('for pressure, and everything it gives you, it takes')
            term.print('back the moment you leave or die."')
            term.print('VESPER: "The deeper you push, the harder it pushes')
            term.print('back. That is the whole of the bargain."')
            term.pause("Continue")
        elif choice == 1:
            term.print("")
            term.print('VESPER: "A watcher. The name I kept was Vesper')
            term.print('Erebus. The rest of it was eaten years ago — by a')
            term.print('smaller tear than this one."')
            term.print('VESPER: "The echo you hear is not an effect. There')
            term.print('is simply a part of me still falling."')
            term.pause("Continue")
        elif choice == 2:
            term.print("")
            term.print('VESPER: "Nothing that can be asked in a language made')
            term.print('of time. It winds tighter, and it stains what it')
            term.print('touches. If it keeps winding, one day the far country')
            term.print('will be the near country."')
            term.print('VESPER: "You are a climber of floors. A handler of')
            term.print('monster girls. You are the nearest thing to a pin I')
            term.print('have found. That is all I know how to want."')
            term.pause("Continue")
        else:
            break

    player["eh_intro_seen"] = True
    term.print("")
    term.print('VESPER: "Then look at your map. I have marked it. You will')
    term.print('not be able to miss it — it hurts to look at directly."')
    term.print('VESPER: "When you reach it: step in. When it is too much:')
    term.print('step out the way you came. And when you go under for the')
    term.print('third or fourth time — bring me a coin. I want to know')
    term.print('if they still land."')
    term.print("")
    term.print("(A new site appears on the world map: THE EVENT HORIZON.)")
    term.print("(Progress there persists until you die or abandon the run —")
    term.print(" you can save & quit to suspend it from inside.)")
    term.pause("Continue")


def _eh_lore_lines():
    term.print("")
    term.print('VESPER: "Rooms. That is the only honest word for what is')
    term.print('in there. Every room you clear feeds the wheel, and the')
    term.print('wheel pays in weight — gold, motes, power pressed into')
    term.print('your party like heat into iron."')
    term.print('VESPER: "Feed the flask to whoever you can spare least.')
    term.print('And mind the trial rooms — the deep ones think. They lay')
    term.print('cards on the table, and the table is you."')
    term.print('VESPER: "When it is too much: step out the way you came.')
    term.print('Save, quit. It will hold. Death is the only thing down')
    term.print('there that does not."')
    term.pause("Continue")


# ── Vesper's arrival greetings (idle-dialogue system) ───────────────────────
#
# The greeting depends on story context, not randomness:
#   * first-ever arrival — the "you actually came" version;
#   * a newly reached 25-room milestone ("reaching rN for the first time") —
#     bespoke lines at r25 / r50 / r75 / r100 / r125+; acknowledged once per
#     save via the ``eh_vesper_milestone`` high-water mark;
#   * otherwise idle — rotates through a small pool driven by ``eh_visits``
#     so consecutive visits never repeat the same lines.

_EH_IDLE_GREETINGS = (
    ('VESPER: "You are back. The seam did not miss you."',
     'VESPER: "I cannot honestly say the same about myself."'),
    ('VESPER: "It is quiet today. That is how it swallows — politely,"',
     'the way a debt collector is polite."'),
    ('VESPER: "Every descent turns the wheel a fraction. Fractions add."',
     'VESPER: "Nothing you do in there is small. That is not a compliment."'),
    ('VESPER: "The map blurs when I stand this close. You are still the"',
     'nearest thing to a pin I have found."'),
    ('VESPER: "Somewhere down there is a room built out of the idea of you."',
     'VESPER: "Do not linger in it."'),
    ('VESPER: "Bring me a coin some day. I want to know if they still land."',
     'VESPER: "No hurry. I have become good at waiting."'),
)


def _milestone_greeting(room):
    """Bespoke lines for the first time each 25-room mark is reached."""
    if room >= 125:  # every 25 past 100 grants a Beating Root
        return [
            'VESPER: "Past a hundred and still climbing. The wheel hands out',
            'roots now — small, beating things. Keep them. Do not plant them."',
            'VESPER: "It has started giving back. That is not the same as',
            'being kind."',
        ]
    if room >= 100:
        return [
            'VESPER: "A hundred rooms. It gave you something that is not an',
            'object — a piece of a bond, measured and paid out."',
            'VESPER: "Do not let it do the measuring for you."',
        ]
    if room >= 75:
        return [
            'VESPER: "Seventy-five. An old robe came up with you — somebody',
            'stopped climbing early and left it to the wheel."',
            'VESPER: "Wear it like a warning that fits."',
        ]
    if room >= 50:
        return [
            'VESPER: "Fifty rooms, and it paid you in a coin."',
            'VESPER: "I asked you once to bring me one — do you remember? Keep',
            'this one. Flip it where I cannot see."',
        ]
    # r25 — the first high-grade flask milestone.
    return [
        'VESPER: "Twenty-five rooms. Most stop at the first taste."',
        'VESPER: "The wheel pays in weight — a deeper flask came up with you.',
        'Spend it on whoever you can spare least."',
    ]


def plan_vesper_greeting(player, state, room, suspended):
    """Return Vesper's arrival greeting lines; update visit/milestone state.

    Pure text selection (no terminal calls) so tests can drive it headlessly.
    Mutates two player-level bookkeeping flags:
      * ``eh_visits`` — arrival counter (drives idle rotation + first visit);
      * ``eh_vesper_milestone`` — highest 25-room mark already acknowledged.
    """
    visits = int(player.get("eh_visits", 0) or 0) + 1
    player["eh_visits"] = visits

    deepest = max(int(state.get("best_room", 0) or 0), int(room or 0))
    milestone = (deepest // 25) * 25
    acknowledged = int(player.get("eh_vesper_milestone", 0) or 0)
    if milestone > acknowledged:
        player["eh_vesper_milestone"] = milestone
        lines = list(_milestone_greeting(milestone))
        if suspended:
            lines += [f'VESPER: "It is still turning at room {room}. It kept',
                      'turning without you — that is what it does."']
        return lines

    if visits == 1:
        return [
            'VESPER: "You came. Good. It has been getting louder."',
            'VESPER: "Stand here a while. The cold comes off it in waves —',
            'like breath on glass. Now you know what I watch."',
            'VESPER: "When you are ready, step in. I will keep the edge."',
        ]

    lines = list(_EH_IDLE_GREETINGS[(visits - 2) % len(_EH_IDLE_GREETINGS)])
    if suspended:
        lines += [f'VESPER: "You left it turning at room {room}. It kept',
                  'turning without you. It always does."']
    return lines


def event_horizon_arrival_service(player, city_id=None):
    """Site arrival scene (docs §6.1). Returns a result code for on_close:

    ``"enter"`` — no active run; enter fresh
    ``"resume"`` — suspended run; keep descending
    ``"fresh"`` — suspended run; abandon (payout handled by caller) and enter
    ``"boss_rush"`` — minimum progress met; face the gathered echoes (§6.4)
    ``"boss_rush_fresh"`` — suspended run; collapse it (payout by caller) and raise the echoes
    ``"leave"`` — walk away (or scene aborted)
    """
    import event_horizon as eh
    player["eh_intro_seen"] = True  # defensive: never queue the city scene after visiting
    state = eh.ensure_eh_state(player)
    room = int(state.get("room", 0))
    suspended = bool(state.get("run_active")) and room > 0

    term.clear()
    term.print("═" * 64)
    term.print("  THE EVENT HORIZON")
    term.print("═" * 64)
    term.print("The last mile is wrong. The grass ends at a seam of black")
    term.print("glass — not a wall, not a hole: a place where the sky has")
    term.print("been folded until it cuts. Cold light leaks out of it the")
    term.print("way sound leaks from a locked room.")
    term.print("")
    term.print("Vesper stands at the edge as if the edge were a doorstep.")
    for line in plan_vesper_greeting(player, state, room, suspended):
        term.print(line)
    term.pause("Continue")

    # Boss Rush offer (§6.4) — only when every gate is met AND no run is
    # turning (a suspended run still claims the seam).
    rush_offered = (not suspended) and eh.boss_rush_available(player)
    if rush_offered:
        term.print("")
        term.print('VESPER: "Something in there remembers your old kills. It gathers')
        term.print('what you have already felled — an audience of echoes."')
        term.pause("Continue")

    while True:
        if suspended:
            opts = ["Resume the descent",
                    "Abandon the run & start fresh"]
            rush_idx = None
            if eh.boss_rush_requirements(player)[0]:
                rush_idx = len(opts)
                opts.append("⚔ Face the gathered echoes — Boss Rush [WIP]")
            lore_idx = len(opts)
            opts.append("Ask about the distortion")
            opts.append("Leave")
            choice = term.menu(
                opts,
                prompt="The seam waits.",
                allow_cancel=False,
            )
            if choice == 0:
                return "resume"
            if choice == 1:
                confirm = term.menu(
                    ["Yes — collapse it",
                     "No — keep the run"],
                    prompt=("Abandon the run? Everything the Horizon gave you "
                            "is wiped — cards, Entropy, flask buffs. Only the "
                            "gold payout remains."),
                    allow_cancel=False,
                )
                if confirm == 0:
                    return "fresh"
                continue
            if rush_idx is not None and choice == rush_idx:
                confirm = term.menu(
                    ["Yes — collapse it and face the echoes",
                     "No — keep the run"],
                    prompt=("The sitting run blocks the seam. Collapse it to "
                            "raise the echoes? Cards, Entropy and flask buffs "
                            "are wiped — only the gold payout remains."),
                    allow_cancel=False,
                )
                if confirm == 0:
                    return "boss_rush_fresh"
                continue
            if choice == lore_idx:
                _eh_lore_lines()
                continue
            return "leave"

        opts = ["Enter the Event Horizon"]
        if rush_offered:
            opts.append("⚔ Face the gathered echoes — Boss Rush [WIP]")
        lore_idx = len(opts)
        opts.append("Ask about the distortion")
        opts.append("Leave")
        choice = term.menu(
            opts,
            prompt="The seam waits.",
            allow_cancel=False,
        )
        if choice == 0:
            return "enter"
        if rush_offered and choice == 1:
            return "boss_rush"
        if choice == lore_idx:
            _eh_lore_lines()
            continue
        return "leave"
