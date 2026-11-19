"""Router layer for offices (Part 4)."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import office_crud
from app.database import get_db
from app.logger import get_logger
from app.schemas.employee_schemas import EmployeeOut
from app.schemas.office_schemas import OfficeCreate, OfficeOut, OfficeUpdate

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[OfficeOut])
def list_offices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info("GET /offices skip=%s limit=%s", skip, limit)
    return office_crud.get_offices(db, skip=skip, limit=limit)


@router.post("/", response_model=OfficeOut, status_code=status.HTTP_201_CREATED)
def create_office(payload: OfficeCreate, db: Session = Depends(get_db)):
    logger.info("POST /offices officeCode=%s", payload.officeCode)
    return office_crud.create_office(db, payload)


@router.get("/count")
def count_offices(db: Session = Depends(get_db)):
    logger.info("GET /offices/count")
    return {"count": office_crud.count_offices(db)}


@router.get("/{office_code}", response_model=OfficeOut)
def get_office(office_code: str, db: Session = Depends(get_db)):
    logger.info("GET /offices/%s", office_code)
    return office_crud.get_office(db, office_code)


@router.get("/{office_code}/employees", response_model=List[EmployeeOut])
def get_office_employees(office_code: str, db: Session = Depends(get_db)):
    logger.info("GET /offices/%s/employees", office_code)
    return office_crud.get_office_employees(db, office_code)


@router.put("/{office_code}", response_model=OfficeOut)
def update_office(office_code: str, payload: OfficeUpdate, db: Session = Depends(get_db)):
    logger.info("PUT /offices/%s", office_code)
    return office_crud.update_office(db, office_code, payload)


@router.delete("/{office_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_office(office_code: str, db: Session = Depends(get_db)):
    logger.info("DELETE /offices/%s", office_code)
    office_crud.delete_office(db, office_code)
