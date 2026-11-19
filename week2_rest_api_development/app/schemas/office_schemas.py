"""Pydantic schemas for the offices resource (Part 4)."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class OfficeCreate(BaseModel):
    officeCode: str
    city: str
    phone: str
    addressLine1: str
    addressLine2: Optional[str] = None
    state: Optional[str] = None
    country: str
    postalCode: str
    territory: str


class OfficeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    officeCode: str
    city: str
    phone: str
    addressLine1: str
    addressLine2: Optional[str] = None
    state: Optional[str] = None
    country: str
    postalCode: str
    territory: str


class OfficeUpdate(BaseModel):
    city: Optional[str] = None
    phone: Optional[str] = None
    addressLine1: Optional[str] = None
    addressLine2: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postalCode: Optional[str] = None
    territory: Optional[str] = None
