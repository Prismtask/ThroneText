"""
gui/screens/city_screen.py — City hub with service buttons and action bar.

Shows all city services as clickable buttons, plus Inventory, Skill Book,
Travel, Dungeon, and Save & Quit actions.
"""

import tkinter as tk
import tkinter.font as tkfont

import karma
from karma_dialogue import service_line

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme
from gui.widgets.confirm_dialog import choice_dialog, confirm_dialog, ok_dialog
from gui.widgets.hp_bar import HPBar

from resources.cities import CITIES
from character import player_max_hp
from save_load import save_game
from utils import display_name
from events import format_date, get_event_queue_events
from combat.combat_ui import _get_entity_buff_tags


# The hero card is laid out for a full 8-actor party. Each member box uses
# this fixed slot size, so a 2-member party does not stretch into huge boxes
# and an 8-member party still fits without overflow.
HERO_CARD_MAX_SLOTS = 8          # == combat.ally.MAX_PARTY_SIZE (player + 7)
# Worst-case non-box width at 8 members: gaps + front/back dividers + margin.
HERO_ROW_EXTRAS_MAX = 8 * (HERO_CARD_MAX_SLOTS - 1) + 15 + 32 + 10


def _fit_text_to_width(text, font, max_width, ellipsis="\u2026"):
    """Truncate `text` with an ellipsis so its rendered width fits `max_width`.

    Used by the single-row party card: character names and titles are free
    text, and a long one used to push the card past the window edge.
    """
    if not text:
        return ""
    if max_width <= 0:
        return ""
    try:
        measure = tkfont.Font(font=font).measure
    except Exception:
        # No Tk root yet (e.g. headless call) — leave the text untouched.
        return text
    if measure(text) <= max_width:
        return text
    ell_width = measure(ellipsis)
    if ell_width > max_width:
        return ""
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if measure(text[:mid]) + ell_width <= max_width:
            lo = mid
        else:
            hi = mid - 1
    if lo <= 0:
        return ellipsis
    return text[:lo].rstrip() + ellipsis


class CityScreen(BaseScreen):
    """The city hub — main navigation screen between dungeon runs."""

    def build_ui(self):
        self._refresh_city_id()
        self.sm.clear_history()
        self._update_top_bar()
        self.sm.clear_log()

        # Arrival checks run in order: Karma gate first, then story beats /
        # Event Horizon. A low-Karma gate must never stack with a story overlay.

        # ── Main layout ────────────────────────────────────────────────────────
        self.content = self.styled_frame(self)
        self.content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # City name header
        city_name = self.city.get("name", "Unknown City")
        tk.Label(
            self.content,
            text=city_name.upper(),
            bg=Theme.BG_DARK,
            fg=Theme.ACCENT,
            font=Theme.FONT_LARGE,
        ).pack(pady=(0, 4))

        # Description
        desc = self.city.get("description", "")
        if desc:
            tk.Label(
                self.content,
                text=desc,
                bg=Theme.BG_DARK,
                fg=Theme.TEXT_DIM,
                font=Theme.FONT_SMALL,
                wraplength=700,
                justify=tk.CENTER,
            ).pack(pady=(0, 6))

        # ── Receptionist dialogue ─────────────────────────────────────────
        from city_dialogue import service_dialogue, get_city_dialogues
        receptionist_lines = get_city_dialogues(self.city_id, "receptionist").get("enter", [])
        if receptionist_lines:
            import random as _random
            dialogue = service_line(self.player, "receptionist", self.city_id)
            if not dialogue:
                dialogue = _random.choice(receptionist_lines)
            tk.Label(
                self.content,
                text=f'"{dialogue}"',
                bg=Theme.BG_DARK,
                fg=Theme.TEXT_DIM,
                font=(Theme.FONT_FAMILY, Theme.FONT_SIZE - 2, "italic") if Theme.FONT_SIZE > 1 else Theme.FONT_SMALL,
                wraplength=700,
                justify=tk.CENTER,
            ).pack(pady=(0, 10))
            # Also log to the session log
            self.sm.log(dialogue, category="dialogue")

        # ── Hero Status Card ────────────────────────────────────────────────
        if self.player:
            self._build_hero_card()

        # ── City Map (clickable ASCII art) ─────────────────────────────────────
        from resources.city_maps import get_city_map, CITY_SERVICE_POSITIONS
        from gui.widgets.city_map import CityMapWidget

        positions = CITY_SERVICE_POSITIONS.get(self.city_id, {})
        from time_blocks import is_service_open
        closed_services = [
            svc for svc in positions
            if svc != "dungeon"
            and not is_service_open(self.player, svc, self.city_id)
        ]

        self._map_frame = tk.Frame(self.content, bg=Theme.BG_DARK,
                                   highlightthickness=1, highlightbackground=Theme.BORDER)
        self._map_frame.pack(fill=tk.BOTH, expand=True, pady=8)

        self.city_map = CityMapWidget(
            self._map_frame,
            city_id=self.city_id,
            city=self.city,
            positions=positions,
            closed_services=closed_services,
            on_service_click=self._open_service,
            on_dungeon_click=self._enter_dungeon,
        )
        self.city_map.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # House button (below the map, if player owns a house in this city)
        has_house = self.city_id in self.player.get("houses", {})
        if has_house:
            house_data = self.player["houses"][self.city_id]
            from facilities.house import HOUSE_LEVELS, _pending_income
            lvl_name = HOUSE_LEVELS[house_data["level"]]["name"]
            pending = _pending_income(self.player, self.city_id, house_data)
            house_text = f"🏠 Your House ({lvl_name})"
            if pending > 0:
                house_text += f" [{pending}g]"

            self._house_btn = self.styled_button(
                self.content,
                text=house_text,
                command=self._open_house,
                width=28,
                bg=Theme.BG_LIGHT,
            )
            self._house_btn.pack(pady=(4, 0))

        # ── Bottom action bar ──────────────────────────────────────────────────
        self._action_frame = tk.Frame(self.content, bg=Theme.BG_DARK)
        self._action_frame.pack(fill=tk.X, pady=(12, 0))
        action_frame = self._action_frame  # alias for local use below

        actions = [
            ("[I] Inventory", self._open_inventory),
            ("[K] Skill Book", self._open_skill_book),
            ("[M] World Map", self._open_world_map),
            ("[W] Wait", self._do_wait),
            ("[S] Settings", self._open_settings),
            ("[Q] Save & Quit", self._save_and_quit),
            ("[?] Help", self._show_help),
        ]

        for text, cmd in actions:
            btn = self.styled_button(action_frame, text=text, command=cmd, width=16)
            btn.pack(side=tk.LEFT, padx=4, expand=True)

        # ── Keyboard shortcuts ─────────────────────────────────────────────
        self._setup_city_keys()

        # ── Arrival checks ─────────────────────────────────────────────────
        # Deferred so navigation callbacks stay clean. The gate is one-shot
        # per travel/menu arrival (flag set by the travel/load paths).
        self.after(50, self._begin_arrival)

    def _setup_city_keys(self):
        """Bind keyboard shortcuts for city services and actions."""
        self.bind("<KeyPress>", self._on_city_key)
        self.focus_set()

    def _on_city_key(self, event):
        """Handle keyboard shortcuts in the city screen."""
        key = event.char
        # Number keys 1-9 → services (cycle through position keys)
        if key and key in "123456789":
            from resources.city_maps import CITY_SERVICE_POSITIONS
            positions = CITY_SERVICE_POSITIONS.get(self.city_id, {})
            svc_keys = [k for k in positions.keys() if k != "dungeon"]
            idx = int(key) - 1
            if idx < len(svc_keys):
                self._open_service(svc_keys[idx])
            return
        # Letter keys → bottom actions
        key_map = {
            "i": self._open_inventory,
            "k": self._open_skill_book,
            "m": self._open_world_map,
            "w": self._do_wait,
            "d": self._enter_dungeon,
            "s": self._open_settings,
            "q": self._save_and_quit,
        }
        action = key_map.get(key.lower())
        if action:
            action()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _refresh_city_id(self):
        if self.player:
            loc = self.player.get("location", "solmere")
            if loc == "dungeon":
                loc = self.player.get("origin_city", "solmere")
            self.city_id = loc
        else:
            self.city_id = "solmere"
        self.city = CITIES.get(self.city_id, CITIES["solmere"])

        # Refresh the map widget if it exists
        if hasattr(self, 'city_map') and self.city_map.winfo_exists():
            from resources.city_maps import CITY_SERVICE_POSITIONS
            positions = CITY_SERVICE_POSITIONS.get(self.city_id, {})
            self.city_map.refresh(self.city_id, self.city, positions)

    # ── Karma gate (Phase 2) ──────────────────────────────────────────────────

    def _begin_arrival(self):
        """Run the one-shot gate check, then resume normal city arrivals."""
        if not self.winfo_exists():
            return
        if self._start_karma_gate():
            return
        self._resume_arrival()

    def _resume_arrival(self):
        """Show queued world events, then schedule story beats / EH intro."""
        if not self.winfo_exists():
            return
        self._show_queued_events()
        self.after(200, self._check_story_beats)
        if self.player:
            self.after(700, self._maybe_event_horizon_intro)

    def _show_queued_events(self):
        """Display queued dungeon/world events once the gate is resolved."""
        if not self.player:
            return
        events = get_event_queue_events(self.player)
        if not events:
            return
        from events import format_event_alert
        for evt in events:
            self.sm.log(format_event_alert(evt), category="event")
        from gui.widgets.event_dialog import show_event_notice
        show_event_notice(
            events,
            day_text=format_date(self.player),
            parent=self.sm.root,
        )

    def _start_karma_gate(self):
        p = self.player
        if not p:
            return False
        karma.ensure_state(p)
        gate = p["karma_gate"]
        if not gate.pop("check_pending", False):
            return False
        response = karma.get_gate_response(p, self.city_id)
        if not response:
            return False
        self._show_karma_gate(response)
        return True

    def _show_karma_gate(self, response):
        tier = response["tier"]
        fee = int(response["fee"])
        gold = max(0, int(self.player.get("gold", 0) or 0))
        karma_tier = karma.get_karma_tier(self.player)

        if tier == "warning":
            heading = "The Gate Captain Stops You"
            details = (
                f"Karma: {karma_tier['label']} ({karma.get_karma(self.player):+d})\n\n"
                "Your reputation has preceded you. This once, the captain offers "
                f"to overlook it for a {fee}-gold processing fee."
            )
        elif tier == "suspect":
            heading = "The Watch Is Waiting"
            details = (
                f"Karma: {karma_tier['label']} ({karma.get_karma(self.player):+d})\n\n"
                f"They name a fee of {fee} gold. Pay it, or turn away."
            )
        elif tier == "wanted":
            heading = "Wanted at the Gate"
            details = (
                f"Karma: {karma_tier['label']} ({karma.get_karma(self.player):+d})\n\n"
                f"Three guards block the gate. The fee is {fee} gold — or you "
                "can talk, submit, or fight."
            )
        else:
            heading = "The Gate Is Closed to You"
            details = (
                f"Karma: {karma_tier['label']} ({karma.get_karma(self.player):+d})\n\n"
                f"Two elite guards and two guards bar the way. The fee is {fee} gold "
                "— or you can talk, submit, or fight."
            )

        if gold < fee:
            details += f"\n\nYou only have {gold} gold."
        guard_line = service_line(self.player, "guard", self.city_id)
        if guard_line:
            details += f"\n\n\"{guard_line}\""

        options = []
        if gold >= fee:
            options.append(("pay", f"Pay {fee} gold and enter"))
        if tier in ("wanted", "outlaw"):
            options.append(("talk", "Talk them down (CHA check)"))
            options.append(("submit", "Submit to judgment"))
            options.append(("fight", "Fight the guards"))
        options.append(("leave", "Turn away (return to map)"))

        choice_dialog(
            parent=self,
            title="City Gate",
            heading=heading,
            subtitle=f"{self.city.get('name', self.city_id)} — Gate Check",
            details=details,
            options=options,
            on_choice=lambda key: self._on_gate_choice(key, response),
            default_choice="leave",
        )

    def _on_gate_choice(self, key, response):
        if key == "pay":
            self._gate_pay(response)
        elif key == "talk":
            self._gate_talk(response)
        elif key == "submit":
            self._gate_submit(response)
        elif key == "fight":
            self._gate_fight(response)
        else:
            self._gate_turn_away()

    def _refresh_after_gate(self):
        self._update_top_bar()
        if hasattr(self, "_hero_card") and self._hero_card.winfo_exists():
            self._refresh_hero_card()

    def _gate_pay(self, response):
        fee = int(response["fee"])
        p = self.player
        if int(p.get("gold", 0) or 0) < fee:
            ok_dialog(self, "Not Enough Gold",
                      f"You need {fee} gold, but you only have {p.get('gold', 0)}.")
            return

        p["gold"] = int(p.get("gold", 0) or 0) - fee
        from combat.city_guards import resolve_gate
        warning = response["tier"] == "warning"
        resolve_gate(p, self.city_id, days=1 if warning else 3, warning=warning)
        self.sm.log(
            f"Gate fee paid: {fee} gold. "
            + ("The captain waves you through — this once." if warning
               else "The guards step aside.")
        )
        self._refresh_after_gate()
        self._resume_arrival()

    def _gate_talk(self, response):
        import random
        from combat.stats import compute_player_stats

        p = self.player
        cha = compute_player_stats(p)[5]
        dc = karma.get_gate_talkdown_dc(p)
        roll = random.randint(1, 20)
        total = roll + cha
        # Natural 20 always talks the guards down, no matter the DC.
        if roll == 20 or total >= dc:
            fee = max(1, int(response["fee"]) // 2)
            if int(p.get("gold", 0) or 0) < fee:
                ok_dialog(
                    self, "Talk-Down Succeeded",
                    f"You roll {roll} + {cha} = {total} vs DC {dc}.\n\n"
                    f"They halve the fee to {fee} gold, but you cannot pay it. "
                    "They offer you a cell instead.",
                    on_ok=lambda: self._gate_submit(response),
                )
                return
            p["gold"] = int(p.get("gold", 0) or 0) - fee
            from combat.city_guards import resolve_gate
            resolve_gate(p, self.city_id, days=3)
            self.sm.log(
                f"Talk-down: {roll} + {cha} = {total} vs DC {dc} — success. "
                f"Half fee paid: {fee} gold."
            )
            self._refresh_after_gate()
            self._resume_arrival()
            return

        ok_dialog(
            self, "Talk-Down Failed",
            f"You roll {roll} + {cha} = {total} vs DC {dc}.\n\n"
            "The guards do not buy it. Steel rings as they close in.",
            on_ok=lambda: self._gate_fight(response),
        )

    def _gate_submit(self, response):
        from combat.city_guards import city_guard_jail
        from gui.screens.city_screen import CityScreen

        info = city_guard_jail(self.player, self.city_id)
        msg = f"You spend the night in a cell. Fine: {info['fine']} gold."
        if info.get("karma"):
            msg += f"  Karma {info['karma']:+d}."
        self.sm.switch_to(CityScreen, push_history=False)
        self.sm.log(msg)

    def _gate_fight(self, response):
        from combat.city_guards import spawn_city_guards
        from gui.screens.combat_screen import CombatScreen

        enemies = spawn_city_guards(self.player, response["tier"])
        self.sm.log("The guards draw steel.")
        self.sm.switch_to(
            CombatScreen,
            enemy_keys=[],
            enemies=enemies,
            combat_context="city_guard",
            on_result=self._after_city_guard_combat,
        )

    def _gate_turn_away(self):
        from gui.screens.world_map_screen import WorldMapScreen

        self.sm.switch_to(WorldMapScreen, travel_mode=True)
        self.sm.log("You turn away from the gate. The road is still open.")

    def _after_city_guard_combat(self, result):
        """Resolve a non-lethal gate fight without ever showing DeathScreen."""
        from combat import city_guards
        from gui.screens.city_screen import CityScreen

        if result == "victory":
            city_guards.city_guard_victory(self.player, self.city_id)
            self.sm.switch_to(CityScreen, push_history=False)
            self.sm.log("The guards lower their weapons. You enter under watch.")
            return
        if result in ("dead", "defeat"):
            info = city_guards.city_guard_jail(self.player, self.city_id)
            self.sm.switch_to(CityScreen, push_history=False)
            msg = f"You wake in a cell. Fine: {info['fine']} gold."
            if info.get("karma"):
                msg += f"  Karma {info['karma']:+d}."
            self.sm.log(msg)
            return
        if result == "fled":
            city_guards.city_guard_flee(self.player, self.city_id)
            from gui.screens.world_map_screen import WorldMapScreen
            self.sm.switch_to(WorldMapScreen, travel_mode=True)
            self.sm.log("You slip away from the gate. The watch will remember.")
            return

        # Error / aborted combat: return to the city without a death penalty.
        self.sm.switch_to(CityScreen, push_history=False)
        self.sm.log(f"Gate combat ended unexpectedly: {result}.")

    def _build_hero_card(self):
        """Show party status card — all members in one horizontal row: 
        player + front allies + back allies. Front/back separated by a subtle divider.

        Click-to-swap: clicking two ally cards swaps their positions in
        player['party_order'] (front row ↔ bench). The player card is fixed.
        """
        from combat.ally import (ensure_party_order, get_all_active_allies_including_defeated,
                                 get_all_reserve_allies_including_defeated)
        p = self.player
        ensure_party_order(p)
        front_allies = get_all_active_allies_including_defeated(p)
        back_allies = get_all_reserve_allies_including_defeated(p)

        # Click-to-swap state: absolute ally index awaiting a swap partner
        self._swap_selected = None
        self._member_blocks = {}  # absolute ally index -> card frame (highlight)
        # Name labels are ellipsized to fit the party row (see _fit_hero_names)
        self._hero_name_labels = []
        self._hero_blocks = []      # (block, hp_bar, tag_label, full_tags)
        self._hero_fit_state = None

        allies_list = p.get("allies", [])

        def _abs_index(ally):
            """Absolute index of an ally in player['allies'] (identity match)."""
            for i, a in enumerate(allies_list):
                if a is ally:
                    return i
            return None

        self._hero_card = tk.Frame(self.content, bg=Theme.BG_CARD, highlightthickness=1,
                                   highlightbackground=Theme.BORDER)
        # On refresh the map frame already exists, so keep the card above it.
        map_frame = getattr(self, "_map_frame", None)
        if map_frame is not None and map_frame.winfo_exists():
            self._hero_card.pack(fill=tk.X, pady=(0, 10), padx=20, before=map_frame)
        else:
            self._hero_card.pack(fill=tk.X, pady=(0, 10), padx=20)
        card = self._hero_card  # alias for local use below

        # ── Collect all party members in order ─────────────────────────────
        from titles import format_name as _format_title_name
        members = []
        # Player (always first, FRONT)
        members.append({
            "name": _format_title_name(
                p, "full",
                show_title=self.sm.settings.get("show_title_beside_name", True)),
            "level": p.get("level", 1),
            "hp": p.get("current_hp", 1),
            "max_hp": player_max_hp(p),
            "tags": _get_entity_buff_tags(p),
            "color": Theme.ACCENT,
            "section": "player",
            "defeated": False,
            "party_idx": None,  # player is fixed
        })

        # Front-row allies
        for ally in front_allies:
            defeated = ally.get("defeated") or ally.get("current_hp", 0) <= 0
            members.append({
                "name": display_name(ally),
                "level": ally.get("level", 1),
                "hp": 0 if defeated else ally.get("current_hp", 0),
                "max_hp": ally.get("max_hp", 1),
                "tags": _get_entity_buff_tags(ally),
                "color": Theme.TEXT_DIM if defeated else Theme.TEXT,
                "section": "front",
                "defeated": defeated,
                "party_idx": _abs_index(ally),
            })

        # Back-row allies (go beside front, after a divider)
        for ally in back_allies:
            defeated = ally.get("defeated") or ally.get("current_hp", 0) <= 0
            members.append({
                "name": display_name(ally),
                "level": ally.get("level", 1),
                "hp": 0 if defeated else ally.get("current_hp", 0),
                "max_hp": ally.get("max_hp", 1),
                "tags": _get_entity_buff_tags(ally),
                "color": "#8b7355" if not defeated else "#555555",
                "section": "back",
                "defeated": defeated,
                "party_idx": _abs_index(ally),
            })

        # ── Single horizontal party row ─────────────────────────────────────
        party_row = tk.Frame(card, bg=Theme.BG_CARD)
        party_row.pack(fill=tk.X, padx=10, pady=(8, 4))
        self._hero_party_row = party_row
        # Fixed layout budget for a full 8-actor party (gaps + dividers).
        self._hero_row_extras = HERO_ROW_EXTRAS_MAX
        party_row.bind("<Configure>", lambda e: self._fit_hero_names(e.width))

        last_section = None
        for i, m in enumerate(members):
            # Insert a subtle divider between front and back sections
            if m["section"] != last_section and i > 0:
                if m["section"] == "back":
                    # Divider between front and back
                    sep = tk.Frame(party_row, bg=Theme.BG_CARD, width=2)
                    sep.pack(side=tk.LEFT, padx=6)
                    tk.Label(sep, text="│", bg=Theme.BG_CARD,
                             fg="#8b7355", font=(Theme.FONT_FAMILY, 16, "bold")).pack()
                    sep_frame = tk.Frame(party_row, bg=Theme.BG_CARD, width=6)
                    sep_frame.pack(side=tk.LEFT)
                elif m["section"] == "front" and last_section == "player":
                    # Subtle space after player
                    sep = tk.Frame(party_row, bg=Theme.BG_CARD, width=1)
                    sep.pack(side=tk.LEFT, padx=2)
                    tk.Label(sep, text="│", bg=Theme.BG_CARD,
                             fg=Theme.BORDER, font=(Theme.FONT_FAMILY, 14)).pack()
                    sep_frame = tk.Frame(party_row, bg=Theme.BG_CARD, width=6)
                    sep_frame.pack(side=tk.LEFT)
            last_section = m["section"]

            # highlightthickness=2 reserved from the start so selecting a card
            # only recolors the border without shifting the layout
            block = tk.Frame(party_row, bg=Theme.BG_CARD,
                             highlightthickness=2, highlightbackground=Theme.BG_CARD)
            block.pack(side=tk.LEFT, padx=(0 if i == 0 else 8, 0))

            name_color = m["color"]
            if m.get("defeated"):
                name_color = "#555555"

            # Name + level on one row. The name gets ellipsized later to the
            # per-member slot width so long names/titles never overflow.
            name_row = tk.Frame(block, bg=Theme.BG_CARD)
            name_row.pack(anchor=tk.W)
            name_lbl = tk.Label(name_row, text=m["name"],
                                bg=Theme.BG_CARD, fg=name_color,
                                font=Theme.FONT_BOLD, anchor=tk.W)
            name_lbl.pack(side=tk.LEFT)
            level_lbl = tk.Label(name_row, text=f"Lv.{m['level']}",
                                 bg=Theme.BG_CARD, fg=name_color,
                                 font=Theme.FONT_BOLD)
            level_lbl.pack(side=tk.LEFT, padx=(5, 0))
            self._hero_name_labels.append((name_lbl, level_lbl, m["name"]))

            ratio = m["hp"] / max(1, m["max_hp"])
            if m["section"] == "back":
                if ratio > 0.5:
                    hp_fill = "#7a6a4a"
                elif ratio > 0.25:
                    hp_fill = "#8b6914"
                else:
                    hp_fill = "#aa4444"
            else:
                if ratio > 0.5:
                    hp_fill = Theme.HP_BAR_FILL
                elif ratio > 0.25:
                    hp_fill = "#f39c12"
                else:
                    hp_fill = Theme.ACCENT
            if m.get("defeated"):
                hp_fill = "#333333"

            hp_bar = HPBar(block, current=m["hp"], maximum=m["max_hp"],
                           width=90, height=14, show_text=True,
                           fill_color=hp_fill)
            hp_bar.pack(anchor=tk.W, pady=(2, 0))

            # Always show tag label to maintain vertical alignment;
            # use a non-breaking space when there are no tags.
            tag_text = m["tags"] if m["tags"] else " "
            tag_lbl = tk.Label(block, text=tag_text, bg=Theme.BG_CARD,
                               fg=Theme.BUFF_NEUTRAL,
                               font=(Theme.FONT_FAMILY, 7),
                               anchor=tk.W)
            tag_lbl.pack(anchor=tk.W)
            self._hero_blocks.append((block, hp_bar, tag_lbl, tag_text))

            # Click-to-swap registration (player card stays fixed)
            if m.get("party_idx") is not None:
                self._member_blocks[m["party_idx"]] = block
                self._bind_party_card_clicks(block, m)

        # Widths are only known after the first layout pass — fit then, and
        # refit whenever the window (and therefore the row) is resized.
        self.after_idle(self._fit_hero_names)

        # ── Gold row ──────────────────────────────────────────────────────
        gold = p.get("gold", 0)
        gold_frame = tk.Frame(card, bg=Theme.BG_CARD)
        gold_frame.pack(fill=tk.X, padx=10, pady=(4, 8))
        tk.Label(gold_frame, text=f"💰 {gold}g", bg=Theme.BG_CARD,
                 fg=Theme.TEXT, font=Theme.FONT_SMALL).pack(side=tk.LEFT)
        if len(members) > 2:
            tk.Label(gold_frame,
                     text="Click two allies to swap positions",
                     bg=Theme.BG_CARD, fg=Theme.TEXT_DIM,
                     font=Theme.FONT_SMALL).pack(side=tk.RIGHT)

    def _fit_hero_names(self, row_width=None):
        """Ellipsize party-card names so the single-row party bar fits.

        The player's name can include a title ("hundur the Hundred") and
        ally nicknames are free text, so a fixed label grew the row past the
        card/window edge. Each member gets the SAME fixed slot — sized for a
        full 8-actor card — so a 2-member party does not stretch into huge
        boxes. Only the name is shortened (the level suffix stays visible).
        """
        labels = getattr(self, "_hero_name_labels", None)
        if not labels or not self.winfo_exists():
            return
        if row_width is None:
            row = getattr(self, "_hero_party_row", None)
            try:
                row_width = row.winfo_width() if row is not None else 0
            except tk.TclError:
                return
        if row_width <= 60:          # not mapped yet
            return

        extras = getattr(self, "_hero_row_extras", HERO_ROW_EXTRAS_MAX)
        # Fixed slot sized for a full 8-actor card. Short parties keep the
        # same box size and simply leave empty space to the right.
        slot = max(56, (row_width - extras) // HERO_CARD_MAX_SLOTS)
        block_w = max(52, slot - 4)

        blocks = getattr(self, "_hero_blocks", [])
        max_h = 0
        for block, _hp, _tag, _tags in blocks:
            try:
                max_h = max(max_h, block.winfo_reqheight())
            except tk.TclError:
                pass
        freeze_ok = max_h >= 20       # requested height is laid out

        state = (row_width,
                 tuple((full, lvl.cget("text")) for _, lvl, full in labels),
                 freeze_ok)
        if state == getattr(self, "_hero_fit_state", None):
            return
        self._hero_fit_state = state

        for name_lbl, level_lbl, full_name in labels:
            try:
                level_w = level_lbl.winfo_reqwidth()
            except tk.TclError:
                level_w = 40
            # 14px = level spacing + Tk label padding/border margin.
            available = max(16, block_w - level_w - 14)
            text = _fit_text_to_width(full_name, Theme.FONT_BOLD, available)
            try:
                name_lbl.config(text=text)
            except tk.TclError:
                pass

        if freeze_ok:
            # Freeze every member box at the same width/height so short
            # names no longer produce visibly smaller cards.
            for block, hp_bar, tag_lbl, full_tags in blocks:
                try:
                    block.pack_propagate(False)
                    block.config(width=block_w, height=max_h)
                except tk.TclError:
                    pass
                # Default bar is 90px; shrink only when the fixed slot is
                # too narrow (e.g. 8 members at the minimum window width).
                try:
                    hp_bar.set_width(min(90, max(50, block_w - 10)))
                except tk.TclError:
                    pass
                if full_tags.strip():
                    tag_text = _fit_text_to_width(
                        full_tags, (Theme.FONT_FAMILY, 7), max(20, block_w - 8))
                    try:
                        tag_lbl.config(text=tag_text)
                    except tk.TclError:
                        pass

    # ── Party position swap (click-to-swap) ──────────────────────────────

    def _bind_party_card_clicks(self, widget, member):
        """Recursively bind click handlers on a party member card.

        Tk delivers mouse events to the deepest widget under the cursor, so
        every child (labels, HP bar canvas) needs its own binding.
        """
        try:
            widget.config(cursor="hand2")
        except tk.TclError:
            pass
        widget.bind("<Button-1>", lambda e, m=member: self._on_party_member_click(m))
        for child in widget.winfo_children():
            self._bind_party_card_clicks(child, member)

    def _on_party_member_click(self, member):
        """Handle a click on a party member card.

        First click selects the member (highlighted border); clicking a
        second member swaps their positions in player['party_order'].
        Clicking the selected member again deselects. The player is fixed.
        """
        idx = member.get("party_idx")
        if idx is None:
            return

        if self._swap_selected is None:
            self._swap_selected = idx
            self._update_swap_highlights()
            self.sm.log(f"Selected {member['name']} — click another ally to swap positions.")
        elif self._swap_selected == idx:
            self._swap_selected = None
            self._update_swap_highlights()
        else:
            self._swap_party_positions(self._swap_selected, idx)

    def _swap_party_positions(self, idx_a, idx_b):
        """Swap two allies' slots in player['party_order'].

        A pure position swap never changes the front/bench head-counts, so
        no capacity validation is needed — the first get_active_limit()
        positions are the front row, the next bench entries are the reserve.
        """
        from combat.ally import ensure_party_order, get_active_limit

        p = self.player
        ensure_party_order(p)
        allies = p.get("allies", [])
        order = p.get("party_order", [])

        self._swap_selected = None

        valid = (idx_a != idx_b and idx_a in order and idx_b in order
                 and idx_a < len(allies) and idx_b < len(allies))
        if not valid:
            self._refresh_hero_card()
            return

        pos_a, pos_b = order.index(idx_a), order.index(idx_b)
        order[pos_a], order[pos_b] = order[pos_b], order[pos_a]

        name_a = display_name(allies[idx_a])
        name_b = display_name(allies[idx_b])
        limit = get_active_limit(p)
        a_was_front = pos_a < limit
        b_was_front = pos_b < limit

        if a_was_front == b_was_front:
            msg = f"{name_a} and {name_b} swap places."
        else:
            fwd, back = (name_a, name_b) if not a_was_front else (name_b, name_a)
            msg = f"{fwd} steps forward! {back} moves to the back row."

        self.sm.log(msg)
        self._refresh_hero_card()

    def _update_swap_highlights(self):
        """Apply or clear the selection highlight on member cards."""
        for idx, block in getattr(self, "_member_blocks", {}).items():
            try:
                if not block.winfo_exists():
                    continue
                color = Theme.ACCENT if idx == self._swap_selected else Theme.BG_CARD
                block.config(highlightbackground=color)
            except tk.TclError:
                pass

    def _refresh_hero_card(self):
        """Rebuild the hero card in place (used after a position swap)."""
        if hasattr(self, "_hero_card") and self._hero_card.winfo_exists():
            self._hero_card.destroy()
        self._build_hero_card()

    def _update_top_bar(self):
        # Priority-driven header (see base_screen.city_header_parts): the clock
        # stays bright; floor, karma and the watched marker sit in the dim tier.
        from gui.screens.base_screen import city_header_parts
        primary, secondary = city_header_parts(self.player, self.city_id)
        self.sm.update_top_bar_parts(primary, secondary)

    # ── Service handlers ──────────────────────────────────────────────────────

    def _open_service(self, service):
        """Open a facility in the GUI FacilityScreen wrapper."""
        from time_blocks import is_service_open, service_closed_message
        if not is_service_open(self.player, service, self.city_id):
            msg = (service_closed_message(self.player, service, self.city_id)
                   or "Closed right now.")
            ok_dialog(self, service.replace("_", " ").title(), msg)
            return
        # Port opens the World Map instead of the old terminal UI
        if service == "port":
            self._open_world_map()
            return
        from city import SERVICE_HANDLERS
        handler = SERVICE_HANDLERS.get(service)
        if handler:
            from karma_dialogue import title_line
            _title_greeting = title_line(self.player, service, self.city_id)
            if _title_greeting:
                self.sm.log(_title_greeting)
            self.sm.log(f"Entering {service.replace('_', ' ').title()}...")
            from gui.screens.facility_screen import FacilityScreen
            self.sm.switch_to(
                FacilityScreen,
                title=service.replace("_", " ").title(),
                func=handler,
                func_args=(self.player, self.city_id),
                on_close=lambda _: self._after_facility(),
            )

    def _do_wait(self):
        """Wait: a brief moment (1 block) or a while (until the next phase)."""
        confirm_dialog(
            parent=self, title="Wait",
            message=("How long would you like to wait?\n\n"
                     "· A brief moment — pass a little time.\n"
                     "· A while — pass until the next phase"
                     " (from Night you simply greet the morning, exhausted)."),
            on_yes=self._wait_brief,
            on_no=self._wait_a_while,
            yes_text="A Brief", no_text="A While",
            on_close=lambda: None,      # X = cancel, do nothing
        )

    def _wait_brief(self):
        """Pass one block; day rollover handles fatigue normally."""
        import time_blocks
        time_blocks.wait_blocks(self.player, 1)
        self.sm.log("You wait a brief moment.")
        self.sm.switch_to(CityScreen, push_history=False)

    def _wait_a_while(self):
        """Pass to the next phase (from Night: greet the morning, +1 fatigue)."""
        import time_blocks
        result = time_blocks.wait_to_next_phase(self.player)
        if result is None:
            # Wonderland time pocket — nothing passes here
            self.sm.log("Time politely declines to pass in Wonderland.")
        elif result == "morning":
            self.sm.log("A while passes — you greet the morning, exhausted.")
        else:
            self.sm.log(f"A while passes — it is now {result}.")
        self.sm.switch_to(CityScreen, push_history=False)

    def _maybe_event_horizon_intro(self):
        """Play Vesper's first-contact scene once the EH gate is met."""
        if getattr(self, "_eh_intro_launched", False):
            return
        p = self.player
        if not p or p.get("eh_intro_seen"):
            return
        from event_horizon import site_unlocked
        if not site_unlocked(p):
            return
        if p.get("location") == "dungeon":
            return
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self._eh_intro_launched = True
        from gui.screens.facility_screen import FacilityScreen
        from facilities.event_horizon_intro import event_horizon_intro_service
        self.sm.switch_to(
            FacilityScreen,
            title="A Tear in the Sky",
            func=event_horizon_intro_service,
            func_args=(p, self.city_id),
            on_close=lambda _: self.sm.switch_to(CityScreen, push_history=False),
        )

    def _open_house(self):
        """Open the player's house in this city."""
        self.sm.log("Entering Your House...")
        from facilities.house import house_menu
        from gui.screens.facility_screen import FacilityScreen
        self.sm.switch_to(
            FacilityScreen,
            title="Your House",
            func=house_menu,
            func_args=(self.player, self.city_id),
            on_close=lambda _: self._after_facility(),
        )

    def _after_facility(self):
        """Called when any facility screen closes. Refresh state."""
        self._update_top_bar()
        if self.player and self.player.get("current_hp", 1) <= 0:
            self._handle_death()
        elif self.player and self.player.pop("_pending_dummy_combat", None):
            self._launch_dummy_combat()
        else:
            self.sm.switch_to(CityScreen, push_history=False)

    # ── Story beats ───────────────────────────────────────────────────────────

    def _check_story_beats(self):
        """Resolve quest state and deliver story beats on city entry.

        Runs on every CityScreen entry — which covers travel arrivals, dungeon
        exits, post-floor returns and menu loads, because every path funnels
        back through CityScreen. Story never interrupts combat or dungeons.
        """
        if not self.winfo_exists() or not self.player:
            return

        import quests

        # Resolve any state-based objectives (own a house, capture a girl...).
        # Results are recorded in the session log + Journal — no popups.
        messages = quests.update_quests(self.player)
        for msg in messages:
            self.sm.log(msg)

        # Deliver the next story beat: the Archivist intro first, then queue.
        flags = quests.ensure_quest_state(self.player)["flags"]
        if not flags.get("intro_seen"):
            self._open_story_beat("archivist_intro")
            return
        from facilities.story_beats import ensure_city_story_triggers
        ensure_city_story_triggers(self.player, self.city_id)
        if quests.has_pending_story(self.player):
            beat_id = quests.pop_pending_story(self.player)
            if beat_id:
                self._open_story_beat(beat_id)
                return

        # Fireside Tales can also find the player while travelling (city or
        # phase triggers), instead of waiting at home.
        from facilities.house_stories import claim_city_trigger
        part = claim_city_trigger(self.player, self.city_id)
        if part:
            self._open_house_story(part)

    def _open_house_story(self, part):
        """Open a city-triggered house story as an overlay."""
        from facilities.house_stories import play_part
        from resources.house_stories import get_part
        from gui.screens.story_screen import StoryScreen

        _, story, _, _ = get_part(part["id"])
        title = part.get("title", "Story")
        if story:
            title = f"{story.get('title', 'Story')} — {title}"

        self.sm.push_overlay(
            StoryScreen,
            title=title,
            func=play_part,
            func_args=(self.player, part["id"]),
            on_close=lambda _result: self.sm.dismiss_overlay(),
        )

    def _open_story_beat(self, beat_id):
        """Open a story conversation as an overlay over the city."""
        from facilities.story_beats import get_story_beat
        from gui.screens.story_screen import StoryScreen

        func = get_story_beat(beat_id)
        if func is None:
            return
        titles = {"archivist_intro": "A Message in Starlight",
                  "voss_epilogue": "The First Page"}
        self.sm.push_overlay(
            StoryScreen,
            title=titles.get(beat_id, "Story"),
            func=func,
            func_args=(self.player,),
            on_close=lambda _result: self.sm.dismiss_overlay(),
        )

    def _launch_dummy_combat(self):
        """Launch a sparring match against the training dummy in CombatScreen."""
        config = self.player.pop("_pending_dummy_combat", None)
        if not config:
            self.sm.switch_to(CityScreen, push_history=False)
            return

        self.sm.log("Entering sparring arena...")
        self.sm.update_top_bar("⚔ Training Dummy")

        def dummy_combat_func(player, floor=None, enemies=None):
            """Custom combat function for the training dummy."""
            from combat.dummy import create_dummy_enemy, _run_dummy_combat

            # Inject the dummy into the shared enemies list so the HUD sees it
            dummy = create_dummy_enemy(config)
            if enemies is not None:
                enemies.clear()
                enemies.append(dummy)

            # Use the protected runner that disables Pandemonium flee blocking.
            # Pass enemies (shared list) so the HUD reflects live combat state.
            return _run_dummy_combat(player, config, enemies=enemies)

        from gui.screens.combat_screen import CombatScreen
        self.sm.switch_to(
            CombatScreen,
            enemy_keys=[],
            combat_context="training",
            combat_func=dummy_combat_func,
            on_result=lambda result: self._after_dummy_combat(result),
        )

    def _after_dummy_combat(self, result):
        """Handle return from dummy sparring — always go back to city."""
        self.sm.log(f"Sparring ended: {result.upper()}")
        self._update_top_bar()
        if self.player and self.player.get("current_hp", 1) <= 0:
            self._handle_death()
        else:
            self.sm.switch_to(CityScreen, push_history=False)

    def _open_inventory(self):
        self.sm.log("Opening Inventory...")
        from gui.screens.inventory_screen import InventoryScreen
        self.sm.switch_to(InventoryScreen)

    def _open_skill_book(self):
        self.sm.log("Opening Skill Book...")
        from facilities.skill_book import skill_book_menu
        from gui.screens.facility_screen import FacilityScreen
        self.sm.switch_to(
            FacilityScreen,
            title="Skill Book",
            func=skill_book_menu,
            func_args=(self.player,),
            on_close=lambda _: self._after_facility(),
        )

    def _open_world_map(self):
        """Open the unified world map — travel mode with pathfinding + Travel Here."""
        self.sm.log("Opening World Map...")
        from gui.screens.world_map_screen import WorldMapScreen
        self.sm.switch_to(WorldMapScreen, travel_mode=True)

    def _enter_dungeon(self):
        """Prompt for floor selection, then launch the dungeon."""
        # Guard against double-invocation (e.g., double-click on button)
        if getattr(self, '_entering_dungeon', False):
            return
        self._entering_dungeon = True
        try:
            self._do_enter_dungeon()
        finally:
            self._entering_dungeon = False

    def _do_enter_dungeon(self):
        # Ensure per-city progress exists
        from dungeon import _ensure_city_floors
        _ensure_city_floors(self.player, self.city_id)
        city_prog = self.player["city_floors"][self.city_id]
        max_unlocked = city_prog["max_floor"]
        current_floor = city_prog["floor"]

        # ── Pandemonium lock check ───────────────────────────────────────
        if self.city_id == "isle_of_glass":
            from leveling import is_pandemonium_unlocked
            if not is_pandemonium_unlocked(self.player):
                ok_dialog(
                    parent=(self.sm.root if self.sm else self),
                    title="Pandemonium Sealed",
                    message=(
                        "The crystalline gates of Pandemonium stand sealed.\n\n"
                        "REQUIREMENT: Clear Floor 40 in at least 4 unique biomes.\n"
                        "(Visit any Guild Hall to check your biome progress.)"
                    ),
                )
                return
            else:
                self.sm.log("The crystalline gates of Pandemonium shimmer open...")

        # ── Floor selection dialog ────────────────────────────────────────
        self._show_floor_selection(current_floor, max_unlocked)

    def _launch_dungeon(self, floor):
        """Set the chosen floor and launch the DungeonScreen."""
        city_prog = self.player["city_floors"][self.city_id]
        city_prog["floor"] = floor
        self.player["dungeon_region"] = self.city.get("biome", "temperate")
        self.player["origin_city"] = self.city_id
        self.player["location"] = "dungeon"

        # Pandemonium mode is a per-run flag: only true inside the Isle of
        # Glass dungeon. Clear it for every other dungeon so a stale flag
        # (e.g. from a canceled floor selection or an old save) can't make
        # Elderfen or other dungeons display as PANDEMONIUM.
        if self.city_id == "isle_of_glass":
            self.player["pandemonium_mode"] = True
        else:
            self.player.pop("pandemonium_mode", None)

        # Clear any saved dungeon state and log for a fresh start
        for key in ("saved_dungeon_floor", "saved_dungeon_rooms", "saved_dungeon_room_index"):
            self.player.pop(key, None)
        self.player.pop("_dungeon_log", None)
        # A stale wild-dungeon id must never hijack a city-floor run
        self.player.pop("wild_dungeon_id", None)
        self.player.pop("_combat_floor_label", None)
        for key in ("saved_wild_floor", "saved_wild_rooms", "saved_wild_room_index"):
            self.player.pop(key, None)
        # A stale Event Horizon gate must never hijack a city-floor run
        # (the suspended run state itself is preserved).
        self.player.pop("_eh_in_run", None)

        # ── Receptionist "leave" dialogue ─────────────────────────────────
        from city_dialogue import get_city_dialogues
        leave_lines = get_city_dialogues(self.city_id, "receptionist").get("leave", [])
        if leave_lines:
            import random as _random
            self.sm.log(_random.choice(leave_lines), category="dialogue")

        self.sm.log(f"Entering dungeon — Floor {floor}...")
        from gui.screens.dungeon_screen import DungeonScreen
        self.sm.switch_to(
            DungeonScreen,
            on_result=self._return_from_dungeon,
        )

    def _show_floor_selection(self, current_floor, max_unlocked):
        """Show floor selection as a scrollable grid of buttons.

        Hides the hero card and city map to claim maximum screen real
        estate, then displays every unlocked floor as a clickable button
        in a multi-column grid.  The current floor is highlighted.
        Pressing Escape or clicking Cancel restores the original layout.
        """
        import tkinter as tk

        # ── Hide city UI elements to free up space ────────────────────────
        self._map_frame.pack_forget()
        if hasattr(self, '_hero_card') and self._hero_card.winfo_exists():
            self._hero_card.pack_forget()
        # Also hide the house button if visible
        if hasattr(self, '_house_btn') and self._house_btn.winfo_exists():
            self._house_btn.pack_forget()

        # ── Floor-selection panel ─────────────────────────────────────────
        sel_frame = tk.Frame(
            self.content, bg=Theme.BG_DARK,
            highlightthickness=1, highlightbackground=Theme.BORDER,
        )
        sel_frame.pack(fill=tk.BOTH, expand=True, pady=8)

        min_floor = max(1, int(self.city.get("dungeon_start_floor", 1) or 1))

        # Header
        tk.Label(
            sel_frame, text="Select Floor",
            bg=Theme.BG_DARK, fg=Theme.ACCENT, font=Theme.FONT_LARGE,
        ).pack(pady=(12, 2))

        tk.Label(
            sel_frame,
            text=f"Click a floor to descend  ({min_floor} – {max_unlocked}):",
            bg=Theme.BG_DARK, fg=Theme.TEXT_DIM, font=Theme.FONT,
        ).pack(pady=(0, 6))

        # ── Scrollable grid of floor buttons ──────────────────────────────
        canvas = tk.Canvas(sel_frame, bg=Theme.BG_DARK, highlightthickness=0,
                           bd=0)
        scrollbar = tk.Scrollbar(sel_frame, orient=tk.VERTICAL,
                                 command=canvas.yview)
        grid_inner = tk.Frame(canvas, bg=Theme.BG_DARK)

        grid_inner.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=grid_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0), pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 20), pady=5)

        # Mouse-wheel scrolling
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        COLS = 5
        BTN_W = 14

        # ── Shadow floor guard (Wonderland floors 41-50) ────────────────
        # When the player is on floors 41-50 in Wonderland, they carry
        # accumulated Shadows.  To prevent going back to earlier floors
        # to pick different Shadows, only the current floor is selectable.
        # The lock releases after Mary Sue is defeated (floor > 50).
        wonderland_biome = self.city.get("biome", "") == "wonderland"
        shadow_locked = wonderland_biome and 41 <= current_floor <= 50
        if shadow_locked:
            lock_warning = tk.Label(
                sel_frame,
                text="🌑 Shadows bind you — only your current floor is accessible.",
                bg=Theme.BG_DARK, fg="#d4a574", font=Theme.FONT_SMALL,
            )
            lock_warning.pack(pady=(0, 6))

        def _restore_and_go(floor):
            """Destroy the selection panel, restore hidden widgets, launch dungeon."""
            canvas.unbind_all("<MouseWheel>")
            sel_frame.destroy()
            self._restore_city_widgets()
            self._launch_dungeon(floor)

        def _restore_and_cancel():
            """Destroy the selection panel, restore hidden widgets, do nothing."""
            canvas.unbind_all("<MouseWheel>")
            sel_frame.destroy()
            self._restore_city_widgets()
            self.focus_set()

        for f in range(min_floor, max_unlocked + 1):
            row = (f - min_floor) // COLS
            col = (f - min_floor) % COLS
            is_current = f == current_floor
            is_locked = shadow_locked and not is_current

            if is_locked:
                bg = "#3a2a3a"        # dimmed, unclickable
                fg = "#6a5a6a"        # greyed-out text
                txt = f"🔒 Floor {f}"
                state = tk.DISABLED
            elif is_current:
                bg = Theme.ACCENT
                fg = Theme.BG_DARK
                txt = f"★ Floor {f}"
                state = tk.NORMAL
            else:
                bg = Theme.BG_MID
                fg = Theme.TEXT
                txt = f"Floor {f}"
                state = tk.NORMAL

            btn = tk.Button(
                grid_inner, text=txt,
                command=lambda floor=f: _restore_and_go(floor),
                bg=bg, fg=fg,
                font=Theme.FONT_BOLD,
                width=BTN_W,
                relief=tk.RAISED if is_current else tk.FLAT,
                bd=3 if is_current else 1,
                state=state,
                disabledforeground="#6a5a6a",
                activebackground=Theme.ACCENT,
                activeforeground=Theme.BG_DARK,
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")

        # Make columns equally wide
        for c in range(COLS):
            grid_inner.grid_columnconfigure(c, weight=1, uniform="floor_col")

        # ── Cancel button at the bottom of the grid ───────────────────────
        cancel_btn = tk.Button(
            sel_frame, text="Cancel", command=_restore_and_cancel,
            bg="#5a3a5a", fg=Theme.BUTTON_FG,
            font=Theme.FONT_BOLD, width=12,
        )
        cancel_btn.pack(pady=(4, 12))

        # ── Keyboard shortcuts ────────────────────────────────────────────
        sel_frame.bind("<Escape>", lambda e: _restore_and_cancel())
        canvas.bind("<Escape>", lambda e: _restore_and_cancel())
        # Focus the canvas so scroll wheel works immediately
        canvas.focus_set()

    def _restore_city_widgets(self):
        """Re-pack city widgets that were hidden during floor selection.

        All restored widgets are inserted *before* the action bar so the
        bottom buttons stay pinned at the bottom of the content area.
        """
        # Pack map_frame first so 'before' references can resolve.
        self._map_frame.pack(
            fill=tk.BOTH, expand=True, pady=8,
            before=self._action_frame,
        )
        if hasattr(self, '_hero_card') and self._hero_card.winfo_exists():
            self._hero_card.pack(
                fill=tk.X, pady=(0, 10), padx=20,
                before=self._map_frame,
            )
        if hasattr(self, '_house_btn') and self._house_btn.winfo_exists():
            self._house_btn.pack(pady=(4, 0), before=self._action_frame)

    def _cleanup_dungeon_exit(self):
        """Clear all dungeon-specific state when leaving a dungeon.
        Mirrors the cleanup done in dungeon.py's synchronous loop.
        
        NOTE: Wonderland Shadows are intentionally NOT cleared here.
        Shadows persist across floor clears and city returns so the
        player's accumulated shadow choices are preserved when they
        re-enter the dungeon.  Shadows are only cleared on death/flee
        (handled in dungeon.py) or on floors 46/50 (by design).
        """
        p = self.player
        from pandemonium_curses import end_pandemonium_run
        end_pandemonium_run(p)
        # Reset High Tide stacks
        p["cutlass_high_tide_stacks"] = 0
        p.pop("cutlass_high_tide_floor", None)
        # Clear Wonderland floor quirk (but NOT persistent Shadows)
        from wonderland_curses import clear_wonderland_quirk
        clear_wonderland_quirk(p)
        # Reset location to origin city
        p["location"] = p.get("origin_city", "solmere")

    def _return_from_dungeon(self, result):
        """Called when dungeon run ends."""
        if result == "dead":
            self._handle_death()
        elif result == "fled":
            self._cleanup_dungeon_exit()
            self.sm.log("You fled the dungeon.")
            self.sm.switch_to(CityScreen, push_history=False)
        elif result == "save_exit":
            self.sm.log("Game saved. Exiting to menu.")
            self.sm.player = None
            from gui.screens.main_menu_screen import MainMenuScreen
            self.sm.switch_to(MainMenuScreen)
        elif result is True:
            # explore_dungeon() returns True when a floor was actually cleared.
            self._show_post_floor_menu()
        else:
            # "timeout" / "error" / None — the run was interrupted (e.g. a
            # combat overlay crashed). Do NOT treat this as a floor clear:
            # that used to pop the "Floor Cleared!" dialog on a failed fight.
            self._cleanup_dungeon_exit()
            self.sm.log(f"Dungeon run interrupted ({result}). Returning to city.",
                        category="warning")
            self.sm.switch_to(CityScreen, push_history=False)

    def _show_post_floor_menu(self):
        """Show the 3-option menu after clearing a floor."""
        import tkinter as tk
        from time_blocks import format_block_track
        from character import player_max_hp

        p = self.player
        city_prog = p["city_floors"].get(self.city_id, {"floor": 1})
        cleared_floor = city_prog["floor"] - 1

        root = self.sm.root if self.sm else self.winfo_toplevel()
        dialog = tk.Toplevel(root)
        dialog.title("Floor Cleared!")
        dialog.transient(root)
        dialog.withdraw()   # build offscreen to avoid a blank flash
        dialog.resizable(False, False)
        dialog.configure(bg=Theme.BG_DARK)

        # Center
        dialog.update_idletasks()
        root = self.sm.root if self.sm else self.winfo_toplevel()
        px = root.winfo_x()
        py = root.winfo_y()
        pw = root.winfo_width()
        ph = root.winfo_height()
        dw = 360
        dh = 260
        dialog.geometry(f"{dw}x{dh}+{px + (pw - dw)//2}+{py + (ph - dh)//2}")

        # Header
        tk.Label(
            dialog,
            text=f"=== FLOOR {cleared_floor} CLEARED ===",
            bg=Theme.BG_DARK, fg=Theme.ACCENT,
            font=Theme.FONT_LARGE,
        ).pack(pady=(14, 4))

        tk.Label(
            dialog,
            text=f"Now entering Floor {city_prog['floor']}",
            bg=Theme.BG_DARK, fg=Theme.TEXT,
            font=Theme.FONT,
        ).pack(pady=(0, 8))

        # Stats
        stats_text = (
            f"HP: {p.get('current_hp', 0)}/{player_max_hp(p)}\n"
            f"Gold: {p.get('gold', 0)}"
        )
        _track = format_block_track(p)
        if _track:
            stats_text += f"\nTime: {_track}"
        tk.Label(
            dialog,
            text=stats_text,
            bg=Theme.BG_DARK, fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL,
            justify=tk.CENTER,
        ).pack(pady=(0, 10))

        choice = [None]  # Mutable container

        def _choose(opt):
            choice[0] = opt
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg=Theme.BG_DARK)
        btn_frame.pack(pady=5)

        tk.Button(
            btn_frame, text="1. Continue to next floor",
            command=lambda: _choose("continue"),
            bg=Theme.BUTTON_BG, fg=Theme.BUTTON_FG,
            font=Theme.FONT_BOLD, width=26, anchor=tk.W,
        ).pack(pady=3)

        tk.Button(
            btn_frame, text="2. Return to city",
            command=lambda: _choose("city"),
            bg=Theme.BUTTON_BG, fg=Theme.BUTTON_FG,
            font=Theme.FONT_BOLD, width=26, anchor=tk.W,
        ).pack(pady=3)

        tk.Button(
            btn_frame, text="3. Save and return to main menu",
            command=lambda: _choose("save_exit"),
            bg=Theme.BUTTON_BG, fg=Theme.BUTTON_FG,
            font=Theme.FONT_BOLD, width=26, anchor=tk.W,
        ).pack(pady=3)

        dialog.protocol("WM_DELETE_WINDOW", lambda: _choose("city"))

        # Show only once the content is built (prevents a blank window flash)
        dialog.deiconify()
        dialog.lift()
        dialog.grab_set()
        dialog.wait_window()

        opt = choice[0]
        if opt == "continue":
            self.player["location"] = "dungeon"
            from gui.screens.dungeon_screen import DungeonScreen
            self.sm.switch_to(
                DungeonScreen,
                on_result=self._return_from_dungeon,
            )
        elif opt == "save_exit":
            self._cleanup_dungeon_exit()
            from save_load import save_game
            self.player["location"] = self.city_id
            save_game(self.player)
            self.sm.log("Game saved. Returning to main menu.")
            self.sm.player = None
            from gui.screens.main_menu_screen import MainMenuScreen
            self.sm.switch_to(MainMenuScreen)
        else:
            # Default: return to city
            self._cleanup_dungeon_exit()
            self.sm.switch_to(CityScreen, push_history=False)

    def _save_and_quit(self):
        def _do_save():
            self.player["location"] = self.city_id
            save_game(self.player)
            self.sm.log("Game saved. Returning to main menu.")
            self.sm.player = None
            from gui.screens.main_menu_screen import MainMenuScreen
            self.sm.switch_to(MainMenuScreen)

        confirm_dialog(
            parent=self,
            title="Save & Quit",
            message="Save your progress and return to the main menu?",
            on_yes=_do_save,
        )

    def _handle_death(self):
        from gui.screens.death_screen import DeathScreen

        # Safety net: death always ends the run — scrub Pandemonium run state
        # so no stale curse can survive into other dungeons or the next save.
        from pandemonium_curses import end_pandemonium_run
        end_pandemonium_run(self.player)

        def _continue_game():
            from utils import apply_death_penalty
            apply_death_penalty(self.player)
            self.sm.switch_to(CityScreen, push_history=False)

        def _quit_to_menu():
            self.sm.player = None
            from gui.screens.main_menu_screen import MainMenuScreen
            self.sm.switch_to(MainMenuScreen)

        self.sm.switch_to(
            DeathScreen,
            floor=self.player.get("city_floors", {}).get(self.city_id, {}).get("floor", "?"),
            city_id=self.city_id,
            on_continue=_continue_game,
            on_quit=_quit_to_menu,
        )

    def _show_help(self):
        """Show a keyboard shortcut reference dialog."""
        help_text = (
            "Keyboard Shortcuts:\n\n"
            "City Screen:\n"
            "  1–9  — Open city service\n"
            "  I    — Inventory\n"
            "  K    — Skill Book\n"
            "  M    — World Map / Travel\n"
            "  D    — Enter Dungeon\n"
            "  S    — Settings\n"
            "  Q    — Save & Quit\n\n"
            "Combat:\n"
            "  A    — Attack\n"
            "  D    — Defend\n"
            "  F    — Flee (confirm)\n"
            "  C    — Capture\n"
            "  U    — Use Item\n"
            "  1–9  — Skills / Select target\n"
            "  Esc  — Cancel target selection\n\n"
            "Global:\n"
            "  Esc      — Go back\n"
            "  Ctrl+Q   — Quit"
        )
        from gui.widgets.confirm_dialog import ok_dialog
        ok_dialog(self, "Help — Keyboard Shortcuts", help_text)

    def _open_settings(self):
        from gui.screens.settings_screen import SettingsScreen
        self.sm.switch_to(SettingsScreen, push_history=True)

    # ── Keyboard shortcut support ────────────────────────────────────────────

    def handle_escape(self):
        """Override: Esc does nothing in city (no modal to cancel)."""
        pass  # City has no modal state to cancel; player uses buttons
