# city.py — Service handler registry for city facilities.
#
# The terminal-mode visit_city() loop has been retired.
# The GUI CityScreen handles all city UI via gui/screens/city_screen.py.
# This file now serves only as the SERVICE_HANDLERS registry.

# Import all facility handlers
from facilities.shop import city_shop
from facilities.inn import inn_menu
from facilities.blacksmith import blacksmith_menu
from facilities.temple import temple_menu
from facilities.port import port_service
from facilities.shipyard import shipyard_service
from facilities.trade_hall import trade_hall_service
from facilities.barracks import barracks_service
from facilities.herbalist import herbalist_service
from facilities.arcane_tower import arcane_tower_service
from facilities.black_market import black_market_service
from facilities.guild import guild_service
from facilities.house import house_menu
from facilities.gift_shop import gift_shop_service

# Map service names to handler functions
SERVICE_HANDLERS = {
    "shop":          city_shop,
    "inn":           inn_menu,
    "blacksmith":    blacksmith_menu,
    "port":          port_service,
    "shipyard":      shipyard_service,
    "trade_hall":    trade_hall_service,
    "temple":        temple_menu,
    "barracks":      barracks_service,
    "herbalist":     herbalist_service,
    "arcane_tower":  arcane_tower_service,
    "black_market":  black_market_service,
    "guild":         guild_service,
    "gift_shop":     gift_shop_service,
}