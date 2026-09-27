import uuid

import pytest
from httpx import AsyncClient

from app.schemas.common import Category, Priority, Status


@pytest.mark.asyncio
async def test_create_complaint_success(client: AsyncClient):
    payload = {
        "text": "Major water pipeline burst flooding street since fajr",
        "location": "Street 12, Sector F-8/2, Islamabad",
        "reporter_contact": "+923001234567",
    }
    response = await client.post("/api/complaints", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["text"] == payload["text"]
    assert data["location"] == payload["location"]
    assert data["category"] in [c.value for c in Category]
    assert data["priority"] in [p.value for p in Priority]
    assert data["status"] == Status.OPEN.value
    assert data["triaged_by"] in ["simulated", "rules", "llm:groq"]
    assert "triage_latency_ms" in data
    assert response.headers.get("X-Request-ID") is not None


@pytest.mark.asyncio
async def test_create_complaint_validation_error(client: AsyncClient):
    # Text shorter than 10 characters
    payload = {
        "text": "short",
        "location": "A",  # Also shorter than 3 characters
    }
    response = await client.post("/api/complaints", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "errors" in data
    fields = [err["field"] for err in data["errors"]]
    assert "text" in fields or "location" in fields


@pytest.mark.asyncio
async def test_get_complaint_by_id(client: AsyncClient):
    create_payload = {
        "text": "Streetlight bulb broken causing darkness at night",
        "location": "Sector G-10 Markaz, Islamabad",
    }
    create_res = await client.post("/api/complaints", json=create_payload)
    assert create_res.status_code == 201
    complaint_id = create_res.json()["id"]

    # Fetch existing
    get_res = await client.get(f"/api/complaints/{complaint_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == complaint_id

    # Fetch non-existent
    fake_id = str(uuid.uuid4())
    not_found_res = await client.get(f"/api/complaints/{fake_id}")
    assert not_found_res.status_code == 404


@pytest.mark.asyncio
async def test_list_complaints_and_pagination(client: AsyncClient):
    # Create multiple complaints
    for i in range(5):
        await client.post(
            "/api/complaints",
            json={
                "text": f"Pothole number {i} on main boulevard creating traffic jams",
                "location": f"Lane {i}, Rawalpindi",
            },
        )

    res = await client.get("/api/complaints?page=1&page_size=2")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_status_transitions(client: AsyncClient):
    create_res = await client.post(
        "/api/complaints",
        json={
            "text": "Dangerous sparking transformer near mosque chowk",
            "location": "Jamia Masjid, Lahore",
        },
    )
    complaint_id = create_res.json()["id"]

    # 1. Valid transition: open -> in_progress
    patch_res = await client.patch(
        f"/api/complaints/{complaint_id}/status",
        json={"status": "in_progress"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "in_progress"

    # 2. Invalid transition: in_progress -> open (must return 409 naming transition)
    invalid_res = await client.patch(
        f"/api/complaints/{complaint_id}/status",
        json={"status": "open"},
    )
    assert invalid_res.status_code == 409
    detail = invalid_res.json()["detail"]
    assert "Invalid transition from in_progress to open" in detail

    # 3. Valid transition to terminal: in_progress -> resolved
    resolve_res = await client.patch(
        f"/api/complaints/{complaint_id}/status",
        json={"status": "resolved"},
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "resolved"

    # 4. Terminal cannot transition: resolved -> in_progress -> 409
    terminal_res = await client.patch(
        f"/api/complaints/{complaint_id}/status",
        json={"status": "in_progress"},
    )
    assert terminal_res.status_code == 409


@pytest.mark.asyncio
async def test_stats_and_cache_header(client: AsyncClient):
    # First call: cache miss
    res1 = await client.get("/api/stats")
    assert res1.status_code == 200
    assert res1.headers.get("X-Cache") == "MISS"
    data1 = res1.json()
    assert "total" in data1
    assert "by_category" in data1
    assert "by_priority" in data1

    # Second call: cache hit
    res2 = await client.get("/api/stats")
    assert res2.status_code == 200
    assert res2.headers.get("X-Cache") == "HIT"


@pytest.mark.asyncio
async def test_meta_providers_endpoint(client: AsyncClient):
    res = await client.get("/api/meta/providers")
    assert res.status_code == 200
    data = res.json()
    assert "active_provider" in data
    assert "recent_outcomes" in data


@pytest.mark.asyncio
async def test_health_and_readiness_endpoints(client: AsyncClient):
    # Liveness check does not touch database
    health_res = await client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "alive"

    # Readiness check verifies dependencies
    ready_res = await client.get("/ready")
    # In test environment with sqlite/mock, ready should respond
    assert ready_res.status_code in [200, 503]


@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    res = await client.get("/metrics")
    assert res.status_code == 200
    assert "civicpulse" in res.text or "python_info" in res.text
