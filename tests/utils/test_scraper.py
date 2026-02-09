from unittest.mock import patch

from app.utils.scraper import expand_collection_urls


def test_expand_collection_urls_depth_limit():
    """Ensure recursion stops at depth 3."""
    with patch("app.utils.scraper.run_command") as mock_run:
        # If it didn't stop, it would call run_command indefinitely

        result = expand_collection_urls("http://test.com", depth=4)
        assert result == []
        assert mock_run.call_count == 0
