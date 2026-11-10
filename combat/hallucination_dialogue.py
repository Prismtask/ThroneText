"""Ally reactions to fatigue hallucinations (docs/time_system_design.md §5).

The illusion is a SOLO fight — companions vanish for its duration and come
back to find the player dueling empty air (``victory``) or collapsed at
1 HP (``collapse``). This module gives every recruitable ally her own voice
for both outcomes instead of the old one-line-for-everyone pool.

Lookup order in :func:`get_ally_line`:
    1. ``_heroine_key`` (Alice / Red Hood / Dorothy / Palette)
    2. enemy ``key`` (captured monster girls)
    3. ``race`` (true-born children and synthetic ally records)
    4. generic pool (unknown records)

Lines are spoken text only — the caller adds the ``Name: "..."`` framing.
Keep braces out of the text; ``str.format`` is not used.
"""

import random

# ═══════════════════════════════════════════════════════════════════════
# HEROINES
# ═══════════════════════════════════════════════════════════════════════

VICTORY_LINES = {
    "alice": [
        "You were duelling a lamppost when I found you. I counted the dents. You won.",
        "Curious. You looked so certain it was real. What did it want from you?",
    ],
    "red_hood": [
        "Ha! You won! What did you win? Because I saw nothing but you and a lot of angry air.",
        "Good form, though. Even if the wolf was imaginary. Especially because of that.",
    ],
    "dorothy": [
        "You were talking to someone. They weren't there. That is the most interesting thing I've seen all week.",
        "Your eyes were still somewhere else when I found you. Where?",
    ],
    "palette": [
        "You were painting the air. Bold technique. Wrong medium.",
        "The marks you left in the air... I want to put them on canvas. The fear, mostly.",
    ],

    # ── Captured monster girls ─────────────────────────────────────────
    "goblin_girl": [
        "You were swinging at shadows. Shiny shadows, at least. Can I have the corpse? There isn't one. Rude.",
        "Next time, save some fight for the rest of us.",
    ],
    "harpy_scout": [
        "I flew the whole road looking for you. When I found you, you were alone, swinging at nothing.",
        "Your eyes kept catching on a spot in the air. There was nothing there. Nothing.",
    ],
    "alraune_fledger": [
        "You fought a phantom, love. It smelled like rot and wishful thinking.",
        "You are covered in sweat, not blood. That is the only reason I am still calm.",
    ],
    "kobold_tinkerer": [
        "You were fighting air. Air! I can build you goggles next time!",
        "My instruments say nothing was there. My instruments are never wrong.",
    ],
    "dryad_protector": [
        "The forest held its breath while you fought. It is still holding it.",
        "You struck deep grooves into the air. The roots will remember them.",
    ],
    "ghost_maid": [
        "You were rapping at an empty doorway, master. It did not answer.",
        "I would have dusted the thing. If it had existed.",
    ],
    "centaur_scout": [
        "You fought like the wind was your enemy. It nearly was.",
        "There were no tracks but yours. You had it all to yourself.",
    ],
    "moth_girl_flutterer": [
        "You were chasing a light that wasn't there. I know the feeling.",
        "You looked right past me when I found you. Right through me. It's fine. It's fine.",
    ],
    "slime_girl": [
        "You were punching a puddle of nothing! And winning! Very impressive!",
        "I would have dissolved if you'd hit me like that. Please don't.",
    ],
    "lamia_constrictor": [
        "You fought a shape in the air. I could have wrapped it for you. If it had a body.",
        "All that thrashing, and nothing to show for it. I am almost jealous.",
    ],
    "lizard_queen": [
        "You have an amusing opponent-tier imagination. The opponent, however, was imaginary.",
        "Cold air, warm rage. You should rule something.",
    ],
    "mimic_girl": [
        "You kept trying to open me and then hit the air instead. Rude. Also funny.",
        "There was no treasure chest there. I checked. There was barely a there.",
    ],
    "umbral_weaver": [
        "You were weaving your own shadow into a duel. I saw the threads.",
        "You fought something made of the same dark I was born in. It looked lonely.",
    ],
    "winter_fairy": [
        "You fought the cold. But the cold wasn't mine, and mine wasn't there.",
        "There was frost on your lips when I found you. It was yours, not mine.",
    ],
    "holstaur_brawler": [
        "You were wrestling a barn ghost. It had nothing on the real fights.",
        "Next time, hit something with a neck.",
    ],
    "gargoyle_watcher": [
        "When I found you, my eyes could not leave your weapon. There was nothing in front of it.",
        "You fought with the conviction of a stone saint. There was no one there.",
    ],
    "vampire_seductress": [
        "You bled nothing for a fight that wasn't there. What a waste of a good evening.",
        "I asked you to save some of the adrenaline for me. You didn't. Rude.",
    ],
    "yuki_onna": [
        "You fought a snowflake that thought itself a storm. I would have melted it first.",
        "You must have been so focused. I almost forgot to be lonely.",
    ],
    "amazon_warrior": [
        "Good footwork, bad target. There was no one there and you nearly beat them.",
        "I have watched a thousand duels. Yours must have been the bravest dance with nothing.",
    ],
    "banshee_wailer": [
        "You fought to a dirge only you could hear. It was almost beautiful.",
        "I nearly wailed for you. Then I saw the enemy was air and felt silly.",
    ],
    "neko_ninja": [
        "You were slicing shadows off nothing. Your form: decent. Your target: imaginary.",
        "I could have settled that in a blink. But it was your fight. Apparently.",
    ],
    "arachne_weaver": [
        "You were following a thread that led nowhere. Trust me, I know threads.",
        "You tore through the air like a fly in a web. It was charming.",
    ],
    "mummy_princess": [
        "You fought like a soldier from my century. But the battlefield was only memory.",
        "The dead do not dream. You did. What did you see?",
    ],
    "oni_bruiser": [
        "You threw a haymaker at the sky! The sky lost!",
        "No enemy, no blood. You still enjoyed it. Respect.",
    ],
    "salamander_dancer": [
        "You danced with a flame that wasn't there. I wanted to teach you the steps.",
        "Your heat, though. That was real. That was very real.",
    ],
    "succubus_seductress": [
        "You fought something no one else could see. What did it want? Was it me?",
        "All that desperation. You should let me take it out of you sometime.",
    ],
    "dullahan_knight": [
        "A clean duel against an absent foe. My head would applaud if I'd brought it.",
        "No foe, no oath. Yet you still charged. My kind understands that.",
    ],
    "kitsune_miko": [
        "They were dream-shaped, weren't they? My foxes do that. Yours was bigger.",
        "You were fighting an illusion. One blessing would have done it. Ah, well.",
    ],
    "siren_empress": [
        "You fought to music only you could hear. I approve.",
        "There was no enemy. There was, however, a performance.",
    ],
    "crimson_countess": [
        "A duel against nothing, and you still kept excellent form. Entertaining.",
        "You were fighting a ghost of your own making. Mine are better-dressed.",
    ],
    "demon_whip_master": [
        "Your footwork was messy. Your enemy was missing. Take the win.",
        "Whose law were you enforcing out there? Nobody's. Tsk.",
    ],
    "minotaur_gladiator": [
        "The crowd would have cheered, if there had been one. There was only me, arriving late.",
        "You charged nothing and did not flinch. That is a true bull's courage.",
    ],
    "vampire_matriarch": [
        "You fought a phantom with a grandchild's fury. Sit down. Drink something.",
        "You were very brave against nothing at all. My children do the same at bedtime.",
    ],
    "centaur_champion": [
        "You carried the whole duel on two legs. Impressive. Imaginary opponent, but still.",
        "I raced to the end of the fight. It was already over. You had won nothing.",
    ],
    "infernal_empress": [
        "You duel the fire in your own head. That is where I live too.",
        "Kneel later. First, tell me where you went.",
    ],
    "scylla_wrecker": [
        "You were grabbing at a shadow with six hands' worth of fury. I have six hands. Mine would have won.",
        "Down here the deep does that too. Gives you something to fight that isn't there.",
    ],
    "gorgon_petrifier": [
        "You never met my eyes when I found you. The thing you fought never met anything.",
        "If you'd wanted it dead, I could have supplied the stones. It did not exist.",
    ],
    "ninetales_fox": [
        "I know an illusion when I see one. Mine are prettier. Yours nearly bit you, didn't it?",
        "Nine tails: I looked from all nine angles. The air was empty from every one.",
    ],
    "mermaid_siren_queen": [
        "The tide brought no foe. Your song was lovely, though. Off key.",
        "The sea keeps no secrets from me. There was nothing there but you.",
    ],
    "draconic_valkyrie": [
        "You fought on foot, alone, against nothing. Your wings were not in that fight.",
        "A valkyrie chooses the slain. I kept saying your name because I refused to choose.",
    ],
    "sphinx_riddler": [
        "Riddle me this: what fights nothing, wins, and looks very pleased? You.",
        "You answered the question with a blade. Wrong method. Fine answer.",
    ],
    "lich_queen_avatar": [
        "You fight as if death has not already measured you. Charming.",
        "I saw your soul flicker. It lit on something that wasn't there.",
    ],
    "valkyrie_commander": [
        "You held the line against nothing. The line held. Good.",
        "Command is not about enemies. It is about not breaking. You didn't.",
    ],
    "dragon_goddess_avatar": [
        "You fought a thought. I am the goddess of thoughts. That one was yours.",
        "Small thing, you must have been magnificent. The enemy was not there.",
    ],
    "arachne_brood_queen": [
        "You knocked down a thread of a dream. My brood does the same to dust.",
        "Come sit. Let me weave you a chair. Your legs are shaking.",
    ],
    "cosmic_slime_empress": [
        "You fought a nebula of your own making. Star-stuff is stubborn, hm?",
        "You leaked fury into the void. The void is rude. It ignored you.",
    ],
    "gnome_gear_maiden": [
        "You fought a phantom. The tolerances were terrible.",
        "You need a stabilizer. And a target. Both available.",
    ],
    "orc_war_sister": [
        "The air was still ringing when I found you. Good form, wrong enemy.",
        "War is war, even when it's in your skull. Maybe especially then.",
    ],
    "shadow_dusk_weaver": [
        "You dueled the dusk. Dusk does not take prisoners. You are still here.",
        "The light had changed by the time I found you. The shadow hadn't. You were somewhere else.",
    ],
    "clockwork_automata_doll": [
        "Query. Hostile entity is absent. Question. What were you striking?",
        "Observation: your combat timing was optimal. Target fidelity: zero.",
    ],
    "giant_maiden_of_stone": [
        "You fought a mountain that wasn't there. You looked very small and very brave.",
        "The ground shook. It was you, not a foe.",
    ],
    "dragonkin_flame_heart": [
        "You were breathing fire at nothing. I respect the confidence.",
        "Your flame was so bright. The thing you fought was yours alone.",
    ],
    "angel_seraph_ascendant": [
        "You fought a shadow with the fury of a prayer. There was nothing there.",
        "I heard your voice break in the silence. I came. The fight was already yours.",
    ],
    "fey_star_court_dancer": [
        "You danced with a dream. I would have given you a better partner.",
        "The stars watched. They were confused. They are not often confused.",
    ],
    "demon_infernal_bride": [
        "You must have fought beautifully for something that wasn't there. I would have married you for that alone.",
        "The vows did not cover imaginary enemies. I must amend them.",
    ],
    "undead_grave_queen": [
        "Nothing dies out there. You fought a wave that thought itself a grave.",
        "I searched the ground for a new corpse. There was none. You are still here, luckily.",
    ],
}


# ═══════════════════════════════════════════════════════════════════════
# COLLAPSE (the pseudo-death: the player wakes at 1 HP)
# ═══════════════════════════════════════════════════════════════════════

COLLAPSE_LINES = {
    "alice": [
        "There you are. I have been calling your name into the dark for an hour. Do not do that again.",
        "You fell like a cut puppet. I nearly started believing in endings.",
    ],
    "red_hood": [
        "Get up. Get UP. I am not dragging you out of the woods again.",
        "I thought you were gone. I hate that I thought that.",
    ],
    "dorothy": [
        "You collapsed mid-sentence. I have your pulse. It's fast, it's there, it's fine.",
        "Don't close your eyes again. I have questions. Lots of them.",
    ],
    "palette": [
        "You went grey. Grey is a terrible color on you — I would know.",
        "Stay still. I am mixing something for the shakes. Do not argue.",
    ],

    # ── Captured monster girls ─────────────────────────────────────────
    "goblin_girl": [
        "Oi! Oi! You went down like a sack of loot! Wake up, I haven't stolen anything yet!",
        "I thought we lost you. My hands are shaking. Don't tell anyone.",
    ],
    "harpy_scout": [
        "I found you face-down in the dirt! I nearly flew into a tree getting to you! Breathe, idiot!",
        "I circled you for a full minute. You didn't move. Don't ever do that.",
    ],
    "alraune_fledger": [
        "I felt you fall through the roots. Wake now. I don't want to bury anything.",
        "Your breathing stopped for three whole heartbeats. Mine nearly did too.",
    ],
    "kobold_tinkerer": [
        "You dropped like a broken spring! Wake up! I don't know how to fix people!",
        "I counted your breaths. Two. Then one. Then... don't do that to me.",
    ],
    "dryad_protector": [
        "I felt your weight hit the moss. The green went quiet. Wake.",
        "You were so far away from us. Wherever you were, it was cold.",
    ],
    "ghost_maid": [
        "You lay cold and still. I have served enough graves to know the look. Do not become one.",
        "The others could not wake you. I could not touch you. I am sorry.",
    ],
    "centaur_scout": [
        "You fell on the road, and the road did not slow. I caught you. Barely.",
        "I galloped with you over my back. You said nothing for hours.",
    ],
    "moth_girl_flutterer": [
        "You fluttered down like a dead lamp. I kept calling you. You didn't come.",
        "Your eyes were wide open the whole way. That was the worst part.",
    ],
    "slime_girl": [
        "You were a heap in the road! A bad heap! Come on, get up!",
        "I held what was left of you together. You were cold. You are never cold.",
    ],
    "lamia_constrictor": [
        "I wrapped around you to stop the shaking. You did not squeeze back.",
        "You were breathing so shallow. I counted every one. I would have started over.",
    ],
    "lizard_queen": [
        "Queens do not kneel. But I knelt for you. Remember that.",
        "Your blood ran cold. Colder than mine. Wake.",
    ],
    "mimic_girl": [
        "I can mimic anything. I couldn't mimic your heartbeat. It wouldn't come on.",
        "You fell into my lid and nearly stayed. I don't keep people. Not like that.",
    ],
    "umbral_weaver": [
        "Your shadow let go of you. I held it until you came back.",
        "You went where the light does not follow. I almost let you.",
    ],
    "winter_fairy": [
        "You were colder than snow in my arms. I thought the dark had taken you.",
        "Your first warm breath made me cry. I will deny it.",
    ],
    "holstaur_brawler": [
        "You went down hard, right on the road. I carried you like a calf. Don't tell.",
        "I have held down bulls bigger than you. I still couldn't hold your life in.",
    ],
    "gargoyle_watcher": [
        "I am made to watch. I watched you not breathe. Do not make me do that again.",
        "Stone does not panic. I have learned it can. Today.",
    ],
    "vampire_seductress": [
        "Your pulse stopped under my fingers. Do you know how much restraint it took not to change that?",
        "One more minute. I would have done something unforgivable to keep you.",
    ],
    "yuki_onna": [
        "I would have frozen time itself to keep your breath inside you.",
        "You burned cold in my arms. I could not warm you. I have never hated snow before.",
    ],
    "amazon_warrior": [
        "I have carried champions to their pyres. I will not carry you. Get up.",
        "You were down before I reached you. I've seen arrows slower.",
    ],
    "banshee_wailer": [
        "I have wailed for the dead for centuries. I will not start for you. Wake.",
        "My scream caught in my throat. It has never done that. Never.",
    ],
    "neko_ninja": [
        "You dropped and I couldn't find the wound. There was no wound. That's worse.",
        "I stayed in the rafters all night. You know what you did. Never again.",
    ],
    "arachne_weaver": [
        "I spun you a blanket while you slept. It will hold. You will hold.",
        "Your breath caught in my silk. I loosened it. I did not let go.",
    ],
    "mummy_princess": [
        "I have lain dead a thousand years. I know the posture. Do not make it yours.",
        "The linen around your heart would not bind you back. I was so afraid.",
    ],
    "oni_bruiser": [
        "Big fighter down. Big fighter DOWN. Get up, I'm not good at the quiet part.",
        "I carried you. You're heavy. Worth it. Don't tell anyone.",
    ],
    "salamander_dancer": [
        "Your spark dipped so low. I fed it with mine. Do not waste it.",
        "If you had gone out, I would have danced in the ashes. I'm glad I didn't.",
    ],
    "succubus_seductress": [
        "You were so alive, then so still. I did not realize how much I liked the first part.",
        "I would have made a bargain with the thing in your head if it had come to me.",
    ],
    "dullahan_knight": [
        "I knelt and could not find a wound. It is worse when the blade is unseen.",
        "Mine own head watched from my hands. It saw your breath stop. It wept.",
    ],
    "kitsune_miko": [
        "I purified the air and the dark, and you still would not wake. Frightening.",
        "Nine tails could not stir your eyes. I was the one who cried first.",
    ],
    "siren_empress": [
        "I sang your name into the dark. The dark sang it back. I stopped singing.",
        "You are my worst audience: silent, still. Do not leave.",
    ],
    "crimson_countess": [
        "Your blood was slow under my lips. It has never been slow before.",
        "I could have brought you over. It was the hardest thing I have ever refused.",
    ],
    "demon_whip_master": [
        "You fell. There was no lash, no reason. Only you and your balance failing.",
        "I counted your heartbeats like lashes. Seventy-two. Then none. Then you.",
    ],
    "minotaur_gladiator": [
        "I have seen fighters fall in the arena and never rise. I could not watch that again.",
        "I roared at the empty air until my voice broke. It didn't bring you back. You did.",
    ],
    "vampire_matriarch": [
        "You were gone from me. Do you understand? Gone. I do not permit that.",
        "I am old enough to know grief. I am too proud to feel it for a corpse. Wake.",
    ],
    "centaur_champion": [
        "You fell like your legs forgot their job. My heart forgot its rhythm.",
        "I have run every racetrack. None felt longer than the way back with you.",
    ],
    "infernal_empress": [
        "The crown did not feel heavy until I thought you were gone. Interesting.",
        "I would burn a realm to keep that breath inside you. I nearly did.",
    ],
    "scylla_wrecker": [
        "I latched onto you with every limb I have and pulled. You did not float up on your own.",
        "You were drifting down. I don't let things sink. Not you.",
    ],
    "gorgon_petrifier": [
        "I could not turn you to stone. You were nearly stone already. I hate that.",
        "My snakes hissed your name until you woke. They are not good at names.",
    ],
    "ninetales_fox": [
        "I know my own tricks. I know when a mind is caught in one. You were caught. I was scared.",
        "I could have made you see anything. I could not make you see me. That was the worst moment.",
    ],
    "mermaid_siren_queen": [
        "I sang the deep awake to call you. It sent you back. It had no right to take you.",
        "You were so light in my arms. The sea is lighter. Do not go there.",
    ],
    "draconic_valkyrie": [
        "You fell like a broken banner. I caught it. I caught you. You still fell.",
        "I have carried the dead. I would rather carry you living. Stay living.",
    ],
    "sphinx_riddler": [
        "Here is my riddle: what is silent, still, and refuses to wake? Do not answer me.",
        "I asked you to stay. You did not solve it. I will ask again.",
    ],
    "lich_queen_avatar": [
        "The dead do not scare me. Your stillness did. Wake, little spark.",
        "I would have anchored you. Do not test me on this.",
    ],
    "valkyrie_commander": [
        "A commander does not weep. She counts. I counted too long.",
        "On your feet. There is no battle where you are not needed.",
    ],
    "dragon_goddess_avatar": [
        "I have watched worlds end. None of them frightened me like your silence.",
        "I could not let go. The dragon does not let go of what is hers. Remember that.",
    ],
    "arachne_brood_queen": [
        "My children gather at the door. They know the smell of ending. I shut it.",
        "You are not a thing to be kept in a web. But I nearly made you one, to keep you.",
    ],
    "cosmic_slime_empress": [
        "You fell out of your own shape for a while. The stars and I waited.",
        "I have absorbed whole galaxies. I could not absorb your sorrow. Tell me next time.",
    ],
    "gnome_gear_maiden": [
        "You dropped at a funny angle. I nearly laughed. Then I nearly cried. I'm still deciding.",
        "I took your pulse with the good calipers. You can't keep doing this to me.",
    ],
    "orc_war_sister": [
        "I carried you away from a fight that wasn't there. If that's not war, I don't know what is.",
        "Stand up before I start shouting. I am not good at the other thing.",
    ],
    "shadow_dusk_weaver": [
        "I kept a shadow folded over you so nothing worse came. You were so cold.",
        "You left. Dusk always comes back. You did too. Do it sooner.",
    ],
    "clockwork_automata_doll": [
        "Alert. Hostile presence detected. Error. Hostile presence is me. You did not respond.",
        "Directive: wake. Directive repeated. My readings say you did. My heartbeat says I am frightened.",
    ],
    "giant_maiden_of_stone": [
        "You lay still. The earth was still. I do not like that stillness.",
        "I would have held you the way mountains hold the sky. I did not let go.",
    ],
    "dragonkin_flame_heart": [
        "Your fire went out. Cold. I had never known you cold.",
        "I would have given you my ember. I nearly did. Do not make me decide again.",
    ],
    "angel_seraph_ascendant": [
        "Your light dimmed. I held what was left. It was enough. Barely.",
        "I do not beg. I nearly did. Whatever that thing was, tell me.",
    ],
    "fey_star_court_dancer": [
        "You stepped out of the dance and did not step back in. I was so afraid, the stars blinked.",
        "Come back to the music. It has missed you.",
    ],
    "demon_infernal_bride": [
        "You left me standing at the altar of your heart and all of you went dark. Do not do that.",
        "I would have gone into the dark with you. I am offended you did not wait.",
    ],
    "undead_grave_queen": [
        "You were almost mine. Almost. I have never been so pleased to lose a subject.",
        "I ordered the dead to stay put while I waited for you. They obeyed. The wait was the hard part.",
    ],
}


# ═══════════════════════════════════════════════════════════════════════
# RACE FALLBACKS (true-born children / synthetic ally records)
# ═══════════════════════════════════════════════════════════════════════

RACE_VICTORY_LINES = {
    "Goblin": [
        "You were fighting nothing. If it had loot, I would have helped.",
        "Good swings. Bad target. We can work on one of those.",
    ],
    "Beast": [
        "Your scent went wild out there. There was no prey. I checked.",
        "You fought like something cornered. The corner was only in your head.",
    ],
    "Fey": [
        "You danced with a dream. The court would have laughed. I didn't.",
        "There was glamour in your eyes. Not mine. Someone older.",
    ],
    "Dragonkin": [
        "You flamed the empty air. Bold. Inefficient.",
        "A dragon fights what is there. You fought what wasn't. Interesting.",
    ],
    "Shadow": [
        "You were fighting the dark. The dark was you.",
        "Your shadow was somewhere else. So were you.",
    ],
    "Elemental": [
        "You fought the wind like it owed you something. It does not.",
        "Nothing was there. The air is still deciding whether to forgive you.",
    ],
    "Lizardfolk": [
        "Cold blood, hot fight. There was no enemy. Sit in the sun.",
        "You struck faster than anything out there. There was nothing out there.",
    ],
    "Abomination": [
        "You were fighting a shape that only you could see. I know shapes.",
        "Nothing there. Nothing at all. Yet you bled for it.",
    ],
    "Construct": [
        "No damage taken. No target present. An efficient, empty victory.",
        "Your form was sound. The enemy was not.",
    ],
    "Vampire": [
        "You spilled nothing out there. What a waste of a good night.",
        "Your pulse was racing for an empty room. How delicious.",
    ],
    "Human": [
        "You fought your own shadow, and honestly, you nearly lost.",
        "Nothing was there. You still stood your ground. That counts.",
    ],
    "Undead": [
        "You fought like the dead do: with nothing left to lose. There was nothing to fight.",
        "Nothing died out there, which is rare for me. Well done.",
    ],
    "Demon": [
        "You dueled a thought. Thoughts can be crueler than demons.",
        "All that fury for an empty patch of air. I approve.",
    ],
    "Giant": [
        "You fought a mountain that wasn't there. You are small and brave.",
        "The ground shook. It was you. There was no foe.",
    ],
    "Gnome": [
        "You fought a phantom. The tolerances were terrible.",
        "You need a target and a stabilizer. I can supply one of those.",
    ],
    "Orc": [
        "You hit the air so hard I felt it. Good form. Wrong enemy.",
        "War is war, even when it's in your head. Stand tall.",
    ],
    "Clockwork": [
        "Query: hostile entity absent. Conclusion: you won nothing.",
        "Your combat cycle ran clean. Target acquisition failed.",
    ],
    "Angel": [
        "You fought a shadow with the fury of a prayer. It was not there.",
        "Your light held. The darkness you struck was your own.",
    ],
    "Storybook": [
        "That was a very strange chapter. There was no antagonist in it but you.",
        "The page turned, and the monster was gone. It was never on the page.",
    ],
}

RACE_COLLAPSE_LINES = {
    "Goblin": [
        "You dropped like a sack of loot! Wake up, I haven't stolen anything yet!",
        "My hands are shaking. Don't tell anyone.",
    ],
    "Beast": [
        "You went down and I couldn't smell a wound. That's worse.",
        "I kept watch over you all night. Nothing came. Nothing. Wake.",
    ],
    "Fey": [
        "You stepped out of the story and didn't step back. I was afraid.",
        "The court is quieter when you're still. I don't like it.",
    ],
    "Dragonkin": [
        "Your fire went out. I had never known you cold.",
        "I would have given you my ember. Do not make me decide that again.",
    ],
    "Shadow": [
        "Your shadow let go of you. I held it until you came back.",
        "You went where the light does not follow. I almost let you.",
    ],
    "Elemental": [
        "You went still as stone. That is not your nature.",
        "Your breath stopped. The air has been holding its own ever since.",
    ],
    "Lizardfolk": [
        "Your blood ran cold. Colder than mine. Wake.",
        "I warmed you with my own body. You did not stir. Do not do that.",
    ],
    "Abomination": [
        "You fell into a shape I couldn't hold. I kept trying.",
        "Nothing about you should be still. Wake up.",
    ],
    "Construct": [
        "Readings: no pulse. Error. Readings corrected: faint pulse. Do not repeat.",
        "I am not built to grieve. I was building the shape of it anyway.",
    ],
    "Vampire": [
        "Your pulse stopped under my fingers. I nearly changed that.",
        "One more minute and I would have done something unforgivable.",
    ],
    "Human": [
        "You fell and I couldn't find a wound. There was no wound. That's worse.",
        "I thought you were gone. I hate that I thought that.",
    ],
    "Undead": [
        "You were almost one of mine. Almost. I have never been so glad to be denied.",
        "I ordered the dead to stay put. You were the one I was waiting for.",
    ],
    "Demon": [
        "You left for the dark and did not ask permission. Do not do that.",
        "I would have gone with you. I am offended you did not wait.",
    ],
    "Giant": [
        "You lay still. The earth was still. I do not like that stillness.",
        "I held you the way mountains hold the sky. I did not let go.",
    ],
    "Gnome": [
        "You dropped at a funny angle. I nearly laughed. Then I nearly cried.",
        "I took your pulse with the good calipers. You can't keep doing this.",
    ],
    "Orc": [
        "Big fighter down. Get up. I am not good at the quiet part.",
        "I carried you. You're heavy. Worth it.",
    ],
    "Clockwork": [
        "Alert. Hostile presence detected. Error. Hostile presence is me.",
        "Directive: wake. Directive repeated. My readings say you did. My heartbeat says otherwise.",
    ],
    "Angel": [
        "Your light dimmed. I held what was left. It was enough. Barely.",
        "I do not beg. I nearly did. Tell me what you saw.",
    ],
    "Storybook": [
        "The chapter ended with you on the ground. I refused to turn the page.",
        "You left the story. I waited at the edge of it until you came back.",
    ],
}


# ═══════════════════════════════════════════════════════════════════════
# GENERIC FALLBACK (unknown ally records)
# ═══════════════════════════════════════════════════════════════════════

GENERIC_VICTORY = [
    "Who were you fighting?",
    "There was nothing there. There was nobody there.",
    "Your weapon is still shaking. So are you.",
]

GENERIC_COLLAPSE = [
    "Hey — hey! You walked straight into that wall!",
    "You were fighting NOTHING. Look at me.",
    "We couldn't wake you. What did you see out there?",
]


def ally_identity_key(ally):
    """The most specific identity key for dialogue lookup."""
    if not ally:
        return ""
    heroine = (ally.get("_heroine_key") or "").strip()
    if heroine:
        return heroine
    return (ally.get("key") or "").strip()


def has_personalized_lines(ally):
    """True if the ally has a key- or heroine-specific response pool."""
    key = ally_identity_key(ally)
    return bool(key and key in VICTORY_LINES and key in COLLAPSE_LINES)


def get_ally_line(ally, outcome):
    """Pick a response line for ``outcome`` ("victory" or "collapse").

    Resolution: heroine/key pool → race pool → generic pool. Lines are
    returned without speaker framing; the caller adds the name and quotes.
    """
    collapse = outcome == "collapse"
    specific = COLLAPSE_LINES if collapse else VICTORY_LINES
    by_race = RACE_COLLAPSE_LINES if collapse else RACE_VICTORY_LINES
    generic = GENERIC_COLLAPSE if collapse else GENERIC_VICTORY

    key = ally_identity_key(ally)
    pool = specific.get(key)
    if pool:
        return random.choice(pool)

    race = (ally or {}).get("race")
    pool = by_race.get(race)
    if pool:
        return random.choice(pool)

    return random.choice(generic)
