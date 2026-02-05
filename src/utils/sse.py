import json
import queue
from typing import Any, Dict, List

from common.logger import logger
from scripts.media_server.src.constants import EventType


class MessageAnnouncer:
    def __init__(self) -> None:
        self.listeners: List[queue.Queue[str]] = []
        self.max_listeners = 10

    def listen(self) -> queue.Queue[str]:
        q: queue.Queue[str] = queue.Queue(maxsize=self.max_listeners)
        self.listeners.append(q)
        return q

    def _announce(self, msg: str) -> None:
        # Iterate backwards to remove dead listeners safely
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]

    def announce_event(self, event_type: EventType, payload: Dict[str, Any]) -> None:
        """Wraps the payload in a standard envelope and announces it."""
        msg = {"type": event_type.value, "data": payload}
        logger.debug(f"Announcement: {msg}")

        self._announce(f"data: {json.dumps(msg)}\n\n")
