from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, rate_limit_auth
from app.models.user import User
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create-invoice")
async def create_invoice(
    request: Request,
    plan_id: str,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Generate a Telegram Stars invoice link for a plan upgrade."""
    service = PaymentService(db, request.app.state.bot)
    try:
        invoice_link = await service.create_plan_invoice(user, plan_id)
        return {"invoice_link": invoice_link}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"Error creating invoice: {e}")
        raise HTTPException(status_code=500, detail="Error al generar factura")


@router.get("/plans")
async def list_plans(db: AsyncSession = Depends(get_db)):
    """Return available plan information."""
    service = PaymentService(db)
    return service.get_available_plans()
