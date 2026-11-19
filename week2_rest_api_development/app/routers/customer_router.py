"""Router layer for customers (Task 2 / Part 4)."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import customer_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.customer_schemas import CustomerCreate, CustomerOut, CustomerUpdate
from app.schemas.order_schemas import OrderOut
from app.schemas.payment_schemas import PaymentOut

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[CustomerOut])
def list_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info("GET /customers skip=%s limit=%s", skip, limit)
    return customer_crud.get_customers(db, skip=skip, limit=limit)


@router.post("/", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    logger.info("POST /customers customerNumber=%s", payload.customerNumber)
    return customer_crud.create_customer(db, payload)


@router.get("/count")
def count_customers(db: Session = Depends(get_db)):
    logger.info("GET /customers/count")
    return {"count": customer_crud.count_customers(db)}


@router.get("/{customer_number}", response_model=CustomerOut)
def get_customer(customer_number: int, db: Session = Depends(get_db)):
    logger.info("GET /customers/%s", customer_number)
    return customer_crud.get_customer(db, customer_number)


@router.get("/{customer_number}/orders", response_model=List[OrderOut])
def get_customer_orders(customer_number: int, db: Session = Depends(get_db)):
    logger.info("GET /customers/%s/orders", customer_number)
    return customer_crud.get_customer_orders(db, customer_number)


@router.get("/{customer_number}/payments", response_model=List[PaymentOut])
def get_customer_payments(customer_number: int, db: Session = Depends(get_db)):
    logger.info("GET /customers/%s/payments", customer_number)
    return customer_crud.get_customer_payments(db, customer_number)


@router.put("/{customer_number}", response_model=CustomerOut)
def update_customer(customer_number: int, payload: CustomerUpdate, db: Session = Depends(get_db)):
    logger.info("PUT /customers/%s", customer_number)
    return customer_crud.update_customer(db, customer_number, payload)


@router.delete("/{customer_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_number: int, db: Session = Depends(get_db)):
    logger.info("DELETE /customers/%s", customer_number)
    customer_crud.delete_customer(db, customer_number)
