from fastapi import APIRouter, Depends
from routers.deps import require_role

router = APIRouter()


@router.get("/admin/dashboard")
async def dashboard(
    user=Depends(require_role("admin"))
):
    return {
        "message": "Welcome admin"
    }