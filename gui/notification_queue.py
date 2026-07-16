"""
gui/notification_queue.py — In-game alert / toast system (replaces event prints).

When the player is in the dungeon, day-rollover events are queued and shown
when they return to the city. This system also handles generic toasts for
one-off notifications.
"""

from typing import List, Dict, Any


class NotificationQueue:
    """
    A simple queue for in-game notifications.

    - push(msg): add a notification
    - pop_all(): retrieve and clear all pending notifications
    - peek(): view without clearing
    """

    def __init__(self):
        self._queue: List[Dict[str, Any]] = []

    def push(self, message: str, category: str = "info", duration_ms: int = 3000):
        """
        Add a notification.

        Args:
            message: Text to display.
            category: "info", "warning", "success", "error", "event"
            duration_ms: How long the toast should remain visible.
        """
        self._queue.append({
            "message": message,
            "category": category,
            "duration_ms": duration_ms,
        })

    def pop_all(self) -> List[Dict[str, Any]]:
        """Retrieve all queued notifications and clear the queue."""
        batch = self._queue[:]
        self._queue.clear()
        return batch

    def peek(self) -> List[Dict[str, Any]]:
        """View queued notifications without clearing."""
        return self._queue[:]

    def clear(self):
        """Drop all pending notifications."""
        self._queue.clear()

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def __len__(self) -> int:
        return len(self._queue)
