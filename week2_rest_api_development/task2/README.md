# Task 2 — FastAPI Customer API

This stage covered building the Customer API on top of the Task 1
database, using a 4-layer architecture: connection, schemas, crud,
router.

What was built at this stage:

- `app/database.py` — engine, session factory, and the `Customer` ORM
  model, reading all config from `.env`.
- `app/schemas/customer_schemas.py` — `CustomerCreate`, `CustomerOut`,
  `CustomerUpdate`.
- `app/crud/customer_crud.py` — get/create/update/delete plus
  `get_customer_orders` and `get_customer_payments`, all logged.
- `app/routers/customer_router.py` — the HTTP endpoints
  (`GET/POST /customers/`, `GET/PUT/DELETE /customers/{id}`,
  `GET /customers/{id}/orders`, `GET /customers/{id}/payments`).
- `app/logger.py` — the shared logging config used by every layer, from
  this task onward.

The written reflection for this task (Dependencies, Backing Services,
Config) is in [`/reflection.md`](../reflection.md).

This folder is a marker for where Task 2 sits in the overall project —
the actual code lives in `/app`, since the project was built as one
cumulative app rather than a separate copy per task. See the root
[`README.md`](../README.md) for the full endpoint reference.
