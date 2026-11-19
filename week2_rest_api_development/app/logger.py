"""
Central logging configuration (Task 2, Step 5).

Every layer (database.py, schemas/*, crud/*, routers/*) imports
get_logger(__name__) from here so that log formatting and destinations
(console + app.log) stay consistent across the whole project, instead of
each module configuring logging on its own.

Levels used throughout the project:
  INFO    -> normal operations (request received, record found, query ran)
  WARNING -> unexpected but handled situations (record not found, FK conflict)
  ERROR   -> failures / exceptions (DB connection errors, integrity errors)

Never log secrets (passwords, full connection strings) -- see database.py,
which logs that a connection was established without logging the URL.
"""

import logging
import sys

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root_logger() -> None:
    global _configured
    if _configured:
        return

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler("app.log")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger that writes to console and app.log."""
    _configure_root_logger()
    return logging.getLogger(name)
