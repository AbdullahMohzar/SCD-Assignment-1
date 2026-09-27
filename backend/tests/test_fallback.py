import pytest
from httpx import AsyncClient

from app.dependencies import get_complaint_service
from app.main import app
from app.providers.triage.simulated import SimulatedTriage
from app.repositories.complaint_repository import ComplaintRepository
from app.services.complaint_service import ComplaintService
from app.services.triage_service import TriageService


@pytest.mark.asyncio
async def test_triage_fallback_on_failing_provider(client: AsyncClient, db_session, mock_cache):
    """MANDATORY TEST (§2.5): Given a provider that always raises,

    POST /api/complaints still returns 201 and triaged_by == 'rules:fallback'.
    """
    # 1. Inject a crashing provider that always raises
    failing_provider = SimulatedTriage(failure_mode="raise")

    def failing_complaint_service_override():
        repo = ComplaintRepository(db_session)
        service = ComplaintService(repo)
        service.cache_provider = mock_cache
        service.triage_service = TriageService(provider=failing_provider)
        service.triage_service.cache = mock_cache
        return service

    app.dependency_overrides[get_complaint_service] = failing_complaint_service_override

    # 2. Issue POST request
    payload = {
        "text": "Water pipeline leaking and flooding main entrance gate",
        "location": "Sector F-7/1, Islamabad",
        "reporter_contact": "+923000000000",
    }
    response = await client.post("/api/complaints", json=payload)

    # 3. Assert resilience contract
    assert response.status_code == 201
    data = response.json()
    assert data["triaged_by"] == "rules:fallback"
    assert data["category"] == "water"
    assert data["priority"] in ["high", "normal"]
    assert "id" in data


@pytest.mark.asyncio
async def test_triage_fallback_on_timeout(client: AsyncClient, db_session, mock_cache):
    """Test fallback when provider encounters a network timeout."""
    timeout_provider = SimulatedTriage(failure_mode="timeout")

    def timeout_service_override():
        repo = ComplaintRepository(db_session)
        service = ComplaintService(repo)
        service.cache_provider = mock_cache
        service.triage_service = TriageService(provider=timeout_provider)
        service.triage_service.cache = mock_cache
        return service

    app.dependency_overrides[get_complaint_service] = timeout_service_override

    payload = {
        "text": "Transformer sparking with smoke coming out near hospital",
        "location": "Civil Hospital Road, Karachi",
    }
    response = await client.post("/api/complaints", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["triaged_by"] == "rules:fallback"
    assert data["category"] == "electricity"
