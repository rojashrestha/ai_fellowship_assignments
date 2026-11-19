"""
generate_decompositions.py  (Task 2 deliverable runner)
-----------------------------------------------------------
Runs decomposer.py's rule-based decompose() over every question in
sql_questions_only.csv and writes the structured breakdown to:
  - decomposed_queries.json
  - decomposed_queries.csv

This is the actual Task 2 submission artifact: proof that each question
was broken into intent / tables / columns / filters / joins.
"""

import csv
import json

from decomposer import decompose


def main():
    with open("sql_questions_only.csv", encoding="utf-8") as f:
        questions = [row["question"].strip() for row in csv.DictReader(f)]

    decompositions = []
    for q in questions:
        d = decompose(q)
        decompositions.append({
            "question": q,
            "intent": d["intent"],
            "tables": ", ".join(d["tables"]) if isinstance(d["tables"], list) else d["tables"],
            "columns": ", ".join(d["columns"]) if isinstance(d["columns"], list) else d["columns"],
            "filters": d["filters"],
            "joins": ", ".join(d["joins"]) if isinstance(d["joins"], list) else d["joins"],
        })
        print(f"{q}\n  intent : {d['intent']}\n  tables : {d['tables']}\n  columns: {d['columns']}\n  filters: {d['filters']}\n  joins  : {d['joins']}\n")

    with open("decomposed_queries.json", "w", encoding="utf-8") as f:
        json.dump(decompositions, f, indent=2)

    with open("decomposed_queries.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["question", "intent", "tables", "columns", "filters", "joins"])
        writer.writeheader()
        writer.writerows(decompositions)

    print(f"\nDone. Decomposed {len(decompositions)} questions.")
    print("Saved: decomposed_queries.json, decomposed_queries.csv")


if __name__ == "__main__":
    main()
