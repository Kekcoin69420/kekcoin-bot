from unittest.mock import MagicMock, patch

from commands.define import _format, _lookup, _terms


def _mock_client(responses: list):
    """Build a mock httpx.Client that returns JSON list responses in order."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()
    mock_client.get.side_effect = [
        MagicMock(json=MagicMock(return_value=r), raise_for_status=MagicMock(return_value=None))
        for r in responses
    ]
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    return mock_client


def test_format_includes_origin_and_related():
    text = _format({
        "id": "kek",
        "term": "kek",
        "definition": "laughter.",
        "origin": "wow",
        "related": ["topkek"],
    })
    assert "kek" in text
    assert "laughter." in text
    assert "origin: wow" in text
    assert "topkek" in text


def test_lookup_by_id():
    row = {"id": "kek", "term": "kek", "definition": "laughter."}
    with patch("commands.define.httpx.Client", return_value=_mock_client([[row]])):
        assert _lookup("kek") == row


def test_lookup_by_partial_term():
    row = {"id": "wagmi", "term": "wagmi", "definition": "we all gonna make it."}
    with patch("commands.define.httpx.Client") as mock_cls:
        mock_cls.return_value = _mock_client([[], [], [], [row]])
        assert _lookup("wag") == row


def test_lookup_miss_returns_none():
    with patch("commands.define.httpx.Client", return_value=_mock_client([[], [], [], []])):
        assert _lookup("nope") is None


def test_terms_returns_sorted_names():
    rows = [{"term": "based"}, {"term": "kek"}]
    with patch("commands.define.httpx.Client", return_value=_mock_client([rows])):
        assert _terms() == ["based", "kek"]