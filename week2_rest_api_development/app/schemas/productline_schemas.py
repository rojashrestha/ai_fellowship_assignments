"""
Pydantic schemas for the productlines resource (Part 4).

`image` (BYTEA in Postgres) is intentionally excluded from these schemas.
The assignment notes it should be "handled carefully" and suggests either
excluding it from ProductLineOut or base64-encoding it; this project takes
the simpler, explicitly-allowed option and leaves it out of the API
entirely, since none of the seed data populates it anyway.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ProductLineCreate(BaseModel):
    productLine: str
    textDescription: Optional[str] = None
    htmlDescription: Optional[str] = None

    @field_validator("textDescription")
    @classmethod
    def text_description_max_length(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(value) > 4000:
            raise ValueError("textDescription must be 4000 characters or fewer")
        return value


class ProductLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    productLine: str
    textDescription: Optional[str] = None
    htmlDescription: Optional[str] = None


class ProductLineUpdate(BaseModel):
    textDescription: Optional[str] = None
    htmlDescription: Optional[str] = None
