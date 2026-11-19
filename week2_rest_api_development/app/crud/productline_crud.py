"""CRUD layer for productlines (Part 4)."""

from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud.utils import safe_commit
from app.database import Product, ProductLine
from app.logger import get_logger
from app.schemas.productline_schemas import ProductLineCreate, ProductLineUpdate

logger = get_logger(__name__)


def get_productlines(db: Session, skip: int = 0, limit: int = 100) -> List[ProductLine]:
    logger.info("Querying productlines skip=%s limit=%s", skip, limit)
    return db.query(ProductLine).offset(skip).limit(limit).all()


def get_productline(db: Session, product_line: str) -> ProductLine:
    line = db.query(ProductLine).filter(ProductLine.productLine == product_line).first()
    if line is None:
        logger.warning("Product line not found: %s", product_line)
        raise HTTPException(status_code=404, detail=f"Product line '{product_line}' not found")
    logger.info("Product line found: %s", product_line)
    return line


def create_productline(db: Session, data: ProductLineCreate) -> ProductLine:
    line = ProductLine(**data.model_dump())
    db.add(line)
    safe_commit(db, logger, action="create")
    db.refresh(line)
    logger.info("Product line created: %s", line.productLine)
    return line


def update_productline(db: Session, product_line: str, data: ProductLineUpdate) -> ProductLine:
    line = get_productline(db, product_line)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(line, field, value)
    safe_commit(db, logger, action="update")
    db.refresh(line)
    logger.info("Product line updated: %s", product_line)
    return line


def delete_productline(db: Session, product_line: str) -> None:
    line = get_productline(db, product_line)
    db.delete(line)
    # If products still reference this line, safe_commit turns the FK
    # violation into a 409 Conflict instead of a raw 500 error.
    safe_commit(db, logger, action="delete")
    logger.info("Product line deleted: %s", product_line)


def get_productline_products(db: Session, product_line: str) -> List[Product]:
    get_productline(db, product_line)  # 404s if the line itself doesn't exist
    logger.info("Querying products for product line %s", product_line)
    return db.query(Product).filter(Product.productLine == product_line).all()


def count_productlines(db: Session) -> int:
    return db.query(ProductLine).count()
