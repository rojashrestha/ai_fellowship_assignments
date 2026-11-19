"""Pydantic schemas for the payments resource (Part 4). Composite PK: (customerNumber, checkNumber)."""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class PaymentCreate(BaseModel):
    customerNumber: int
    checkNumber: str
    paymentDate: date
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("amount must be > 0")
        return value

    @field_validator("paymentDate")
    @classmethod
    def payment_date_not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("paymentDate cannot be in the future")
        return value


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customerNumber: int
    checkNumber: str
    paymentDate: date
    amount: Decimal


class PaymentUpdate(BaseModel):
    paymentDate: Optional[date] = None
    amount: Optional[Decimal] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is not None and value <= 0:
            raise ValueError("amount must be > 0")
        return value

    @field_validator("paymentDate")
    @classmethod
    def payment_date_not_in_future(cls, value: Optional[date]) -> Optional[date]:
        if value is not None and value > date.today():
            raise ValueError("paymentDate cannot be in the future")
        return value
