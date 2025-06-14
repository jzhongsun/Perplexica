from fastapi import APIRouter, Depends
from .service import ConfigService
from .schemas import ConfigResponse, ConfigUpdate

router = APIRouter(prefix="/config", tags=["config"])

@router.get("", response_model=ConfigResponse)
async def get_config(
    config_service: ConfigService = Depends(ConfigService)
) -> ConfigResponse:
    """Get current configuration."""
    return await config_service.get_config()

@router.post("")
async def update_config(
    config_update: ConfigUpdate,
    config_service: ConfigService = Depends(ConfigService)
) -> dict:
    """Update configuration value."""
    await config_service.update_config(config_update)
    return {"status": "success", "message": "Configuration updated"} 