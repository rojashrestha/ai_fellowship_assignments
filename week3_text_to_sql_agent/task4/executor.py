"""
executor.py  (Task 3, Step 4 & 5: Execute Query / Validate and Retry)
-----------------------------------------------------------------------
Runs a SQL query against PostgreSQL through database.py, validates it
first with validator.py, and -- if execution fails -- tries one simple,
explainable auto-fix before retrying (Step 5 of the assignment: "read the
error message, attempt to fix the query, retry execution once").

The only auto-fix implemented here is the most common real failure on
this schema: a camelCase column used unquoted (Postgres lower-cases
unquoted identifiers, so "customerName" becomes customername and a
"column does not exist" error is raised). We detect that error and
re-quote the offending identifier, then retry exactly once.
"""

import re
import time
import logging

from database import run_query
from validator import is_safe_select

logger = logging.getLogger("executor")


from schema_kb import TABLE_COLUMNS

# Build a lowercase -> correct-case lookup for every real column name in the
# schema, e.g. "customername" -> "customerName". Postgres error messages
# always report unquoted identifiers in lowercase, so this is needed to
# restore the correct camelCase spelling before quoting it.
_ALL_COLUMNS = set()
for _cols in TABLE_COLUMNS.values():
    for _v in _cols.values():
        _ALL_COLUMNS.add(_v.strip('"'))
_LOWER_TO_REAL = {c.lower(): c for c in _ALL_COLUMNS}


def _attempt_autofix(sql: str, error_msg: str) -> str | None:
    """Return a fixed SQL string, or None if no fix could be applied."""
    m = re.search(r'column "?([A-Za-z_]+)"? does not exist', error_msg, re.IGNORECASE)
    if m:
        bad_col = m.group(1)
        real_col = _LOWER_TO_REAL.get(bad_col.lower())
        if real_col:
            # Replace the bad (possibly already mis-quoted) identifier with
            # the correctly-cased, double-quoted real column name.
            pattern = rf'"?{re.escape(bad_col)}"?'
            fixed = re.sub(pattern, f'"{real_col}"', sql, flags=re.IGNORECASE)
            if fixed != sql:
                return fixed
    return None


def execute_with_retry(sql: str, max_retries: int = 1):
    """
    Validate + execute `sql`. On failure, attempt at most `max_retries`
    auto-fix-and-retry cycles (Task 3 requires exactly 1; Task 4's agent
    passes a higher max_retries for its own 3-attempt rule).

    Returns a dict:
        {
          "success": bool,
          "final_sql": str,
          "rows": list[dict],
          "columns": list[str],
          "message": str,
          "attempts": int,
          "elapsed_ms": int,
        }
    """
    ok, reason = is_safe_select(sql)
    if not ok:
        logger.warning("Blocked unsafe query: %s | reason=%s", sql, reason)
        return {
            "success": False, "final_sql": sql, "rows": [], "columns": [],
            "message": f"Validation failed: {reason}", "attempts": 0, "elapsed_ms": 0,
        }

    current_sql = sql
    start = time.time()
    for attempt in range(1, max_retries + 2):  # first try + N retries
        try:
            logger.info("Attempt %d: executing -> %s", attempt, current_sql)
            rows, cols = run_query(current_sql)
            elapsed_ms = int((time.time() - start) * 1000)
            logger.info("Success on attempt %d (%d rows, %dms)", attempt, len(rows), elapsed_ms)
            return {
                "success": True, "final_sql": current_sql, "rows": rows, "columns": cols,
                "message": "Success" if attempt == 1 else f"Success after {attempt - 1} retry/ies",
                "attempts": attempt, "elapsed_ms": elapsed_ms,
            }
        except Exception as e:
            error_msg = str(e).strip()
            logger.warning("Attempt %d failed: %s", attempt, error_msg)
            if attempt > max_retries:
                elapsed_ms = int((time.time() - start) * 1000)
                return {
                    "success": False, "final_sql": current_sql, "rows": [], "columns": [],
                    "message": f"Failed after {attempt} attempt(s): {error_msg}",
                    "attempts": attempt, "elapsed_ms": elapsed_ms,
                }
            fixed = _attempt_autofix(current_sql, error_msg)
            if fixed:
                logger.info("Auto-fix applied: %s", fixed)
                current_sql = fixed
            # else: retry the same SQL once more in case it was transient
