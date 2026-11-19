"""Pydantic schemas for the orders resource (Part 4)."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, model_validator

OrderStatus = Literal["Shipped", "Resolved", "Cancelled", "On Hold", "Disputed", "In Process"]


class OrderCreate(BaseModel):
    orderNumber: int
    orderDate: date
    requiredDate: date
    shippedDate: Optional[date] = None
    status: OrderStatus
    comments: Optional[str] = None
    customerNumber: int

    @model_validator(mode="after")
    def required_date_after_order_date(self):
        if self.requiredDate < self.orderDate:
            raise ValueError("requiredDate must be on or after orderDate")
        return self


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    orderNumber: int
    orderDate: date
    requiredDate: date
    shippedDate: Optional[date] = None
    status: str
    comments: Optional[str] = None
    customerNumber: int


class OrderUpdate(BaseModel):
    orderDate: Optional[date] = None
    requiredDate: Optional[date] = None
    shippedDate: Optional[date] = None
    status: Optional[OrderStatus] = None
    comments: Optional[str] = None
    customerNumber: Optional[int] = None

    @model_validator(mode="after")
    def required_date_after_order_date(self):
        if self.orderDate is not None and self.requiredDate is not None:
            if self.requiredDate < self.orderDate:
                raise ValueError("requiredDate must be on or after orderDate")
        return self
