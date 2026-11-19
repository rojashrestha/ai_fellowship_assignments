# Task 4 - Mini SQL Agent (FastAPI)

`POST /agent/sql` with `{"question": "..."}` returns:

```json
{
  "sql": "SELECT COUNT(*) AS result FROM orders ;",
  "result": [{"result": 326}],
  "summary": "There are 326 matching records.",
  "status": "success"
}
```

## Agent flow

1. **Understand Query** -- `decomposer.decompose(question)` (same rule-based
   logic as Task 2, called live on every request -- not a lookup table)
2. **Generate SQL** -- `sql_generator.generate_sql(decomp)`
3. **Execute Query** -- `executor.execute_with_retry(sql, max_retries=3)`
4. **Error Handling** -- on failure, the executor inspects the Postgres
   error, attempts a fix, and retries (up to 3 times total, per the
   assignment's rule)
5. **Final Output** -- SQL + raw rows + a natural-language `summary`
   (count-style answers get a sentence, single-value aggregates get
   "The result is X.", row sets get a row dump)

Every step is logged to `logs/agent.log` (decomposition, generated SQL,
execution time, attempt count) and the agent's `try/except` paths mean a
malformed or unrecognized question returns `status: "failed"` with an
apologetic summary instead of crashing the server.

## Why this isn't the same as a hardcoded lookup

The earlier version loaded a static `decompositions.json` and only worked
if the incoming question matched one of the 50 exact strings byte-for-byte.
This version calls the actual rule-based decomposer at request time, so
"Show all order statuses" (a rephrasing, not in the file verbatim) still
resolves correctly -- see `test_agent.py` for a worked example.

## Run it

```bash
pip install -r requirements.txt
python main.py          # starts the API on :8000
# or, without starting a server:
python test_agent.py    # smoke-tests 6 questions including one rephrased one
```

`sample_agent_outputs.json` has the agent's response for all 50 benchmark
questions (50/50 succeeded).

## Known limitation

Same as Task 2/3: this is a rule-based agent, not an LLM-based one. It
generalizes across verb choice and the phrasing patterns the rules cover,
but it doesn't parse arbitrary WHERE-clause filters (e.g. "orders from
Germany") since none of the benchmark questions need them. A question
shaped very differently from the benchmark will fall back to a best-effort
table guess rather than crash, but isn't guaranteed to be the right query.
