import json
from unittest.mock import patch

from scripts.media_server.app.constants import EventType
from scripts.media_server.app.utils.scraper import expand_collection_urls
from scripts.media_server.app.utils.sse import event_generator


def test_stream_generator_logic(announcer):
    """
    Verify that the event generator yields formatted SSE messages.
    """
    test_payload = {"id": 99, "status": "testing"}

    messages = announcer.listen()
    gen = event_generator(messages)
    announcer.announce(EventType.UPDATE, test_payload)

    # Since the queue already holds the item, next() returns immediately.
    sse_message = next(gen)

    # SSE format is "data: <json>\n\n"
    assert "data:" in sse_message

    # Clean up the string to parse JSON
    json_part = sse_message.replace("data: ", "").strip()
    data = json.loads(json_part)

    assert data["type"] == EventType.UPDATE.value
    assert data["data"]["id"] == 99


def test_expand_collection_urls_depth_limit():
    """Ensure recursion stops at depth 3."""
    with patch("scripts.media_server.app.utils.scraper.run_command") as mock_run:
        # If it didn't stop, it would call run_command indefinitely

        result = expand_collection_urls("http://test.com", depth=4)
        assert result == []
        assert mock_run.call_count == 0
