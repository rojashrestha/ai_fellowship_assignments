"""CRUD layer for customers (Task 2 / Part 4)."""

from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud.utils import safe_commit
from app.database import Customer, Order, Payment
from app.logger import get_logger
from app.schemas.customer_schemas import CustomerCreate, CustomerUpdate

logger = get_logger(__name__)


def get_customers(db: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
    logger.info("Querying customers skip=%s limit=%s", skip, limit)
    return db.query(Customer).offset(skip).limit(limit).all()


def get_customer(db: Session, customer_number: int) -> Customer:
    customer = db.query(Customer).filter(Customer.customerNumber == customer_number).first()
    if customer is None:
        logger.warning("Customer not found: %s", customer_number)
        raise HTTPException(status_code=404, detail=f"Customer {customer_number} not found")
    logger.info("Customer found: %s", customer_number)
    return customer


def create_customer(db: Session, data: CustomerCreate) -> Customer:
    customer = Customer(**data.model_dump())
    db.add(customer)
    safe_commit(db, logger, action="create")
    db.refresh(customer)
    logger.info("Customer created: %s", customer.customerNumber)
    return customer


def update_customer(db: Session, customer_number: int, data: CustomerUpdate) -> Customer:
    customer = get_customer(db, customer_number)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    safe_commit(db, logger, action="update")
    db.refresh(customer)
    logger.info("Customer updated: %s", customer_number)
    return customer


def delete_customer(db: Session, customer_number: int) -> None:
    customer = get_customer(db, customer_number)
    db.delete(customer)
    safe_commit(db, logger, action="delete")
    logger.info("Customer deleted: %s", customer_number)


def get_customer_orders(db: Session, customer_number: int) -> List[Order]:
    get_customer(db, customer_number)  # 404s if the customer itself doesn't exist
    logger.info("Querying orders for customer %s", customer_number)
    return db.query(Order).filter(Order.customerNumber == customer_number).all()


def get_customer_payments(db: Session, customer_number: int) -> List[Payment]:
    get_customer(db, customer_number)
    logger.info("Querying payments for customer %s", customer_number)
    return db.query(Payment).filter(Payment.customerNumber == customer_number).all()


def count_customers(db: Session) -> int:
    return db.query(Customer).count()
