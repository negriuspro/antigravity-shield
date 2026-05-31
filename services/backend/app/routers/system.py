from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.services.adguard import AdGuardClient

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status")
async def system_status(_=Depends(get_current_user)):
    client = AdGuardClient()
    try:
        ag_status = await client.get_status()
    except Exception as e:
        ag_status = {"error": str(e)}
    return {
        "adguard": ag_status,
        "version": "1.0.0",
        "name": "AntiGravity Shield",
    }


@router.get("/adguard/stats")
async def adguard_stats(_=Depends(get_current_user)):
    client = AdGuardClient()
    return await client.get_stats()


@router.get("/adguard/top")
async def adguard_top(limit: int = 10, _=Depends(get_current_user)):
    client = AdGuardClient()
    return await client.get_top_domains(limit)
