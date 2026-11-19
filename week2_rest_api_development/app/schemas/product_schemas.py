"""Pydantic schemas for the products resource (Part 4)."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class ProductCreate(BaseModel):
    productCode: str
    productName: str
    productLine: str
    productScale: str
    productVendor: str
    productDescription: str
    quantityInStock: int
    buyPrice: Decimal
    MSRP: Decimal

    @field_validator("quantityInStock")
    @classmethod
    def quantity_must_be_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("quantityInStock must be >= 0")
        return value

    @model_validator(mode="after")
    def msrp_must_cover_buy_price(self):
        if self.MSRP < self.buyPrice:
            raise ValueError("MSRP must be >= buyPrice")
        return self


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    productCode: str
    productName: str
    productLine: str
    productScale: str
    productVendor: str
    productDescription: str
    quantityInStock: int
    buyPrice: Decimal
    MSRP: Decimal


class ProductUpdate(BaseModel):
    productName: Optional[str] = None
    productLine: Optional[str] = None
    productScale: Optional[str] = None
    productVendor: Optional[str] = None
    productDescription: Optional[str] = None
    quantityInStock: Optional[int] = None
    buyPrice: Optional[Decimal] = None
    MSRP: Optional[Decimal] = None

    @field_validator("quantityInStock")
    @classmethod
    def quantity_must_be_non_negative(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 0:
            raise ValueError("quantityInStock must be >= 0")
        return value

    @model_validator(mode="after")
    def msrp_must_cover_buy_price(self):
        if self.MSRP is not None and self.buyPrice is not None and self.MSRP < self.buyPrice:
            raise ValueError("MSRP must be >= buyPrice")
        return self
