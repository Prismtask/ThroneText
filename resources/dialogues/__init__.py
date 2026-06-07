from .solmere import *
from .brinewatch import *
from .greyharbor import *
from .elderfen import *
from .irondeep import *
from .skylume import *
from .ashkara import *
from .sunreach import *
from .thornwall import *
from .dunemar import *
from .tidebreak import *
from .stormhold import *
from .coralhaven import *
from .blackwake import *
from .isle_of_glass import *

# Recreate BLACKSMITH_DIALOGUES mapping (originally at end of old dialogues.py)
BLACKSMITH_DIALOGUES = {
    "solmere": SOLMERE_BLACKSMITH_DIALOGUE,
    "brinewatch": BRINEWATCH_BLACKSMITH_DIALOGUE,
    "irondeep": IRONDEEP_BLACKSMITH_DIALOGUE,
    "ashkara": ASHKARA_BLACKSMITH_DIALOGUE,
}