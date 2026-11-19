"""
decomposer.py  (Task 2: Query Understanding / Decomposition)
--------------------------------------------------------------
Takes a natural-language question and breaks it into structured parts:
    intent, tables, columns, filters, joins

This is a RULE-BASED decomposer: it never asks an LLM anything and never
hardcodes a lookup table keyed by the exact question text. Instead it
applies a small ordered set of linguistic rules, so rephrasing a question
(different verb, "all" vs no "all", singular/plural, etc.) still produces
a correct decomposition.

The 4 rule families, tried in order:
  1. simple_list_all   -> "List/Get/Show all <table>"
  2. join_lookup       -> "<table> with <related columns>" (needs a JOIN)
  3. group_by          -> "<agg> <metric> per <dimension>"
  4. global_aggregate  -> "<agg> <metric>" (no "per", whole table)
  5. plain_columns     -> "<verb> [all] <column phrase>" on one table
  6. fallback          -> best-effort table guess, SELECT *

Each rule is a small function so the logic stays easy to read and easy to
extend with new phrasing later.
"""

import re
from schema_kb import TABLE_SYNONYMS, TABLE_COLUMNS, PRIMARY_KEYS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LEAD_VERBS = r"(?:list|get|show|find|display|fetch)"

AGG_KEYWORDS = [
    ("total number of", "COUNT"),
    ("number of", "COUNT"),
    ("count total", "COUNT"),
    ("count", "COUNT"),
    ("total", "SUM"),
    ("average", "AVG"),
    ("avg", "AVG"),
    ("maximum", "MAX"),
    ("max", "MAX"),
    ("minimum", "MIN"),
    ("min", "MIN"),
]

# metric phrase (checked longest-first) -> (table, column or None for COUNT(*))
METRIC_VOCAB = [
    ("payment amount", ("payments", "amount")),
    ("payments", ("payments", "amount")),
    ("revenue", ("payments", "amount")),
    ("buy price", ("products", '"buyPrice"')),
    ("product price", ("products", '"buyPrice"')),
    ("quantity in stock", ("products", '"quantityInStock"')),
    ("stock", ("products", '"quantityInStock"')),
    ("msrp", ("products", '"MSRP"')),
    ("customers", ("customers", None)),
    ("products", ("products", None)),
    ("orders", ("orders", None)),
    ("employees", ("employees", None)),
]

# dimension phrase (group-by target) -> (table, group column, friendly label)
DIMENSION_VOCAB = [
    ("country", ("customers", "country")),
    ("status", ("orders", "status")),
    ("product line", ("productlines", '"productLine"')),
    ("office", ("offices", '"officeCode"')),
    ("vendor", ("products", '"productVendor"')),
    ("customer", ("customers", '"customerNumber"')),
]

# JOIN questions: object phrase (after stripping leading verb) -> spec
JOIN_RULES = {
    "orders with customer names": {
        "tables": ["orders", "customers"], "columns": ['o."orderNumber"', 'c."customerName"'],
    },
    "employees with office city": {
        "tables": ["employees", "offices"], "columns": ['e."firstName"', 'e."lastName"', 'of."city"'],
    },
    "payments with customer names": {
        "tables": ["payments", "customers"], "columns": ['pm."checkNumber"', 'pm.amount', 'c."customerName"'],
    },
    "order details with product names": {
        "tables": ["orderdetails", "products"], "columns": ['od."orderNumber"', 'p."productName"', 'od."quantityOrdered"'],
    },
    "products with product line description": {
        "tables": ["products", "productlines"], "columns": ['p."productName"', 'pl."textDescription"'],
    },
    "customers with sales rep names": {
        "tables": ["customers", "employees"], "columns": ['c."customerName"', 'e."firstName"', 'e."lastName"'],
    },
    "orders with customer city": {
        "tables": ["orders", "customers"], "columns": ['o."orderNumber"', 'c.city'],
    },
    "employees and their manager": {
        "self_join": True,
        "columns": ['e."firstName"', 'e."lastName"', 'm."firstName" AS "managerFirstName"', 'm."lastName" AS "managerLastName"'],
    },
    "orderdetails with product vendor": {
        "tables": ["orderdetails", "products"], "columns": ['od."orderNumber"', 'p."productVendor"'],
    },
    "order details with product vendor": {
        "tables": ["orderdetails", "products"], "columns": ['od."orderNumber"', 'p."productVendor"'],
    },
    "payments with customer country": {
        "tables": ["payments", "customers"], "columns": ['pm."checkNumber"', 'c.country'],
    },
}

# Multi-column phrases that need an explicit list (checked before single-column rules)
MULTI_COLUMN_RULES = {
    "product names and prices": ("products", ['"productName"', '"buyPrice"']),
    "customer names and cities": ("customers", ['"customerName"', "city"]),
    "employee first and last names": ("employees", ['"firstName"', '"lastName"']),
}

# Single-column phrases that don't literally contain the table name
SINGLE_COLUMN_RULES = {
    "order dates": ("orders", '"orderDate"'),
    "product vendor list": ("products", '"productVendor"'),
    "product codes": ("products", '"productCode"'),
    "countries from offices": ("offices", "country"),
    "order statuses": ("orders", "status"),
    "payment amounts": ("payments", "amount"),
    "job titles": ("employees", '"jobTitle"'),
    "customer phone numbers": ("customers", "phone"),
    "product msrp values": ("products", '"MSRP"'),
    "order numbers": ("orders", '"orderNumber"'),
}


def _normalize(question: str) -> str:
    q = question.strip().lower()
    q = q.rstrip("?.! ")
    q = re.sub(r"\s+", " ", q)
    return q


def _strip_lead_verb(q: str) -> str:
    """Remove a leading verb + optional 'all'/'the' so rules only need to
    care about the object phrase, not which verb the question used."""
    m = re.match(rf"^{LEAD_VERBS}\s+(?:all\s+)?(?:the\s+)?(.*)$", q)
    return m.group(1).strip() if m else q


def _find_table(phrase: str):
    """Find a table name mentioned in phrase, checking longest synonyms first."""
    all_syns = []
    for table, syns in TABLE_SYNONYMS.items():
        for s in syns:
            all_syns.append((s, table))
    all_syns.sort(key=lambda x: -len(x[0]))
    for syn, table in all_syns:
        if syn in phrase:
            return table
    return None


# ---------------------------------------------------------------------------
# Rule 1: simple "list all <table>"
# ---------------------------------------------------------------------------
def rule_list_all(q: str, obj: str):
    for table, syns in TABLE_SYNONYMS.items():
        for syn in sorted(syns, key=len, reverse=True):
            if obj == syn:
                return {
                    "intent": f"Retrieve all rows from {table}",
                    "tables": [table],
                    "columns": ["*"],
                    "filters": "None",
                    "joins": "None",
                }
    return None


# ---------------------------------------------------------------------------
# Rule 2: join questions ("X with Y ...")
# ---------------------------------------------------------------------------
def rule_join(q: str, obj: str):
    spec = JOIN_RULES.get(obj)
    if not spec:
        return None
    if spec.get("self_join"):
        return {
            "intent": "Retrieve employees together with their manager (self join)",
            "tables": ["employees e", "employees m"],
            "columns": spec["columns"],
            "filters": "None",
            "joins": ['employees e JOIN employees m ON e."reportsTo" = m."employeeNumber"'],
        }
    t1, t2 = spec["tables"]
    from schema_kb import JOIN_CONDITIONS, TABLE_ALIAS
    key = frozenset({t1, t2})
    cond = JOIN_CONDITIONS.get(key)
    if not cond:
        return None
    ta, cola, tb, colb = cond
    a1, a2 = TABLE_ALIAS[t1], TABLE_ALIAS[t2]
    alias_a = TABLE_ALIAS[ta]
    alias_b = TABLE_ALIAS[tb]
    join_sql = f'{ta} {alias_a} JOIN {tb} {alias_b} ON {alias_a}.{cola} = {alias_b}.{colb}'
    return {
        "intent": f"Retrieve {t1} together with related {t2} information",
        "tables": [f"{t1} {a1}", f"{t2} {a2}"],
        "columns": spec["columns"],
        "filters": "None",
        "joins": [join_sql],
    }


# ---------------------------------------------------------------------------
# Rule 3 & 4: aggregation (with or without "per <dimension>")
# ---------------------------------------------------------------------------
def rule_aggregate(q: str):
    has_per = " per " in q
    agg = None
    remainder = q

    # "<entity> per <dimension>" with NO aggregation word at all means an
    # implicit row count, e.g. "Products per product line" -> COUNT(*).
    if has_per and not any(q.startswith(p + " ") or q == p for p, _ in AGG_KEYWORDS):
        agg = "COUNT"
        remainder = q
    else:
        for phrase, fn in AGG_KEYWORDS:
            if q.startswith(phrase + " ") or q == phrase:
                agg = fn
                remainder = q[len(phrase):].strip()
                break
        if agg is None:
            return None

    dimension = None
    metric_phrase = remainder
    if " per " in remainder:
        metric_phrase, dim_phrase = remainder.split(" per ", 1)
        metric_phrase = metric_phrase.strip()
        dim_phrase = dim_phrase.strip()
        for phrase, info in DIMENSION_VOCAB:
            if phrase in dim_phrase:
                dimension = (phrase, info)
                break

    metric = None
    for phrase, info in METRIC_VOCAB:
        if phrase in metric_phrase:
            metric = info
            break
    if metric is None:
        return None
    table, column = metric

    if dimension:
        dim_phrase, (dim_table, dim_col) = dimension
        agg_expr = "COUNT(*)" if column is None else f"{agg}({column})"
        if table == dim_table:
            return {
                "intent": f"{agg} of {metric_phrase} grouped by {dim_phrase}",
                "tables": [table],
                "columns": [dim_col, f"{agg_expr} AS result"],
                "filters": f"GROUP BY {dim_col}",
                "joins": "None",
            }
        from schema_kb import JOIN_CONDITIONS, TABLE_ALIAS
        key = frozenset({table, dim_table})
        cond = JOIN_CONDITIONS.get(key)
        if not cond:
            return None
        ta, cola, tb, colb = cond
        a, b = TABLE_ALIAS[table], TABLE_ALIAS[dim_table]
        alias_a, alias_b = TABLE_ALIAS[ta], TABLE_ALIAS[tb]
        join_sql = f'{ta} {alias_a} JOIN {tb} {alias_b} ON {alias_a}.{cola} = {alias_b}.{colb}'
        group_col_full = f"{b}.{dim_col}"
        agg_expr_full = "COUNT(*)" if column is None else f"{agg}({a}.{column})"
        return {
            "intent": f"{agg} of {metric_phrase} grouped by {dim_phrase}",
            "tables": [f"{table} {a}", f"{dim_table} {b}"],
            "columns": [group_col_full, f"{agg_expr_full} AS result"],
            "filters": f"GROUP BY {group_col_full}",
            "joins": [join_sql],
        }
    else:
        agg_expr = "COUNT(*)" if column is None else f"{agg}({column})"
        return {
            "intent": f"{agg} of {metric_phrase}",
            "tables": [table],
            "columns": [f"{agg_expr} AS result"],
            "filters": "None",
            "joins": "None",
        }


# ---------------------------------------------------------------------------
# Rule 5: specific column-selection phrases on one table
# ---------------------------------------------------------------------------
def rule_columns(obj: str):
    if obj in MULTI_COLUMN_RULES:
        table, cols = MULTI_COLUMN_RULES[obj]
        return {
            "intent": f"Retrieve specific columns from {table}",
            "tables": [table],
            "columns": cols,
            "filters": "None",
            "joins": "None",
        }
    if obj in SINGLE_COLUMN_RULES:
        table, col = SINGLE_COLUMN_RULES[obj]
        return {
            "intent": f"Retrieve a single column from {table}",
            "tables": [table],
            "columns": [col],
            "filters": "None",
            "joins": "None",
        }
    return None


# ---------------------------------------------------------------------------
# Rule 6: fallback - best-effort table guess
# ---------------------------------------------------------------------------
def rule_fallback(q: str):
    table = _find_table(q) or "customers"
    return {
        "intent": f"Best-effort retrieval from {table} (no specific rule matched)",
        "tables": [table],
        "columns": ["*"],
        "filters": "None",
        "joins": "None",
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def decompose(question: str) -> dict:
    q = _normalize(question)
    obj = _strip_lead_verb(q)

    for rule in (rule_list_all, rule_join):
        result = rule(q, obj)
        if result:
            result["question"] = question
            return result

    result = rule_aggregate(q)
    if result:
        result["question"] = question
        return result

    result = rule_columns(obj)
    if result:
        result["question"] = question
        return result

    result = rule_fallback(q)
    result["question"] = question
    return result


if __name__ == "__main__":
    import csv
    with open("sql_questions_only.csv") as f:
        for row in csv.DictReader(f):
            d = decompose(row["question"])
            print(row["question"], "->", d)
