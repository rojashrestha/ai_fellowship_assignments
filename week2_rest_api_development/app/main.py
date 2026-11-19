"""
Application entry point.

Registers every router (Task 2's customers, Part 4's seven additional
resources, and Task 3's concurrency dashboard), and adds a single
app-wide middleware that logs every request and response -- this is what
satisfies the "router.py: log incoming request, response status, 404/500
errors" requirement for every endpoint in the project without repeating
the same logging boilerplate in fifty different functions.
"""

import time

from fastapi import FastAPI, Request

from app.logger import get_logger
from app.routers import (
    counts_router,
    customer_router,
    employee_router,
    office_router,
    order_router,
    orderdetail_router,
    payment_router,
    product_router,
    productline_router,
)

logger = get_logger(__name__)
request_logger = get_logger("app.request")

app = FastAPI(
    title="Week 2 API",
    description=(
        "Full REST API for the Week 2 fellowship assignment. Built across "
        "Task 1 (Docker/Postgres), Task 2 (Customer API, layered architecture), "
        "Task 3 (Factor VIII concurrency dashboard), and Part 4 (full CRUD for "
        "every remaining table)."
    ),
    version="2.0",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    request_logger.info("Incoming request: %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception:
        request_logger.exception(
            "Unhandled error while processing %s %s", request.method, request.url.path
        )
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    request_logger.info(
        "Completed request: %s %s -> status=%s duration=%.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.include_router(customer_router.router, prefix="/customers", tags=["Customers"])
app.include_router(product_router.router, prefix="/products", tags=["Products"])
app.include_router(productline_router.router, prefix="/productlines", tags=["ProductLines"])
app.include_router(office_router.router, prefix="/offices", tags=["Offices"])
app.include_router(employee_router.router, prefix="/employees", tags=["Employees"])
app.include_router(order_router.router, prefix="/orders", tags=["Orders"])
app.include_router(orderdetail_router.router, prefix="/orderdetails", tags=["OrderDetails"])
app.include_router(payment_router.router, prefix="/payments", tags=["Payments"])
app.include_router(counts_router.router, tags=["Counts"])


@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"message": "Week 2 API is running! Visit /docs for the interactive API documentation."}
