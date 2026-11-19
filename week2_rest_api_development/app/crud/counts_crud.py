"""
Standalone count functions used only by the /overall_counts aggregator
(Task 3, Part 2).

Every other crud module's count_x(db) takes a request-scoped session via
Depends(get_db), which is correct for a single, independent request like
GET /customers/count. But /overall_counts runs all eight counts at once
across a thread pool with asyncio.gather(), and a single SQLAlchemy
Session is not safe to use concurrently from multiple threads. So each
function here opens and closes its own short-lived session instead of
receiving one.
"""

from app.database import (
    Customer,
    Employee,
    Office,
    Order,
    OrderDetail,
    Payment,
    Product,
    ProductLine,
    SessionLocal,
)
from app.logger import get_logger

logger = get_logger(__name__)


def count_customers() -> int:
    db = SessionLocal()
    try:
        return db.query(Customer).count()
    finally:
        db.close()


def count_orders() -> int:
    db = SessionLocal()
    try:
        return db.query(Order).count()
    finally:
        db.close()


def count_products() -> int:
    db = SessionLocal()
    try:
        return db.query(Product).count()
    finally:
        db.close()


def count_employees() -> int:
    db = SessionLocal()
    try:
        return db.query(Employee).count()
    finally:
        db.close()


def count_offices() -> int:
    db = SessionLocal()
    try:
        return db.query(Office).count()
    finally:
        db.close()


def count_payments() -> int:
    db = SessionLocal()
    try:
        return db.query(Payment).count()
    finally:
        db.close()


def count_orderdetails() -> int:
    db = SessionLocal()
    try:
        return db.query(OrderDetail).count()
    finally:
        db.close()


def count_productlines() -> int:
    db = SessionLocal()
    try:
        return db.query(ProductLine).count()
    finally:
        db.close()
