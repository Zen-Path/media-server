import json
import queue
from typing import Any, Dict, List

from common.logger import logger
from scripts.media_server.app.constants import EventType


class MessageAnnouncer:
    """
    Handles subscriptions for SSE.
    """

    def __init__(self) -> None:
        self.listeners: List[queue.Queue] = []
        self.msg_buffer_size = 10

    def listen(self) -> queue.Queue:
        """
        Returns a Queue that receives new messages.
        """
        q: queue.Queue = queue.Queue(maxsize=self.msg_buffer_size)
        self.listeners.append(q)
        return q

    def announce(self, event_type: EventType, payload: Dict[str, Any]) -> None:
        """
        Broadcasts a message to all active listeners.
        Removes listeners that are full (stale or disconnected).
        """
        msg = {"type": event_type.value, "data": payload}
        logger.debug(f"Announcement: {msg}")

        # SSE Standard format: "data: <json>\n\n"
        msg_fmt = f"data: {json.dumps(msg)}\n\n"

        # Iterate backwards to safely delete while looping
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg_fmt)
            except queue.Full:
                del self.listeners[i]
