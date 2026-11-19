"""CRUD layer for orders (Part 4)."""

from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud.utils import safe_commit
from app.database import Order, OrderDetail
from app.logger import get_logger
from app.schemas.order_schemas import OrderCreate, OrderUpdate

logger = get_logger(__name__)


def get_orders(db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
    logger.info("Querying orders skip=%s limit=%s", skip, limit)
    return db.query(Order).offset(skip).limit(limit).all()


def get_order(db: Session, order_number: int) -> Order:
    order = db.query(Order).filter(Order.orderNumber == order_number).first()
    if order is None:
        logger.warning("Order not found: %s", order_number)
        raise HTTPException(status_code=404, detail=f"Order {order_number} not found")
    logger.info("Order found: %s", order_number)
    return order


def create_order(db: Session, data: OrderCreate) -> Order:
    order = Order(**data.model_dump())
    db.add(order)
    safe_commit(db, logger, action="create")
    db.refresh(order)
    logger.info("Order created: %s", order.orderNumber)
    return order


def update_order(db: Session, order_number: int, data: OrderUpdate) -> Order:
    order = get_order(db, order_number)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(order, field, value)
    safe_commit(db, logger, action="update")
    db.refresh(order)
    logger.info("Order updated: %s", order_number)
    return order


def delete_order(db: Session, order_number: int) -> None:
    order = get_order(db, order_number)
    db.delete(order)
    # Fails with 409 if orderdetails rows still reference this order.
    safe_commit(db, logger, action="delete")
    logger.info("Order deleted: %s", order_number)


def get_order_orderdetails(db: Session, order_number: int) -> List[OrderDetail]:
    get_order(db, order_number)  # 404s if the order itself doesn't exist
    logger.info("Querying line items for order %s", order_number)
    return db.query(OrderDetail).filter(OrderDetail.orderNumber == order_number).all()


def get_orders_by_customer(db: Session, customer_number: int) -> List[Order]:
    # Intentionally does not 404 -- a customer with zero orders is normal
    # and should return [], per the assignment's explicit instruction.
    logger.info("Querying orders for customer %s", customer_number)
    return db.query(Order).filter(Order.customerNumber == customer_number).all()


def count_orders(db: Session) -> int:
    return db.query(Order).count()
