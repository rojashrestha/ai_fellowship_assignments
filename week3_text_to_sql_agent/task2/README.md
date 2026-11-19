# Task 2 - Query Understanding (Decomposition)

`decomposer.py` is a rule-based engine that breaks a natural-language
question into: `intent`, `tables`, `columns`, `filters`, `joins`.

## Why rule-based, and how it actually works

Six rule families are tried in order, each a small function:

1. **`rule_list_all`** -- "List/Get/Show all `<table>`" -> `SELECT * FROM table`
2. **`rule_join`** -- "`<table>` with `<related column>`" -> looks up the FK
   relationship in `schema_kb.JOIN_CONDITIONS` and builds a real `JOIN ... ON ...`
3. **`rule_aggregate`** -- handles both "`<agg> <metric> per <dimension>`"
   (-> `GROUP BY`) and "`<agg> <metric>`" (global aggregate, no grouping).
   Recognizes COUNT / SUM / AVG / MAX / MIN, including the implicit-COUNT
   case ("Products per product line" has no aggregation word but clearly
   means "count of products, grouped by product line").
4. **`rule_columns`** -- specific column phrases that don't literally repeat
   the table name (e.g. "job titles" -> `employees."jobTitle"`)
5. **`rule_fallback`** -- if nothing matched, guess the most-mentioned table
   and `SELECT *`, so the system never crashes on an unrecognized question.

Before any of these run, `_strip_lead_verb()` removes the leading
list/get/show/find/display and optional "all"/"the" -- this is what lets
the same rule match "List all products", "Show all products", and "Get
products" identically, instead of needing a separate hardcoded entry for
every verb variant (which is what the previous version did wrong).

`schema_kb.py` is the single source of table/column vocabulary that this
file, and Task 3/4, all share.

## Run it

```bash
python generate_decompositions.py
```

Outputs `decomposed_queries.json` and `decomposed_queries.csv` -- one row
per benchmark question with its full decomposition. All 50 questions
resolve through a real rule (verified: zero fall back to the catch-all).
