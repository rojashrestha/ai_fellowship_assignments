"""
Router for the Task 3 concurrency dashboard.

The eight individual /<table>/count endpoints already live in each
resource's own router (e.g. GET /customers/count in customer_router.py)
to keep Part 1's "modular design" requirement satisfied without
duplicating routes. This file only adds the aggregated endpoint.
"""

import asyncio
import time

from fastapi import APIRouter

from app.crud import counts_crud
from app.logger import get_logger
from app.schemas.counts_schemas import OverallCounts

logger = get_logger(__name__)
router = APIRouter()


@router.get("/overall_counts", response_model=OverallCounts)
async def overall_counts():
    logger.info("GET /overall_counts - starting 8 concurrent count queries")
    start = time.perf_counter()

    (
        customers,
        orders,
        products,
        employees,
        offices,
        payments,
        orderdetails,
        productlines,
    ) = await asyncio.gather(
        asyncio.to_thread(counts_crud.count_customers),
        asyncio.to_thread(counts_crud.count_orders),
        asyncio.to_thread(counts_crud.count_products),
        asyncio.to_thread(counts_crud.count_employees),
        asyncio.to_thread(counts_crud.count_offices),
        asyncio.to_thread(counts_crud.count_payments),
        asyncio.to_thread(counts_crud.count_orderdetails),
        asyncio.to_thread(counts_crud.count_productlines),
    )

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info("GET /overall_counts - asyncio.gather completed in %.1fms", duration_ms)

    return OverallCounts(
        customers=customers,
        orders=orders,
        products=products,
        employees=employees,
        offices=offices,
        payments=payments,
        orderdetails=orderdetails,
        productlines=productlines,
    )
