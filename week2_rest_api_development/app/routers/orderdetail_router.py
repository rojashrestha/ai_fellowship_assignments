"""
Router layer for orderdetails (Part 4). Composite PK: (orderNumber, productCode).

Route order matters here: /order/{order_number}, /product/{product_code},
and /count must be registered before the generic /{order_number}/{product_code}
pair, otherwise a request like GET /orderdetails/order/5 would match the
generic two-segment route first (order_number="order") and fail int
conversion with a 422 instead of reaching the intended handler.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import orderdetail_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.orderdetail_schemas import OrderDetailCreate, OrderDetailOut, OrderDetailUpdate

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[OrderDetailOut])
def list_orderdetails(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info("GET /orderdetails skip=%s limit=%s", skip, limit)
    return orderdetail_crud.get_orderdetails(db, skip=skip, limit=limit)


@router.post("/", response_model=OrderDetailOut, status_code=status.HTTP_201_CREATED)
def create_orderdetail(payload: OrderDetailCreate, db: Session = Depends(get_db)):
    logger.info(
        "POST /orderdetails order=%s product=%s", payload.orderNumber, payload.productCode
    )
    return orderdetail_crud.create_orderdetail(db, payload)


@router.get("/count")
def count_orderdetails(db: Session = Depends(get_db)):
    logger.info("GET /orderdetails/count")
    return {"count": orderdetail_crud.count_orderdetails(db)}


@router.get("/order/{order_number}", response_model=List[OrderDetailOut])
def get_orderdetails_by_order(order_number: int, db: Session = Depends(get_db)):
    logger.info("GET /orderdetails/order/%s", order_number)
    return orderdetail_crud.get_orderdetails_by_order(db, order_number)


@router.get("/product/{product_code}", response_model=List[OrderDetailOut])
def get_orderdetails_by_product(product_code: str, db: Session = Depends(get_db)):
    logger.info("GET /orderdetails/product/%s", product_code)
    return orderdetail_crud.get_orderdetails_by_product(db, product_code)


@router.get("/{order_number}/{product_code}", response_model=OrderDetailOut)
def get_orderdetail(order_number: int, product_code: str, db: Session = Depends(get_db)):
    logger.info("GET /orderdetails/%s/%s", order_number, product_code)
    return orderdetail_crud.get_orderdetail(db, order_number, product_code)


@router.put("/{order_number}/{product_code}", response_model=OrderDetailOut)
def update_orderdetail(
    order_number: int,
    product_code: str,
    payload: OrderDetailUpdate,
    db: Session = Depends(get_db),
):
    logger.info("PUT /orderdetails/%s/%s", order_number, product_code)
    return orderdetail_crud.update_orderdetail(db, order_number, product_code, payload)


@router.delete("/{order_number}/{product_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_orderdetail(order_number: int, product_code: str, db: Session = Depends(get_db)):
    logger.info("DELETE /orderdetails/%s/%s", order_number, product_code)
    orderdetail_crud.delete_orderdetail(db, order_number, product_code)
