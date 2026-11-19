"""CRUD layer for payments (Part 4). Composite PK: (customerNumber, checkNumber)."""

from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud.utils import safe_commit
from app.database import Payment
from app.logger import get_logger
from app.schemas.payment_schemas import PaymentCreate, PaymentUpdate

logger = get_logger(__name__)


def get_payments(db: Session, skip: int = 0, limit: int = 100) -> List[Payment]:
    logger.info("Querying payments skip=%s limit=%s", skip, limit)
    return db.query(Payment).offset(skip).limit(limit).all()


def get_payment(db: Session, customer_number: int, check_number: str) -> Payment:
    payment = (
        db.query(Payment)
        .filter(Payment.customerNumber == customer_number, Payment.checkNumber == check_number)
        .first()
    )
    if payment is None:
        logger.warning(
            "Payment not found: customer=%s check=%s", customer_number, check_number
        )
        raise HTTPException(
            status_code=404,
            detail=f"Payment for customer {customer_number} / check {check_number} not found",
        )
    logger.info("Payment found: customer=%s check=%s", customer_number, check_number)
    return payment


def create_payment(db: Session, data: PaymentCreate) -> Payment:
    payment = Payment(**data.model_dump())
    db.add(payment)
    safe_commit(db, logger, action="create")
    db.refresh(payment)
    logger.info(
        "Payment created: customer=%s check=%s", payment.customerNumber, payment.checkNumber
    )
    return payment


def update_payment(
    db: Session, customer_number: int, check_number: str, data: PaymentUpdate
) -> Payment:
    payment = get_payment(db, customer_number, check_number)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)
    safe_commit(db, logger, action="update")
    db.refresh(payment)
    logger.info("Payment updated: customer=%s check=%s", customer_number, check_number)
    return payment


def delete_payment(db: Session, customer_number: int, check_number: str) -> None:
    payment = get_payment(db, customer_number, check_number)
    db.delete(payment)
    safe_commit(db, logger, action="delete")
    logger.info("Payment deleted: customer=%s check=%s", customer_number, check_number)


def get_payments_by_customer(db: Session, customer_number: int) -> List[Payment]:
    # No 404 here -- a customer with no payments yet returns [].
    logger.info("Querying payments for customer %s", customer_number)
    return db.query(Payment).filter(Payment.customerNumber == customer_number).all()


def count_payments(db: Session) -> int:
    return db.query(Payment).count()
