"""
gui/screens/inventory_screen.py — Tabbed inventory, stats, skills, allies, and bounties.

Replaces the terminal-based inventory_ui.py with a full GUI using tkinter's Notebook.
"""

import tkinter as tk
from tkinter import ttk

from gui.screens.base_screen import BaseScreen
from gui.theme import Theme


class InventoryScreen(BaseScreen):
    """
    Tabbed inventory interface.

    Tabs:
        1. Stats & Equipment
        2. Bag
        3. Skills
        4. Allies
        5. Bounties

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
        self._build_bounties_tab()

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

        # ── Equipment ────────────────────────────────────────────────────────
        eq_frame = tk.LabelFrame(
            inner, text=" Equipment ", bg=Theme.BG_DARK, fg=Theme.TEXT,
            font=Theme.FONT_BOLD, highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        eq_frame.pack(fill=tk.X, pady=4, padx=4)

        for slot in ["weapon", "armor", "accessory1", "accessory2"]:
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

                self.styled_button(
                    row, text="Unequip", width=8,
                    command=lambda s=slot: self._unequip_slot(s),
                ).pack(side=tk.RIGHT)
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
                self.log(f"Select an item in Bag to equip to {ally['name']}'s {_slot_display_name(slot_name)}.")
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

        from inventory import get_inventory_caps, count_inventory
        eq_cap, other_cap = get_inventory_caps(self.player)
        eq_count, other_count = count_inventory(self.player)

        cap_text = f"Equipment: {eq_count}/{eq_cap}  |  Items: {other_count}/{other_cap}"
        self.styled_label(self.bag_frame, text=cap_text).pack(anchor=tk.W, pady=(4, 8))

        # ── Scrollable container ─────────────────────────────────────────────
        scroll = tk.Scrollbar(self.bag_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(self.bag_frame, bg=Theme.BG_DARK, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=canvas.yview)
        canvas.config(yscrollcommand=scroll.set)

        inner = tk.Frame(canvas, bg=Theme.BG_DARK)
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
            canvas.config(scrollregion=canvas.bbox("all"))

        inner.bind("<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", _on_configure)

        # ── Equipment list ───────────────────────────────────────────────────
        from inventory import get_sorted_equipment
        equip_items = get_sorted_equipment(self.player)
        if equip_items:
            eq_frame = tk.LabelFrame(
                inner, text=" Equipment ", bg=Theme.BG_DARK, fg=Theme.TEXT,
                font=Theme.FONT_BOLD, highlightthickness=1,
                highlightbackground=Theme.BORDER,
            )
            eq_frame.pack(fill=tk.X, pady=4, padx=4)

            for item in equip_items:
                self._render_bag_item(eq_frame, item, is_equip=True)

        # ── Other items ──────────────────────────────────────────────────────
        from inventory import get_sorted_items, get_key_items
        items = get_sorted_items(self.player)
        if items:
            it_frame = tk.LabelFrame(
                inner, text=" Items ", bg=Theme.BG_DARK, fg=Theme.TEXT,
                font=Theme.FONT_BOLD, highlightthickness=1,
                highlightbackground=Theme.BORDER,
            )
            it_frame.pack(fill=tk.X, pady=4, padx=4)

            for item in items:
                self._render_bag_item(it_frame, item, is_equip=False)

        # ── Key Items ────────────────────────────────────────────────────────
        key_items = get_key_items(self.player)
        if key_items:
            key_frame = tk.LabelFrame(
                inner, text=" Key Items ", bg=Theme.BG_DARK, fg=Theme.TEXT,
                font=Theme.FONT_BOLD, highlightthickness=1,
                highlightbackground=Theme.BORDER,
            )
            key_frame.pack(fill=tk.X, pady=4, padx=4)

            for item in key_items:
                self._render_bag_item(key_frame, item, is_equip=False, is_key=True)

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
            type_label = "Key Item" if item_type in ("key_item", "crafting_material") else item_type
            text = f"{item['name']}{count_str}  ({type_label})"

        row = tk.Frame(parent, bg=Theme.BG_DARK)
        row.pack(fill=tk.X, padx=6, pady=(2, 0))

        tk.Label(
            row, text=text, bg=Theme.BG_DARK, fg=color,
            font=Theme.FONT, anchor=tk.W,
        ).pack(side=tk.LEFT)

        # Key items and crafting materials cannot be dropped, sold, or used
        if is_key:
            sep = tk.Frame(parent, height=1, bg=Theme.BORDER)
            sep.pack(fill=tk.X, padx=10, pady=0)
            return

        if is_equip:
            self.styled_button(
                row, text="Equip", width=6,
                command=lambda it=item: self._equip_item(it),
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
            tab_label = f" {ally.get('name', 'Ally')} "
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
            f"=== {ally.get('name', 'Ally')} "
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

        # ── Equipment ────────────────────────────────────────────────────────
        eq_frame = tk.LabelFrame(
            inner, text=" Equipment ", bg=Theme.BG_DARK, fg=Theme.TEXT,
            font=Theme.FONT_BOLD, highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        eq_frame.pack(fill=tk.X, pady=4, padx=4)

        for slot in ["weapon", "armor", "accessory1", "accessory2"]:
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

                self.styled_button(
                    row, text="Unequip", width=8,
                    command=lambda a=ally, s=slot: self._unequip_ally_slot(a, s),
                ).pack(side=tk.RIGHT)
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
        )
        skill_lines = []
        for sid in ally.get("innate_skills", []):
            sdef = get_innate_skill_def(sid)
            if sdef:
                m = get_ally_skill_mastery_level(ally, sid)
                stars = "★" * m if m > 0 else ""
                cd = ally.get("skill_cooldowns", {}).get(sid, 0)
                cd_str = f" [CD: {cd}]" if cd > 0 else ""
                skill_lines.append(f"[Innate] {sdef['name']}{cd_str} {stars}")
        for sid in ally.get("learned_skills", []):
            sdef = get_learnable_skill_def(sid)
            if sdef:
                m = get_ally_skill_mastery_level(ally, sid)
                stars = "★" * m if m > 0 else ""
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
    #  TAB 5 — Bounties
    # ═══════════════════════════════════════════════════════════════════════

    def _build_bounties_tab(self):
        self.bounties_frame = tk.Frame(self.notebook, bg=Theme.BG_DARK)
        self.notebook.add(self.bounties_frame, text=" Bounties ")
        self.bounties_frame.grid_columnconfigure(0, weight=1)
        self._refresh_bounties_tab()

    def _refresh_bounties_tab(self):
        for w in self.bounties_frame.winfo_children():
            w.destroy()

        if not self.player:
            self.styled_label(self.bounties_frame, text="No player data.").pack(pady=20)
            return

        bounties = self.player.get("active_bounties", [])
        if not bounties:
            self.styled_label(self.bounties_frame, text="No active bounties.").pack(pady=20)
            return

        for b in bounties:
            current = b.get("current", 0)
            required = b["required"]
            days_left = b["deadline"] - self.player.get("day", 1)
            ready = current >= required

            frame = tk.LabelFrame(
                self.bounties_frame,
                text=f" {b['target_name']} ",
                bg=Theme.BG_DARK,
                fg=Theme.BUFF_POSITIVE if ready else Theme.TEXT,
                font=Theme.FONT_BOLD,
                highlightthickness=1,
                highlightbackground=Theme.BORDER,
            )
            frame.pack(fill=tk.X, pady=4, padx=4)

            status = "✓ READY TO CLAIM" if ready else f"{current}/{required}"
            self.styled_label(
                frame, text=f"Progress: {status}",
                fg=Theme.BUFF_POSITIVE if ready else Theme.TEXT,
            ).pack(anchor=tk.W, padx=6, pady=2)
            self.styled_label(frame, text=f"Expires in {days_left} days").pack(
                anchor=tk.W, padx=6, pady=2
            )

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
            if item.get("slot") == "accessory" and slot_hint not in ("accessory1", "accessory2"):
                eq = ally.get("equipped", {})
                if eq.get("accessory1") and eq.get("accessory2"):
                    self._prompt_accessory_choice(item, target="ally", ally=ally)
                    return

            from combat.ally import equip_ally_item
            result = equip_ally_item(ally, item, self.player, target_slot=slot_hint)
            self.sm.log(result if isinstance(result, str) else f"Equipped {item['name']} on {ally['name']}.")
            self._refresh_all()
            return

        # ── Player path (original) ───────────────────────────────────────
        from inventory import equip_item

        # Handle accessory slot selection
        if item.get("slot") == "accessory":
            eq = self.player.get("equipped", {})
            if eq.get("accessory1") and eq.get("accessory2"):
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
        self.sm.log(result if isinstance(result, str) else f"Unequipped {slot}.")
        self._refresh_all()

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
        if item.get("unique"):
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
        self.sm.log(result if isinstance(result, str) else f"Unequipped {ally['name']}'s {slot}.")
        self._refresh_all()

    def _prompt_accessory_choice(self, item, target="player", ally=None):
        """Prompt user to choose which accessory slot to replace."""
        if target == "player":
            eq = self.player.get("equipped", {})
            acc1 = eq.get("accessory1")
            acc2 = eq.get("accessory2")
        else:
            acc1 = ally.get("equipped", {}).get("accessory1")
            acc2 = ally.get("equipped", {}).get("accessory2")

        dlg = tk.Toplevel(self)
        dlg.title("Choose Accessory Slot")
        dlg.configure(bg=Theme.BG_DARK)
        dlg.geometry("400x200")
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(
            dlg, text=f"Both accessory slots occupied. Replace which?",
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
                self.sm.log(result if isinstance(result, str) else f"Equipped {item['name']} on {ally['name']}.")

            dlg.destroy()
            self._refresh_all()

        btn1_text = f"Replace {acc1['name']}" if acc1 else "Accessory 1"
        btn2_text = f"Replace {acc2['name']}" if acc2 else "Accessory 2"

        self.styled_button(dlg, text=btn1_text, command=lambda: choose("accessory1")).pack(pady=4)
        self.styled_button(dlg, text=btn2_text, command=lambda: choose("accessory2")).pack(pady=4)
        self.styled_button(dlg, text="Cancel", command=dlg.destroy).pack(pady=4)

    # ═══════════════════════════════════════════════════════════════════════
    #  Navigation / Refresh
    # ═══════════════════════════════════════════════════════════════════════

    def _refresh_all(self):
        self._refresh_stats_tab()
        self._refresh_bag_tab()
        self._refresh_skills_tab()
        self._refresh_allies_tab()
        self._refresh_bounties_tab()

    def _on_back(self):
        """Return to the previous screen — dismiss overlay or go back in history."""
        if self.is_overlay:
            self.sm.dismiss_overlay()
        else:
            self.sm.go_back()

    def handle_escape(self):
        """Override: Esc dismisses overlay or returns to previous screen."""
        self._on_back()


def _slot_display_name(slot):
    if slot == "accessory1":
        return "Accessory 1"
    if slot == "accessory2":
        return "Accessory 2"
    return slot.title()
