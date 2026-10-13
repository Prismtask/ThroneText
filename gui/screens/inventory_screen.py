"""
gui/screens/inventory_screen.py — Tabbed inventory, stats, skills, allies, and journal.

Replaces the terminal-based inventory_ui.py with a full GUI using tkinter's Notebook.
"""

import tkinter as tk
from tkinter import ttk

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme
from inventory import format_scaling_stat
from utils import display_name


class InventoryScreen(BaseScreen):
    """
    Tabbed inventory interface.

    Tabs:
        1. Stats & Equipment
        2. Bag
        3. Skills
        4. Allies
        5. Journal
        6. Event Horizon (only while a run is active/suspended)

    Constructor kwargs:
        is_overlay  — if True, this screen is shown via push_overlay (e.g. from
                      dungeon); the Back button dismisses the overlay instead of
                      using the history stack.
    """

    def __init__(self, parent, screen_manager, is_overlay=False, **kwargs):
        self.is_overlay = is_overlay
        self._equip_target_ally = None   # If set, bag "Equip" goes to this ally dict
        self._equip_target_slot = None   # Desired slot hint (weapon/armor/accessory1/accessory2)
        super().__init__(parent, screen_manager, **kwargs)

    def build_ui(self):
        self.sm.clear_log()
        self.sm.update_top_bar("Inventory")

        # ── Main container ───────────────────────────────────────────────────
        container = self.styled_frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Inv.TNotebook",
            background=Theme.BG_DARK,
            foreground=Theme.TEXT,
            tabmargins=[2, 5, 2, 0],
        )
        style.configure(
            "Inv.TNotebook.Tab",
            background=Theme.BG_MID,
            foreground=Theme.TEXT,
            font=Theme.FONT_BOLD,
            padding=[10, 4],
        )
        style.map(
            "Inv.TNotebook.Tab",
            background=[("selected", Theme.BG_LIGHT)],
            foreground=[("selected", Theme.TEXT_HEADER)],
        )

        # Sub-notebook style for ally tabs (slightly smaller)
        style.configure(
            "Ally.TNotebook",
            background=Theme.BG_DARK,
            foreground=Theme.TEXT,
            tabmargins=[2, 5, 2, 0],
        )
        style.configure(
            "Ally.TNotebook.Tab",
            background=Theme.BG_MID,
            foreground=Theme.TEXT,
            font=Theme.FONT,
            padding=[8, 3],
        )
        style.map(
            "Ally.TNotebook.Tab",
            background=[("selected", Theme.BG_LIGHT)],
            foreground=[("selected", Theme.TEXT_HEADER)],
        )

        self.notebook = ttk.Notebook(container, style="Inv.TNotebook")
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Create tabs
        self._build_stats_tab()
        self._build_bag_tab()
        self._build_skills_tab()
        self._build_allies_tab()
        self._build_journal_tab()
        # Event Horizon tab: live/suspended run or a quiet history stub
        if self._eh_tab_visible():
            self._build_eh_tab()

        # ── Bottom action bar ────────────────────────────────────────────────
        action_frame = tk.Frame(container, bg=Theme.BG_DARK)
        action_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))

        back_label = "← Close" if self.is_overlay else "← Back"
        self.styled_button(
            action_frame,
            text=back_label,
            command=self._on_back,
            width=16,
        ).pack(side=tk.LEFT)

        refresh_btn = self.styled_button(
            action_frame,
            text="Refresh",
            command=self._refresh_all,
            width=12,
        )
        refresh_btn.pack(side=tk.RIGHT)

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB 1 — Stats & Equipment
    # ═══════════════════════════════════════════════════════════════════════

    def _build_stats_tab(self):
        self.stats_frame = tk.Frame(self.notebook, bg=Theme.BG_DARK)
        self.notebook.add(self.stats_frame, text=" Stats & Equip ")
        self.stats_frame.grid_columnconfigure(0, weight=1)
        self._refresh_stats_tab()

    def _refresh_stats_tab(self):
        for w in self.stats_frame.winfo_children():
            w.destroy()

        if not self.player:
            self.styled_label(self.stats_frame, text="No player data.").pack(pady=20)
            return

        scroll = tk.Scrollbar(self.stats_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(self.stats_frame, bg=Theme.BG_DARK, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=canvas.yview)
        canvas.config(yscrollcommand=scroll.set)

        inner = tk.Frame(canvas, bg=Theme.BG_DARK)
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
            canvas.config(scrollregion=canvas.bbox("all"))

        inner.bind("<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all")))
        self.stats_frame.bind("<Configure>", _on_configure)

        # ── Header ───────────────────────────────────────────────────────────
        from character import player_max_hp
        hp = f"{self.player.get('current_hp', 0)}/{player_max_hp(self.player)}"
        header = (
            f"=== {self.player.get('name', 'Unknown')} "
            f"(Level {self.player.get('level', 1)}) ==="
        )
        tk.Label(
            inner, text=header, bg=Theme.BG_DARK, fg=Theme.ACCENT,
            font=Theme.FONT_LARGE,
        ).pack(anchor=tk.W, pady=(0, 4))

        info = f"HP: {hp}  |  Gold: {self.player.get('gold', 0)}"
        self.styled_label(inner, text=info).pack(anchor=tk.W, pady=(0, 8))

        # ── Attributes ───────────────────────────────────────────────────────
        from inventory import get_total_equipment_mods
        from resources.races_classes import ATTRIBUTES

        equip_mods = get_total_equipment_mods(self.player)
        buff_mods = self._compute_buff_mods(self.player)

        attr_frame = tk.LabelFrame(
            inner, text=" Attributes ", bg=Theme.BG_DARK, fg=Theme.TEXT,
            font=Theme.FONT_BOLD, highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        attr_frame.pack(fill=tk.X, pady=4, padx=4)

        for attr in ATTRIBUTES:
            base = self.player["attributes"][attr]
            eq = equip_mods.get(attr, 0)
            bf = buff_mods.get(attr, 0)
            total = base + eq + bf
            short = attr[:3].upper()

            if bf > 0:
                line = f"{short}: {base} + {eq}(eq) + {bf}(buff) = {total}"
            else:
                line = f"{short}: {base} + {eq} = {total}"

            from combat.stat_milestones import format_milestone_label
            milestone = format_milestone_label(self.player, attr)
            if milestone:
                line += f"  [{milestone}]"

            self.styled_label(attr_frame, text=line).pack(anchor=tk.W, padx=6, pady=1)

        # ── Crit summary — chance + damage (includes overflow conversion) ──
        from combat.stats import format_crit_summary
        self.styled_label(
            attr_frame, text=format_crit_summary(self.player, "player")
        ).pack(anchor=tk.W, padx=6, pady=1)

        # ── Equipment ────────────────────────────────────────────────────────
        eq_frame = tk.LabelFrame(
            inner, text=" Equipment ", bg=Theme.BG_DARK, fg=Theme.TEXT,
            font=Theme.FONT_BOLD, highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        eq_frame.pack(fill=tk.X, pady=4, padx=4)

        eq_slots = ["weapon", "armor", "accessory1", "accessory2"]
        if self.player.get("acc3_unlocked"):
            eq_slots.append("accessory3")
        for slot in eq_slots:
            item = self.player.get("equipped", {}).get(slot)
            slot_name = _slot_display_name(slot)

            row = tk.Frame(eq_frame, bg=Theme.BG_DARK)
            row.pack(fill=tk.X, padx=6, pady=2)

            if item:
                rarity = item.get("rarity", "common")
                color = Theme.RARITY_COLORS.get(rarity, Theme.TEXT)
                name = item["name"]
                mods = item.get("mods", {})
                mod_txt = ", ".join(
                    f"{k[:3]} {'+' if v >= 0 else ''}{v}" for k, v in mods.items()
                )
                txt = f"{slot_name}: {name}"
                if mod_txt:
                    txt += f"  ({mod_txt})"
                lbl = tk.Label(
                    row, text=txt, bg=Theme.BG_DARK, fg=color,
                    font=Theme.FONT, anchor=tk.W,
                )
                lbl.pack(side=tk.LEFT)

                scale_txt = format_scaling_stat(item)
                if scale_txt:
                    tk.Label(
                        row, text=f"  {scale_txt}", bg=Theme.BG_DARK,
                        fg=Theme.RARITY_LEGENDARY, font=Theme.FONT_SMALL,
                    ).pack(side=tk.LEFT)

                self.styled_button(
                    row, text="Unequip", width=8,
                    command=lambda s=slot: self._unequip_slot(s),
                ).pack(side=tk.RIGHT)
                # Unique gear stays examinable while it is worn.
                if self._is_unique_item(item):
                    self.styled_button(
                        row, text="Examine", width=9,
                        command=lambda it=item: self._examine_item(it),
                    ).pack(side=tk.RIGHT, padx=2)
            else:
                self.styled_label(row, text=f"{slot_name}: (empty)").pack(side=tk.LEFT)
                # Allow quick jump to Bag to equip an item into this empty slot
                self.styled_button(
                    row, text="Equip", width=6,
                    command=lambda s=slot: self._jump_to_bag_and_hint(s),
                ).pack(side=tk.RIGHT)

        # ── Passive skill ────────────────────────────────────────────────────
        from combat.skills import get_passive_skill
        passive = get_passive_skill(self.player)
        if passive:
            ps_frame = tk.LabelFrame(
                inner, text=" Passive Skill ", bg=Theme.BG_DARK, fg=Theme.TEXT,
                font=Theme.FONT_BOLD, highlightthickness=1,
                highlightbackground=Theme.BORDER,
            )
            ps_frame.pack(fill=tk.X, pady=4, padx=4)
            tk.Label(
                ps_frame, text=f"{passive['name']}: {passive['description']}",
                bg=Theme.BG_DARK, fg=Theme.TEXT, font=Theme.FONT,
                wraplength=600, justify=tk.LEFT,
            ).pack(anchor=tk.W, padx=6, pady=4)

        # ── Milestones ───────────────────────────────────────────────────────
        from combat.stat_milestones import format_milestone_bonuses
        mb = format_milestone_bonuses(self.player)
        if mb:
            mb_frame = tk.LabelFrame(
                inner, text=" Milestones ", bg=Theme.BG_DARK, fg=Theme.TEXT,
                font=Theme.FONT_BOLD, highlightthickness=1,
                highlightbackground=Theme.BORDER,
            )
            mb_frame.pack(fill=tk.X, pady=4, padx=4)
            tk.Label(
                mb_frame, text=mb,
                bg=Theme.BG_DARK, fg=Theme.TEXT, font=Theme.FONT,
                wraplength=600, justify=tk.LEFT,
            ).pack(anchor=tk.W, padx=6, pady=4)

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB 2 — Bag
    # ═══════════════════════════════════════════════════════════════════════

    def _build_bag_tab(self):
        self.bag_frame = tk.Frame(self.notebook, bg=Theme.BG_DARK)
        self.notebook.add(self.bag_frame, text=" Bag ")
        self.bag_frame.grid_columnconfigure(0, weight=1)
        self._refresh_bag_tab()

    def _jump_to_bag_and_hint(self, slot_name: str, ally=None):
        """Switch to the Bag tab and hint the user to choose an item to equip.

        If *ally* is provided, subsequent Equip clicks in the bag will target
        that ally instead of the player.  *slot_name* is the desired slot.
        """
        try:
            self.notebook.select(self.bag_frame)
            if ally:
                self._equip_target_ally = ally
                self._equip_target_slot = slot_name
                self.log(f"Select an item in Bag to equip to {display_name(ally)}'s {_slot_display_name(slot_name)}.")
            else:
                self._equip_target_ally = None
                self._equip_target_slot = slot_name
                self.log(f"Select an item in Bag to equip to {slot_name}.")
        except Exception:
            pass

    def _refresh_bag_tab(self):
        for w in self.bag_frame.winfo_children():
            w.destroy()

        if not self.player:
            self.styled_label(self.bag_frame, text="No player data.").pack(pady=20)
            return

        from inventory import (
            get_inventory_caps, count_inventory,
            get_sorted_equipment, get_sorted_items, get_key_items, get_cargo_items,
        )
        from resources.trade_goods import cargo_total_weight, cargo_capacity
        eq_cap, other_cap = get_inventory_caps(self.player)
        eq_count, other_count = count_inventory(self.player)

        cap_text = f"Equipment: {eq_count}/{eq_cap}  |  Items: {other_count}/{other_cap}"
        load = cargo_total_weight(self.player)
        if load > 0:
            cap = cargo_capacity(self.player)
            cap_text += f"  |  Cargo: {load} wt"
            cap_text += f"/{cap} wt" if cap > 0 else " wt (no mount)"
        self.styled_label(self.bag_frame, text=cap_text).pack(anchor=tk.W, pady=(4, 8))

        # ── Sub-tabs dividing the bag by item type ──────────────────────────
        self.bag_sub = ttk.Notebook(self.bag_frame, style="Ally.TNotebook")
        self.bag_sub.pack(fill=tk.BOTH, expand=True)

        sections = [
            (" Equipment ", get_sorted_equipment(self.player), True, False),
            (" Items ", get_sorted_items(self.player), False, False),
            (" Cargo ", get_cargo_items(self.player), False, False),
            (" Key Items ", get_key_items(self.player), False, True),
        ]
        for label, items, is_equip, is_key in sections:
            self._build_bag_subtab(label, items, is_equip, is_key)

    def _build_bag_subtab(self, label, items, is_equip, is_key):
        """One scrollable sub-tab in the bag notebook."""
        tab = tk.Frame(self.bag_sub, bg=Theme.BG_DARK)
        self.bag_sub.add(tab, text=label)

        scroll = tk.Scrollbar(tab)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(tab, bg=Theme.BG_DARK, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=canvas.yview)
        canvas.config(yscrollcommand=scroll.set)

        inner = tk.Frame(canvas, bg=Theme.BG_DARK)
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        if not items:
            self.styled_label(inner, text="Nothing here.").pack(pady=20)
            return

        for item in items:
            self._render_bag_item(inner, item, is_equip=is_equip, is_key=is_key)

    def _is_unique_item(self, item):
        """True if the item is unique (template fallback covers old saves)."""
        if item.get("unique"):
            return True
        try:
            from resources.items import ITEMS
            return bool(ITEMS.get(item.get("id"), {}).get("unique"))
        except Exception:
            return False

    def _render_bag_item(self, parent, item, is_equip, is_key=False):
        rarity = item.get("rarity", "common")
        color = Theme.RARITY_COLORS.get(rarity, Theme.TEXT)
        count = item.get("count", 1)
        count_str = f" (x{count})" if count > 1 else ""
        item_type = item.get("type", "?")

        if is_equip:
            mods = item.get("mods", {})
            mod_txt = ", ".join(
                f"{k[:3]} {'+' if v >= 0 else ''}{v}" for k, v in mods.items()
            )
            slot = item.get("slot", "?")
            text = f"{item['name']}{count_str}  [{slot}]"
            if mod_txt:
                text += f"  ({mod_txt})"
        else:
            if item_type in ("key_item", "crafting_material"):
                type_label = "Key Item"
            elif item_type == "cargo":
                type_label = "Cargo"
            else:
                type_label = item_type
            text = f"{item['name']}{count_str}  ({type_label})"

        # Living key items (the resonance blank) carry a fill-meter.
        meter = item.get("resonance_meter")
        if meter:
            text += f"  {meter}"

        row = tk.Frame(parent, bg=Theme.BG_DARK)
        row.pack(fill=tk.X, padx=6, pady=(2, 0))

        tk.Label(
            row, text=text, bg=Theme.BG_DARK, fg=color,
            font=Theme.FONT, anchor=tk.W,
        ).pack(side=tk.LEFT)

        if is_equip:
            scale_txt = format_scaling_stat(item)
            if scale_txt:
                tk.Label(
                    row, text=f"  {scale_txt}", bg=Theme.BG_DARK,
                    fg=Theme.RARITY_LEGENDARY, font=Theme.FONT_SMALL,
                ).pack(side=tk.LEFT)

        # Key items and crafting materials cannot be dropped, sold, or used,
        # but they can be examined for their name and lore. (The Beating Root
        # is the exception — it opens a third accessory slot for one actor.)
        if is_key:
            if item.get("special") == "beating_root":
                self.styled_button(
                    row, text="Use", width=5,
                    command=lambda it=item: self._use_beating_root(it),
                ).pack(side=tk.RIGHT, padx=2)
            self.styled_button(
                row, text="Examine", width=9,
                command=lambda it=item: self._examine_item(it),
            ).pack(side=tk.RIGHT, padx=2)
            sep = tk.Frame(parent, height=1, bg=Theme.BORDER)
            sep.pack(fill=tk.X, padx=10, pady=0)
            return

        if is_equip:
            self.styled_button(
                row, text="Equip", width=6,
                command=lambda it=item: self._equip_item(it),
            ).pack(side=tk.RIGHT, padx=2)
            # Unique equipment carries lore + an equip effect — always examinable.
            if self._is_unique_item(item):
                self.styled_button(
                    row, text="Examine", width=9,
                    command=lambda it=item: self._examine_item(it),
                ).pack(side=tk.RIGHT, padx=2)

        if item.get("type") in ("consumable", "utility"):
            self.styled_button(
                row, text="Use", width=5,
                command=lambda it=item: self._use_item(it),
            ).pack(side=tk.RIGHT, padx=2)

        self.styled_button(
            row, text="Drop", width=6,
            command=lambda it=item: self._drop_item(it),
        ).pack(side=tk.RIGHT, padx=2)

        # Thin separator line between items
        sep = tk.Frame(parent, height=1, bg=Theme.BORDER)
        sep.pack(fill=tk.X, padx=10, pady=0)

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB 3 — Skills
    # ═══════════════════════════════════════════════════════════════════════

    def _build_skills_tab(self):
        self.skills_frame = tk.Frame(self.notebook, bg=Theme.BG_DARK)
        self.notebook.add(self.skills_frame, text=" Skills ")
        self.skills_frame.grid_columnconfigure(0, weight=1)
        self._refresh_skills_tab()

    def _refresh_skills_tab(self):
        for w in self.skills_frame.winfo_children():
            w.destroy()

        if not self.player:
            self.styled_label(self.skills_frame, text="No player data.").pack(pady=20)
            return

        from combat.skills import get_class_skill_map, format_mastery_label
        from combat.skills import get_skill_mastery_level

        skill_map = get_class_skill_map(self.player)
        if not skill_map:
            self.styled_label(self.skills_frame, text="No skills available.").pack(pady=20)
            return

        unlocked = set(self.player.get("skills", []))
        level = self.player.get("level", 1)
        cooldowns = self.player.get("skill_cooldowns", {})

        scroll = tk.Scrollbar(self.skills_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas = tk.Canvas(self.skills_frame, bg=Theme.BG_DARK, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=canvas.yview)
        canvas.config(yscrollcommand=scroll.set)

        inner = tk.Frame(canvas, bg=Theme.BG_DARK)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all")))

        unlocked_frame = tk.LabelFrame(
            inner, text=" Unlocked ", bg=Theme.BG_DARK, fg=Theme.BUFF_POSITIVE,
            font=Theme.FONT_BOLD, highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        unlocked_frame.pack(fill=tk.X, pady=4, padx=4)

        locked_frame = tk.LabelFrame(
            inner, text=" Locked ", bg=Theme.BG_DARK, fg=Theme.TEXT_DIM,
            font=Theme.FONT_BOLD, highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        locked_frame.pack(fill=tk.X, pady=4, padx=4)

        for sid, sdef in skill_map.items():
            ul = sdef["unlock_level"]
            is_unlocked = sid in unlocked and level >= ul
            cd = cooldowns.get(sid, 0)
            cd_str = f" [CD: {cd}]" if cd > 0 else ""
            mastery = format_mastery_label(sid, self.player)
            label = f"{sdef['name']}{cd_str}  {mastery}  — Lv.{ul}"

            if is_unlocked:
                self.styled_label(unlocked_frame, text=label, fg=Theme.BUFF_POSITIVE).pack(
                    anchor=tk.W, padx=6, pady=1
                )
            else:
                self.styled_label(locked_frame, text=f"{sdef['name']}  — Lv.{ul}  [LOCKED]").pack(
                    anchor=tk.W, padx=6, pady=1
                )

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB 4 — Allies  (sub-notebook: one tab per ally)
    # ═══════════════════════════════════════════════════════════════════════

    def _build_allies_tab(self):
        self.allies_frame = tk.Frame(self.notebook, bg=Theme.BG_DARK)
        self.notebook.add(self.allies_frame, text=" Allies ")
        self.allies_frame.grid_rowconfigure(0, weight=1)
        self.allies_frame.grid_columnconfigure(0, weight=1)
        self._refresh_allies_tab()

    def _refresh_allies_tab(self):
        for w in self.allies_frame.winfo_children():
            w.destroy()

        if not self.player:
            self.styled_label(self.allies_frame, text="No player data.").pack(pady=20)
            return

        allies = self.player.get("allies", [])
        if not allies:
            self.styled_label(self.allies_frame, text="No allies recruited.").pack(pady=20)
            return

        # ── Sub-notebook for ally tabs ───────────────────────────────────────
        self.ally_notebook = ttk.Notebook(self.allies_frame, style="Ally.TNotebook")
        self.ally_notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        for ally in allies:
            ally_tab = tk.Frame(self.ally_notebook, bg=Theme.BG_DARK)
            tab_label = f" {display_name(ally) or 'Ally'} "
            self.ally_notebook.add(ally_tab, text=tab_label)
            self._render_ally_page(ally_tab, ally)

    def _render_ally_page(self, parent, ally):
        """Render a full dedicated page for an ally — mirrors the player Stats & Equip tab."""
        from inventory import get_total_equipment_mods
        from resources.races_classes import ATTRIBUTES

        # ── Reconcile vorpal skills before display ───────────────────────────
        # Safety net: ensures innate/learned skills match the vorpal flags even
        # if the load-time reconciliation in ensure_player_fields was missed.
        from character import _reconcile_heroine_vorpal_skills
        _reconcile_heroine_vorpal_skills(ally, self.player)

        # ── Scrollable inner ─────────────────────────────────────────────────
        scroll = tk.Scrollbar(parent)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(parent, bg=Theme.BG_DARK, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=canvas.yview)
        canvas.config(yscrollcommand=scroll.set)

        inner = tk.Frame(canvas, bg=Theme.BG_DARK)
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
            canvas.config(scrollregion=canvas.bbox("all"))

        inner.bind("<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all")))
        parent.bind("<Configure>", _on_configure)

        # ── Header ───────────────────────────────────────────────────────────
        defeated = ally.get("defeated") or ally.get("current_hp", 0) <= 0
        status_str = " [INCAPACITATED]" if defeated else ""
        header = (
            f"=== {display_name(ally) or 'Ally'} "
            f"(Lv.{ally.get('level', 1)}){status_str} ==="
        )
        tk.Label(
            inner, text=header, bg=Theme.BG_DARK,
            fg=Theme.BUFF_NEGATIVE if defeated else Theme.ACCENT,
            font=Theme.FONT_LARGE,
        ).pack(anchor=tk.W, pady=(0, 4))

        hp = ally.get("current_hp", 0)
        max_hp = ally.get("max_hp", 1)
        pct = max(0, min(100, int(100 * hp / max_hp))) if max_hp > 0 else 0
        hp_color = Theme.HP_BAR_FILL if pct > 50 else (Theme.BUFF_NEUTRAL if pct > 25 else Theme.BUFF_NEGATIVE)
        info = f"HP: {hp}/{max_hp}"
        tk.Label(
            inner, text=info, bg=Theme.BG_DARK, fg=hp_color,
            font=Theme.FONT_BOLD,
        ).pack(anchor=tk.W, pady=(0, 8))

        # ── Attributes ───────────────────────────────────────────────────────
        equip_mods = get_total_equipment_mods(ally)
        buff_mods = self._compute_buff_mods(ally)

        attr_frame = tk.LabelFrame(
            inner, text=" Attributes ", bg=Theme.BG_DARK, fg=Theme.TEXT,
            font=Theme.FONT_BOLD, highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        attr_frame.pack(fill=tk.X, pady=4, padx=4)

        for attr in ATTRIBUTES:
            base = ally["attributes"][attr]
            eq = equip_mods.get(attr, 0)
            bf = buff_mods.get(attr, 0)
            total = base + eq + bf
            short = attr[:3].upper()

            if bf > 0:
                line = f"{short}: {base} + {eq}(eq) + {bf}(buff) = {total}"
            else:
                line = f"{short}: {base} + {eq} = {total}"

            from combat.stat_milestones import format_milestone_label
            milestone = format_milestone_label(ally, attr)
            if milestone:
                line += f"  [{milestone}]"

            self.styled_label(attr_frame, text=line).pack(anchor=tk.W, padx=6, pady=1)

        # ── Crit summary — chance + damage (includes overflow conversion) ──
        from combat.stats import format_crit_summary
        from combat.ally import compute_ally_stats
        _a_str, _a_con, a_dex, a_ler, _a_wis, _a_cha = compute_ally_stats(ally)
        self.styled_label(
            attr_frame, text=format_crit_summary(ally, "ally", dex=a_dex, lrn=a_ler)
        ).pack(anchor=tk.W, padx=6, pady=1)

        # ── Equipment ────────────────────────────────────────────────────────
        eq_frame = tk.LabelFrame(
            inner, text=" Equipment ", bg=Theme.BG_DARK, fg=Theme.TEXT,
            font=Theme.FONT_BOLD, highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        eq_frame.pack(fill=tk.X, pady=4, padx=4)

        eq_slots = ["weapon", "armor", "accessory1", "accessory2"]
        if ally.get("acc3_unlocked"):
            eq_slots.append("accessory3")
        for slot in eq_slots:
            item = ally.get("equipped", {}).get(slot)
            slot_name = _slot_display_name(slot)

            row = tk.Frame(eq_frame, bg=Theme.BG_DARK)
            row.pack(fill=tk.X, padx=6, pady=2)

            if item:
                rarity = item.get("rarity", "common")
                color = Theme.RARITY_COLORS.get(rarity, Theme.TEXT)
                name = item["name"]
                mods = item.get("mods", {})
                mod_txt = ", ".join(
                    f"{k[:3]} {'+' if v >= 0 else ''}{v}" for k, v in mods.items()
                )
                txt = f"{slot_name}: {name}"
                if mod_txt:
                    txt += f"  ({mod_txt})"
                tk.Label(
                    row, text=txt, bg=Theme.BG_DARK, fg=color,
                    font=Theme.FONT, anchor=tk.W,
                ).pack(side=tk.LEFT)

                scale_txt = format_scaling_stat(item)
                if scale_txt:
                    tk.Label(
                        row, text=f"  {scale_txt}", bg=Theme.BG_DARK,
                        fg=Theme.RARITY_LEGENDARY, font=Theme.FONT_SMALL,
                    ).pack(side=tk.LEFT)

                self.styled_button(
                    row, text="Unequip", width=8,
                    command=lambda a=ally, s=slot: self._unequip_ally_slot(a, s),
                ).pack(side=tk.RIGHT)
                # Unique gear stays examinable while it is worn.
                if self._is_unique_item(item):
                    self.styled_button(
                        row, text="Examine", width=9,
                        command=lambda it=item: self._examine_item(it),
                    ).pack(side=tk.RIGHT, padx=2)
            else:
                self.styled_label(row, text=f"{slot_name}: (empty)").pack(side=tk.LEFT)
                self.styled_button(
                    row, text="Equip", width=6,
                    command=lambda a=ally, s=slot: self._jump_to_bag_and_hint(s, ally=a),
                ).pack(side=tk.RIGHT)

        # ── Passive skill ────────────────────────────────────────────────────
        from combat.ally_skills import (
            get_race_passive, get_passive_by_id,
        )
        race = ally.get("race")
        passive = get_race_passive(race) if race else None
        if not passive and ally.get("passive_skill"):
            passive = get_passive_by_id(ally["passive_skill"])
        if not passive and ally.get("key"):
            from resources.enemies import ENEMIES
            template = ENEMIES.get(ally["key"], {})
            template_race = template.get("race")
            if template_race:
                passive = get_race_passive(template_race)

        if passive:
            ps_frame = tk.LabelFrame(
                inner, text=" Passive Skill ", bg=Theme.BG_DARK, fg=Theme.TEXT,
                font=Theme.FONT_BOLD, highlightthickness=1,
                highlightbackground=Theme.BORDER,
            )
            ps_frame.pack(fill=tk.X, pady=4, padx=4)
            tk.Label(
                ps_frame, text=f"{passive['name']}: {passive['description']}",
                bg=Theme.BG_DARK, fg=Theme.TEXT, font=Theme.FONT,
                wraplength=600, justify=tk.LEFT,
            ).pack(anchor=tk.W, padx=6, pady=4)

        # ── Skills ───────────────────────────────────────────────────────────
        from combat.ally_skills import (
            get_innate_skill_def, get_learnable_skill_def,
            get_ally_skill_mastery_level, format_skill_learning_progress,
            format_ally_mastery_label,
        )
        skill_lines = []
        for sid in ally.get("innate_skills", []):
            sdef = get_innate_skill_def(sid)
            if sdef:
                m = get_ally_skill_mastery_level(ally, sid)
                stars = format_ally_mastery_label(sid, ally)
                cd = ally.get("skill_cooldowns", {}).get(sid, 0)
                cd_str = f" [CD: {cd}]" if cd > 0 else ""
                skill_lines.append(f"[Innate] {sdef['name']}{cd_str} {stars}")
        for sid in ally.get("upgrade_skills", []):
            sdef = get_innate_skill_def(sid)
            if sdef:
                stars = format_ally_mastery_label(sid, ally)
                cd = ally.get("skill_cooldowns", {}).get(sid, 0)
                cd_str = f" [CD: {cd}]" if cd > 0 else ""
                skill_lines.append(f"[Upgrade] {sdef['name']}{cd_str} {stars}")
        for sid in ally.get("learned_skills", []):
            sdef = get_learnable_skill_def(sid)
            if sdef:
                m = get_ally_skill_mastery_level(ally, sid)
                stars = format_ally_mastery_label(sid, ally)
                cd = ally.get("skill_cooldowns", {}).get(sid, 0)
                cd_str = f" [CD: {cd}]" if cd > 0 else ""
                skill_lines.append(f"[Learned] {sdef['name']}{cd_str} {stars}")

        progress = format_skill_learning_progress(ally)
        if progress and "Not learning" not in progress:
            skill_lines.append(f"[Learning] {progress}")

        if skill_lines:
            sk_frame = tk.LabelFrame(
                inner, text=" Skills ", bg=Theme.BG_DARK, fg=Theme.TEXT,
                font=Theme.FONT_BOLD, highlightthickness=1,
                highlightbackground=Theme.BORDER,
            )
            sk_frame.pack(fill=tk.X, pady=4, padx=4)
            for line in skill_lines:
                self.styled_label(sk_frame, text=f"  {line}").pack(
                    anchor=tk.W, padx=6, pady=1
                )

        # ── Milestones ───────────────────────────────────────────────────────
        from combat.stat_milestones import format_milestone_bonuses
        mb = format_milestone_bonuses(ally)
        if mb:
            mb_frame = tk.LabelFrame(
                inner, text=" Milestones ", bg=Theme.BG_DARK, fg=Theme.TEXT,
                font=Theme.FONT_BOLD, highlightthickness=1,
                highlightbackground=Theme.BORDER,
            )
            mb_frame.pack(fill=tk.X, pady=4, padx=4)
            tk.Label(
                mb_frame, text=mb,
                bg=Theme.BG_DARK, fg=Theme.TEXT, font=Theme.FONT,
                wraplength=600, justify=tk.LEFT,
            ).pack(anchor=tk.W, padx=6, pady=4)

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB 5 — Journal  (sub-notebook: Bounty, Main Quest, Side Quest, Event)
    # ═══════════════════════════════════════════════════════════════════════

    def _build_journal_tab(self):
        self.journal_frame = tk.Frame(self.notebook, bg=Theme.BG_DARK)
        self.notebook.add(self.journal_frame, text=" Journal ")
        self.journal_frame.grid_rowconfigure(0, weight=1)
        self.journal_frame.grid_columnconfigure(0, weight=1)
        self._refresh_journal_tab()

    def _refresh_journal_tab(self):
        for w in self.journal_frame.winfo_children():
            w.destroy()

        if not self.player:
            self.styled_label(self.journal_frame, text="No player data.").pack(pady=20)
            return

        # ── Sub-notebook for journal categories ──────────────────────────────
        self.journal_notebook = ttk.Notebook(self.journal_frame, style="Ally.TNotebook")
        self.journal_notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Bounty sub-tab
        bounty_tab = tk.Frame(self.journal_notebook, bg=Theme.BG_DARK)
        self.journal_notebook.add(bounty_tab, text=" Bounty ")
        self._render_bounty_subtab(bounty_tab)

        # Main Quest sub-tab
        main_quest_tab = tk.Frame(self.journal_notebook, bg=Theme.BG_DARK)
        self.journal_notebook.add(main_quest_tab, text=" Main Quest ")
        self._render_quest_subtab(main_quest_tab, "main_quests", "No main quests yet.")

        # Side Quest sub-tab
        side_quest_tab = tk.Frame(self.journal_notebook, bg=Theme.BG_DARK)
        self.journal_notebook.add(side_quest_tab, text=" Side Quest ")
        self._render_quest_subtab(side_quest_tab, "side_quests", "No side quests yet.")

        # Event sub-tab
        event_tab = tk.Frame(self.journal_notebook, bg=Theme.BG_DARK)
        self.journal_notebook.add(event_tab, text=" Event ")
        self._render_event_subtab(event_tab)

    def _render_bounty_subtab(self, parent):
        """Render the Bounty sub-tab showing active bounties."""
        bounties = self.player.get("active_bounties", [])
        if not bounties:
            self.styled_label(parent, text="No active bounties.", fg=Theme.TEXT_DIM).pack(
                anchor=tk.CENTER, expand=True
            )
            return

        # Scrollable container
        scroll = tk.Scrollbar(parent)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas = tk.Canvas(parent, bg=Theme.BG_DARK, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=canvas.yview)
        canvas.config(yscrollcommand=scroll.set)

        inner = tk.Frame(canvas, bg=Theme.BG_DARK)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all")))

        current_day = self.player.get("day", 1)

        for b in bounties:
            current = b.get("current", 0)
            required = b["required"]
            days_left = b.get("deadline", 0) - current_day
            ready = current >= required
            expired = days_left <= 0 and not ready

            frame_color = Theme.BORDER
            title_color = Theme.BUFF_POSITIVE if ready else (Theme.BUFF_NEGATIVE if expired else Theme.TEXT)
            status_text = "✓ READY TO CLAIM" if ready else ("✗ EXPIRED" if expired else f"{current}/{required}")
            status_color = Theme.BUFF_POSITIVE if ready else (Theme.BUFF_NEGATIVE if expired else Theme.TEXT)

            frame = tk.LabelFrame(
                inner,
                text=f" {b['target_name']} ",
                bg=Theme.BG_DARK,
                fg=title_color,
                font=Theme.FONT_BOLD,
                highlightthickness=1,
                highlightbackground=frame_color,
            )
            frame.pack(fill=tk.X, pady=4, padx=4)

            self.styled_label(
                frame, text=f"Progress: {status_text}",
                fg=status_color,
            ).pack(anchor=tk.W, padx=6, pady=2)
            self.styled_label(
                frame, text=f"Difficulty: {b.get('difficulty', '?')}",
            ).pack(anchor=tk.W, padx=6, pady=1)
            self.styled_label(
                frame, text=f"Reward: {b.get('reward_gold', 0)} gold, {b.get('reward_favor', 0)} favor",
            ).pack(anchor=tk.W, padx=6, pady=1)
            days_text = f"Expires in {days_left} days" if days_left > 0 else "EXPIRED"
            self.styled_label(
                frame, text=days_text,
                fg=Theme.BUFF_NEGATIVE if days_left <= 0 else Theme.TEXT_DIM,
            ).pack(anchor=tk.W, padx=6, pady=2)

    def _render_quest_subtab(self, parent, quest_key, empty_text):
        """Render a quest sub-tab (main or side).

        Entries come from the quest runtime's Journal mirror (quests.sync_journal).
        Active quests are listed first; completed quests trail at the bottom,
        dimmed, as a paper trail.
        """
        quests = self.player.get("journal", {}).get(quest_key, [])
        if not quests:
            self.styled_label(parent, text=empty_text, fg=Theme.TEXT_DIM).pack(
                anchor=tk.CENTER, expand=True
            )
            return

        scroll = tk.Scrollbar(parent)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas = tk.Canvas(parent, bg=Theme.BG_DARK, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=canvas.yview)
        canvas.config(yscrollcommand=scroll.set)

        inner = tk.Frame(canvas, bg=Theme.BG_DARK)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all")))

        ordered = sorted(
            quests,
            key=lambda q: (q.get("status") == "complete", q.get("day", 0)),
        )

        for q in ordered:
            status = q.get("status", "active")
            completed = status == "complete"
            ready = status == "ready"

            frame = tk.LabelFrame(
                inner,
                text=f" {q.get('name', 'Quest')} ",
                bg=Theme.BG_DARK,
                fg=Theme.TEXT_DIM if completed else Theme.TEXT,
                font=Theme.FONT_BOLD,
                highlightthickness=1,
                highlightbackground=Theme.BORDER,
            )
            frame.pack(fill=tk.X, pady=4, padx=4)

            # Status chip
            if completed:
                chip_text, chip_color = "✓ COMPLETE", Theme.TEXT_DIM
            elif ready:
                chip_text, chip_color = "★ READY TO TURN IN", Theme.BUFF_POSITIVE
            else:
                chip_text, chip_color = "ACTIVE", Theme.ACCENT
            self.styled_label(
                frame, text=chip_text, fg=chip_color, font=Theme.FONT_SMALL
            ).pack(anchor=tk.W, padx=6, pady=(2, 0))

            self.styled_label(
                frame,
                text=q.get("desc", ""),
                fg=Theme.TEXT_DIM if completed else Theme.TEXT,
            ).pack(anchor=tk.W, padx=6, pady=2)

            for obj in q.get("objectives", []):
                done = bool(obj.get("done"))
                mark = "✓" if done else "☐"
                color = Theme.BUFF_POSITIVE if done else Theme.TEXT_DIM
                self.styled_label(
                    frame, text=f"   {mark} {obj.get('label', '')}", fg=color
                ).pack(anchor=tk.W, padx=6, pady=0)

            if q.get("day"):
                self.styled_label(frame, text=f"Day {q['day']}", fg=Theme.TEXT_DIM).pack(
                    anchor=tk.W, padx=6, pady=(2, 2)
                )

    def _render_event_subtab(self, parent):
        """Render the Event sub-tab showing all recorded events."""
        from events import format_date
        events = self.player.get("journal", {}).get("events", [])
        if not events:
            self.styled_label(parent, text="No events recorded yet.", fg=Theme.TEXT_DIM).pack(
                anchor=tk.CENTER, expand=True
            )
            return

        # Scrollable container
        scroll = tk.Scrollbar(parent)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas = tk.Canvas(parent, bg=Theme.BG_DARK, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=canvas.yview)
        canvas.config(yscrollcommand=scroll.set)

        inner = tk.Frame(canvas, bg=Theme.BG_DARK)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all")))

        # Show most recent events first
        for evt in reversed(events):
            tag = evt.get("tag", "")
            tag_color = Theme.ACCENT if "[FIXED]" in tag else Theme.BUFF_NEUTRAL

            frame = tk.LabelFrame(
                inner,
                text=f" {tag}  {evt.get('name', 'Event')} ",
                bg=Theme.BG_DARK,
                fg=tag_color,
                font=Theme.FONT_BOLD,
                highlightthickness=1,
                highlightbackground=Theme.BORDER,
            )
            frame.pack(fill=tk.X, pady=4, padx=4)

            self.styled_label(frame, text=evt.get("desc", "")).pack(
                anchor=tk.W, padx=6, pady=2
            )
            if evt.get("day"):
                # Create a temp dict with the day for format_date
                day_info = {"day": evt["day"]}
                self.styled_label(
                    frame, text=f"Day {evt['day']} ({format_date(day_info)})",
                    fg=Theme.TEXT_DIM,
                ).pack(anchor=tk.W, padx=6, pady=1)

    # ═══════════════════════════════════════════════════════════════════════
    #  Actions
    # ═══════════════════════════════════════════════════════════════════════

    def _compute_buff_mods(self, entity):
        """Compute attribute buffs from active_buffs for any entity."""
        from resources.races_classes import ATTRIBUTES
        buff_mods = {}
        for buff in entity.get("active_buffs", []):
            if buff.get("stat") == "all" or buff.get("type") == "blessing":
                for attr in ATTRIBUTES:
                    buff_mods[attr] = buff_mods.get(attr, 0) + buff["value"]
            elif buff.get("stat") in ATTRIBUTES:
                attr = buff["stat"]
                buff_mods[attr] = buff_mods.get(attr, 0) + buff["value"]
        return buff_mods

    def _equip_item(self, item):
        """Equip an item on the player, or on the targeted ally if set."""
        # ── Ally target path ─────────────────────────────────────────────
        if self._equip_target_ally is not None:
            ally = self._equip_target_ally
            slot_hint = self._equip_target_slot
            # Clear target immediately to avoid stale references
            self._equip_target_ally = None
            self._equip_target_slot = None

            # Handle accessory slot selection
            if item.get("slot") == "accessory" and slot_hint not in (
                    "accessory1", "accessory2", "accessory3"):
                eq = ally.get("equipped", {})
                if _acc_slots_full(eq, ally.get("acc3_unlocked")):
                    self._prompt_accessory_choice(item, target="ally", ally=ally)
                    return

            from combat.ally import equip_ally_item
            result = equip_ally_item(ally, item, self.player, target_slot=slot_hint)
            self.sm.log(result if isinstance(result, str) else f"Equipped {item['name']} on {display_name(ally)}.")
            self._refresh_all()
            return

        # ── Player path (original) ───────────────────────────────────────
        from inventory import equip_item

        # Handle accessory slot selection
        if item.get("slot") == "accessory":
            eq = self.player.get("equipped", {})
            if _acc_slots_full(eq, self.player.get("acc3_unlocked")):
                self._prompt_accessory_choice(item, target="player")
                return

        # Remove from inventory first
        try:
            idx = next(i for i, itm in enumerate(self.player.get("inventory", [])) if itm is item)
            self.player["inventory"].pop(idx)
        except (StopIteration, IndexError):
            pass

        result = equip_item(self.player, item)
        if result is False:
            # Equip failed (inventory full) — restore item
            self.player.setdefault("inventory", []).append(item)
            self.sm.log(f"Cannot equip {item['name']} — inventory full.")
        else:
            self.sm.log(f"Equipped {item['name']}.")
        self._refresh_all()

    def _unequip_slot(self, slot):
        """Unequip a slot on the player."""
        from inventory import unequip_slot
        result = unequip_slot(self.player, slot)
        self._handle_unequip_result(result)
        self._refresh_all()

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB 6 — Event Horizon (visible only while a run is active/suspended)
    # ═══════════════════════════════════════════════════════════════════════

    def _eh_meta(self):
        """The persistent Event Horizon state dict (never None)."""
        return (self.player or {}).get("event_horizon") or {}

    def _eh_run_state(self):
        """The active/suspended Event Horizon run dict, or None."""
        state = self._eh_meta()
        return state if state.get("run_active") else None

    def _eh_tab_visible(self):
        """Tab shows while a run is live/suspended — or as a quiet history stub."""
        state = self._eh_meta()
        return (bool(state.get("run_active"))
                or int(state.get("best_room", 0) or 0) > 0)

    def _build_eh_tab(self):
        self.eh_frame = tk.Frame(self.notebook, bg=Theme.BG_DARK)
        self.notebook.add(self.eh_frame, text=" Event Horizon ")
        self._refresh_eh_tab()

    def _refresh_eh_tab(self):
        for w in self.eh_frame.winfo_children():
            w.destroy()

        import event_horizon as eh

        state = self._eh_meta()
        running = bool(state.get("run_active"))
        inside = bool((self.player or {}).get("_eh_in_run"))
        best = max(int(state.get("best_room", 0) or 0),
                   int(state.get("room", 0) or 0))

        if not running:
            # History stub — no live run to manage right now.
            self.styled_label(
                self.eh_frame,
                text=(f"No active Event Horizon run.\n\n"
                      f"Best room ever: {best}\n\n"
                      "Step into the rift again at the Event Horizon site "
                      "(world map, east of Veilholt)."),
                fg=Theme.TEXT_DIM, justify=tk.CENTER,
            ).pack(anchor=tk.CENTER, expand=True, padx=18, pady=18)
            return

        scroll = tk.Scrollbar(self.eh_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas = tk.Canvas(self.eh_frame, bg=Theme.BG_DARK, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=canvas.yview)
        canvas.config(yscrollcommand=scroll.set)
        inner = tk.Frame(canvas, bg=Theme.BG_DARK)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.config(scrollregion=canvas.bbox("all")))

        room = int(state.get("room", 0))
        motes = int(state.get("motes", 0))
        entropy = eh.get_entropy_total(self.player)
        pct = int(round(eh.entropy_stat_penalty(entropy) * 100))

        # ── Run status ──────────────────────────────────────────────────
        status = tk.LabelFrame(
            inner, text=" The Run ", bg=Theme.BG_DARK, fg=Theme.ACCENT,
            font=Theme.FONT_BOLD, highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        status.pack(fill=tk.X, pady=4, padx=4)
        if inside:
            banner, banner_fg = ("▶ IN RUN — deep in the distortion. "
                                 "Everything below is live.", Theme.ACCENT)
        else:
            banner, banner_fg = ("⏸ SUSPENDED — resume at the Event Horizon "
                                 "site. Flasks, cards and Entropy wait there.",
                                 Theme.TEXT_DIM)
        tk.Label(status, text=banner, bg=Theme.BG_DARK, fg=banner_fg,
                 font=Theme.FONT_SMALL, anchor=tk.W, wraplength=620,
                 justify=tk.LEFT).pack(fill=tk.X, padx=8, pady=(4, 2))
        rows = [
            ("Next room", f"{room + 1}"),
            ("Deepest room (this run)", f"{room}"),
            ("Best room ever", f"{best}"),
            ("Horizon Motes", f"\u25ce {motes}"),
            ("Entropy", f"{entropy} stacks  (attributes \u2212{pct}%)"),
        ]
        for label, value in rows:
            row = tk.Frame(status, bg=Theme.BG_DARK)
            row.pack(fill=tk.X, padx=8, pady=1)
            tk.Label(row, text=label, bg=Theme.BG_DARK, fg=Theme.TEXT_DIM,
                     font=Theme.FONT_SMALL, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=value, bg=Theme.BG_DARK, fg=Theme.TEXT,
                     font=Theme.FONT_SMALL, anchor=tk.E).pack(side=tk.RIGHT)
        tk.Frame(status, bg=Theme.BG_DARK, height=3).pack()

        # ── Entropy afflictions ─────────────────────────────────────────
        aff_frame = tk.LabelFrame(
            inner, text=" Entropy Afflictions (battle-start debuffs) ",
            bg=Theme.BG_DARK, fg=Theme.BUFF_NEGATIVE, font=Theme.FONT_BOLD,
            highlightthickness=1, highlightbackground=Theme.BORDER,
        )
        aff_frame.pack(fill=tk.X, pady=4, padx=4)
        aff = list(state.get("entropy_afflictions") or [])
        if aff:
            for i, key in enumerate(aff, 1):
                name, desc = eh.ENTROPY_AFFLICTION_INFO.get(
                    key, (str(key).title(), ""))
                tk.Label(
                    aff_frame, text=f"{i}. {name} — {desc}",
                    bg=Theme.BG_DARK, fg=Theme.TEXT, font=Theme.FONT_SMALL,
                    anchor=tk.W, wraplength=620, justify=tk.LEFT,
                ).pack(fill=tk.X, padx=8, pady=1)
        else:
            self.styled_label(aff_frame, text="None yet.",
                              fg=Theme.TEXT_DIM).pack(anchor=tk.W, padx=8,
                                                      pady=2)
        if len(aff) < len(eh.ENTROPY_DEBUFF_POOL):
            next_at = (len(aff) + 1) * eh.EH_ENTROPY_AFFLICTION_EVERY
            self.styled_label(
                aff_frame,
                text=(f"Entropy gains a random affliction every "
                      f"{eh.EH_ENTROPY_AFFLICTION_EVERY} stacks "
                      f"(next at {next_at}). Battles only use the afflictions "
                      f"listed above."),
                fg=Theme.TEXT_DIM,
            ).pack(anchor=tk.W, padx=8, pady=(2, 4))

        # ── Flask effects per actor ─────────────────────────────────────
        flask_frame = tk.LabelFrame(
            inner, text=" Flask Effects (permanent for the run) ",
            bg=Theme.BG_DARK, fg=Theme.BUFF_POSITIVE, font=Theme.FONT_BOLD,
            highlightthickness=1, highlightbackground=Theme.BORDER,
        )
        flask_frame.pack(fill=tk.X, pady=4, padx=4)
        flasks = state.get("actor_flasks") or {}
        if flasks:
            for key in sorted(flasks):
                who = "You" if key == "player" else str(key).split(":", 1)[-1]
                # Running total of the actor's flasks rides on the name row
                # (2026-10-08 request: "+n% dmg, so on" beside the actor name).
                total = eh.format_flask_summary(flasks[key])
                head = tk.Frame(flask_frame, bg=Theme.BG_DARK)
                head.pack(fill=tk.X, padx=8, pady=(4, 0))
                tk.Label(head, text=who, bg=Theme.BG_DARK,
                         fg=Theme.TEXT_HEADER, font=Theme.FONT_BOLD,
                         anchor=tk.W).pack(side=tk.LEFT)
                if total:
                    tk.Label(head, text=total, bg=Theme.BG_DARK,
                             fg=Theme.BUFF_POSITIVE, font=Theme.FONT_SMALL,
                             anchor=tk.E).pack(side=tk.RIGHT)
                for rec in flasks[key]:
                    tk.Label(
                        flask_frame,
                        text=f"    \u2022 {rec.get('label') or rec.get('name', '?')}",
                        bg=Theme.BG_DARK, fg=Theme.TEXT, font=Theme.FONT_SMALL,
                        anchor=tk.W, wraplength=620, justify=tk.LEFT,
                    ).pack(fill=tk.X, padx=8)
        else:
            self.styled_label(flask_frame, text="No flasks consumed yet.",
                              fg=Theme.TEXT_DIM).pack(anchor=tk.W, padx=8, pady=4)

        # ── Tarot hand (the Joker's arcana, docs/joker_cards_proposal.md) ──
        tarot_frame = tk.LabelFrame(
            inner, text=" Tarot Hand (the Joker's arcana) ", bg=Theme.BG_DARK,
            fg=Theme.TEXT_HEADER, font=Theme.FONT_BOLD,
            highlightthickness=1, highlightbackground=Theme.BORDER,
        )
        tarot_frame.pack(fill=tk.X, pady=4, padx=4)
        jokers = state.get("joker_cards") or []
        head = tk.Frame(tarot_frame, bg=Theme.BG_DARK)
        head.pack(fill=tk.X, padx=8, pady=(4, 0))
        tk.Label(head, text=f"Hand: {len(jokers)} / {eh.EH_JOKER_HAND_CAP}",
                 bg=Theme.BG_DARK, fg=Theme.TEXT, font=Theme.FONT_SMALL,
                 anchor=tk.W).pack(side=tk.LEFT)
        if any(r.get("id") == "joker_world" for r in jokers):
            tk.Label(head, text="The deal is closed.", bg=Theme.BG_DARK,
                     fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL,
                     anchor=tk.E).pack(side=tk.RIGHT)
        else:
            tk.Label(head, text="the Joker deals 2 at every 25th room",
                     bg=Theme.BG_DARK, fg=Theme.TEXT_DIM,
                     font=Theme.FONT_SMALL,
                     anchor=tk.E).pack(side=tk.RIGHT)
        if jokers:
            for r in jokers:
                tk.Label(
                    tarot_frame,
                    text=f"  \u2022 {r.get('name', '?')} — {r.get('desc', '')}",
                    bg=Theme.BG_DARK, fg=Theme.TEXT, font=Theme.FONT_SMALL,
                    anchor=tk.W, wraplength=620, justify=tk.LEFT,
                ).pack(fill=tk.X, padx=8, pady=1)
        else:
            self.styled_label(tarot_frame, text="No arcana taken yet.",
                              fg=Theme.TEXT_DIM).pack(anchor=tk.W, padx=8, pady=4)

        # ── Positive cards ──────────────────────────────────────────────
        pos_frame = tk.LabelFrame(
            inner, text=" Deep Boons (team cards) ", bg=Theme.BG_DARK,
            fg=Theme.BUFF_POSITIVE, font=Theme.FONT_BOLD,
            highlightthickness=1, highlightbackground=Theme.BORDER,
        )
        pos_frame.pack(fill=tk.X, pady=4, padx=4)
        pos = state.get("positive_cards") or []
        if pos:
            for c in pos:
                tk.Label(
                    pos_frame,
                    text=(f"\u2022 {c.get('name', '?')} (T{c.get('tier', '?')}) "
                          f"— {c.get('desc', '')}"),
                    bg=Theme.BG_DARK, fg=Theme.TEXT, font=Theme.FONT_SMALL,
                    anchor=tk.W, wraplength=620, justify=tk.LEFT,
                ).pack(fill=tk.X, padx=8, pady=1)
        else:
            self.styled_label(pos_frame, text="None taken.",
                              fg=Theme.TEXT_DIM).pack(anchor=tk.W, padx=8, pady=4)

        # ── Negative cards ──────────────────────────────────────────────
        neg_frame = tk.LabelFrame(
            inner, text=" Trial Burdens (enemy cards) ", bg=Theme.BG_DARK,
            fg=Theme.BUFF_NEGATIVE, font=Theme.FONT_BOLD,
            highlightthickness=1, highlightbackground=Theme.BORDER,
        )
        neg_frame.pack(fill=tk.X, pady=4, padx=4)
        neg = state.get("negative_cards") or []
        if neg:
            for c in neg:
                cost = c.get("entropy_cost", 0)
                tk.Label(
                    neg_frame,
                    text=(f"\u2022 {c.get('name', '?')} (T{c.get('tier', '?')}) "
                          f"— {c.get('desc', '')}  [Entropy +{cost}]"),
                    bg=Theme.BG_DARK, fg=Theme.TEXT, font=Theme.FONT_SMALL,
                    anchor=tk.W, wraplength=620, justify=tk.LEFT,
                ).pack(fill=tk.X, padx=8, pady=1)
        else:
            self.styled_label(neg_frame, text="None taken.",
                              fg=Theme.TEXT_DIM).pack(anchor=tk.W, padx=8, pady=4)

        # ── Footer ───────────────────────────────────────────────────────
        self.styled_label(
            inner,
            text=("Everything here is lost on death or abandon — only your "
                  "best room is kept. Save & quit suspends the run."),
            fg=Theme.TEXT_DIM,
        ).pack(anchor=tk.W, padx=6, pady=(6, 10))

    def _examine_item(self, item):
        """Popup showing an item's name, rarity, lore, and equip effect.

        Covers key items and every unique (in the bag or equipped). Uniques
        state their equip effect: boss drops / guild legacies / Event Horizon
        trophies via `resources.unique_effects.py`, wedding accessories via
        their combat blurbs (base + bonded variant), and flavour-only uniques
        say so instead of staying silent.
        """
        from gui.widgets.confirm_dialog import ok_dialog
        from resources.items import ITEMS
        from resources.unique_effects import unique_effect_text

        name = item.get("name", "Key Item")
        template = ITEMS.get(item.get("id"), {}) or {}
        desc = item.get("description")
        if not desc:
            # Instances built before descriptions were carried through (old saves)
            desc = template.get("description")
        special = item.get("special") or template.get("special")

        effect = unique_effect_text(special)
        bonded_note = ""
        if not effect and special:
            # Wedding accessories keep their blurbs next to their implementation.
            try:
                from combat.weapon.wedding_specials import wedding_special_blurb
                effect = wedding_special_blurb(special, bonded=False)
                bonded = wedding_special_blurb(special, bonded=True)
                if bonded and bonded != effect:
                    bonded_note = f"Bonded (girl in active party): {bonded}"
            except Exception:
                effect = ""

        rarity = (item.get("rarity")
                  or template.get("drop_rarity")
                  or template.get("rarity") or "")
        rarity = rarity.capitalize()
        body = f"{name}  ({rarity})" if rarity else name
        if desc:
            body += f"\n\n{desc}"
        if effect:
            body += f"\n\nEquip Effect: {effect}"
        if bonded_note:
            body += f"\n\n{bonded_note}"
        elif not desc and not effect:
            body += "\n\nNo description recorded for this keepsake."
        ok_dialog(self, name, body)

    def _use_beating_root(self, item):
        """Pick one actor to consume a Beating Root (opens their 3rd slot)."""
        import event_horizon as eh

        actors = [self.player] + list(self.player.get("allies", []))
        locked = [a for a in actors if not a.get("acc3_unlocked")]

        dlg = tk.Toplevel(self)
        dlg.title("Beating Root")
        dlg.configure(bg=Theme.BG_DARK)
        dlg.geometry(f"420x{150 + 38 * max(1, len(locked))}")
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(
            dlg, text="Whose third accessory slot should open?",
            bg=Theme.BG_DARK, fg=Theme.TEXT, font=Theme.FONT_BOLD,
            wraplength=380, justify=tk.CENTER,
        ).pack(pady=(10, 4))
        tk.Label(
            dlg, text=("The root is consumed — the chosen actor keeps the "
                       "unlock forever, even at home in the house."),
            bg=Theme.BG_DARK, fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL,
            wraplength=380, justify=tk.CENTER,
        ).pack(pady=(0, 6))

        def choose(actor):
            self.sm.log(eh.consume_beating_root(self.player, actor))
            dlg.destroy()
            self._refresh_all()

        if locked:
            for actor in locked:
                name = "You" if actor is self.player else display_name(actor)
                self.styled_button(
                    dlg, text=name, width=30,
                    command=lambda a=actor: choose(a),
                ).pack(pady=2)
        else:
            tk.Label(dlg, text="Every actor already carries the root.",
                     bg=Theme.BG_DARK, fg=Theme.TEXT_DIM,
                     font=Theme.FONT_SMALL).pack(pady=8)
        self.styled_button(dlg, text="Cancel", command=dlg.destroy).pack(pady=(8, 6))

    def _use_item(self, item):
        """Use a consumable/utility item."""
        from inventory import use_consumable, remove_item_by_reference, is_combat_only_item
        if is_combat_only_item(item):
            self.sm.log(f"{item['name']} can only be used in combat.")
            return
        msg = use_consumable(self.player, item, combat_state=None)
        self.sm.log(msg)
        remove_item_by_reference(self.player, item)
        self._refresh_all()

    def _drop_item(self, item):
        """Drop an item from inventory. Confirms for rare+ items. Key/unique items cannot be dropped."""
        if item.get("type") in ("key_item", "crafting_material"):
            self.sm.log("Key items cannot be dropped.")
            return
        if self._is_unique_item(item):
            self.sm.log("Unique items cannot be dropped.")
            return
        rarity = item.get("rarity", "common")
        if rarity in ("rare", "epic", "legendary", "mythic"):
            from gui.widgets.confirm_dialog import confirm_dialog
            confirm_dialog(
                parent=self,
                title="Drop Rare Item?",
                message=f"Are you sure you want to drop {item['name']} ({rarity})?\nThis cannot be undone.",
                on_yes=lambda: self._do_drop(item),
            )
        else:
            self._do_drop(item)

    def _do_drop(self, item):
        """Actually perform the drop."""
        from inventory import remove_item_by_reference
        remove_item_by_reference(self.player, item, item.get("count", 1))
        self.sm.log(f"Dropped {item['name']}.")
        self._refresh_all()

    def _unequip_ally_slot(self, ally, slot):
        """Unequip a slot on an ally."""
        from combat.ally import unequip_ally_slot
        result = unequip_ally_slot(ally, slot, self.player)
        self._handle_unequip_result(result)
        self._refresh_all()

    def _handle_unequip_result(self, result):
        """Log an unequip result; pop up a warning window if inventory is full."""
        if result and "inventory is full" in result.lower():
            from gui.widgets.confirm_dialog import ok_dialog
            self.sm.log(result)
            ok_dialog(
                parent=self,
                title="Inventory Full",
                message=(
                    f"{result}\n\n"
                    "Unequip failed. Drop or sell an item from your Bag "
                    "to make room, then try again."
                ),
            )
            return
        self.sm.log(result if isinstance(result, str) else "Done.")

    def _prompt_accessory_choice(self, item, target="player", ally=None):
        """Prompt user to choose which accessory slot to replace."""
        if target == "player":
            eq = self.player.get("equipped", {})
            unlocked3 = bool(self.player.get("acc3_unlocked"))
        else:
            eq = ally.get("equipped", {})
            unlocked3 = bool(ally.get("acc3_unlocked"))
        acc1 = eq.get("accessory1")
        acc2 = eq.get("accessory2")
        acc3 = eq.get("accessory3") if unlocked3 else None

        dlg = tk.Toplevel(self)
        dlg.title("Choose Accessory Slot")
        dlg.configure(bg=Theme.BG_DARK)
        dlg.geometry("400x240" if unlocked3 else "400x200")
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(
            dlg, text=f"All accessory slots occupied. Replace which?",
            bg=Theme.BG_DARK, fg=Theme.TEXT, font=Theme.FONT_BOLD,
        ).pack(pady=8)

        def choose(slot):
            if target == "player":
                # Remove from inventory first
                try:
                    idx = next(i for i, itm in enumerate(self.player.get("inventory", [])) if itm is item)
                    self.player["inventory"].pop(idx)
                except (StopIteration, IndexError):
                    pass

                from inventory import equip_item
                result = equip_item(self.player, item, target_slot=slot)
                if result is False:
                    self.player.setdefault("inventory", []).append(item)
                    self.sm.log(f"Cannot equip {item['name']} — inventory full.")
                else:
                    self.sm.log(f"Equipped {item['name']} in {slot}.")
            else:
                # equip_ally_item handles inventory removal internally
                from combat.ally import equip_ally_item
                result = equip_ally_item(ally, item, self.player, target_slot=slot)
                self.sm.log(result if isinstance(result, str) else f"Equipped {item['name']} on {display_name(ally)}.")

            dlg.destroy()
            self._refresh_all()

        btn1_text = f"Replace {acc1['name']}" if acc1 else "Accessory 1"
        btn2_text = f"Replace {acc2['name']}" if acc2 else "Accessory 2"

        self.styled_button(dlg, text=btn1_text, command=lambda: choose("accessory1")).pack(pady=4)
        self.styled_button(dlg, text=btn2_text, command=lambda: choose("accessory2")).pack(pady=4)
        if unlocked3:
            btn3_text = f"Replace {acc3['name']}" if acc3 else "Accessory 3"
            self.styled_button(dlg, text=btn3_text, command=lambda: choose("accessory3")).pack(pady=4)
        self.styled_button(dlg, text="Cancel", command=dlg.destroy).pack(pady=4)

    # ═══════════════════════════════════════════════════════════════════════
    #  Navigation / Refresh
    # ═══════════════════════════════════════════════════════════════════════

    def _refresh_all(self):
        self._refresh_stats_tab()
        self._refresh_bag_tab()
        self._refresh_skills_tab()
        self._refresh_allies_tab()
        self._refresh_journal_tab()
        if hasattr(self, "eh_frame"):
            self._refresh_eh_tab()

    def _on_back(self):
        """Return to the previous screen — dismiss overlay or go back in history."""
        if self.is_overlay:
            self.sm.dismiss_overlay()
        else:
            self.sm.go_back()

    def handle_escape(self):
        """Override: Esc dismisses overlay or returns to previous screen."""
        self._on_back()


def _acc_slots_full(eq, acc3_unlocked):
    """True when every accessory slot this actor owns is occupied."""
    if not (eq.get("accessory1") and eq.get("accessory2")):
        return False
    if acc3_unlocked and not eq.get("accessory3"):
        return False
    return True


def _slot_display_name(slot):
    if slot == "accessory1":
        return "Accessory 1"
    if slot == "accessory2":
        return "Accessory 2"
    if slot == "accessory3":
        return "Accessory 3"
    return slot.title()
