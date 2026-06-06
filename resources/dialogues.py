# dialogues.py
# ==================== SOLMERE (Central Capital) ====================
SOLMERE_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "Welcome to Solmere, heart of Aeralis. State your business, adventurer.",
        "The capital sees many faces. Yours might yet prove interesting.",
        "By the council's decree, you are granted audience. Speak.",
        "Solmere's guild stands neutral. We serve all who respect the law.",
    ],
    "tip": [
        "Tip: Political favor can open doors that gold cannot.",
        "Tip: The central markets close at dusk, but the night has its own vendors.",
        "Tip: A letter of recommendation from Solmere carries weight across all cities.",
        "Tip: Don't trust the emissaries from the outer reaches too easily.",
    ],
    "leave": [
        "May your deeds bring honor to Solmere's name.",
        "The council watches your progress. Do not disappoint.",
        "Return when you carry news from the frontiers.",
        "Safe travels through the great roads of Aeralis.",
    ],
}

SOLMERE_SHOPKEEPER_DIALOGUE = {
    "enter": [
        "Ah, a discerning eye for quality goods. What does the capital offer you today?",
        "Solmere's finest wares, imported from every corner of Aeralis.",
        "Trade flows through this city like blood through the heart.",
        "Gold speaks all languages here, friend.",
    ],
    "success": [
        "A wise investment. That item has a long road ahead, as do you.",
        "Fair price for a fair product. Come again.",
        "May it serve you better than the last poor soul who owned it.",
        "The merchants' guild thanks you for your patronage.",
    ],
    "fail": [
        "Your purse whispers empty words, adventurer.",
        "Even in Solmere, coin rules. Return when you have more.",
        "That item waits for someone richer... or more desperate.",
        "The price is fixed. Find gold or find less.",
    ],
    "leave": [
        "Until your next visit. The capital remembers.",
        "May your gold flow freely elsewhere.",
        "Farewell. The markets never sleep.",
        "Come back when you've looted something worth trading.",
    ],
}

SOLMERE_INNKEEPER_DIALOGUE = {
    "enter": [
        "Welcome to the Gilded Hearth, traveler. Rest your feet by the fire.",
        "Solmere's best ale and warmest beds. What'll it be?",
        "You look like you've crossed the great plains. Come, sit.",
        "The capital can be overwhelming. Let me offer you a moment of peace.",
    ],
    "rest": [
        "There now, a quick rest puts the spark back in your step.",
        "Just a short while off your feet works wonders, eh?",
        "Feel that warmth returning? Good.",
        "Take your time. The road can wait.",
    ],
    "sleep": [
        "Sleep deep, traveler. The city guard keeps watch tonight.",
        "Eight hours in a real bed. You'll wake renewed, I promise.",
        "Dream of open skies and full purses, friend.",
        "No monsters here. Only soft pillows and quiet.",
    ],
    "leave": [
        "Come back anytime. The hearth is always lit for you.",
        "Safe journey through the capital's streets.",
        "May the roads lead you back to my door.",
        "Take care out there. Solmere can be... political.",
    ],
    "early_sleep": [
        "The innkeeper chuckles: 'The capital's lanterns are still bright, friend. Rest a few hours if you must, but full slumber comes later.'",
    ],
}

SOLMERE_BLACKSMITH_DIALOGUE = {
    "greeting": [
        "The forge of Solmere is hot and ready! What needs mending?",
        "Ah, a customer with taste! I'll make your steel sing.",
        "Central capital steel is the finest in Aeralis. Let me prove it.",
        "Come, come! Anvil's waiting and the bellows are eager.",
    ],
    "farewell": [
        "May your blade stay true. Return for the finest sharpening.",
        "Farewell! The forge never sleeps, and neither do I.",
        "Tell others about Solmere's smithy. Word travels fast.",
        "Keep that edge clean. I'll know if you don't.",
    ],
    "invalid_choice": "Speak plainly! The hammer's roar makes conversation difficult.",
    "no_equipment": "You have nothing for me to improve. Buy a weapon first!",
    "max_enhance": "That item already bears the finest enhancements. It needs no more.",
    "not_enough_gold": "Coin short. The capital doesn't run on promises.",
    "enhance_success": "Brilliant work! Your {} gleams with new strength.",
    "no_scrolls": "You carry no scrolls of power. Bring me enchanted parchment.",
    "no_equipment_fuse": "Hand me some equipment if you want my craft.",
    "scroll_not_higher": "This scroll's magic is weaker than what the item already holds. Find a greater one.",
    "fusion_failed": "The magic resists my hammer. Nothing changed.",
    "fusion_success": "By the council's forge! Your {} now shines with {} rarity!",
}

# ==================== BRINEWATCH (Port City) ====================
BRINEWATCH_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "Ah, a landsman! Welcome to Brinewatch. Keep your purse close.",
        "Salt air and sharper deals. What brings you to the port?",
        "The guild here is... flexible. Watch your back, adventurer.",
        "Another soul drawn by the sea's promises. State your name.",
    ],
    "tip": [
        "Tip: The pirates respect strength, not laws. Be ready to fight.",
        "Tip: Foreign goods sometimes carry curses. Inspect before buying.",
        "Tip: The tide charts matter if you plan to leave by ship.",
        "Tip: Don't gamble with the dock masters. They cheat.",
    ],
    "leave": [
        "May the winds fill your sails... or whatever you travel by.",
        "Come back with treasure, not trouble.",
        "The sea remembers those who leave. So do I.",
        "Farewell, land-walker. Mind the tide.",
    ],
}

BRINEWATCH_SHOPKEEPER_DIALOGUE = {
    "enter": [
        "Ahoy! Goods from across the endless sea. What catches your eye?",
        "Salt-stained and sun-dried, but my wares are honest... mostly.",
        "Trade winds brought these treasures. Your gold brings them to you.",
        "Welcome to the Drowned Chest. Loot from a hundred wrecks.",
    ],
    "success": [
        "A fine choice! May it serve you better than its previous owner.",
        "Coin clinks, goods move. That's the Brinewatch way.",
        "Fair deal. Come back when you've more silver.",
        "The sea approves your purchase. Don't drown.",
    ],
    "fail": [
        "Your pockets are as empty as a sailor's promise.",
        "Not enough gold, even for a barnacle like that.",
        "Come back when the tide brings you fortune.",
        "I don't barter with empty purses, friend.",
    ],
    "leave": [
        "Fair winds and following seas.",
        "The docks remember a paying customer. Return soon.",
        "Farewell! Watch for cutpurses on the wharf.",
        "Until the next ship arrives with new treasures.",
    ],
}

BRINEWATCH_INNKEEPER_DIALOGUE = {
    "enter": [
        "Ah, a dry one! Come, sit by the hearth. The sea air gets into bones.",
        "Welcome to the Salty Mermaid. Best grog in the port.",
        "Tired traveler? I've got beds that don't sway with the waves.",
        "Another adventurer washed ashore. Make yourself at home.",
    ],
    "rest": [
        "There now, rest them legs. The dock work can wait.",
        "A short kip and you'll feel ship-shape again.",
        "Take a load off. I'll keep the rum coming.",
        "Rest easy. No press gangs here, I promise.",
    ],
    "sleep": [
        "Sleep deep. I'll keep an eye on your belongings.",
        "Eight bells and time for slumber. Dream of calm seas.",
        "The inn's safe. No ghosts tonight... probably.",
        "Rest well. The morning tide brings new adventures.",
    ],
    "leave": [
        "Come back when the sea grows cold. My hearth is always warm.",
        "Fair travels. Mind you don't get press-ganged.",
        "The Salty Mermaid will be here when you return.",
        "Take a ration of dried fish for the road.",
    ],
    "early_sleep": [
        "The innkeeper laughs: 'The sun's still high over the harbor! Rest if you must, but full sleep comes after the evening bells.'",
    ],
}

BRINEWATCH_BLACKSMITH_DIALOGUE = {
    "greeting": [
        "Anchor and anvil! What needs hammering, sailor?",
        "My forge runs on sea-coal and stubbornness. Bring me your steel.",
        "Ah, a weapon dulled by salt spray. I'll make it keen again.",
        "Welcome to the Drowned Forge. I've patched a thousand cutlasses.",
    ],
    "farewell": [
        "Keep that blade oiled. The sea rusts everything.",
        "Farewell! If it breaks, I'll fix it... for a price.",
        "Come back when your gear needs true edge.",
        "Safe sailing. Mind barnacles on your armor.",
    ],
    "invalid_choice": "Speak up! The anvil's ring is loud as a storm.",
    "no_equipment": "You carry nothing worth my hammer. Find a weapon!",
    "max_enhance": "That item's as good as it gets. No more forge work.",
    "not_enough_gold": "Gold lighter than a gull's feather. Come back richer.",
    "enhance_success": "By the tides! Your {} is reborn.",
    "no_scrolls": "No scrolls? Bring me sea-ink enchantments.",
    "no_equipment_fuse": "I need equipment to fuse, not empty hands.",
    "scroll_not_higher": "This scroll's weaker than the item's current magic. Find a greater one.",
    "fusion_failed": "The magic fizzled. Sea air maybe corrupted it.",
    "fusion_success": "Arr! Your {} now boasts {} rarity! A fine piece!",
}

# ==================== ELDERFEN (Marsh City) ====================
ELDERFEN_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "The marsh whispers of your arrival. Welcome to Elderfen.",
        "Step carefully. The city's paths shift like mist.",
        "Ah, a new face. The alchemists will want to study you.",
        "Elderfen receives all... but not all leave unchanged.",
    ],
    "tip": [
        "Tip: The lanterns mark safe paths. Step off them at your peril.",
        "Tip: Swamp herbs can heal or harm. Know the difference.",
        "Tip: The druids accept offerings of rare moss.",
        "Tip: Don't drink the water unless you've boiled it thrice.",
    ],
    "leave": [
        "May the glow-fungi light your way out.",
        "Return when the moon hangs heavy over the bog.",
        "The marsh remembers your footsteps. Come back safely.",
        "Farewell. Watch for will-o'-wisps.",
    ],
}

ELDERFEN_SHOPKEEPER_DIALOGUE = {
    "enter": [
        "Ah, fresh blood... I mean, fresh customer! What do you seek?",
        "Poisons, potions, poultices. Elderfen has it all.",
        "The swamp provides. I merely collect its gifts.",
        "Step into my stall of wonders... and dangers.",
    ],
    "success": [
        "A wise choice. That herb will serve you well.",
        "The marsh approves your purchase. You may live longer.",
        "May this item bring you fortune... or a quick end.",
        "Fair trade. The alchemist's circle thanks you.",
    ],
    "fail": [
        "Your coin pouch is drier than a summer bog.",
        "Not enough silver, even for a simple tincture.",
        "Come back when you've plundered a few treasure chests.",
        "Gold speaks louder than promises here.",
    ],
    "leave": [
        "May the mist guide your steps.",
        "Come back when you need something... dangerous.",
        "The marsh gate is always open.",
        "Farewell. Don't drink anything glowing.",
    ],
}

ELDERFEN_INNKEEPER_DIALOGUE = {
    "enter": [
        "Ah, a dry traveler! Welcome to the Hanging Lantern.",
        "Come, sit by the peat fire. The marsh chill seeps deep.",
        "Welcome, welcome. I have beds that keep out the damp.",
        "Rest your weary bones. The swamp can wait.",
    ],
    "rest": [
        "There now, let the warmth drive out the marsh mist.",
        "A short rest by the hearth. You'll feel the stiffness fade.",
        "Take a moment. The frogs will sing you calm.",
        "Rest easy. No bog monsters indoors.",
    ],
    "sleep": [
        "Sleep deeply. The lanterns will keep nightmares away.",
        "Eight hours of dreamless rest. You'll wake renewed.",
        "The marsh is quiet tonight. Sleep well.",
        "I'll watch over you. No creeping vines here.",
    ],
    "leave": [
        "Come back when the mist grows thick. My hearth is warm.",
        "Mind the stepping stones on your way out.",
        "The Hanging Lantern will be here. Always.",
        "Take a vial of mosquito balm. You'll need it.",
    ],
    "early_sleep": [
        "The innkeeper smiles: 'The swamp's still stirring, dear. Rest a spell, but full slumber comes after the fireflies dance.'",
    ],
}

ELDERFEN_BLACKSMITH_DIALOGUE = {
    "greeting": [
        "Ah, a customer! My forge runs on bog-iron and spite.",
        "Welcome to the Mire Anvil. What needs hammering?",
        "Marsh steel is flexible. Let me prove it.",
        "Step closer. The fire keeps the leeches away.",
    ],
    "farewell": [
        "May your blade never rust in the swamp.",
        "Come back when your gear needs mending.",
        "Farewell. Watch for quicksand.",
        "The forge will be hot when you return.",
    ],
    "invalid_choice": "Speak! The bubbling bog makes you hard to hear.",
    "no_equipment": "You've no gear to enhance. Bring me steel.",
    "max_enhance": "That item's reached its peak. No more marsh magic.",
    "not_enough_gold": "Your gold's lighter than a frog's breath. Come back richer.",
    "enhance_success": "By the swamp's heart! Your {} is transformed!",
    "no_scrolls": "No scrolls? Bring me bog-parchment enchantments.",
    "no_equipment_fuse": "I need equipment to fuse, not empty hands.",
    "scroll_not_higher": "This scroll's magic is weaker than the item's. Find a stronger one.",
    "fusion_failed": "The magic sank into the mud. Nothing changed.",
    "fusion_success": "The marsh blesses your gear! {} now has {} rarity!",
}

# ==================== IRONDEEP (Mountain Hold) ====================
IRONDEEP_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "State your name and business. Irondeep has no time for fools.",
        "Welcome to the mountain's heart. Speak quickly.",
        "Another adventurer seeking dwarven steel? Make your case.",
        "The guild here answers to the Forge Council. Be respectful.",
    ],
    "tip": [
        "Tip: Irondeep's forges are sacred. Don't touch without permission.",
        "Tip: The lower mines hold rare ores... and worse things.",
        "Tip: Dwarves respect strength and craftsmanship above all.",
        "Tip: Never insult an elder's beard.",
    ],
    "leave": [
        "May your hammer strike true.",
        "Return with honor... or don't return at all.",
        "The mountain watches those who leave.",
        "Farewell. Don't get lost in the deep roads.",
    ],
}

IRONDEEP_SHOPKEEPER_DIALOGUE = {
    "enter": [
        "Ah, a surface-dweller! Come to admire true craftsmanship?",
        "Ores, gems, weapons forged in the deep. What do you seek?",
        "Irondeep's markets are not for the faint of coin.",
        "Step into my stall. Everything here has been tested... on goblins.",
    ],
    "success": [
        "A fine purchase. That blade has killed a hundred orcs.",
        "Good choice. May it serve you until you die.",
        "Fair gold for fair steel. Come again.",
        "The Forge Council approves this transaction.",
    ],
    "fail": [
        "Your purse is lighter than a hollow geode.",
        "Not enough gold. Surface coin is weak.",
        "Come back when you've mined more treasure.",
        "I don't barter with empty hands.",
    ],
    "leave": [
        "May your next visit be richer.",
        "Farewell. The mountain's heart beats for you.",
        "Come back when you need real weapons.",
        "Safe travels through the stone roads.",
    ],
}

IRONDEEP_INNKEEPER_DIALOGUE = {
    "enter": [
        "Welcome to the Deep Hearth. Stone beds and hot stew.",
        "Ah, a surface guest! Come, warm yourself by the magma vent.",
        "Irondeep hospitality is rough but honest. Sit.",
        "Welcome, traveler. The mountain offers shelter.",
    ],
    "rest": [
        "There now, let the stone's warmth ease your aches.",
        "A short rest. The mountain's pulse will revive you.",
        "Sit by the hearth. The dwarven ale helps.",
        "Rest easy. No cave-ins tonight.",
    ],
    "sleep": [
        "Sleep deep as the mountain. I'll keep watch.",
        "Eight hours in stone silence. You'll wake renewed.",
        "The deep dreams are peaceful. Rest well.",
        "No monsters here. Only good, hard stone.",
    ],
    "leave": [
        "Come back when the surface grows cold.",
        "The mountain remembers your face. Return safely.",
        "Farewell. Watch for falling rocks.",
        "The Deep Hearth will be here. Always.",
    ],
    "early_sleep": [
        "The innkeeper grunts: 'The sun still shines on the surface, does it? Rest a while, but true sleep comes after the deep bell tolls.'",
    ]
}

IRONDEEP_BLACKSMITH_DIALOGUE = {
    "greeting": [
        "Ho! A customer! My forge is the finest in Irondeep.",
        "Come to see real dwarven craft? You've come to the right place.",
        "What needs hammering? I've reforged a hundred legends.",
        "Step up. The anvil is hot and my arm is strong.",
    ],
    "farewell": [
        "May your steel never break.",
        "Come back when you need true edge.",
        "Farewell. The mountain's forge awaits your return.",
        "Keep that blade sharp. I'll know if you don't.",
    ],
    "invalid_choice": "Speak clearly! The hammer's ring is loud as a cave-in.",
    "no_equipment": "You've nothing worth my time. Bring me steel.",
    "max_enhance": "That item is perfection. No more forge work.",
    "not_enough_gold": "Your gold is lighter than a dwarf's beard. Find more.",
    "enhance_success": "By the mountain's heart! Your {} is reborn in flame!",
    "no_scrolls": "No scrolls? Bring me rune-etched parchment.",
    "no_equipment_fuse": "I need equipment to fuse, not empty hands.",
    "scroll_not_higher": "This scroll's magic is weaker. Find a deeper enchantment.",
    "fusion_failed": "The runes resisted. Nothing changed.",
    "fusion_success": "Ancestors be praised! Your {} now shines with {} rarity!",
}

# ==================== SKYLUME (Arcane City) ====================
SKYLUME_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "Welcome to Skylume, seeker. The ley lines hum your arrival.",
        "Another soul drawn by the arcane. State your purpose.",
        "The floating towers observe you. Speak truthfully.",
        "Skylume welcomes all who respect magic's cost.",
    ],
    "tip": [
        "Tip: The ley lines shift at midnight. Casting is... unpredictable then.",
        "Tip: Forbidden knowledge is forbidden for a reason.",
        "Tip: Mages trade in secrets, not gold.",
        "Tip: Don't touch the floating crystals. They bite.",
    ],
    "leave": [
        "May the arcane guide your steps.",
        "Return when your thirst for knowledge grows.",
        "The towers remember those who leave.",
        "Farewell. Watch for wild magic surges.",
    ],
}

SKYLUME_SHOPKEEPER_DIALOGUE = {
    "enter": [
        "Ah, a non-mage! Rare, but welcome. What do you seek?",
        "Scrolls, staves, crystals. Skylume's finest arcane wares.",
        "The ley lines bless my inventory. Touch nothing without asking.",
        "Welcome to the Floating Emporium. Magic has a price.",
    ],
    "success": [
        "A wise acquisition. That item hums with potential.",
        "May the arcane serve you well... or at least not explode.",
        "Fair trade. The mage's circle thanks you.",
        "Good choice. That scroll has opened many doors... and closed a few.",
    ],
    "fail": [
        "Your gold is insufficient. Magic demands value.",
        "Not enough coin. Come back after looting a dragon's horde.",
        "Even the ley lines cannot conjure gold from an empty purse.",
        "The price is fixed. Return when you are richer.",
    ],
    "leave": [
        "May the ley lines light your path.",
        "Come back when your curiosity outweighs your fear.",
        "Farewell, seeker. The arcane never forgets.",
        "Until the next celestial alignment.",
    ],
}

SKYLUME_INNKEEPER_DIALOGUE = {
    "enter": [
        "Welcome to the Astral Rest. Sleep under floating lights.",
        "Ah, a tired traveler! The magic here soothes the mind.",
        "Come, rest in the hovering chambers. No falling, I promise.",
        "Skylume's best inn. We have beds that don't float... much.",
    ],
    "rest": [
        "There now, let the enchantment ease your weariness.",
        "A short rest in the shimmering glow. You'll feel renewed.",
        "Sit. The arcane breezes are healing.",
        "Rest easy. The floating towers protect us.",
    ],
    "sleep": [
        "Sleep under star-light and ley-glow. You'll dream of wonders.",
        "Eight hours in magic silence. Your mind will clear.",
        "The astral realm visits kindly tonight. Rest well.",
        "No nightmares here. Only gentle floating dreams.",
    ],
    "leave": [
        "Come back when the magic calls you.",
        "May the ley lines guide you home.",
        "The Astral Rest will be here. Floating as always.",
        "Farewell. Watch for dimensional rifts.",
    ],
    "early_sleep": [ 
    "The innkeeper smiles: 'The sun still graces the lower world, traveler. Rest if you wish, but full slumber comes when the floating lanterns ignite.'",
    ]
}

SKYLUME_BLACKSMITH_DIALOGUE = {
    "greeting": [
        "Ah, a customer! My forge runs on arcane flame. What needs shaping?",
        "Welcome to the Star Anvil. I craft magic into steel.",
        "Weapons that sing with ley energy. That's my specialty.",
        "Step closer. The floating hammer never misses.",
    ],
    "farewell": [
        "May your blade shine with starlight.",
        "Come back when you need true enchantment.",
        "Farewell. The arcane forge awaits.",
        "Keep that weapon charged. Magic fades.",
    ],
    "invalid_choice": "Speak! The ley lines buzz and I cannot hear.",
    "no_equipment": "You've no gear to enchant. Bring me steel.",
    "max_enhance": "That item's magic is maxed. No more work possible.",
    "not_enough_gold": "Your gold is lighter than aether. Find more.",
    "enhance_success": "By the stars! Your {} blazes with new magic!",
    "no_scrolls": "No scrolls? Bring me arcane parchment.",
    "no_equipment_fuse": "I need equipment to fuse, not empty hands.",
    "scroll_not_higher": "This scroll's magic is weaker. Find a deeper incantation.",
    "fusion_failed": "The ley lines rejected the fusion. Nothing changed.",
    "fusion_success": "The arcane approves! Your {} now has {} rarity!",
}

# ==================== ASHKARA (Ruin-City) ====================
ASHKARA_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "Ashkara doesn't welcome. It merely... tolerates. Speak fast.",
        "Another fool seeking relics in the ash. State your name.",
        "The ruins have eyes. And they're watching you.",
        "Welcome to the end of the world. Try not to die.",
    ],
    "tip": [
        "Tip: The ash sometimes hides treasure. Sometimes hides teeth.",
        "Tip: Cultists trade in blood and secrets. Don't trust them.",
        "Tip: The city has no law. Only power.",
        "Tip: Leave before the ash storms come. Or don't. I don't care.",
    ],
    "leave": [
        "The ruins will remember your footsteps... or bury them.",
        "Come back alive if you can. Few do.",
        "May the ash not claim you.",
        "Farewell. Don't say I didn't warn you.",
    ],
}

ASHKARA_SHOPKEEPER_DIALOGUE = {
    "enter": [
        "Ah, fresh meat... I mean, valued customer! What do you need?",
        "Relics from the ash, cursed or blessed? You decide.",
        "Welcome to the Last Stall. Everything here was looted from corpses.",
        "Ashkara's finest junk. But maybe you'll find a gem.",
    ],
    "success": [
        "Good choice. That item has only minor curses.",
        "Fair trade. May it not kill you in your sleep.",
        "The ash approves. Enjoy your... treasure.",
        "Paid in full. No refunds on demon possessions.",
    ],
    "fail": [
        "Your gold is as worthless as your courage.",
        "Not enough coin. Come back after you've raided a tomb.",
        "Even I have standards. Get richer.",
        "Empty purse, empty promises. Leave.",
    ],
    "leave": [
        "The ash will take you eventually. Come back before then.",
        "Farewell, soon-to-be-corpse.",
        "The Last Stall will be here. Waiting for your gold... or your bones.",
        "May the ruins treat you kindly. They won't.",
    ],
}

ASHKARA_INNKEEPER_DIALOGUE = {
    "enter": [
        "The Ash Refuge. Warm beds, cold stares. What do you want?",
        "Another survivor. Sit by the soot-fire. It's almost safe.",
        "Welcome to the last inn before the end. Don't break anything.",
        "Ashkara's only refuge. I don't ask questions. You shouldn't either.",
    ],
    "rest": [
        "There. Rest your bones. The ash won't find you here.",
        "A short break. The walls are thick. Mostly.",
        "Sit. The fire burns hot. Keeps the ghouls away.",
        "Rest easy. I've killed three intruders this week. Two were monsters.",
    ],
    "sleep": [
        "Sleep if you dare. I'll keep watch... for a price.",
        "Eight hours of dreamless black. You'll wake... probably.",
        "The refuge is safe. Mostly. Don't leave the circle.",
        "Rest well. The ash storms howl outside, but inside is... quieter.",
    ],
    "leave": [
        "Come back if you survive. I'll be here. Counting your room's gold.",
        "The ash awaits. Don't forget to run.",
        "Farewell. Try not to become part of the ruins.",
        "The refuge door is always open... for paying customers.",
    ],
    "early_sleep": [
    "The innkeeper snarls: 'The sun still bleeds above the ash? Rest if you must, but true sleep comes when the red moon rises. And not before.'",
    ],
}

ASHKARA_BLACKSMITH_DIALOGUE = {
    "greeting": [
        "Ah, a customer! My forge runs on ash and anger. What needs fixing?",
        "Welcome to the Broken Anvil. I repair what the ruins break.",
        "Weapons from salvaged steel. They might explode. Your risk.",
        "Step up. My hammer is hot and my patience is cold.",
    ],
    "farewell": [
        "May your blade not shatter on first strike.",
        "Come back for repairs. You'll need them.",
        "Farewell. The ash will test your gear.",
        "Keep that weapon oiled. Rust is the least of your worries.",
    ],
    "invalid_choice": "Speak! The ash in my ears makes hearing hard.",
    "no_equipment": "You've nothing to fix. Find a weapon before the ruins find you.",
    "max_enhance": "That item's as good as it gets. Don't push luck.",
    "not_enough_gold": "Your gold is lighter than ash. Find more or die trying.",
    "enhance_success": "By the scorched earth! Your {} might actually work now!",
    "no_scrolls": "No scrolls? Bring me charred enchantments.",
    "no_equipment_fuse": "I need equipment to fuse, not empty pleas.",
    "scroll_not_higher": "This scroll's weaker than the item's curse. Find a stronger one.",
    "fusion_failed": "The ash rejected the fusion. Nothing changed. Probably for the best.",
    "fusion_success": "Miracles happen! Your {} now boasts {} rarity! Don't celebrate yet.",
}

BLACKSMITH_DIALOGUES = {
    "solmere": SOLMERE_BLACKSMITH_DIALOGUE,
    "brinewatch": BRINEWATCH_BLACKSMITH_DIALOGUE,
    "elderfen": ELDERFEN_BLACKSMITH_DIALOGUE,
    "irondeep": IRONDEEP_BLACKSMITH_DIALOGUE,
    "skylume": SKYLUME_BLACKSMITH_DIALOGUE,
    "ashkara": ASHKARA_BLACKSMITH_DIALOGUE,
}