"""Router layer for employees (Part 4)."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import employee_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.customer_schemas import CustomerOut
from app.schemas.employee_schemas import EmployeeCreate, EmployeeOut, EmployeeUpdate

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[EmployeeOut])
def list_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info("GET /employees skip=%s limit=%s", skip, limit)
    return employee_crud.get_employees(db, skip=skip, limit=limit)


@router.post("/", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    logger.info("POST /employees employeeNumber=%s", payload.employeeNumber)
    return employee_crud.create_employee(db, payload)


@router.get("/count")
def count_employees(db: Session = Depends(get_db)):
    logger.info("GET /employees/count")
    return {"count": employee_crud.count_employees(db)}


@router.get("/{employee_number}", response_model=EmployeeOut)
def get_employee(employee_number: int, db: Session = Depends(get_db)):
    logger.info("GET /employees/%s", employee_number)
    return employee_crud.get_employee(db, employee_number)


@router.get("/{employee_number}/customers", response_model=List[CustomerOut])
def get_employee_customers(employee_number: int, db: Session = Depends(get_db)):
    logger.info("GET /employees/%s/customers", employee_number)
    return employee_crud.get_employee_customers(db, employee_number)


@router.get("/{employee_number}/reports", response_model=List[EmployeeOut])
def get_employee_reports(employee_number: int, db: Session = Depends(get_db)):
    logger.info("GET /employees/%s/reports", employee_number)
    return employee_crud.get_employee_reports(db, employee_number)


@router.put("/{employee_number}", response_model=EmployeeOut)
def update_employee(employee_number: int, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    logger.info("PUT /employees/%s", employee_number)
    return employee_crud.update_employee(db, employee_number, payload)


@router.delete("/{employee_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_number: int, db: Session = Depends(get_db)):
    logger.info("DELETE /employees/%s", employee_number)
    employee_crud.delete_employee(db, employee_number)
