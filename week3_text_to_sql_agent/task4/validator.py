"""
validator.py
------------
Safety gate: only read-only SELECT statements are allowed through to the
executor. This is the "Important Rules" requirement from the assignment:
DELETE / DROP / UPDATE / INSERT must be blocked, every query must be
validated before it touches the database.
"""

import re

BLOCKED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "MERGE",
]


def is_safe_select(sql: str) -> tuple[bool, str]:
    """
    Returns (ok, reason). ok=False means the query must NOT be executed.
    """
    stripped = sql.strip().rstrip(";").strip()

    if not stripped:
        return False, "Empty query"

    if not re.match(r"(?is)^\s*select\b", stripped):
        return False, "Only SELECT statements are allowed"

    upper = stripped.upper()
    for kw in BLOCKED_KEYWORDS:
        if re.search(rf"\b{kw}\b", upper):
            return False, f"Blocked keyword detected: {kw}"

    # Disallow stacked statements (basic injection guard)
    if ";" in stripped:
        return False, "Multiple statements are not allowed"

    return True, "OK"
