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

SOLMERE_TRADE_HALL_DIALOGUE = {
    "enter": [
        "Welcome to the Solmere Trade Hall, where fortunes are made and lost.",
        "Merchants from a hundred cities gather here. What do you seek?",
        "The hall echoes with the sound of coin and quills. State your business.",
        "Letters of credit, rare permits, trade routes – we handle it all.",
    ],
    "leave": [
        "May your ventures prosper under the council's eye.",
        "Come back when you need to move goods across Aeralis.",
        "The Trade Hall never closes for those with ambition.",
        "Farewell. Remember – everything has a price.",
    ],
}

SOLMERE_TEMPLE_DIALOGUE = {
    "enter": [
        "The Light of Order welcomes you. Seek blessings or offer prayers?",
        "Solmere's temple stands as a pillar of peace. Speak your heart.",
        "May the divine council hear your plea. What brings you here?",
        "The temple doors are always open to the faithful and the lost.",
    ],
    "bless": [
        "The priest murmurs a blessing over you. May it guide your path.",
        "Light radiates from the altar. You feel... protected.",
        "A soft warmth settles in your chest. The gods have heard you.",
        "Your spirit feels lighter. The blessing will linger for a time.",
    ],
    "leave": [
        "Go with the council's grace.",
        "May order follow your footsteps.",
        "Return when your soul needs mending.",
        "The temple's light will wait for you.",
    ],
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

BRINEWATCH_PORTMASTER_DIALOGUE = {
    "enter": [
        "Portmaster's office. State your vessel and cargo.",
        "If you need passage or permits, you talk to me.",
        "The docks are mine. What do you want?",
        "Another traveler seeking sea-roads. Speak quickly.",
    ],
    "buy_ticket": [
        "Fair winds and a fair price. Here's your passage.",
        "Ticket's booked. Don't miss the tide.",
        "One voyage, paid in full. Mind the gangplank.",
        "You're on the manifest. Safe sailing.",
    ],
    "leave": [
        "Keep to the schedule. The sea waits for no one.",
        "Come back when you need to sail again.",
        "Farewell. Watch for storms.",
        "The port is always busy. Return anytime.",
    ],
}

BRINEWATCH_SHIPYARD_DIALOGUE = {
    "enter": [
        "Welcome to the Brinewatch Shipyard. Looking to buy or repair?",
        "Hulls and masts – we build 'em sturdy.",
        "Need a ship that laughs at storms? You've come to the right place.",
        "The best vessels on the coast come from this yard.",
    ],
    "buy_ship": [
        "A fine vessel! Treat her well.",
        "She's yours. May she carry you to glory.",
        "The sea accepts your new ship. Don't drown.",
        "A wise purchase. That boat has years left.",
    ],
    "leave": [
        "Come back when you need a bigger boat.",
        "Fair winds to your new vessel.",
        "The yard stays busy. Return anytime.",
        "Farewell. Keep the hull tarred.",
    ],
}

BRINEWATCH_TRADE_HALL_DIALOGUE = {
    "enter": [
        "Welcome to the Brinewatch Exchange. Smuggled goods welcome – discreetly.",
        "The hall is loud with haggling. What's your offer?",
        "Salt, spice, and secrets. We trade in all three.",
        "Mind the cutpurses. Trade here is honest... mostly.",
    ],
    "leave": [
        "May your profits be large and your losses small.",
        "Come back with more cargo.",
        "The Exchange never truly closes.",
        "Farewell. Watch your back on the docks.",
    ],
}

# ==================== GREYHARBOR (Foggy Port) ====================
GREYHARBOR_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "Ah, another soul through the mist. Welcome to Greyharbor.",
        "The fog hides many things. State your business quickly.",
        "Greyharbor welcomes the lost and the clever. Which are you?",
        "The guild keeps a low profile here. Speak softly.",
    ],
    "tip": [
        "Tip: The fog lifts at noon for exactly one hour. Use it wisely.",
        "Tip: Some traders only appear when the bells of the sunken church ring.",
        "Tip: Never follow a lantern that moves without a carrier.",
        "Tip: The harbour's depths hold old secrets – and older dangers.",
    ],
    "leave": [
        "May the fog part for your departure.",
        "Return when the mist calls you.",
        "Greyharbor remembers those who leave.",
        "Farewell. Don't trust the lights on the water.",
    ],
}

GREYHARBOR_SHOPKEEPER_DIALOGUE = {
    "enter": [
        "Ah, a customer! The fog keeps my prices low and my goods... mysterious.",
        "Welcome to the Drowned Ledger. Everything has a story.",
        "Need something rare? It's here. Probably.",
        "Step inside. The mist can't follow you in here.",
    ],
    "success": [
        "A fine choice. That item has been waiting for you.",
        "Coin changes hands, secrets stay. Good doing business.",
        "May it serve you better than the last owner.",
        "The fog accepts your gold. Fair trade.",
    ],
    "fail": [
        "Your purse is as empty as the mist is thick.",
        "Not enough gold. Come back after a successful voyage.",
        "I don't haggle with paupers.",
        "The price stands. Find more coin.",
    ],
    "leave": [
        "Come back when the fog grows thin.",
        "The Drowned Ledger is always open... by appointment.",
        "Farewell. Watch for shifting shadows.",
        "May your next visit be richer.",
    ],
}

GREYHARBOR_INNKEEPER_DIALOGUE = {
    "enter": [
        "Welcome to the Misty Hearth. Warm beds, hot stew, and no questions.",
        "Ah, a weary traveler! The fog gets into bones. Sit, warm up.",
        "Greyharbor's finest inn. The ghosts don't bother us much.",
        "Come in, come in. The fire's lit and the ale is dark.",
    ],
    "rest": [
        "There now, let the mist clear from your mind.",
        "A short rest by the fire. You'll feel the fog lift.",
        "Sit. The hearth keeps the damp away.",
        "Rest easy. No ghosts in this room. Probably.",
    ],
    "sleep": [
        "Sleep deep. The fog outside muffles all sound.",
        "Eight hours of quiet. You'll wake... rested?",
        "Dream of clear skies, traveler.",
        "The inn is safe. The mist can't enter.",
    ],
    "leave": [
        "Come back when the fog chills you again.",
        "The Misty Hearth will be here. Hiding in the grey.",
        "Farewell. Mind the lanterns on the pier.",
        "Safe travels through the haze.",
    ],
    "early_sleep": [
        "The innkeeper frowns: 'The sun still tries to pierce the fog, friend. Rest a while, but true sleep comes when the grey deepens.'",
    ],
}

GREYHARBOR_PORTMASTER_DIALOGUE = {
    "enter": [
        "Portmaster's office. The fog delays all ships. What do you want?",
        "If you need passage, speak quickly. The mist is unpredictable.",
        "Greyharbor's port is quiet... too quiet. State your business.",
        "Tide and fog charts are on the wall. Don't touch them.",
    ],
    "buy_ticket": [
        "A berth booked. May the fog lift for your voyage.",
        "Ticket in hand. Don't lose it in the mist.",
        "Fair passage. The ship leaves when it can see the water.",
        "Paid. Now wait by the western pier.",
    ],
    "leave": [
        "The fog may delay your departure. Be patient.",
        "Come back when you need to sail again.",
        "Farewell. Listen for the harbor bell.",
        "The portmaster's eyes follow you into the mist.",
    ],
}

GREYHARBOR_TRADE_HALL_DIALOGUE = {
    "enter": [
        "Greyharbor Trade Consortium. We deal in what others won't touch.",
        "The hall is quiet today. The fog keeps traders away. Good for you.",
        "Secrets and silver. Name your need.",
        "Welcome. Everything here has a hidden cost.",
    ],
    "leave": [
        "May your deals stay in the shadows.",
        "Come back when you have more... interesting goods.",
        "The Consortium never forgets a face.",
        "Farewell. Speak of this place to no one.",
    ],
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

ELDERFEN_HERBALIST_DIALOGUE = {
    "enter": [
        "Ah, a seeker of swamp remedies! What ails you?",
        "Fungi, roots, and rare blossoms. I have it all.",
        "The marsh gives me its secrets. I share them... for a price.",
        "Welcome to the Root and Bloom. Touch nothing without asking.",
    ],
    "buy": [
        "A wise choice. That herb will mend what ails you.",
        "Good eye. This one is potent. Use sparingly.",
        "The swamp's gift, passed to you. May it serve.",
        "Fresh from the bog. Handle with care.",
    ],
    "leave": [
        "May the marsh's medicine keep you alive.",
        "Come back when your wounds need tending.",
        "The Root and Bloom is always here. In the damp.",
        "Farewell. Don't eat the yellow mushrooms.",
    ],
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
    ],
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

IRONDEEP_BARRACKS_DIALOGUE = {
    "enter": [
        "State your name and allegiance. Irondeep's guard doesn't suffer fools.",
        "Barracks of the Mountain Guard. What business have you?",
        "If you seek training or a commission, speak now.",
        "The Forge Council's soldiers keep the deep roads safe. Why are you here?",
    ],
    "train": [
        "The drillmaster puts you through brutal exercises. You feel stronger.",
        "Your muscles ache, but you've learned a new technique.",
        "Sweat and steel. That's the Irondeep way. Your skills improve.",
        "After hours of drills, you feel more combat-ready.",
    ],
    "leave": [
        "The mountain guard watches you leave. Don't return as an enemy.",
        "May your axe bite deep.",
        "Farewell. Train harder next time.",
        "The barracks doors close behind you with a heavy thud.",
    ],
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
    ],
}

SKYLUME_ARCANE_TOWER_DIALOGUE = {
    "enter": [
        "You stand before the Spire of Seven Secrets. Speak your desire.",
        "The tower hums with concentrated magic. State your purpose, seeker.",
        "Few are allowed this close. What arcane need brings you here?",
        "The wards part for you... for now. Enter quickly.",
    ],
    "research": [
        "The archmage shares a fragment of forbidden knowledge. Your mind expands.",
        "Hours among ancient tomes reveal hidden truths. You feel wiser.",
        "The tower's magic sharpens your understanding of the arcane.",
        "A secret whispered by the ley lines themselves – you'll not forget it.",
    ],
    "leave": [
        "The tower's doors close behind you. The magic lingers on your skin.",
        "May your newfound knowledge serve you... and not destroy you.",
        "Return when you seek deeper mysteries.",
        "The Spire of Seven Secrets will remember your visit.",
    ],
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

ASHKARA_BLACK_MARKET_DIALOGUE = {
    "enter": [
        "Ah, a risk-taker. The black market has what the surface shops won't sell.",
        "Keep your voice down. And your gold ready.",
        "Cursed relics, illegal enchantments, smuggled goods. What's your poison?",
        "Welcome to the Underhand. Everything here is stolen or forbidden. Or both.",
    ],
    "buy": [
        "A dangerous choice. Don't say I didn't warn you.",
        "Gold changes hands. The item is yours. What the law doesn't know...",
        "No questions asked. No refunds given.",
        "May this serve your dark purpose.",
    ],
    "leave": [
        "Speak of this place to no one.",
        "The shadows swallow your footsteps. Farewell.",
        "Come back when you need something truly illegal.",
        "The black market always remembers a good customer.",
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

# ==================== SUNREACH (Desert Port) ====================
SUNREACH_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "Welcome to Sunreach, where the sun never hides. State your purpose.",
        "Ah, a traveler with dust on their boots. The guild welcomes you.",
        "Sunreach's gates are open. Business or pleasure?",
        "The desert heat softens no one. Speak quickly.",
    ],
    "tip": [
        "Tip: The sun here can kill. Always carry water.",
        "Tip: Caravans leave at dawn. Don't be late.",
        "Tip: The Sun Temple offers blessings against heatstroke.",
        "Tip: Sandstorms appear without warning. Watch the horizon.",
    ],
    "leave": [
        "May the sun light your path.",
        "Return when the desert calls you again.",
        "Farewell. Don't forget your waterskin.",
        "The sands remember those who leave.",
    ],
}

SUNREACH_SHOPKEEPER_DIALOGUE = {
    "enter": [
        "Ah, a customer! Sunreach's bazaar has everything under the blazing sun.",
        "Spices, silks, and desert steel. What catches your eye?",
        "Welcome to the Golden Sands. My goods are as hot as the weather.",
        "Step into the shade. The sun can wait.",
    ],
    "success": [
        "A fine choice. That item has crossed the Great Dunes to reach you.",
        "Fair price. May it serve you well under the sun.",
        "The desert approves your purchase. Drink water.",
        "Good trade. Come back when your purse refills.",
    ],
    "fail": [
        "Your coin is as dry as a dead oasis.",
        "Not enough gold. Even the sun doesn't give free light.",
        "Come back when your pockets are heavier.",
        "I don't trade with empty purses, desert rat.",
    ],
    "leave": [
        "May your next visit be richer.",
        "The bazaar never truly closes. Return anytime.",
        "Farewell. Watch for sand in your boots.",
        "Come back when you need shelter from the heat.",
    ],
}

SUNREACH_INNKEEPER_DIALOGUE = {
    "enter": [
        "Welcome to the Shaded Palm. Cool water, cooler beds.",
        "Ah, a traveler! The desert sun is cruel. Rest here.",
        "Sunreach's finest inn. We keep the heat out.",
        "Come in, come in. The courtyard fountain is lovely.",
    ],
    "rest": [
        "There now, let the shade cool your brow.",
        "A short rest by the fountain. The sun can wait.",
        "Sit. Drink this. It's not water, but it helps.",
        "Rest easy. No sandstorms indoors.",
    ],
    "sleep": [
        "Sleep under cool linens. The desert night is cold.",
        "Eight hours of quiet. The stars watch over you.",
        "Dream of oases and full waterskins.",
        "The inn is safe. The sun won't find you here.",
    ],
    "leave": [
        "Come back when the sun grows heavy.",
        "The Shaded Palm will be here. Cool as ever.",
        "Farewell. Drink water. Lots of it.",
        "Safe travels through the golden sands.",
    ],
    "early_sleep": [
        "The innkeeper laughs: 'The sun is still high, friend! Rest a while if you must, but full slumber comes when the stars appear.'",
    ],
}

SUNREACH_PORTMASTER_DIALOGUE = {
    "enter": [
        "Sunreach Port Authority. Where are you sailing?",
        "The harbor is small but busy. State your need.",
        "Desert ships and river boats – we manage them all.",
        "If you need passage along the coast, you talk to me.",
    ],
    "buy_ticket": [
        "Ticket booked. The ship leaves at noon.",
        "Fair passage. Don't miss the tide – what little there is.",
        "One voyage, paid. Stay out of the captain's way.",
        "You're on the manifest. Safe sailing.",
    ],
    "leave": [
        "The port is always open. Return anytime.",
        "May your voyage be smooth and short.",
        "Farewell. Watch for pirates near the shallows.",
        "Come back when you need to sail again.",
    ],
}

SUNREACH_TEMPLE_DIALOGUE = {
    "enter": [
        "The Temple of the Eternal Sun welcomes you. Seek light?",
        "Bathe in the sun's blessing. What do you offer?",
        "The priests here heal both body and spirit. State your need.",
        "Sunreach's holiest ground. Speak your prayer.",
    ],
    "bless": [
        "The priest raises a sun-orb. Warmth flows through you.",
        "You feel the desert's harshness soften. A blessing rests on you.",
        "Golden light bathes your soul. You are renewed.",
        "The sun's favor grants you strength. Use it wisely.",
    ],
    "leave": [
        "May the sun always find your face.",
        "Return when your spirit needs warmth.",
        "The Eternal Sun watches over your journey.",
        "Farewell. Stay hydrated.",
    ],
}

# ==================== THORNWALL (Fortress City) ====================
THORNWALL_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "Thornwall stands against the wild. State your allegiance.",
        "Fortress city. We don't trust outsiders. Speak fast.",
        "The wall protects us. What brings you to the frontier?",
        "Another traveler seeking safety behind the stone. Name yourself.",
    ],
    "tip": [
        "Tip: The watch changes every four hours. Don't be on the walls then.",
        "Tip: The forest beyond the wall is forbidden. Trespassers disappear.",
        "Tip: Thornwall's smiths work day and night. They sleep never.",
        "Tip: The commander hates excuses. Be brief or be gone.",
    ],
    "leave": [
        "May the wall hold against what follows you.",
        "Return with news of the wilds.",
        "Farewell. Don't open the postern gate.",
        "The fortress remembers your face.",
    ],
}

THORNWALL_SHOPKEEPER_DIALOGUE = {
    "enter": [
        "Ah, a customer! Thornwall's goods are battle-tested.",
        "Weapons, rations, fortification supplies. What do you need?",
        "The frontier market has what the inner cities lack. Look around.",
        "Welcome to the Bulwark Emporium. Everything here has killed something.",
    ],
    "success": [
        "Good choice. That axe has felled a dozen trolls.",
        "Fair price for frontier steel. Come again.",
        "May this item help you survive the night.",
        "The wall approves your purchase. Now go.",
    ],
    "fail": [
        "Your coin is as thin as a goblin's excuse.",
        "Not enough gold. The frontier doesn't give discounts.",
        "Come back when you've sold something.",
        "Empty purse, empty hands. Leave.",
    ],
    "leave": [
        "Come back when you need better gear.",
        "The Bulwark Emporium is always open. Even during sieges.",
        "Farewell. Keep your blade sharp.",
        "May your next visit be richer.",
    ],
}

THORNWALL_INNKEEPER_DIALOGUE = {
    "enter": [
        "Welcome to the Stubborn Ram. Hot food, cold ale, safe beds.",
        "Ah, a traveler from the south! Sit. The wall keeps us safe.",
        "Thornwall's only decent inn. I don't overcharge much.",
        "Come in, come in. The fire's hot and the stories are wild.",
    ],
    "rest": [
        "There now, let the fire warm your bones.",
        "A short rest. The watch will wake you if trouble comes.",
        "Sit. The ale is strong. Helps with the fear.",
        "Rest easy. The wall is thick and the guards are sober. Mostly.",
    ],
    "sleep": [
        "Sleep deep. I'll keep the lantern lit.",
        "Eight hours of dreamless rest. You'll need it.",
        "The frontier is quiet tonight. Rest well.",
        "No monsters in here. The wall keeps them out.",
    ],
    "leave": [
        "Come back when the wild howls.",
        "The Stubborn Ram will be here. With more ale.",
        "Farewell. Don't go beyond the wall.",
        "Safe travels. Mind the forest's edge.",
    ],
    "early_sleep": [
        "The innkeeper grunts: 'The sun's still up, soldier. Rest a spell if you must, but full sleep comes after the evening bell.'",
    ],
}

THORNWALL_BARRACKS_DIALOGUE = {
    "enter": [
        "Thornwall Garrison. State your name and rank.",
        "If you're not militia, you're not welcome. Speak.",
        "The barracks smell of steel and sweat. What do you want?",
        "Commander's office is that way. Don't waste our time.",
    ],
    "train": [
        "The drill sergeant works you to exhaustion. You're stronger for it.",
        "Hours of sword practice leave you bruised but improved.",
        "Frontier training is brutal. You survive and learn.",
        "Your combat skills sharpen against Thornwall's veterans.",
    ],
    "leave": [
        "The garrison watches you leave. Return ready to fight.",
        "May your blade serve the wall.",
        "Farewell. Train harder next time.",
        "The barracks doors close. The frontier waits.",
    ],
}

# ==================== DUNEMAR (Desert Trade Hub) ====================
DUNEMAR_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "Dunemar – where the desert meets the sea. State your business.",
        "Ah, a traveler with sand in their hair. Welcome.",
        "The guild here is neutral. Trade is sacred. Speak.",
        "Dunemar welcomes all who respect the dunes.",
    ],
    "tip": [
        "Tip: The desert caravans leave at moonrise.",
        "Tip: Salt from the coast is worth more than gold inland.",
        "Tip: Never insult a camel trader. They have long memories.",
        "Tip: The evening markets sell the best spices.",
    ],
    "leave": [
        "May the dunes guide your steps.",
        "Return when your goods run low.",
        "Farewell. Watch for sandstorms.",
        "The desert remembers those who leave.",
    ],
}

DUNEMAR_SHOPKEEPER_DIALOGUE = {
    "enter": [
        "Ah, a customer! Dunemar's bazaar is legendary.",
        "Spices, silks, salt, and steel. What do you seek?",
        "Welcome to the Sand-Swept Stall. Everything here crossed the deep desert.",
        "The best trade on the coast. Look around.",
    ],
    "success": [
        "A fine purchase. That item has traveled far.",
        "Fair gold for fair goods. Come again.",
        "The desert approves your choice.",
        "Good trade. May it serve you well.",
    ],
    "fail": [
        "Your coin is lighter than a desert ghost.",
        "Not enough gold. The bazaar doesn't haggle with paupers.",
        "Come back when you've sold your camel.",
        "Empty purse, empty promises.",
    ],
    "leave": [
        "The bazaar is always open. Return anytime.",
        "May your next visit be richer.",
        "Farewell. Drink water.",
        "Come back when you need more spices.",
    ],
}

DUNEMAR_INNKEEPER_DIALOGUE = {
    "enter": [
        "Welcome to the Oasis Rest. Cool rooms, cooler drinks.",
        "Ah, a weary trader! Sit by the fountain.",
        "Dunemar's finest inn. We keep the desert out.",
        "Come in, come in. The beds are soft and the water is fresh.",
    ],
    "rest": [
        "There now, let the cool air revive you.",
        "A short rest. The fountain's murmur soothes.",
        "Sit. Drink this mint tea. It helps.",
        "Rest easy. No sand in here.",
    ],
    "sleep": [
        "Sleep deep. The desert night is quiet.",
        "Eight hours of peace. You'll wake refreshed.",
        "Dream of green oases and full waterskins.",
        "The inn is safe. The dunes can wait.",
    ],
    "leave": [
        "Come back when the sun burns too hot.",
        "The Oasis Rest will be here. Cool as ever.",
        "Farewell. Watch for bandits on the road.",
        "Safe travels through the golden sands.",
    ],
    "early_sleep": [
        "The innkeeper smiles: 'The sun's still high, traveler. Rest a while, but full slumber comes after the evening call to prayer.'",
    ],
}

DUNEMAR_PORTMASTER_DIALOGUE = {
    "enter": [
        "Dunemar Port Authority. Where to?",
        "The harbor handles both sea and river trade. State your need.",
        "If you need passage, speak quickly. The tide waits for no one.",
        "Desert ships and coastal vessels – we manage them all.",
    ],
    "buy_ticket": [
        "Ticket booked. Don't be late.",
        "Fair passage. The captain is grumpy but skilled.",
        "One voyage, paid. Stay out of the cargo hold.",
        "You're on the manifest. Safe sailing.",
    ],
    "leave": [
        "The port is always busy. Return anytime.",
        "May your voyage be profitable.",
        "Farewell. Watch for pirates.",
        "Come back when you need to sail again.",
    ],
}

DUNEMAR_TRADE_HALL_DIALOGUE = {
    "enter": [
        "Dunemar Trade Consortium. We move goods across sand and sea.",
        "The hall is loud with deals. What do you offer?",
        "Spices, salt, silk – we trade in everything.",
        "Welcome. Mind your purse. The merchants are sharp.",
    ],
    "leave": [
        "May your margins be wide.",
        "Come back with more cargo.",
        "The Consortium never sleeps.",
        "Farewell. Don't trust the desert traders too much.",
    ],
}

DUNEMAR_BLACK_MARKET_DIALOGUE = {
    "enter": [
        "The shadow market. Keep your voice down.",
        "Dunemar's underbelly. What do you need that's... illegal?",
        "We trade in what the guild won't touch. Speak softly.",
        "Welcome to the Sand-Silk Exchange. No questions asked.",
    ],
    "buy": [
        "A dangerous choice. No refunds.",
        "Gold changes hands. The item is yours. Deny everything.",
        "You saw nothing. I sold you nothing.",
        "May this serve your hidden purpose.",
    ],
    "leave": [
        "Speak of this place to no one.",
        "The shadows hide your exit. Farewell.",
        "Come back when you need something... darker.",
        "The black market always has a spot for you.",
    ],
}

# ==================== TIDEBREAK (Stormy Coastal City) ====================
TIDEBREAK_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "Tidebreak – where the sea fights the shore. State your business.",
        "Ah, another soul braving the storm coast. Welcome.",
        "The guild here is used to wet visitors. Speak.",
        "Tidebreak welcomes all who don't fear lightning.",
    ],
    "tip": [
        "Tip: The storms come fast. Stay off the cliffs during lightning.",
        "Tip: Tidebreak's shipwrights are the best. Expensive, though.",
        "Tip: The sea caves below the city hide smugglers – and treasure.",
        "Tip: Never gamble with a Tidebreak sailor. They cheat honestly.",
    ],
    "leave": [
        "May the storms spare your journey.",
        "Return when the tides are calm. Ha! They never are.",
        "Farewell. Watch for rogue waves.",
        "The sea remembers those who leave.",
    ],
}

TIDEBREAK_SHOPKEEPER_DIALOGUE = {
    "enter": [
        "Ah, a customer! Tidebreak's goods are storm-tested.",
        "Sealskins, storm lanterns, salvage from wrecks. What do you need?",
        "Welcome to the Breaker's Stall. Everything here survived the sea.",
        "The best gear for sailors. Look around.",
    ],
    "success": [
        "Good choice. That item has seen worse storms than you.",
        "Fair price for sea-toughened goods. Come again.",
        "The sea approves your purchase. Don't drop it overboard.",
        "May it keep you dry. Probably.",
    ],
    "fail": [
        "Your coin is as wet as a drowned rat.",
        "Not enough gold. The sea doesn't give discounts.",
        "Come back when you've sold something.",
        "Empty purse, empty hands. Leave.",
    ],
    "leave": [
        "Come back when you need more gear.",
        "The Breaker's Stall is always open. Even during hurricanes.",
        "Farewell. Keep your oilskin close.",
        "May your next visit be drier.",
    ],
}

TIDEBREAK_INNKEEPER_DIALOGUE = {
    "enter": [
        "Welcome to the Storm's Rest. Dry beds, hot food.",
        "Ah, a soaked traveler! Sit by the fire. The sea is cruel.",
        "Tidebreak's only decent inn. We keep the rain out. Mostly.",
        "Come in, come in. The roof leaks but the ale is warm.",
    ],
    "rest": [
        "There now, let the fire dry your bones.",
        "A short rest. The storm can wait.",
        "Sit. The rum helps with the shivers.",
        "Rest easy. No lightning in here.",
    ],
    "sleep": [
        "Sleep deep. The walls are thick.",
        "Eight hours of quiet. The storm will howl outside.",
        "Dream of calm seas. You won't find them here.",
        "The inn is safe. The sea can't reach you.",
    ],
    "leave": [
        "Come back when the storm chases you again.",
        "The Storm's Rest will be here. Leaky but warm.",
        "Farewell. Watch for falling masts.",
        "Safe travels. Keep your head down.",
    ],
    "early_sleep": [
        "The innkeeper laughs: 'The sun's still trying to shine, friend. Rest a while, but full slumber comes when the thunder starts.'",
    ],
}

TIDEBREAK_PORTMASTER_DIALOGUE = {
    "enter": [
        "Tidebreak Port Authority. State your vessel and destination.",
        "The harbor is rough. If you need a berth, speak now.",
        "Storms delay everything. What do you want?",
        "Portmaster's office. Don't waste my time.",
    ],
    "buy_ticket": [
        "Ticket booked. The ship leaves when the storm pauses.",
        "Fair passage. Hold on to something.",
        "One voyage, paid. Don't get seasick.",
        "You're on the manifest. Pray for calm weather.",
    ],
    "leave": [
        "The port is always noisy. Return anytime.",
        "May your voyage be less stormy than most.",
        "Farewell. Watch for reefs.",
        "Come back when you need to sail again.",
    ],
}

TIDEBREAK_SHIPYARD_DIALOGUE = {
    "enter": [
        "Tidebreak Shipyard. We build vessels that laugh at storms.",
        "Need a new ship or repairs? You've come to the right place.",
        "The best shipwrights on the coast. Expensive but worth it.",
        "Welcome to the Breaker Yard. We've seen it all.",
    ],
    "buy_ship": [
        "A fine vessel. She's weathered a hundred storms.",
        "She's yours. May she keep you afloat.",
        "Good choice. That ship has years left.",
        "The sea accepts your purchase. Don't drown.",
    ],
    "leave": [
        "Come back when you need a bigger boat.",
        "The yard is always busy. Return anytime.",
        "Farewell. Keep the hull tarred.",
        "May your new ship serve you well.",
    ],
}

TIDEBREAK_TRADE_HALL_DIALOGUE = {
    "enter": [
        "Tidebreak Exchange. We trade in storm salvage and sea goods.",
        "The hall is wet and loud. What do you offer?",
        "Sealskins, whale oil, wreckwood – we deal in it all.",
        "Welcome. Mind the puddles.",
    ],
    "leave": [
        "May your cargo stay dry.",
        "Come back with more salvage.",
        "The Exchange never closes. Even in hurricanes.",
        "Farewell. Watch for waves.",
    ],
}

# ==================== STORMHOLD (Fortress Port) ====================
STORMHOLD_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "Stormhold – fortress of the northern sea. State your name.",
        "The walls keep out both storms and invaders. Speak.",
        "Another traveler seeking shelter from the wind. Welcome.",
        "Stormhold's guild is military-minded. Be respectful.",
    ],
    "tip": [
        "Tip: The north wall has the best view. And the strongest wind.",
        "Tip: Stormhold's navy is always recruiting. Don't volunteer.",
        "Tip: The sea caves below the fortress are forbidden. Obviously.",
        "Tip: The commander's word is law. Don't argue.",
    ],
    "leave": [
        "May the storm walls protect your journey.",
        "Return with news of the north.",
        "Farewell. Don't go near the cliffs.",
        "Stormhold remembers those who leave.",
    ],
}

STORMHOLD_SHOPKEEPER_DIALOGUE = {
    "enter": [
        "Ah, a customer! Stormhold's goods are built to last.",
        "Naval supplies, weapons, storm gear. What do you need?",
        "Welcome to the Iron Quay. Everything here is military surplus.",
        "The best gear for sailors and soldiers. Look around.",
    ],
    "success": [
        "Good choice. That item has served a hundred soldiers.",
        "Fair price for fortress steel. Come again.",
        "The navy approves your purchase.",
        "May it keep you alive.",
    ],
    "fail": [
        "Your coin is as weak as a summer breeze.",
        "Not enough gold. The fortress doesn't haggle.",
        "Come back when you've earned some coin.",
        "Empty purse, empty hands.",
    ],
    "leave": [
        "Come back when you need more gear.",
        "The Iron Quay is always open.",
        "Farewell. Keep your blade sharp.",
        "May your next visit be richer.",
    ],
}

STORMHOLD_PORTMASTER_DIALOGUE = {
    "enter": [
        "Stormhold Naval Port. Civilians stay clear.",
        "If you need passage on a military vessel, state your business.",
        "The port is under martial law. What do you want?",
        "Portmaster's office. Speak quickly.",
    ],
    "buy_ticket": [
        "Passage booked on a supply ship. Don't cause trouble.",
        "Fair warning – the captain is strict.",
        "One voyage, paid. Follow all orders.",
        "You're on the manifest. No complaints.",
    ],
    "leave": [
        "The port is always guarded. Return anytime.",
        "May your voyage be uneventful.",
        "Farewell. Don't steal from the navy.",
        "Come back when you need to sail again.",
    ],
}

STORMHOLD_SHIPYARD_DIALOGUE = {
    "enter": [
        "Stormhold Naval Shipyard. We build warships.",
        "Need a military vessel? You'll need the commander's approval.",
        "The best warships on the coast. Not for sale to civilians.",
        "Welcome to the Hammer and Anchor. We don't do pleasure boats.",
    ],
    "buy_ship": [
        "A fine warship. Use it well.",
        "She's yours. May she strike fear into your enemies.",
        "That vessel has sunk three pirate ships. Keep the streak.",
        "The navy approves this sale. Don't embarrass us.",
    ],
    "leave": [
        "Come back when you need more firepower.",
        "The yard is always busy. Return anytime.",
        "Farewell. Keep the cannons clean.",
        "May your new ship bring you glory.",
    ],
}

STORMHOLD_BARRACKS_DIALOGUE = {
    "enter": [
        "Stormhold Garrison. State your name and allegiance.",
        "If you're not military, you're not welcome. Speak.",
        "The barracks house the north's finest soldiers. What do you want?",
        "Commander's office is that way. Don't waste our time.",
    ],
    "train": [
        "The drill instructor is merciless. You improve.",
        "Hours of combat drills leave you exhausted but stronger.",
        "Stormhold training is legendary. You feel the difference.",
        "Your skills sharpen under the fortress's harsh discipline.",
    ],
    "leave": [
        "The garrison watches you leave. Return ready to serve.",
        "May your sword never falter.",
        "Farewell. Train harder next time.",
        "The barracks doors close. The north waits.",
    ],
}

# ==================== CORALHAVEN (Reef Port) ====================
CORALHAVEN_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "Welcome to Coralhaven, where the sea meets the reef. State your business.",
        "Ah, a traveler with salt on their skin. The guild welcomes you.",
        "Coralhaven is peaceful. Keep it that way.",
        "The reef protects us. What brings you to the coast?",
    ],
    "tip": [
        "Tip: The coral gardens are sacred. Don't touch.",
        "Tip: The best fish in Aeralis comes from these waters.",
        "Tip: The tide pools hold rare ingredients – and sea urchins.",
        "Tip: The temple offers blessings for sailors.",
    ],
    "leave": [
        "May the reef guide your way.",
        "Return when the sea calls you again.",
        "Farewell. Watch for riptides.",
        "Coralhaven remembers those who leave.",
    ],
}

CORALHAVEN_SHOPKEEPER_DIALOGUE = {
    "enter": [
        "Ah, a customer! Coralhaven's wares are as bright as the reef.",
        "Pearls, coral, exotic fish. What catches your eye?",
        "Welcome to the Reef Market. Everything here comes from the sea.",
        "The best coastal goods. Look around.",
    ],
    "success": [
        "A fine choice. That pearl is from the deep reef.",
        "Fair price for sea-treasure. Come again.",
        "The ocean approves your purchase.",
        "May it bring you luck on the water.",
    ],
    "fail": [
        "Your coin is as empty as a broken shell.",
        "Not enough gold. The reef doesn't give gifts.",
        "Come back when you've found some treasure.",
        "Empty purse, empty hands.",
    ],
    "leave": [
        "Come back when you need more sea-goods.",
        "The Reef Market is always open.",
        "Farewell. Watch for low tide.",
        "May your next visit be richer.",
    ],
}

CORALHAVEN_INNKEEPER_DIALOGUE = {
    "enter": [
        "Welcome to the Coral Rest. Soft beds, fresh fish.",
        "Ah, a weary sailor! Sit by the sea-breeze window.",
        "Coralhaven's finest inn. The sound of waves lulls you to sleep.",
        "Come in, come in. The rooms have ocean views.",
    ],
    "rest": [
        "There now, let the sea air revive you.",
        "A short rest. The waves are calming.",
        "Sit. The fish stew is excellent.",
        "Rest easy. No storms tonight.",
    ],
    "sleep": [
        "Sleep to the sound of gentle waves.",
        "Eight hours of peace. The reef protects.",
        "Dream of colorful fish and calm waters.",
        "The inn is safe. The sea is kind tonight.",
    ],
    "leave": [
        "Come back when the sea calls you.",
        "The Coral Rest will be here. Waiting by the shore.",
        "Farewell. Watch for jellyfish.",
        "Safe travels on the coastal roads.",
    ],
    "early_sleep": [
        "The innkeeper smiles: 'The sun still dances on the water, friend. Rest a while, but full slumber comes when the reef glows.'",
    ],
}

CORALHAVEN_PORTMASTER_DIALOGUE = {
    "enter": [
        "Coralhaven Port Authority. Where are you sailing?",
        "The harbor is calm today. State your need.",
        "If you need passage, speak now. The tide is turning.",
        "Portmaster's office. Don't track too much sand inside.",
    ],
    "buy_ticket": [
        "Ticket booked. The ship leaves at dawn.",
        "Fair passage. The captain knows the reef.",
        "One voyage, paid. Enjoy the sea air.",
        "You're on the manifest. Safe sailing.",
    ],
    "leave": [
        "The port is peaceful. Return anytime.",
        "May your voyage be smooth and sunny.",
        "Farewell. Watch for coral heads.",
        "Come back when you need to sail again.",
    ],
}

CORALHAVEN_HERBALIST_DIALOGUE = {
    "enter": [
        "Ah, a seeker of sea-healing! What ails you?",
        "Seaweed, reef-fungi, and coral powders. I have it all.",
        "The ocean provides the best remedies. Welcome.",
        "Welcome to the Tide Apothecary. Touch nothing without asking.",
    ],
    "buy": [
        "A wise choice. That remedy comes from the deep reef.",
        "Good eye. This one cures most poisons.",
        "The sea's gift, passed to you. May it heal.",
        "Fresh from the tide pools. Use carefully.",
    ],
    "leave": [
        "May the sea's medicine keep you well.",
        "Come back when your wounds need tending.",
        "The Tide Apothecary is always here. By the shore.",
        "Farewell. Don't eat the blue seaweed raw.",
    ],
}

CORALHAVEN_TEMPLE_DIALOGUE = {
    "enter": [
        "The Temple of the Tides welcomes you. Seek peace?",
        "The sea's blessing flows through this place. What do you offer?",
        "The priests here calm both storms and spirits. State your need.",
        "Coralhaven's holiest ground. Speak your prayer.",
    ],
    "bless": [
        "The priest sprinkles salt water on you. A cool blessing settles.",
        "You feel the ocean's vast calm. Your mind clears.",
        "The tide's favor grants you resilience. Use it well.",
        "A soft blue light surrounds you. The sea has heard you.",
    ],
    "leave": [
        "May the tides always bring you home.",
        "Return when your soul needs cleansing.",
        "The Temple of the Tides watches over your journey.",
        "Farewell. Listen to the waves.",
    ],
}

# ==================== BLACKWAKE (Pirate Haven) ====================
BLACKWAKE_RECEPTIONIST_DIALOGUE = {
    "enter": [
        "Blackwake doesn't have a real guild. Just me. What do you want?",
        "Ah, a criminal or a fool. Welcome to the pirate port.",
        "State your name and your business. Quickly.",
        "Blackwake welcomes only those with gold or steel.",
    ],
    "tip": [
        "Tip: The pirates run this city. Don't insult them.",
        "Tip: The black market is the only market.",
        "Tip: Never turn your back on anyone here.",
        "Tip: The harbor is full of stolen ships. Don't ask questions.",
    ],
    "leave": [
        "The pirates will remember your face. Maybe.",
        "Come back with more gold.",
        "Farewell. Watch for cutthroats.",
        "Blackwake doesn't forget debts.",
    ],
}

BLACKWAKE_INNKEEPER_DIALOGUE = {
    "enter": [
        "Welcome to the Drowned Rat. Don't steal the beds.",
        "Ah, another desperate soul. Sit by the smoky fire.",
        "Blackwake's only inn. We don't ask your name.",
        "Come in, come in. The floor is sticky but the price is low.",
    ],
    "rest": [
        "There. Don't fall asleep on the bar.",
        "A short rest. Keep one eye open.",
        "Sit. The rum is watered but safe.",
        "Rest easy. No killing in the common room. Usually.",
    ],
    "sleep": [
        "Sleep with your boots on.",
        "Eight hours of... well, sleep if you can.",
        "The rooms have locks. Use them.",
        "I'll wake you if the pirates come for you. Maybe.",
    ],
    "leave": [
        "Come back if you survive.",
        "The Drowned Rat will be here. Still sticky.",
        "Farewell. Don't trust the dock girls.",
        "Safe travels. Ha!",
    ],
    "early_sleep": [
        "The innkeeper snarls: 'The sun still shines? Rest if you must, but full sleep comes when the lanterns of the gallows are lit.'",
    ],
}

BLACKWAKE_PORTMASTER_DIALOGUE = {
    "enter": [
        "Blackwake Port. We don't ask for papers. What do you want?",
        "Need passage on a ship that won't ask questions? You found it.",
        "The harbor is full of... independent vessels. State your need.",
        "Portmaster's office. The one with the hook for a hand.",
    ],
    "buy_ticket": [
        "Ticket booked. The captain doesn't care who you are.",
        "Fair passage on a smuggler's ship. No guarantees.",
        "One voyage, paid. Don't ask about the crew.",
        "You're on the manifest. Fake name, I assume.",
    ],
    "leave": [
        "The port never sleeps. Return anytime.",
        "May your voyage be... discreet.",
        "Farewell. Don't get thrown overboard.",
        "Come back when you need to disappear.",
    ],
}

BLACKWAKE_BLACK_MARKET_DIALOGUE = {
    "enter": [
        "The real market. Underground. What do you need?",
        "Stolen goods, forbidden artifacts, crew for a raid. Name it.",
        "Welcome to the Wreck. No questions, no refunds.",
        "Blackwake's underbelly. Keep your gold hidden.",
    ],
    "buy": [
        "A dangerous purchase. Deny everything.",
        "Gold changes hands. The item is yours. I was never here.",
        "You saw nothing. Good doing business.",
        "May this serve your dark purpose.",
    ],
    "leave": [
        "Speak of this place to no one.",
        "The shadows hide your exit. Farewell.",
        "Come back when you need something... illegal.",
        "The black market always remembers.",
    ],
}

# ==================== ISLE OF GLASS (Crystal Island) ====================
ISLE_OF_GLASS_ARCANE_TOWER_DIALOGUE = {
    "enter": [
        "The Crystal Tower rises from the glass sands. State your purpose.",
        "Welcome to the Isle of Glass, where magic is forged in crystal.",
        "Few are allowed here. What arcane need brings you?",
        "The tower hums with pure ley energy. Speak carefully.",
    ],
    "research": [
        "The crystal mage shares a secret of crystallized magic. You understand more.",
        "Hours among glowing crystals sharpen your arcane senses.",
        "The tower's resonance unlocks a new insight.",
        "A shard of pure knowledge enters your mind. You feel changed.",
    ],
    "leave": [
        "The tower's crystal doors close silently. Magic lingers on your skin.",
        "May the crystal light guide your path.",
        "Return when you seek deeper resonance.",
        "The Isle of Glass will remember your visit.",
    ],
}

# ==================== Existing BLACKSMITH_DIALOGUES (unchanged) ====================
BLACKSMITH_DIALOGUES = {
    "solmere": SOLMERE_BLACKSMITH_DIALOGUE,
    "brinewatch": BRINEWATCH_BLACKSMITH_DIALOGUE,
    "elderfen": ELDERFEN_BLACKSMITH_DIALOGUE,
    "irondeep": IRONDEEP_BLACKSMITH_DIALOGUE,
    "skylume": SKYLUME_BLACKSMITH_DIALOGUE,
    "ashkara": ASHKARA_BLACKSMITH_DIALOGUE,
}