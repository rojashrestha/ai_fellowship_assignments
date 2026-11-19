"""CRUD layer for offices (Part 4)."""

from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud.utils import safe_commit
from app.database import Employee, Office
from app.logger import get_logger
from app.schemas.office_schemas import OfficeCreate, OfficeUpdate

logger = get_logger(__name__)


def get_offices(db: Session, skip: int = 0, limit: int = 100) -> List[Office]:
    logger.info("Querying offices skip=%s limit=%s", skip, limit)
    return db.query(Office).offset(skip).limit(limit).all()


def get_office(db: Session, office_code: str) -> Office:
    office = db.query(Office).filter(Office.officeCode == office_code).first()
    if office is None:
        logger.warning("Office not found: %s", office_code)
        raise HTTPException(status_code=404, detail=f"Office {office_code} not found")
    logger.info("Office found: %s", office_code)
    return office


def create_office(db: Session, data: OfficeCreate) -> Office:
    office = Office(**data.model_dump())
    db.add(office)
    safe_commit(db, logger, action="create")
    db.refresh(office)
    logger.info("Office created: %s", office.officeCode)
    return office


def update_office(db: Session, office_code: str, data: OfficeUpdate) -> Office:
    office = get_office(db, office_code)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(office, field, value)
    safe_commit(db, logger, action="update")
    db.refresh(office)
    logger.info("Office updated: %s", office_code)
    return office


def delete_office(db: Session, office_code: str) -> None:
    office = get_office(db, office_code)
    db.delete(office)
    # Fails with 409 if employees still reference this office.
    safe_commit(db, logger, action="delete")
    logger.info("Office deleted: %s", office_code)


def get_office_employees(db: Session, office_code: str) -> List[Employee]:
    get_office(db, office_code)  # 404s if the office itself doesn't exist
    logger.info("Querying employees for office %s", office_code)
    return db.query(Employee).filter(Employee.officeCode == office_code).all()


def count_offices(db: Session) -> int:
    return db.query(Office).count()
