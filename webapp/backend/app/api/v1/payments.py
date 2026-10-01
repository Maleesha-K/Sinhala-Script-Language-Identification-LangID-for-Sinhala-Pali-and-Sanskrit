import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.payment import PaymentStatus
from app.dependencies import get_db, get_current_user
from app.schemas.response import BaseResponse, success_response
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])

class CreditPackageResponse(BaseModel):
    id: str
    name: str
    credits: float
    amount_lkr: float
    popular: bool
    description: str

class InitiatePaymentRequest(BaseModel):
    package_id: str = Field(..., description="Package identifier: 'starter', 'standard', 'institution', or 'custom'")
    custom_credits: Optional[float] = Field(None, description="Requested credits if package_id is 'custom'")

class InitiatePaymentResponse(BaseModel):
    order_id: str
    package_name: str
    credits_amount: float
    amount_lkr: float
    currency: str
    payhere_params: Dict[str, Any]

class PaymentTransactionResponse(BaseModel):
    id: uuid.UUID
    order_id: str
    package_name: str
    amount_lkr: float
    currency: str
    credits_amount: float
    status: PaymentStatus
    payment_method: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class ConfirmSandboxRequest(BaseModel):
    order_id: str

@router.get("/packages", response_model=BaseResponse[List[CreditPackageResponse]])
async def list_packages(db: AsyncSession = Depends(get_db)):
    """List available credit top-up packages in LKR dynamically derived from system_config."""
    packages = await PaymentService.get_packages(db)
    return success_response(packages)

@router.post("/payhere/initiate", response_model=BaseResponse[InitiatePaymentResponse])
async def initiate_payhere_payment(
    req: InitiatePaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Initiates a PayHere payment order and returns signed PayHere checkout parameters."""
    try:
        data = await PaymentService.initiate_payhere_order(
            db=db,
            user=current_user,
            package_id=req.package_id,
            custom_credits=req.custom_credits,
        )
        return success_response(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payhere/notify")
async def payhere_ipn_notify(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    PayHere Instant Payment Notification (IPN) webhook.
    Receives form-urlencoded parameters from PayHere servers.
    """
    form_data = await request.form()
    payload = dict(form_data)
    
    success, message = await PaymentService.process_payhere_ipn(db, payload)
    if not success:
        # PayHere expects 200 OK or it will retry. We return 400 only on tampered signatures.
        if "signature" in message.lower():
            raise HTTPException(status_code=400, detail="Invalid signature")
        return Response(content=f"Error: {message}", media_type="text/plain", status_code=200)

    return Response(content="OK", media_type="text/plain", status_code=200)

@router.post("/sandbox/confirm", response_model=BaseResponse[Dict[str, Any]])
async def confirm_sandbox_payment(
    req: ConfirmSandboxRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Development/Sandbox helper: immediately validates and fulfills a test transaction
    when PayHere checkout completes on the client without a public IPN tunnel.
    """
    success, message = await PaymentService.simulate_sandbox_success(
        db=db,
        order_id=req.order_id,
        user=current_user,
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return success_response({"order_id": req.order_id, "message": message, "new_balance": float(current_user.credits_balance)})

@router.get("/history", response_model=BaseResponse[List[PaymentTransactionResponse]])
async def get_payment_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the authenticated user's top-up transaction history."""
    history = await PaymentService.get_user_payment_history(db, current_user.id)
    return success_response(history)
