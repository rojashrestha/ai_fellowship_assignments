"""Pydantic schema for the Task 3 aggregated counts dashboard."""

from pydantic import BaseModel


class OverallCounts(BaseModel):
    customers: int
    orders: int
    products: int
    employees: int
    offices: int
    payments: int
    orderdetails: int
    productlines: int
