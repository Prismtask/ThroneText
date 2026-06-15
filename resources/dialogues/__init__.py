from .solmere import *
from .skylume import *
from .ashkara import *
from .brinewatch import *
from .irondeep import *
from .blackwake import *
from .coralhaven import *
from .dunemar import *
from .elderfen import *
from .greyharbor import *
from .isle_of_glass import *
from .stormhold import *
from .sunreach import *
from .thornwall import *
from .tidebreak import *
from .mirefall import *
from .saltmarsh import *
from .cinderpeak import *
from .veilholt import *

# Recreate BLACKSMITH_DIALOGUES mapping (originally at end of old dialogues.py)
BLACKSMITH_DIALOGUES = {
    "solmere": SOLMERE_BLACKSMITH_DIALOGUE,
    "brinewatch": BRINEWATCH_BLACKSMITH_DIALOGUE,
    "irondeep": IRONDEEP_BLACKSMITH_DIALOGUE,
    "ashkara": ASHKARA_BLACKSMITH_DIALOGUE,
}