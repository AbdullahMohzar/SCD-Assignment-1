from fastapi import APIRouter

from app.schemas.complaint import ProviderMetaResponse
from app.services.triage_service import get_triage_service

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get(
    "/providers",
    response_model=ProviderMetaResponse,
)
async def get_providers_metadata() -> ProviderMetaResponse:
    triage_service = get_triage_service()
    metadata = triage_service.get_metadata()
    return ProviderMetaResponse(
        active_provider=metadata["active_provider"],
        recent_outcomes=metadata["recent_outcomes"],
    )
