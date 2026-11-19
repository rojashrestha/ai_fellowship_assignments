"""Router layer for products (Part 4)."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import product_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.orderdetail_schemas import OrderDetailOut
from app.schemas.product_schemas import ProductCreate, ProductOut, ProductUpdate

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[ProductOut])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info("GET /products skip=%s limit=%s", skip, limit)
    return product_crud.get_products(db, skip=skip, limit=limit)


@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    logger.info("POST /products productCode=%s", payload.productCode)
    return product_crud.create_product(db, payload)


@router.get("/count")
def count_products(db: Session = Depends(get_db)):
    logger.info("GET /products/count")
    return {"count": product_crud.count_products(db)}


@router.get("/{product_code}", response_model=ProductOut)
def get_product(product_code: str, db: Session = Depends(get_db)):
    logger.info("GET /products/%s", product_code)
    return product_crud.get_product(db, product_code)


@router.get("/{product_code}/orderdetails", response_model=List[OrderDetailOut])
def get_product_orderdetails(product_code: str, db: Session = Depends(get_db)):
    logger.info("GET /products/%s/orderdetails", product_code)
    return product_crud.get_product_orderdetails(db, product_code)


@router.put("/{product_code}", response_model=ProductOut)
def update_product(product_code: str, payload: ProductUpdate, db: Session = Depends(get_db)):
    logger.info("PUT /products/%s", product_code)
    return product_crud.update_product(db, product_code, payload)


@router.delete("/{product_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_code: str, db: Session = Depends(get_db)):
    logger.info("DELETE /products/%s", product_code)
    product_crud.delete_product(db, product_code)
