"""CRUD layer for orderdetails (Part 4). Composite PK: (orderNumber, productCode)."""

from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud.utils import safe_commit
from app.database import OrderDetail
from app.logger import get_logger
from app.schemas.orderdetail_schemas import OrderDetailCreate, OrderDetailUpdate

logger = get_logger(__name__)


def get_orderdetails(db: Session, skip: int = 0, limit: int = 100) -> List[OrderDetail]:
    logger.info("Querying orderdetails skip=%s limit=%s", skip, limit)
    return db.query(OrderDetail).offset(skip).limit(limit).all()


def get_orderdetail(db: Session, order_number: int, product_code: str) -> OrderDetail:
    detail = (
        db.query(OrderDetail)
        .filter(OrderDetail.orderNumber == order_number, OrderDetail.productCode == product_code)
        .first()
    )
    if detail is None:
        logger.warning("Order detail not found: order=%s product=%s", order_number, product_code)
        raise HTTPException(
            status_code=404,
            detail=f"Order detail for order {order_number} / product {product_code} not found",
        )
    logger.info("Order detail found: order=%s product=%s", order_number, product_code)
    return detail


def create_orderdetail(db: Session, data: OrderDetailCreate) -> OrderDetail:
    detail = OrderDetail(**data.model_dump())
    db.add(detail)
    safe_commit(db, logger, action="create")
    db.refresh(detail)
    logger.info("Order detail created: order=%s product=%s", detail.orderNumber, detail.productCode)
    return detail


def update_orderdetail(
    db: Session, order_number: int, product_code: str, data: OrderDetailUpdate
) -> OrderDetail:
    detail = get_orderdetail(db, order_number, product_code)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(detail, field, value)
    safe_commit(db, logger, action="update")
    db.refresh(detail)
    logger.info("Order detail updated: order=%s product=%s", order_number, product_code)
    return detail


def delete_orderdetail(db: Session, order_number: int, product_code: str) -> None:
    detail = get_orderdetail(db, order_number, product_code)
    db.delete(detail)
    safe_commit(db, logger, action="delete")
    logger.info("Order detail deleted: order=%s product=%s", order_number, product_code)


def get_orderdetails_by_order(db: Session, order_number: int) -> List[OrderDetail]:
    # No 404 here -- an order with no line items yet returns [].
    logger.info("Querying line items for order %s", order_number)
    return db.query(OrderDetail).filter(OrderDetail.orderNumber == order_number).all()


def get_orderdetails_by_product(db: Session, product_code: str) -> List[OrderDetail]:
    logger.info("Querying order lines containing product %s", product_code)
    return db.query(OrderDetail).filter(OrderDetail.productCode == product_code).all()


def count_orderdetails(db: Session) -> int:
    return db.query(OrderDetail).count()
