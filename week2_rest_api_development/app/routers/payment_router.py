"""
Router layer for payments (Part 4). Composite PK: (customerNumber, checkNumber).

As with orderdetails, /customer/{customer_number} and /count are
registered before the generic /{customer_number}/{check_number} pair to
avoid routing ambiguity.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import payment_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.payment_schemas import PaymentCreate, PaymentOut, PaymentUpdate

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[PaymentOut])
def list_payments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info("GET /payments skip=%s limit=%s", skip, limit)
    return payment_crud.get_payments(db, skip=skip, limit=limit)


@router.post("/", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    logger.info(
        "POST /payments customer=%s check=%s", payload.customerNumber, payload.checkNumber
    )
    return payment_crud.create_payment(db, payload)


@router.get("/count")
def count_payments(db: Session = Depends(get_db)):
    logger.info("GET /payments/count")
    return {"count": payment_crud.count_payments(db)}


@router.get("/customer/{customer_number}", response_model=List[PaymentOut])
def get_payments_by_customer(customer_number: int, db: Session = Depends(get_db)):
    logger.info("GET /payments/customer/%s", customer_number)
    return payment_crud.get_payments_by_customer(db, customer_number)


@router.get("/{customer_number}/{check_number}", response_model=PaymentOut)
def get_payment(customer_number: int, check_number: str, db: Session = Depends(get_db)):
    logger.info("GET /payments/%s/%s", customer_number, check_number)
    return payment_crud.get_payment(db, customer_number, check_number)


@router.put("/{customer_number}/{check_number}", response_model=PaymentOut)
def update_payment(
    customer_number: int,
    check_number: str,
    payload: PaymentUpdate,
    db: Session = Depends(get_db),
):
    logger.info("PUT /payments/%s/%s", customer_number, check_number)
    return payment_crud.update_payment(db, customer_number, check_number, payload)


@router.delete("/{customer_number}/{check_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(customer_number: int, check_number: str, db: Session = Depends(get_db)):
    logger.info("DELETE /payments/%s/%s", customer_number, check_number)
    payment_crud.delete_payment(db, customer_number, check_number)
