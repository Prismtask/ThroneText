"""
gui/screens/city_screen.py — City hub with service buttons and action bar.

Shows all city services as clickable buttons, plus Inventory, Skill Book,
Travel, Dungeon, and Save & Quit actions.
"""

import tkinter as tk

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme
from gui.widgets.confirm_dialog import confirm_dialog, ok_dialog
from gui.widgets.hp_bar import HPBar

from resources.cities import CITIES
from character import player_max_hp
from save_load import save_game
from utils import format_time, advance_time
from events import format_date, get_event_queue_messages
from combat.combat_ui import _get_entity_buff_tags


class CityScreen(BaseScreen):
    """The city hub — main navigation screen between dungeon runs."""

    def build_ui(self):
        self._refresh_city_id()
        self.sm.clear_history()
        self._update_top_bar()
        self.sm.clear_log()

        # Show any queued dungeon events — logging with category "event"
        # auto-opens the session log popup so the player never misses them.
        if self.player:
            event_msgs = get_event_queue_messages(self.player)
            if event_msgs:
                for msg in event_msgs:
                    if msg.strip():
                        self.sm.log(msg, category="event")

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

        self._map_frame = tk.Frame(self.content, bg=Theme.BG_DARK,
                                   highlightthickness=1, highlightbackground=Theme.BORDER)
        self._map_frame.pack(fill=tk.BOTH, expand=True, pady=8)

        self.city_map = CityMapWidget(
            self._map_frame,
            city_id=self.city_id,
            city=self.city,
            positions=positions,
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
            ("[S] Settings", self._open_settings),
            ("[Q] Save & Quit", self._save_and_quit),
            ("[?] Help", self._show_help),
        ]

        for text, cmd in actions:
            btn = self.styled_button(action_frame, text=text, command=cmd, width=16)
            btn.pack(side=tk.LEFT, padx=4, expand=True)

        # ── Keyboard shortcuts ─────────────────────────────────────────────
        self._setup_city_keys()

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

    def _build_hero_card(self):
        """Show party status card — all members in one horizontal row: 
        player + front allies + back allies. Front/back separated by a subtle divider."""
        from combat.ally import (ensure_party_order, get_all_active_allies_including_defeated,
                                 get_all_reserve_allies_including_defeated)
        p = self.player
        ensure_party_order(p)
        front_allies = get_all_active_allies_including_defeated(p)
        back_allies = get_all_reserve_allies_including_defeated(p)

        self._hero_card = tk.Frame(self.content, bg=Theme.BG_CARD, highlightthickness=1,
                                   highlightbackground=Theme.BORDER)
        self._hero_card.pack(fill=tk.X, pady=(0, 10), padx=20)
        card = self._hero_card  # alias for local use below

        # ── Collect all party members in order ─────────────────────────────
        members = []
        # Player (always first, FRONT)
        members.append({
            "name": p["name"],
            "level": p.get("level", 1),
            "hp": p.get("current_hp", 1),
            "max_hp": player_max_hp(p),
            "tags": _get_entity_buff_tags(p),
            "color": Theme.ACCENT,
            "section": "player",
            "defeated": False,
        })

        # Front-row allies
        for ally in front_allies:
            defeated = ally.get("defeated") or ally.get("current_hp", 0) <= 0
            members.append({
                "name": ally["name"],
                "level": ally.get("level", 1),
                "hp": 0 if defeated else ally.get("current_hp", 0),
                "max_hp": ally.get("max_hp", 1),
                "tags": _get_entity_buff_tags(ally),
                "color": Theme.TEXT_DIM if defeated else Theme.TEXT,
                "section": "front",
                "defeated": defeated,
            })

        # Back-row allies (go beside front, after a divider)
        for ally in back_allies:
            defeated = ally.get("defeated") or ally.get("current_hp", 0) <= 0
            members.append({
                "name": ally["name"],
                "level": ally.get("level", 1),
                "hp": 0 if defeated else ally.get("current_hp", 0),
                "max_hp": ally.get("max_hp", 1),
                "tags": _get_entity_buff_tags(ally),
                "color": "#8b7355" if not defeated else "#555555",
                "section": "back",
                "defeated": defeated,
            })

        # ── Single horizontal party row ─────────────────────────────────────
        party_row = tk.Frame(card, bg=Theme.BG_CARD)
        party_row.pack(fill=tk.X, padx=10, pady=(8, 4))

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

            block = tk.Frame(party_row, bg=Theme.BG_CARD)
            block.pack(side=tk.LEFT, padx=(0 if i == 0 else 8, 0))

            name_color = m["color"]
            if m.get("defeated"):
                name_color = "#555555"

            name_text = f"{m['name']}  Lv.{m['level']}"
            tk.Label(block, text=name_text,
                     bg=Theme.BG_CARD, fg=name_color,
                     font=Theme.FONT_BOLD).pack(anchor=tk.W)

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
            hp_bar.pack(pady=(2, 0))

            # Always show tag label to maintain vertical alignment;
            # use a non-breaking space when there are no tags.
            tag_text = m["tags"] if m["tags"] else " "
            tk.Label(block, text=tag_text, bg=Theme.BG_CARD,
                     fg=Theme.BUFF_NEUTRAL,
                     font=(Theme.FONT_FAMILY, 7),
                     anchor=tk.W).pack(anchor=tk.W)

        # ── Gold row ──────────────────────────────────────────────────────
        gold = p.get("gold", 0)
        gold_frame = tk.Frame(card, bg=Theme.BG_CARD)
        gold_frame.pack(fill=tk.X, padx=10, pady=(4, 8))
        tk.Label(gold_frame, text=f"💰 {gold}g", bg=Theme.BG_CARD,
                 fg=Theme.TEXT, font=Theme.FONT_SMALL).pack(side=tk.LEFT)

    def _update_top_bar(self):
        if not self.player:
            self.sm.update_top_bar("Pandemonium")
            return
        p = self.player
        _cf = p.get("city_floors", {}).get(self.city_id, {})
        _cur = _cf.get("floor", 1)
        _max = _cf.get("max_floor", 1)
        text = (
            f"{p['name']} | {self.city['name']} | Floor {_cur}/{_max} | "
            f"{format_date(p)} | {format_time(p)}"
        )
        self.sm.update_top_bar(text)

    # ── Service handlers ──────────────────────────────────────────────────────

    def _open_service(self, service):
        """Open a facility in the GUI FacilityScreen wrapper."""
        # Port opens the World Map instead of the old terminal UI
        if service == "port":
            self._open_world_map()
            return
        from city import SERVICE_HANDLERS
        handler = SERVICE_HANDLERS.get(service)
        if handler:
            self.sm.log(f"Entering {service.replace('_', ' ').title()}...")
            from gui.screens.facility_screen import FacilityScreen
            self.sm.switch_to(
                FacilityScreen,
                title=service.replace("_", " ").title(),
                func=handler,
                func_args=(self.player, self.city_id),
                on_close=lambda _: self._after_facility(),
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
        advance_time(self.player, 30)
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

        # Header
        tk.Label(
            sel_frame, text="Select Floor",
            bg=Theme.BG_DARK, fg=Theme.ACCENT, font=Theme.FONT_LARGE,
        ).pack(pady=(12, 2))

        tk.Label(
            sel_frame,
            text=f"Click a floor to descend  (1 – {max_unlocked}):",
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

        for f in range(1, max_unlocked + 1):
            row = (f - 1) // COLS
            col = (f - 1) % COLS
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
        p.pop("pandemonium_mode", None)
        from pandemonium_curses import clear_curse
        clear_curse(p)
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
        else:
            # Floor cleared — show post-floor menu
            self._show_post_floor_menu()

    def _show_post_floor_menu(self):
        """Show the 3-option menu after clearing a floor."""
        import tkinter as tk
        from utils import format_time
        from character import player_max_hp

        p = self.player
        city_prog = p["city_floors"].get(self.city_id, {"floor": 1})
        cleared_floor = city_prog["floor"] - 1

        root = self.sm.root if self.sm else self.winfo_toplevel()
        dialog = tk.Toplevel(root)
        dialog.title("Floor Cleared!")
        dialog.transient(root)
        dialog.grab_set()
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
            f"Gold: {p.get('gold', 0)}\n"
            f"Time: {format_time(p)}"
        )
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
