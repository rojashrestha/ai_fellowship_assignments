"""
Shared crud-layer helper.

This stays inside the crud package (not an external service), so it
doesn't break the rule that crud.py "must strictly interact only with the
database." It exists purely to avoid copy-pasting the same
try/commit/except block into all eight resource crud files.
"""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def safe_commit(db: Session, logger, action: str) -> None:
    """
    Commit the current transaction. On a foreign-key / uniqueness
    violation, roll back and translate it into the right HTTP error:
      - create/update: the client referenced a row that doesn't exist
        -> 422 Unprocessable Entity.
      - delete: other rows still reference this one, so it can't be
        removed -> 409 Conflict.
    """
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.error("Integrity error during %s: %s", action, exc)
        if action == "delete":
            raise HTTPException(
                status_code=409,
                detail="Cannot delete: other records still reference this row.",
            )
        raise HTTPException(
            status_code=422,
            detail="Invalid reference: one of the foreign keys does not exist.",
        )
