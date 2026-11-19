"""CRUD layer for products (Part 4)."""

from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud.utils import safe_commit
from app.database import OrderDetail, Product
from app.logger import get_logger
from app.schemas.product_schemas import ProductCreate, ProductUpdate

logger = get_logger(__name__)


def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    logger.info("Querying products skip=%s limit=%s", skip, limit)
    return db.query(Product).offset(skip).limit(limit).all()


def get_product(db: Session, product_code: str) -> Product:
    product = db.query(Product).filter(Product.productCode == product_code).first()
    if product is None:
        logger.warning("Product not found: %s", product_code)
        raise HTTPException(status_code=404, detail=f"Product {product_code} not found")
    logger.info("Product found: %s", product_code)
    return product


def create_product(db: Session, data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    safe_commit(db, logger, action="create")
    db.refresh(product)
    logger.info("Product created: %s", product.productCode)
    return product


def update_product(db: Session, product_code: str, data: ProductUpdate) -> Product:
    product = get_product(db, product_code)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    safe_commit(db, logger, action="update")
    db.refresh(product)
    logger.info("Product updated: %s", product_code)
    return product


def delete_product(db: Session, product_code: str) -> None:
    product = get_product(db, product_code)
    db.delete(product)
    safe_commit(db, logger, action="delete")
    logger.info("Product deleted: %s", product_code)


def get_product_orderdetails(db: Session, product_code: str) -> List[OrderDetail]:
    get_product(db, product_code)  # 404s if the product itself doesn't exist
    logger.info("Querying order details for product %s", product_code)
    return db.query(OrderDetail).filter(OrderDetail.productCode == product_code).all()


def count_products(db: Session) -> int:
    return db.query(Product).count()
