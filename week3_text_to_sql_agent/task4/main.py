"""
agent.py  (Task 4: Mini SQL Agent - Agentic System Task)
-----------------------------------------------------------
FastAPI agent exposing POST /agent/sql.

Unlike a lookup table keyed by exact question text, this agent calls the
SAME rule-based decomposer from Task 2 live, on every request. That means
it can handle a rephrased question (or any new question that fits one of
the decomposer's rule families), not just the 50 exact benchmark strings.

Agent flow (matches the assignment's Step 1-5):
  1. Understand Query   -> decomposer.decompose()
  2. Generate SQL       -> sql_generator.generate_sql()
  3. Execute Query      -> executor.execute_with_retry()
  4. Error Handling     -> executor retries with auto-fix, up to 3 attempts
  5. Final Output       -> SQL result + natural-language summary
"""

import logging
import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from decomposer import decompose
from sql_generator import generate_sql
from executor import execute_with_retry

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/agent.log"), logging.StreamHandler()],
)
logger = logging.getLogger("agent")

app = FastAPI(
    title="Mini SQL Agent",
    description="Self-correcting Text-to-SQL agent (rule-based decomposition + retry)",
)


class SQLRequest(BaseModel):
    question: str


class SQLResponse(BaseModel):
    sql: str
    result: Any
    summary: str
    status: str


def generate_summary(question: str, rows: list[dict], success: bool) -> str:
    if not success:
        return "Sorry, I could not get a result for that question after retrying."
    if not rows:
        return "The query ran successfully but returned no results."
    # single aggregate value, e.g. COUNT(*)/SUM(...)/AVG(...)
    if len(rows) == 1 and len(rows[0]) == 1:
        value = list(rows[0].values())[0]
        ql = question.lower()
        if any(w in ql for w in ["how many", "count", "number of", "total number"]):
            return f"There are {value} matching {('records' if value != 1 else 'record')}."
        return f"The result is {value}."
    if len(rows) <= 5:
        return f"Found {len(rows)} row(s): {rows}"
    return f"Found {len(rows)} rows. Showing the first 5: {rows[:5]}"


@app.post("/agent/sql", response_model=SQLResponse)
async def agent_sql(request: SQLRequest):
    question = request.question.strip()
    logger.info("Received question: %s", question)

    # Step 1: Understand Query
    decomp = decompose(question)
    logger.info("Decomposition: %s", decomp)

    # Step 2: Generate SQL
    sql = generate_sql(decomp)
    logger.info("Generated SQL: %s", sql)

    # Step 3 + 4: Execute Query with up to 3 retries on failure
    result = execute_with_retry(sql, max_retries=3)
    logger.info(
        "Execution finished: success=%s attempts=%d rows=%d time=%dms",
        result["success"], result["attempts"], len(result["rows"]), result["elapsed_ms"],
    )

    # Step 5: Final Output
    summary = generate_summary(question, result["rows"], result["success"])
    status = "success" if result["success"] else "failed"

    return SQLResponse(
        sql=result["final_sql"],
        result=result["rows"],
        summary=summary,
        status=status,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
