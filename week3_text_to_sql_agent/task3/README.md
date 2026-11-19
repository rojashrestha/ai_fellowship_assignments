# Task 3 - Text-to-SQL Pipeline and Query Execution System

```
question
  -> decomposer.decompose()        (Task 2 logic, imported directly)
  -> sql_generator.generate_sql()  (decomposition dict -> SQL string)
  -> validator.is_safe_select()    (blocks anything but SELECT)
  -> executor.execute_with_retry() (runs it; 1 auto-fix retry on failure)
  -> structured result
```

## Files

- `database.py` -- psycopg2 connection wrapper, reads `PGHOST`/`PGUSER`/etc.
  from env vars (defaults match `docker-compose.yml`: db=`mydatabase`,
  user=`admin`, password=`secret`, host=`localhost`, port=`5432`)
- `sql_generator.py` -- turns `{tables, columns, filters, joins}` into a
  real `SELECT ... FROM ... [JOIN ...] [GROUP BY ...]` string
- `validator.py` -- rejects anything that isn't a single read-only
  `SELECT` (blocks INSERT/UPDATE/DELETE/DROP/ALTER/etc., blocks stacked
  statements)
- `executor.py` -- runs the query; on failure, looks at the Postgres error,
  tries to auto-fix it (the one implemented fix: an unquoted camelCase
  column name, e.g. `customerName` -> `"customerName"`, since that's the
  actual recurring failure mode on this schema), and retries once
- `main.py` -- runs the whole pipeline over `sql_questions_only.csv` and
  writes `evaluation_report.csv` + `decompositions.json` + `logs/pipeline.log`

## Run it

```bash
pip install -r requirements.txt
python main.py
```

## Result (already generated, see `evaluation_report.csv`)

**50 / 50 questions executed successfully.** Only one question needed the
auto-fix-and-retry path during development (a self-join column-quoting
issue while building the manager query) -- it's fixed in the current code,
but `executor.py`'s retry logic is real and does get exercised whenever a
camelCase column slips through unquoted.
