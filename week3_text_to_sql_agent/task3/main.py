"""
main.py  (Task 3: Text-to-SQL Pipeline and Query Execution System)
---------------------------------------------------------------------
Full pipeline:  question -> decompose (Task 2) -> generate SQL ->
validate -> execute (1 retry) -> structured result.

Running this script processes every question in sql_questions_only.csv
and writes:
  - evaluation_report.csv   (one row per question, matches the table
                              format shown in the Task 3 PDF)
  - logs/pipeline.log        (full execution log)
"""

import csv
import json
import logging
import os

from decomposer import decompose
from sql_generator import generate_sql
from executor import execute_with_retry

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/pipeline.log"), logging.StreamHandler()],
)
logger = logging.getLogger("pipeline")


def run_pipeline(question: str) -> dict:
    decomp = decompose(question)
    logger.info("Decomposition for %r: %s", question, decomp)

    sql = generate_sql(decomp)
    logger.info("Generated SQL: %s", sql)

    result = execute_with_retry(sql, max_retries=1)

    return {
        "question": question,
        "decomposition": decomp,
        "generated_sql": result["final_sql"],
        "executed_successfully": result["success"],
        "retry_needed": result["attempts"] > 1,
        "row_count": len(result["rows"]),
        "sample_rows": result["rows"][:5],
        "message": result["message"],
        "elapsed_ms": result["elapsed_ms"],
    }


def main():
    with open("sql_questions_only.csv", encoding="utf-8") as f:
        questions = [row["question"].strip() for row in csv.DictReader(f)]

    results = []
    for q in questions:
        print(f"\nProcessing: {q}")
        res = run_pipeline(q)
        results.append(res)
        print(f"  SQL: {res['generated_sql']}")
        print(f"  Status: {res['executed_successfully']} | retry_needed={res['retry_needed']} | rows={res['row_count']}")

    with open("decompositions.json", "w", encoding="utf-8") as f:
        json.dump({r["question"]: r["decomposition"] for r in results}, f, indent=2)

    with open("evaluation_report.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Question", "Generated SQL", "Executed Successfully",
            "Retry Needed", "Row Count", "Final Status", "Message",
        ])
        for r in results:
            writer.writerow([
                r["question"], r["generated_sql"], r["executed_successfully"],
                r["retry_needed"], r["row_count"],
                "Success" if r["executed_successfully"] else "Failed",
                r["message"],
            ])

    success_count = sum(1 for r in results if r["executed_successfully"])
    print(f"\nDone. {success_count}/{len(results)} queries executed successfully.")
    print("Report saved to evaluation_report.csv, decompositions saved to decompositions.json")


if __name__ == "__main__":
    main()
