import json
import queue
from typing import Any, Dict, List

from colorama import Fore, Style

from app.constants import EventType
from app.utils.logger import logger
from app.utils.tools import recursive_camelize


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
        raw_msg = {"type": event_type.value, "data": payload}
        camel_msg = recursive_camelize(raw_msg)

        logger.info(
            f"{Fore.LIGHTBLUE_EX}ANNOUNCEMENT:\n{Fore.LIGHTBLACK_EX}"
            f"{json.dumps(camel_msg, indent=4)}{Style.RESET_ALL}"
        )

        # SSE Standard format: "data: <json>\n\n"
        msg_fmt = f"data: {json.dumps(camel_msg)}\n\n"

        # Iterate backwards to safely delete while looping
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg_fmt)
            except queue.Full:
                del self.listeners[i]
