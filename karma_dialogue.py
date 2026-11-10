"""Karma-tier NPC lines (Phase 3).

These are deliberately separate from the city dialogue dictionaries: adding a
line here does not rewrite every city's voice. Call sites choose one line per
service. Wonderland is excluded until its own Karma pass is designed.
"""

import random

import karma

_HIGH = {
    "generic": [
        "Word of your deeds runs ahead of you. People stand a little straighter.",
        "You have a reputation for doing the right thing. It opens doors.",
    ],
    "receptionist": [
        "The clerks have heard of you. Your business is welcome here.",
        "A pleasure. The city remembers who has helped it.",
    ],
    "shop": [
        "For you? The good stock, and a fair price.",
        "Your coin is welcome here. So is your reputation.",
    ],
    "blacksmith": [
        "A steady hand and a clean conscience. I can work with that.",
        "For you, I'll use the good coal.",
    ],
    "guild": [
        "The guild remembers its friends. There is work for someone like you.",
        "Honest contracts suit you. The board is open.",
    ],
    "black_market": [
        "A saint in the market? Keep your coin visible and your sermons quiet.",
        "You're too clean for this room — but your gold spends the same.",
    ],
    "port": [
        "Your reputation buys you a clean berth.",
        "No papers needed. Your name is enough.",
    ],
    "guard": [
        "No trouble from you, I'm sure. Go on through.",
        "The watch knows your face — for the right reasons.",
    ],
}

_LOW = {
    "generic": [
        "People make room when you pass. Not out of respect.",
        "Your name is spoken quietly here.",
    ],
    "receptionist": [
        "Keep your hands where the clerks can see them.",
        "We'll be watching you. Say what you came to say.",
    ],
    "shop": [
        "I'll be watching the coin box while you browse.",
        "Everything is paid up front. No exceptions.",
    ],
    "blacksmith": [
        "Pay up front. I know your sort.",
        "I'll forge it. I won't ask what it's for.",
    ],
    "guild": [
        "The guild has work for you — the kind nobody else will take.",
        "You're still allowed through the door. Barely.",
    ],
    "black_market": [
        "Now this is a face that belongs here.",
        "The good shelf is open. Keep your voice down.",
    ],
    "port": [
        "No papers? For you, that's practically a reference.",
        "The captains will take your coin. They won't ask questions.",
    ],
    "guard": [
        "I've got my eye on you.",
        "One wrong move. That's all it takes.",
    ],
}

_BLACKWAKE_NEG = {
    "generic": [
        "Blackwake knows your name. That's either good or bad. Probably both.",
        "The cove remembers its own. Welcome back.",
    ],
    "receptionist": [
        "Blackwake knows your name. The good shelf is open.",
        "You're not a stranger here. That's rare.",
    ],
    "black_market": [
        "The good shelf is open for you. No questions.",
        "For your sort, the price is almost honest.",
    ],
    "port": [
        "A face the harbor trusts. The smuggler's berth is yours.",
        "No papers, no questions, no problem.",
    ],
    "inn": [
        "A room with a lock, for a change. You've earned that much.",
        "The Drowned Rat doesn't judge. Neither do I.",
    ],
}

_BLACKWAKE_POS = {
    "generic": [
        "A saint in Blackwake? Bold. Prices just went up.",
        "Your kind isn't popular here. Your gold still is.",
    ],
    "receptionist": [
        "A saint walks into the cove. Try not to look so honest.",
        "We don't get your sort here. Keep your sermons to yourself.",
    ],
    "black_market": [
        "A clean conscience in the Wreck. You'll pay the saint tax.",
        "The good shelf is for outlaws. You can afford the ordinary one.",
    ],
    "port": [
        "The captains will take you. They'll charge you for the privilege.",
        "A lawful face on a smuggler's dock. Keep your head down.",
    ],
    "inn": [
        "A saint's coin spends fine. The room is still sticky.",
        "No judgment here. Just a lot of side-eye.",
    ],
}


def service_line(player, service, city_id=None, context="enter"):
    """Return one Karma-flavored line for a service, or None.

    ``service`` should be one of receptionist / shop / blacksmith / guild /
    black_market / port / guard / inn. Unknown services fall back to a generic
    line. Wonderland always returns None until its own pass.
    """
    if not player or not karma.is_enabled(player):
        return None
    if city_id == "wonderland":
        return None
    # Inns are neutral except Blackwake's outlaw/saint flavor.
    if service == "inn" and city_id != "blackwake":
        return None

    value = karma.get_karma(player)
    if city_id == "blackwake":
        if value < 0:
            lines = _BLACKWAKE_NEG
        elif value > 0:
            lines = _BLACKWAKE_POS
        else:
            return None
    elif value >= 25:
        lines = _HIGH
    elif value <= -25:
        lines = _LOW
    else:
        return None

    choices = lines.get(service) or lines["generic"]
    return random.choice(choices)


# ── Deed-title greeting flavour (docs/titles_design.md, Phase 3) ──────────
_TITLE_LINES = {
    "combat": [
        "They whisper {title} behind the counter. The coin box is counted twice.",
        "A fighter's hands. The shopkeeper pretends not to look.",
        "The room quiets when {title} walks in. Then the haggling starts.",
    ],
    "travel": [
        "You have the road in your eyes. The clerk stops giving directions.",
        "{title} — even the gate guards have heard the name.",
        "The innkeeper waves you toward the good table without being asked.",
    ],
    "economy": [
        "A careful buyer. The shopkeeper sharpens a price that was already sharp.",
        "They know {title} pays on time. The good stock comes out.",
        "Your purse is famous. Your haggling is infamous.",
    ],
    "dungeon": [
        "There's dungeon dust on your boots. The clerk gives you room.",
        "{title} — the deep places have a way of marking their own.",
        "The torches lean toward you, as if remembering the dark.",
    ],
    "house": [
        "There's a home in your voice. The receptionist softens.",
        "{title} — someone with a hearth waiting for them.",
        "The clerk asks after your household before your business.",
    ],
    "karma": [
        "Your name carries weight here. The counter is a little cleaner.",
        "{title} — the city has decided what it thinks of you.",
        "People make way, politely or otherwise.",
    ],
    "collection": [
        "{title} — the Archive would like a word about your notes.",
        "The clerk glances at your ledger and decides not to ask.",
    ],
    "wonderland": [
        "The shopkeeper blinks, as if you stepped out of a page. The price comes out cleaner.",
        "{title} — the shelves rearrange themselves when you look away.",
        "There is a story in your shadow. The clerk tries not to read it.",
    ],
    "generic": [
        "{title}. The name has reached this counter already.",
        "They have heard of you. The service is a little quicker.",
    ],
}


def title_line(player, service, city_id=None):
    """Return one equipped-title greeting line, or None."""
    from titles import get_active
    title = get_active(player)
    if not title:
        return None
    category = title.get("category", "generic")
    pool = _TITLE_LINES.get(category) or _TITLE_LINES["generic"]
    if service == "black_market" and category == "karma":
        pool = _TITLE_LINES["karma"]
    return random.choice(pool).replace("{title}", title.get("name", ""))
