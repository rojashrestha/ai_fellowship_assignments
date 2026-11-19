"""CRUD layer for employees (Part 4). Self-referencing FK: reportsTo -> employees.employeeNumber."""

from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud.utils import safe_commit
from app.database import Customer, Employee
from app.logger import get_logger
from app.schemas.employee_schemas import EmployeeCreate, EmployeeUpdate

logger = get_logger(__name__)


def get_employees(db: Session, skip: int = 0, limit: int = 100) -> List[Employee]:
    logger.info("Querying employees skip=%s limit=%s", skip, limit)
    return db.query(Employee).offset(skip).limit(limit).all()


def get_employee(db: Session, employee_number: int) -> Employee:
    employee = db.query(Employee).filter(Employee.employeeNumber == employee_number).first()
    if employee is None:
        logger.warning("Employee not found: %s", employee_number)
        raise HTTPException(status_code=404, detail=f"Employee {employee_number} not found")
    logger.info("Employee found: %s", employee_number)
    return employee


def create_employee(db: Session, data: EmployeeCreate) -> Employee:
    employee = Employee(**data.model_dump())
    db.add(employee)
    safe_commit(db, logger, action="create")
    db.refresh(employee)
    logger.info("Employee created: %s", employee.employeeNumber)
    return employee


def update_employee(db: Session, employee_number: int, data: EmployeeUpdate) -> Employee:
    employee = get_employee(db, employee_number)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)
    safe_commit(db, logger, action="update")
    db.refresh(employee)
    logger.info("Employee updated: %s", employee_number)
    return employee


def delete_employee(db: Session, employee_number: int) -> None:
    employee = get_employee(db, employee_number)
    db.delete(employee)
    # Fails with 409 if this employee has direct reports or manages customers.
    safe_commit(db, logger, action="delete")
    logger.info("Employee deleted: %s", employee_number)


def get_employee_customers(db: Session, employee_number: int) -> List[Customer]:
    get_employee(db, employee_number)  # 404s if the employee itself doesn't exist
    logger.info("Querying customers managed by employee %s", employee_number)
    return db.query(Customer).filter(Customer.salesRepEmployeeNumber == employee_number).all()


def get_employee_reports(db: Session, employee_number: int) -> List[Employee]:
    get_employee(db, employee_number)
    logger.info("Querying direct reports for employee %s", employee_number)
    return db.query(Employee).filter(Employee.reportsTo == employee_number).all()


def count_employees(db: Session) -> int:
    return db.query(Employee).count()
