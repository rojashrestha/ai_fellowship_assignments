"""
sql_generator.py  (Task 3, Step 3: Generate SQL Query)
-------------------------------------------------------
Converts the structured decomposition produced by Task 2's decomposer.py
into an executable PostgreSQL SELECT statement.

decomposition shape (see decomposer.py):
    {
      "tables":  [...],          # e.g. ["orders o", "customers c"]
      "columns": [...],          # e.g. ["*"]  or  ['o."orderNumber"', ...]
      "filters": "None" | "GROUP BY ...",
      "joins":   "None" | [ "tableA a JOIN tableB b ON a.x = b.y" ],
    }
"""


def generate_sql(decomp: dict) -> str:
    columns = decomp["columns"]
    tables = decomp["tables"]
    filters = decomp["filters"]
    joins = decomp["joins"]

    select_clause = ", ".join(columns) if isinstance(columns, list) else str(columns)

    # If joins are present, the FROM clause already contains the full
    # "tableA a JOIN tableB b ON ..." text (built by decomposer.py).
    if joins and joins != "None":
        from_clause = "FROM " + " ".join(joins) if isinstance(joins, list) else f"FROM {joins}"
    else:
        from_clause = f"FROM {tables[0]}"

    group_by = filters if (isinstance(filters, str) and filters.startswith("GROUP BY")) else ""
    where = filters if (isinstance(filters, str) and filters.startswith("WHERE")) else ""

    sql = f"SELECT {select_clause} {from_clause} {where} {group_by};"
    sql = " ".join(sql.split())  # collapse extra whitespace
    return sql
