import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
import api

MOCK_PAIR_RESPONSE = {
    "pairs": [{
        "priceUsd": "0.00000234",
        "marketCap": 234500,
        "fdv": 234500,
        "liquidity": {"usd": 45100},
        "volume": {"h24": 18200},
        "priceChange": {"h24": 12.4},
        "txns": {"h24": {"buys": 150, "sells": 80}},
    }]
}

@pytest.mark.asyncio
async def test_get_pair_data_returns_parsed_dict():
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_PAIR_RESPONSE
    mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await api.get_pair_data()

    assert result["price"] == pytest.approx(0.00000234)
    assert result["market_cap"] == 234500
    assert result["volume_24h"] == 18200
    assert result["change_24h"] == pytest.approx(12.4)
    assert result["txns_24h"] == 230

@pytest.mark.asyncio
async def test_get_pair_data_returns_none_on_error():
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.RequestError("fail"))
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await api.get_pair_data()

    assert result is None

MOCK_SIGNATURES = [
    {"signature": "sig_new", "blockTime": 1700000002},
    {"signature": "sig_old", "blockTime": 1700000001},
]

@pytest.mark.asyncio
async def test_get_recent_signatures_returns_list():
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": MOCK_SIGNATURES}
    mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await api.get_recent_signatures(limit=2)

    assert result[0]["signature"] == "sig_new"
    assert len(result) == 2

@pytest.mark.asyncio
async def test_get_recent_signatures_returns_empty_on_error():
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.RequestError("fail"))
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await api.get_recent_signatures()

    assert result == []
