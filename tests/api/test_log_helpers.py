from app.utils.log_helpers import (
    build_request_log,
    build_response_log,
    format_payload,
    truncate_text,
)


def test_truncate_text():
    assert truncate_text("hello", max_length=10) == "hello"

    long_text = "a" * 20
    result = truncate_text(long_text, max_length=10)
    assert result.startswith("aaaaaaaaaa")
    assert result.endswith("... (truncated)")
    assert len(result) == 10 + len("\n... (truncated)")


def test_truncate_text_handles_non_strings():
    assert truncate_text(12345, max_length=10) == "12345"  # type: ignore


def test_format_payload_json():
    data = {"key": "value"}
    result = format_payload(data)
    assert '"key": "value"' in result
    assert "{\n" in result  # Proves indent=4 worked


def test_format_payload_fallback():
    # A set is not JSON serializable, should fallback to string representation
    data = {"a", "b"}
    result = format_payload(data)
    assert "{'a', 'b'}" in result or "{'b', 'a'}" in result


def test_build_request_log_masks_api_key():
    params = {"query": "test", "apiKey": "secret123"}
    log_str = build_request_log(params=params, body=None)

    assert "secret123" not in log_str
    assert "***" in log_str
    assert "query" in log_str


def test_build_request_log_empty():
    # Should return empty str if no params and no body
    assert build_request_log({}, None) == ""


def test_build_request_log_with_body():
    body = {"name": "John"}
    log_str = build_request_log(params={}, body=body)

    assert "REQUEST:" in log_str
    assert "body:" in log_str
    assert '"name": "John"' in log_str


def test_build_response_log():
    log_str = build_response_log(
        method="POST",
        path="/api/data",
        duration=0.12345,
        data={"status": "success"},
        max_length=500,
    )

    assert "RESPONSE:" in log_str
    assert "POST /api/data" in log_str
    assert "duration: 0.1235s" in log_str  # Note the 4-decimal rounding
    assert '"status": "success"' in log_str
