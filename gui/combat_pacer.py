"""Combat presentation pacing — gives every actor's action a readable beat.

The combat IO bridge (GUICombatIO in combat_screen.py) calls ``after_print``
and ``before_input`` on the ENGINE thread. Pacing the engine — not the GUI —
keeps text, HP bars, and flashes in lockstep (the HUD poller reads live state;
a GUI-side buffer would run ahead of the paced text).

Spec: docs/combat_plan_phase_design.md §7. The wait constants are starting
values — tune after playtest (§7.7). Settings value: gui/settings.py
``combat_pacing`` ∈ {"instant", "fast", "normal", "slow"}.
"""

import re
import threading
import time

# Wait constants in milliseconds at normal speed (doc §7.7).
# Revised 2026-10-04 (playtest): selection phase is instant; the beat lands
# after the player confirms, before the action resolves.
HOLD_ENEMY = 400      # pause after an enemy's "[n/m] Name's Turn:" header
HOLD_PARTY = 180      # pause after a party member's turn header
HOLD_ROUND = 0        # round headers are redundant with the top bar — no beat
STAGGER = 130         # pause after each combat-event line
INPUT_SETTLE = 0      # no settle before prompts — choose/confirm stays snappy
RESOLVE_LEAD = 250    # "confirm → delay → damage": lead-in before the first
                      # combat-event line that follows any player input

SPEED_MULTIPLIERS = {"instant": 0.0, "fast": 0.5, "normal": 1.0, "slow": 2.0}

_SLEEP_SLICE_S = 0.025  # skip/abort checks granularity

# "[2/9] Name's Turn:" — same shape combat_screen uses to drive the flash.
_TURN_HEADER_RE = re.compile(r"\[(\d+)/(\d+)\]\s+(.+?)'s\s+Turn:")

# Light heuristic for "this line reports an action result" — pacing only (the
# combat-screen log filter has its own, stricter classifier). Menu and banner
# lines (leading ">") are excluded separately so skill selection stays instant.
_EVENT_HINTS = ("damage", " dmg", "burning", "poisoned", "stunned",
                "defeated", "silenced", "bleeding", "frozen", "shocked",
                "cursed", "heals", "recovers", "crit")


class CombatPacer:
    """Paces combat output; one instance lives on the GUICombatIO bridge.

    All methods except ``request_skip`` / ``configure`` run on the engine
    thread. ``sleep_fn`` and ``active_fn`` are injectable for headless tests.
    """

    def __init__(self, active_fn=None, sleep_fn=None):
        self.active_fn = active_fn or (lambda: True)
        self.sleep_fn = sleep_fn or time.sleep
        self.party_names = set()
        self.speed_name = "normal"
        self._skip = threading.Event()
        self._skip_active = False  # suppress the remainder of the current beat
        self._lead_pending = False  # arm the confirm→delay→damage lead-in

    # ── Configuration (GUI thread, before the fight starts) ────────────────

    def configure(self, party_names=None, speed=None):
        if party_names is not None:
            self.party_names = {str(n).strip().lower() for n in party_names if n}
        if speed in SPEED_MULTIPLIERS:
            self.speed_name = speed

    @property
    def speed(self):
        return SPEED_MULTIPLIERS.get(self.speed_name, 1.0)

    # ── Engine-thread hooks ─────────────────────────────────────────────────

    def after_print(self, text):
        """Sleep after a chunk has been queued — the beat's hold or stagger.

        Turn/round headers print first (so the gold flash shows during the
        hold); the next header's hold doubles as the previous actor's settle.
        """
        kind, actor = self._classify(text)
        if kind == "round":
            self._begin_beat()
            self._sleep(HOLD_ROUND)
        elif kind == "turn":
            self._begin_beat()
            name = (actor or "").strip().lower()
            self._sleep(HOLD_PARTY if name in self.party_names else HOLD_ENEMY)
        elif kind == "event":
            self._sleep(STAGGER)

    def before_print(self, text):
        """Lead-in beat before the first resolution line after any input.

        Produces the confirm → delay → damage rhythm: prompts appear instantly
        (no selection-phase delays), and the first combat event that follows
        the player's answer pauses once so the action reads as a beat.
        """
        if not self._lead_pending:
            return
        kind, _ = self._classify(text)
        if kind == "event":
            self._lead_pending = False
            self._sleep(RESOLVE_LEAD)

    def mark_input_received(self):
        """The player answered a prompt — arm the resolution lead-in."""
        self._lead_pending = True

    def before_input(self):
        """Before handing an input prompt to the player: clear skips (+ settle)."""
        self._begin_beat()
        self._sleep(INPUT_SETTLE)

    def abort(self):
        """Screen torn down — unblock any in-flight or future sleep instantly."""
        self._skip.set()
        self._skip_active = True

    # ── GUI-thread hook ─────────────────────────────────────────────────────

    def request_skip(self):
        """Player input during pacing: finish the current beat now.

        One request = one beat. Stale requests die at the next header/input
        (``_begin_beat``), so clicks can never skip an unrelated beat.
        """
        self._skip.set()

    # ── Internals ───────────────────────────────────────────────────────────

    def _begin_beat(self):
        self._skip.clear()
        self._skip_active = False

    def _classify(self, text):
        """Return ("round"|"turn"|"event"|"other", actor_name_or_None)."""
        if ">> ROUND" in text:
            return "round", None
        m = _TURN_HEADER_RE.search(text)
        if m:
            return "turn", m.group(3)
        for line in text.splitlines():
            t = line.strip()
            if not t:
                continue
            if t.startswith(">"):
                # Menus, banners, skill descriptions — selection-phase output.
                # Never a pacing event, so choose → confirm stays instant.
                continue
            if "→" in t:
                return "event", None
            low = t.lower()
            if any(h in low for h in _EVENT_HINTS):
                return "event", None
        return "other", None

    def _sleep(self, ms):
        total = ms * self.speed / 1000.0
        while total > 0:
            if not self.active_fn():
                return
            if self._skip_active:
                return
            if self._skip.is_set():
                # Consume: this beat's remaining waits are suppressed.
                self._skip.clear()
                self._skip_active = True
                return
            step = min(_SLEEP_SLICE_S, total)
            self.sleep_fn(step)
            total -= step
