"""Router layer for orders (Part 4)."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import order_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.order_schemas import OrderCreate, OrderOut, OrderUpdate
from app.schemas.orderdetail_schemas import OrderDetailOut

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[OrderOut])
def list_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info("GET /orders skip=%s limit=%s", skip, limit)
    return order_crud.get_orders(db, skip=skip, limit=limit)


@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    logger.info("POST /orders orderNumber=%s", payload.orderNumber)
    return order_crud.create_order(db, payload)


@router.get("/count")
def count_orders(db: Session = Depends(get_db)):
    logger.info("GET /orders/count")
    return {"count": order_crud.count_orders(db)}


@router.get("/customer/{customer_number}", response_model=List[OrderOut])
def get_orders_by_customer(customer_number: int, db: Session = Depends(get_db)):
    logger.info("GET /orders/customer/%s", customer_number)
    return order_crud.get_orders_by_customer(db, customer_number)


@router.get("/{order_number}", response_model=OrderOut)
def get_order(order_number: int, db: Session = Depends(get_db)):
    logger.info("GET /orders/%s", order_number)
    return order_crud.get_order(db, order_number)


@router.get("/{order_number}/orderdetails", response_model=List[OrderDetailOut])
def get_order_orderdetails(order_number: int, db: Session = Depends(get_db)):
    logger.info("GET /orders/%s/orderdetails", order_number)
    return order_crud.get_order_orderdetails(db, order_number)


@router.put("/{order_number}", response_model=OrderOut)
def update_order(order_number: int, payload: OrderUpdate, db: Session = Depends(get_db)):
    logger.info("PUT /orders/%s", order_number)
    return order_crud.update_order(db, order_number, payload)


@router.delete("/{order_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_number: int, db: Session = Depends(get_db)):
    logger.info("DELETE /orders/%s", order_number)
    order_crud.delete_order(db, order_number)
