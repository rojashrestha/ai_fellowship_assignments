# Task 3 — Modularity and Concurrency

This stage covered Factor VIII (Concurrency): 8 independent count
endpoints, plus an aggregated dashboard endpoint that runs all 8 at once
instead of one after another.

What was built at this stage:

- A `GET /<resource>/count` endpoint added to each resource's own router
  (e.g. `GET /customers/count` in `app/routers/customer_router.py`) —
  keeps each count modular and independent, per Part 1 of this task.
- `app/crud/counts_crud.py` — 8 standalone count functions, each opening
  and closing its own database session (a single SQLAlchemy session
  isn't safe to share across threads running concurrently).
- `app/routers/counts_router.py` — `GET /overall_counts`, which fires all
  8 counts at once with `asyncio.gather()` + `asyncio.to_thread()` and
  logs how long the whole batch took.

No separate written reflection was required for this task — see the
"Conceptual Lesson" success checklist in the assignment PDF, which this
implementation satisfies (modularity, concurrency, robustness on empty
tables, and logging at every layer).

This folder is a marker for where Task 3 sits in the overall project —
the actual code lives in `/app`, since the project was built as one
cumulative app rather than a separate copy per task. See the root
[`README.md`](../README.md) for the full endpoint reference.
