import pytest
from httpx import AsyncClient

from app.providers.rate_limiter import DistributedRateLimiter, get_rate_limiter


class MockRateLimiter:
    """Mock rate limiter that trips after configured requests."""

    def __init__(self, limit: int = 2):
        self.count = 0
        self.limit = limit

    async def is_allowed(self, client_ip: str):
        self.count += 1
        if self.count > self.limit:
            return False, 45  # 45 seconds remaining
        return True, 0


@pytest.mark.asyncio
async def test_rate_limiter_exceeded_returns_429(client: AsyncClient, monkeypatch):
    mock_limiter = MockRateLimiter(limit=2)
    monkeypatch.setattr("app.routes.complaints.get_rate_limiter", lambda: mock_limiter)

    payload = {
        "text": "Severe road cavity endangering cars on expressway",
        "location": "Expressway KM 14, Rawalpindi",
    }

    # Request 1: allowed
    res1 = await client.post("/api/complaints", json=payload)
    assert res1.status_code == 201

    # Request 2: allowed
    res2 = await client.post("/api/complaints", json=payload)
    assert res2.status_code == 201

    # Request 3: tripped -> 429 Too Many Requests
    res3 = await client.post("/api/complaints", json=payload)
    assert res3.status_code == 429
    assert res3.headers.get("Retry-After") == "45"
    assert "Rate limit exceeded" in res3.json()["detail"]
