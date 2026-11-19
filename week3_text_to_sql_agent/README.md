# Week 3 - Text-to-SQL Agent Assignment

This folder contains Tasks 1-4 for the Week 3 Fusemachines AI Fellowship
assignment, built around the `classicmodels` PostgreSQL schema (8 tables:
`products`, `customers`, `orders`, `employees`, `offices`, `productlines`,
`payments`, `orderdetails`).

## What changed from the first attempt

The first version of Task 3/4 worked, but Task 2's "decomposition" was a
**static `decompositions.json` keyed by the exact 50 question strings**,
with an empty `decomposition.py` -- meaning there was no actual code that
*performed* decomposition. Rephrasing any question ("Show all products"
instead of "List all products") would have failed, because the lookup
only matched the literal string.

This rebuild adds the missing piece: `task2/decomposer.py` is a real
**rule-based decomposer**. It strips the leading verb (list/get/show/...),
matches the remaining phrase against a small set of ordered rules (list-all,
join, group-by, global aggregate, specific columns, fallback), and looks up
table/column names from `schema_kb.py`. Task 3 and Task 4 both call this
decomposer **live**, on every question, instead of reading a pre-baked
answer file.

This is "Option 1: Rule-Based Pipeline" from the assignment brief -- not
an LLM. It's simple, free, fully explainable, and was the actual gap, since
Task 2 never had working code before. (Using an LLM for decomposition, like
Gemini/Claude, is also a valid approach per the assignment -- Option 2 -- it's
just a different, equally acceptable design choice, not "the right answer".)

## Folder structure

```
week3/
├── docker-compose.yml      # Postgres container (shared by task3 & task4)
├── seed.sql                # schema + data for classicmodels
├── task1/                  # (unchanged) SQL_query_explanation.docx, ground-truth SQL for all 50 Qs
├── task2/                  # rule-based decomposer
│   ├── schema_kb.py
│   ├── decomposer.py
│   ├── generate_decompositions.py
│   ├── sql_questions_only.csv
│   ├── decomposed_queries.json   (generated)
│   ├── decomposed_queries.csv    (generated)
│   └── requirements.txt
├── task3/                  # text-to-SQL pipeline (decompose -> generate -> validate -> execute, 1 retry)
│   ├── database.py / sql_generator.py / validator.py / executor.py / main.py
│   ├── evaluation_report.csv     (generated)
│   ├── decompositions.json       (generated)
│   ├── logs/pipeline.log         (generated)
│   └── requirements.txt
└── task4/                  # FastAPI agent: POST /agent/sql, up to 3 retries
    ├── main.py (FastAPI app) / database.py / sql_generator.py / validator.py / executor.py / decomposer.py / schema_kb.py
    ├── test_agent.py
    ├── sample_agent_outputs.json (generated)
    ├── logs/agent.log
    └── requirements.txt
```

`task3` and `task4` each ship their own copies of `decomposer.py`,
`schema_kb.py`, `sql_generator.py`, `validator.py`, `database.py`,
`executor.py` so every task folder can be opened, installed, and run on
its own -- matching how each task is graded as a separate deliverable.

## How to run

```bash
# 1. Start Postgres (from week3/)
docker compose up -d
# wait a few seconds for it to finish loading seed.sql

# 2. Task 2: generate the decomposition deliverable
cd task2 && pip install -r requirements.txt
python generate_decompositions.py

# 3. Task 3: run the full pipeline over all 50 benchmark questions
cd ../task3 && pip install -r requirements.txt
python main.py
# -> writes evaluation_report.csv, decompositions.json, logs/pipeline.log

# 4. Task 4: run the agent API
cd ../task4 && pip install -r requirements.txt
python main.py
# -> POST http://localhost:8000/agent/sql  {"question": "Count customers per country"}
# or run the smoke test instead of starting the server:
python test_agent.py
```

## Result

All 50 benchmark questions execute successfully end-to-end through both
Task 3's pipeline and Task 4's live FastAPI agent (50/50 -- verified, see
`task3/evaluation_report.csv`). One question ("Get employees and their
manager") needed a self-join and was the trickiest case to get right.

## Honest limitation

This decomposer only handles the phrasing patterns present in the 50-question
benchmark (list-all, simple joins, group-by, global aggregates, specific
columns). It does not parse arbitrary filter conditions like "orders from
Germany" or "customers with credit limit over 50000" -- the benchmark
dataset doesn't require WHERE-clause filters, so the rules don't build them.
A genuinely unseen, differently-shaped question falls back to a best-effort
table guess rather than crashing, but won't always be correct. This is the
real trade-off of a rule-based system over an LLM-based one: it's
transparent and free, but it only generalizes as far as its rules cover.
