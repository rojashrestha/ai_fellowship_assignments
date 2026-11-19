"""Pydantic schemas for the orderdetails resource (Part 4). Composite PK: (orderNumber, productCode)."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class OrderDetailCreate(BaseModel):
    orderNumber: int
    productCode: str
    quantityOrdered: int
    priceEach: Decimal
    orderLineNumber: int

    @field_validator("quantityOrdered")
    @classmethod
    def quantity_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("quantityOrdered must be > 0")
        return value

    @field_validator("orderLineNumber")
    @classmethod
    def line_number_in_smallint_range(cls, value: int) -> int:
        if not (1 <= value <= 32767):
            raise ValueError("orderLineNumber must be between 1 and 32767")
        return value


class OrderDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    orderNumber: int
    productCode: str
    quantityOrdered: int
    priceEach: Decimal
    orderLineNumber: int


class OrderDetailUpdate(BaseModel):
    quantityOrdered: Optional[int] = None
    priceEach: Optional[Decimal] = None
    orderLineNumber: Optional[int] = None

    @field_validator("quantityOrdered")
    @classmethod
    def quantity_must_be_positive(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("quantityOrdered must be > 0")
        return value

    @field_validator("orderLineNumber")
    @classmethod
    def line_number_in_smallint_range(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and not (1 <= value <= 32767):
            raise ValueError("orderLineNumber must be between 1 and 32767")
        return value
