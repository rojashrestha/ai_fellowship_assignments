"""Pydantic schemas for the employees resource (Part 4)."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class EmployeeCreate(BaseModel):
    employeeNumber: int
    lastName: str
    firstName: str
    extension: str
    email: EmailStr
    officeCode: str
    reportsTo: Optional[int] = None
    jobTitle: str


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employeeNumber: int
    lastName: str
    firstName: str
    extension: str
    email: EmailStr
    officeCode: str
    reportsTo: Optional[int] = None
    jobTitle: str


class EmployeeUpdate(BaseModel):
    lastName: Optional[str] = None
    firstName: Optional[str] = None
    extension: Optional[str] = None
    email: Optional[EmailStr] = None
    officeCode: Optional[str] = None
    reportsTo: Optional[int] = None
    jobTitle: Optional[str] = None
