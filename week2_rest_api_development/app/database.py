"""
Connection layer (Task 2 / Part 4, Layer 1).

Responsibilities:
  - Read DB config from environment variables (.env) -- never hardcoded.
  - Create the SQLAlchemy engine, session factory, and declarative Base.
  - Define the ORM models that map Python classes to the 8 tables created
    by seed.sql.
  - Provide get_db(), the FastAPI dependency every router uses to obtain a
    request-scoped session.

Column attribute names are camelCase (e.g. customerNumber) to match the
quoted, case-sensitive column names Postgres created from seed.sql. Since
no explicit DB column name is passed to Column(), SQLAlchemy uses the
Python attribute name as the column name, so it lines up exactly with
what's already in the database.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    SmallInteger,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
    logger.error("Missing database configuration in environment variables.")
    raise RuntimeError(
        "Missing database configuration. Copy .env.template to .env and "
        "fill in POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB."
    )

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

try:
    # Factor IV (Backing Services): Postgres is an attached resource
    # identified purely by this URL. Swapping it for a managed database
    # later is a config change, not a code change.
    engine = create_engine(DATABASE_URL)
    logger.info("Database engine created for host=%s db=%s", POSTGRES_HOST, POSTGRES_DB)
except Exception:
    logger.exception("Failed to create database engine")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yield a request-scoped session, always close it."""
    db = SessionLocal()
    logger.info("DB session opened")
    try:
        yield db
    finally:
        db.close()
        logger.info("DB session closed")


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------


class ProductLine(Base):
    __tablename__ = "productlines"

    productLine = Column(String(50), primary_key=True)
    textDescription = Column(String(4000))
    htmlDescription = Column(Text)
    image = Column(LargeBinary)


class Product(Base):
    __tablename__ = "products"

    productCode = Column(String(15), primary_key=True)
    productName = Column(String(70), nullable=False)
    productLine = Column(String(50), ForeignKey("productlines.productLine"), nullable=False)
    productScale = Column(String(10), nullable=False)
    productVendor = Column(String(50), nullable=False)
    productDescription = Column(Text, nullable=False)
    quantityInStock = Column(Integer, nullable=False)
    buyPrice = Column(Numeric(10, 2), nullable=False)
    MSRP = Column(Numeric(10, 2), nullable=False)


class Office(Base):
    __tablename__ = "offices"

    officeCode = Column(String(10), primary_key=True)
    city = Column(String(50), nullable=False)
    phone = Column(String(50), nullable=False)
    addressLine1 = Column(String(50), nullable=False)
    addressLine2 = Column(String(50))
    state = Column(String(50))
    country = Column(String(50), nullable=False)
    postalCode = Column(String(15), nullable=False)
    territory = Column(String(10), nullable=False)


class Employee(Base):
    __tablename__ = "employees"

    employeeNumber = Column(Integer, primary_key=True)
    lastName = Column(String(50), nullable=False)
    firstName = Column(String(50), nullable=False)
    extension = Column(String(10), nullable=False)
    email = Column(String(100), nullable=False)
    officeCode = Column(String(10), ForeignKey("offices.officeCode"), nullable=False)
    reportsTo = Column(Integer, ForeignKey("employees.employeeNumber"))
    jobTitle = Column(String(50), nullable=False)


class Customer(Base):
    __tablename__ = "customers"

    customerNumber = Column(Integer, primary_key=True)
    customerName = Column(String(50), nullable=False)
    contactLastName = Column(String(50), nullable=False)
    contactFirstName = Column(String(50), nullable=False)
    phone = Column(String(50), nullable=False)
    addressLine1 = Column(String(50), nullable=False)
    addressLine2 = Column(String(50))
    city = Column(String(50), nullable=False)
    state = Column(String(50))
    postalCode = Column(String(15))
    country = Column(String(50), nullable=False)
    salesRepEmployeeNumber = Column(Integer, ForeignKey("employees.employeeNumber"))
    creditLimit = Column(Numeric(10, 2))


class Payment(Base):
    __tablename__ = "payments"

    customerNumber = Column(Integer, ForeignKey("customers.customerNumber"), primary_key=True)
    checkNumber = Column(String(50), primary_key=True)
    paymentDate = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)


class Order(Base):
    __tablename__ = "orders"

    orderNumber = Column(Integer, primary_key=True)
    orderDate = Column(Date, nullable=False)
    requiredDate = Column(Date, nullable=False)
    shippedDate = Column(Date)
    status = Column(String(15), nullable=False)
    comments = Column(Text)
    customerNumber = Column(Integer, ForeignKey("customers.customerNumber"), nullable=False)


class OrderDetail(Base):
    __tablename__ = "orderdetails"

    orderNumber = Column(Integer, ForeignKey("orders.orderNumber"), primary_key=True)
    productCode = Column(String(15), ForeignKey("products.productCode"), primary_key=True)
    quantityOrdered = Column(Integer, nullable=False)
    priceEach = Column(Numeric(10, 2), nullable=False)
    orderLineNumber = Column(SmallInteger, nullable=False)
