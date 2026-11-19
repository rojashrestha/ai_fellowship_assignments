"""Router layer for productlines (Part 4)."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import productline_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.product_schemas import ProductOut
from app.schemas.productline_schemas import ProductLineCreate, ProductLineOut, ProductLineUpdate

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[ProductLineOut])
def list_productlines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info("GET /productlines skip=%s limit=%s", skip, limit)
    return productline_crud.get_productlines(db, skip=skip, limit=limit)


@router.post("/", response_model=ProductLineOut, status_code=status.HTTP_201_CREATED)
def create_productline(payload: ProductLineCreate, db: Session = Depends(get_db)):
    logger.info("POST /productlines productLine=%s", payload.productLine)
    return productline_crud.create_productline(db, payload)


@router.get("/count")
def count_productlines(db: Session = Depends(get_db)):
    logger.info("GET /productlines/count")
    return {"count": productline_crud.count_productlines(db)}


@router.get("/{product_line}", response_model=ProductLineOut)
def get_productline(product_line: str, db: Session = Depends(get_db)):
    logger.info("GET /productlines/%s", product_line)
    return productline_crud.get_productline(db, product_line)


@router.get("/{product_line}/products", response_model=List[ProductOut])
def get_productline_products(product_line: str, db: Session = Depends(get_db)):
    logger.info("GET /productlines/%s/products", product_line)
    return productline_crud.get_productline_products(db, product_line)


@router.put("/{product_line}", response_model=ProductLineOut)
def update_productline(
    product_line: str, payload: ProductLineUpdate, db: Session = Depends(get_db)
):
    logger.info("PUT /productlines/%s", product_line)
    return productline_crud.update_productline(db, product_line, payload)


@router.delete("/{product_line}", status_code=status.HTTP_204_NO_CONTENT)
def delete_productline(product_line: str, db: Session = Depends(get_db)):
    logger.info("DELETE /productlines/%s", product_line)
    productline_crud.delete_productline(db, product_line)
