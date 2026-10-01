import hashlib
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.payment import PaymentTransaction, PaymentGateway, PaymentStatus
from app.db.models.user import User

CREDIT_PACKAGES: Dict[str, Dict[str, Any]] = {
    "starter": {
        "id": "starter",
        "name": "Student / Starter Pack",
        "credits": 2500.0,
        "amount_lkr": 750.00,
        "popular": False,
        "description": "Ideal for students and short document experiments.",
    },
    "standard": {
        "id": "standard",
        "name": "Standard Researcher Pack",
        "credits": 10000.0,
        "amount_lkr": 2500.00,
        "popular": True,
        "description": "Best value for continuous classification and multi-page OCR.",
    },
    "institution": {
        "id": "institution",
        "name": "Institutional / Corpus Pack",
        "credits": 50000.0,
        "amount_lkr": 10000.00,
        "popular": False,
        "description": "High-volume tier for large historical archives and deep datasets.",
    },
}

def generate_payhere_hash(
    merchant_id: str,
    order_id: str,
    amount: float,
    currency: str = "LKR",
    merchant_secret: str = settings.PAYHERE_MERCHANT_SECRET,
) -> str:
    """
    Computes PayHere frontend checkout hash:
    hash = strtoupper(md5(merchant_id + order_id + formatted_amount + currency + strtoupper(md5(merchant_secret))))
    """
    formatted_amount = f"{amount:.2f}"
    secret_hash = hashlib.md5(merchant_secret.encode("utf-8")).hexdigest().upper()
    main_string = f"{merchant_id}{order_id}{formatted_amount}{currency}{secret_hash}"
    return hashlib.md5(main_string.encode("utf-8")).hexdigest().upper()

def verify_payhere_ipn_signature(
    merchant_id: str,
    order_id: str,
    payhere_amount: str,
    payhere_currency: str,
    status_code: str,
    md5sig: str,
    merchant_secret: str = settings.PAYHERE_MERCHANT_SECRET,
) -> bool:
    """
    Verifies PayHere IPN notification signature:
    local_md5sig = strtoupper(md5(merchant_id + order_id + payhere_amount + payhere_currency + status_code + strtoupper(md5(merchant_secret))))
    """
    secret_hash = hashlib.md5(merchant_secret.encode("utf-8")).hexdigest().upper()
    check_string = f"{merchant_id}{order_id}{payhere_amount}{payhere_currency}{status_code}{secret_hash}"
    expected_hash = hashlib.md5(check_string.encode("utf-8")).hexdigest().upper()
    return expected_hash.strip() == md5sig.strip().upper()

class PaymentService:
    @staticmethod
    def get_packages() -> List[Dict[str, Any]]:
        return list(CREDIT_PACKAGES.values())

    @staticmethod
    async def initiate_payhere_order(
        db: AsyncSession,
        user: User,
        package_id: str,
        custom_credits: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Creates a PENDING payment transaction and generates PayHere payment parameters.
        """
        if package_id in CREDIT_PACKAGES:
            pkg = CREDIT_PACKAGES[package_id]
            package_name = pkg["name"]
            credits_amount = pkg["credits"]
            amount_lkr = pkg["amount_lkr"]
        elif package_id == "custom" and custom_credits and custom_credits >= 1000:
            credits_amount = float(custom_credits)
            # Price rate: LKR 0.25 per credit for custom top-ups
            amount_lkr = round(credits_amount * 0.25, 2)
            package_name = f"Custom Pack ({credits_amount:,.0f} Credits)"
        else:
            raise ValueError(f"Invalid package_id: {package_id}")

        order_id = f"LANGID-{uuid.uuid4().hex[:12].upper()}"

        transaction = PaymentTransaction(
            user_id=user.id,
            gateway=PaymentGateway.PAYHERE,
            order_id=order_id,
            package_name=package_name,
            amount_lkr=amount_lkr,
            currency="LKR",
            credits_amount=credits_amount,
            status=PaymentStatus.PENDING,
        )
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        payhere_hash = generate_payhere_hash(
            merchant_id=settings.PAYHERE_MERCHANT_ID,
            order_id=order_id,
            amount=amount_lkr,
            currency="LKR",
            merchant_secret=settings.PAYHERE_MERCHANT_SECRET,
        )

        display_name = user.display_name or user.email.split("@")[0]
        parts = display_name.split()
        first_name = parts[0] if parts else "Customer"
        last_name = parts[1] if len(parts) > 1 else "User"

        return {
            "order_id": order_id,
            "package_name": package_name,
            "credits_amount": credits_amount,
            "amount_lkr": amount_lkr,
            "currency": "LKR",
            "payhere_params": {
                "sandbox": settings.PAYHERE_MODE == "sandbox",
                "merchant_id": settings.PAYHERE_MERCHANT_ID,
                "return_url": f"{settings.FRONTEND_URL}/dashboard/billing/success?order_id={order_id}",
                "cancel_url": f"{settings.FRONTEND_URL}/dashboard/usage?canceled=true",
                "notify_url": f"{settings.FRONTEND_URL}/api/payments/payhere/notify",
                "order_id": order_id,
                "items": f"{package_name} ({credits_amount:,.0f} Credits)",
                "amount": f"{amount_lkr:.2f}",
                "currency": "LKR",
                "hash": payhere_hash,
                "first_name": first_name,
                "last_name": last_name,
                "email": user.email,
                "phone": "0771234567",
                "address": "Colombo",
                "city": "Colombo",
                "country": "Sri Lanka",
            },
        }

    @staticmethod
    async def fulfill_transaction(
        db: AsyncSession,
        transaction: PaymentTransaction,
        payhere_payment_id: Optional[str] = None,
        payment_method: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Atomically marks a payment as COMPLETED and tops up the user's credits.
        Guarded against double-crediting.
        """
        if transaction.status == PaymentStatus.COMPLETED:
            return True

        # Fetch user with lock
        stmt = select(User).where(User.id == transaction.user_id).with_for_update()
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return False

        # Add credits
        user.credits_balance = float(user.credits_balance) + float(transaction.credits_amount)

        # Update transaction
        transaction.status = PaymentStatus.COMPLETED
        if payhere_payment_id:
            transaction.payhere_payment_id = payhere_payment_id
        if payment_method:
            transaction.payment_method = payment_method
        if raw_payload:
            transaction.raw_payload = raw_payload
        transaction.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(transaction)
        await db.refresh(user)
        return True

    @staticmethod
    async def process_payhere_ipn(
        db: AsyncSession,
        form_data: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Processes incoming IPN post from PayHere.
        """
        merchant_id = form_data.get("merchant_id", "")
        order_id = form_data.get("order_id", "")
        payhere_amount = form_data.get("payhere_amount", "")
        payhere_currency = form_data.get("payhere_currency", "LKR")
        status_code = str(form_data.get("status_code", ""))
        md5sig = form_data.get("md5sig", "")
        payment_id = form_data.get("payment_id")
        method = form_data.get("method")

        # 1. Verify Signature
        is_valid = verify_payhere_ipn_signature(
            merchant_id=merchant_id,
            order_id=order_id,
            payhere_amount=payhere_amount,
            payhere_currency=payhere_currency,
            status_code=status_code,
            md5sig=md5sig,
        )
        if not is_valid:
            return False, "Invalid signature"

        # 2. Find Transaction
        stmt = select(PaymentTransaction).where(PaymentTransaction.order_id == order_id)
        result = await db.execute(stmt)
        tx = result.scalar_one_or_none()
        if not tx:
            return False, f"Transaction {order_id} not found"

        # 3. Check status code: 2 = Success, 0 = Pending, -1 = Canceled, -2 = Failed
        if status_code == "2":
            success = await PaymentService.fulfill_transaction(
                db=db,
                transaction=tx,
                payhere_payment_id=payment_id,
                payment_method=method,
                raw_payload=form_data,
            )
            return success, "Payment completed successfully"
        elif status_code == "-1":
            tx.status = PaymentStatus.CANCELLED
            tx.raw_payload = form_data
            await db.commit()
            return True, "Payment marked cancelled"
        else:
            tx.status = PaymentStatus.FAILED
            tx.raw_payload = form_data
            await db.commit()
            return True, f"Payment marked failed (status {status_code})"

    @staticmethod
    async def simulate_sandbox_success(
        db: AsyncSession,
        order_id: str,
        user: User,
    ) -> Tuple[bool, str]:
        """
        Helper for development/demo: verifies the order belongs to the user and
        instantly fulfills it without requiring a public IPN tunnel.
        """
        stmt = select(PaymentTransaction).where(
            PaymentTransaction.order_id == order_id,
            PaymentTransaction.user_id == user.id,
        )
        result = await db.execute(stmt)
        tx = result.scalar_one_or_none()
        if not tx:
            return False, "Order not found or unauthorized"

        if tx.status == PaymentStatus.COMPLETED:
            return True, "Order already fulfilled"

        success = await PaymentService.fulfill_transaction(
            db=db,
            transaction=tx,
            payhere_payment_id=f"TEST-PAY-{uuid.uuid4().hex[:8].upper()}",
            payment_method="SANDBOX_TEST_CARD",
            raw_payload={"simulated": True, "timestamp": datetime.utcnow().isoformat()},
        )
        return success, "Simulated payment successfully fulfilled"

    @staticmethod
    async def get_user_payment_history(
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 20,
    ) -> List[PaymentTransaction]:
        stmt = (
            select(PaymentTransaction)
            .where(PaymentTransaction.user_id == user_id)
            .order_by(PaymentTransaction.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
