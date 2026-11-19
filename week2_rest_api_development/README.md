# Week 2 API

A full REST API over the sample sales database, built in layers across
four checkpoints:

- **Task 1** : PostgreSQL database in Docker, seeded automatically from `seed.sql`.
- **Task 2** : Customer API with a 4-layer architecture (`app/database.py`, `app/schemas/`, `app/crud/`, `app/routers/`) and centralized logging.
- **Task 3** : A Factor VIII concurrency dashboard: 8 individual count endpoints plus an aggregated `/overall_counts` that runs them all at once with `asyncio.gather()`.
- **Part 4** : The same layered pattern extended to every remaining table, with full CRUD, foreign-key validation, and composite-key resources.

See [`reflection.md`](./reflection.md) for the written reflections requested in Task 1 and Task 2.

## Project structure

```
.
├── app/
│   ├── main.py               # FastAPI app, middleware, router registration
│   ├── database.py            # Engine/session setup + ORM models (Layer 1)
│   ├── logger.py               # Shared logging config used by every layer
│   ├── schemas/                # Layer 2 - Pydantic Create/Out/Update models
│   │   ├── customer_schemas.py
│   │   ├── product_schemas.py
│   │   ├── productline_schemas.py
│   │   ├── office_schemas.py
│   │   ├── employee_schemas.py
│   │   ├── order_schemas.py
│   │   ├── orderdetail_schemas.py
│   │   ├── payment_schemas.py
│   │   └── counts_schemas.py
│   ├── crud/                   # Layer 3 - database operations
│   │   ├── utils.py            # Shared integrity-error -> 422/409 helper
│   │   ├── customer_crud.py
│   │   ├── product_crud.py
│   │   ├── productline_crud.py
│   │   ├── office_crud.py
│   │   ├── employee_crud.py
│   │   ├── order_crud.py
│   │   ├── orderdetail_crud.py
│   │   ├── payment_crud.py
│   │   └── counts_crud.py      # Thread-isolated counts for /overall_counts
│   └── routers/                # Layer 4 - HTTP endpoints
│       ├── customer_router.py
│       ├── product_router.py
│       ├── productline_router.py
│       ├── office_router.py
│       ├── employee_router.py
│       ├── order_router.py
│       ├── orderdetail_router.py
│       ├── payment_router.py
│       └── counts_router.py
├── seed.sql                    # Schema + sample data (8 tables)
├── docker-compose.yml
├── requirements.txt
├── .env.template
├── reflection.md
├── task1/README.md             # Marker: what Task 1 covered
├── task2/README.md             # Marker: what Task 2 covered
└── task3/README.md             # Marker: what Task 3 covered
```

Application code lives inside `app/` as an importable package; Docker,
environment, and dependency files stay at the project root since they're
infrastructure, not source code. `task1/`, `task2/`, `task3/` are
marker folders, each with a short README pointing back to the code in
`app/` that was added at that stage , the project itself was built as
one cumulative app rather than a separate copy per task.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose

## Setup

1. **Clone and enter the repo**

   ```bash
   git clone <your-repo-url>
   cd <repo-folder>
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.template .env
   ```

   Open `.env` and set real values for `POSTGRES_USER`, `POSTGRES_PASSWORD`,
   and `POSTGRES_DB`. `.env` is gitignored — never commit it.

5. **Start the database**

   ```bash
   docker-compose up -d
   ```

   On first startup, Postgres runs `seed.sql` automatically from
   `/docker-entrypoint-initdb.d/`, creating all 8 tables and loading the
   sample data. This only happens once per data volume — to re-seed from
   scratch, run `docker-compose down -v` then `docker-compose up -d` again.

6. **Run the API**

   ```bash
   uvicorn app.main:app --reload
   ```

7. **Open the docs**

   `http://localhost:8000/docs` for Swagger UI, `http://localhost:8000/redoc` for ReDoc.

## Verifying the database (Task 1, Part 2)

These are the exact commands from the assignment — run them yourself once
the container is up; I can't run Docker from where I'm building this.

```bash
# 1. Confirm the container is up
docker ps

# 2. Open a shell inside it
docker exec -it week2_db /bin/bash

# 3. Connect to Postgres (use the same user/db as your .env)
psql -U <user_name> -d <database_name>

# 4. List tables -- should show 8 rows
\dt

# 5. Spot-check row counts
SELECT COUNT(*) FROM customers;   -- expect 122
SELECT COUNT(*) FROM orders;      -- expect 326
SELECT COUNT(*) FROM products;    -- expect 110
```

If `docker ps` doesn't show the container as `Up`, run
`docker-compose logs db` and paste me the output — I'm happy to help debug
from there even though I can't run it myself.

## API reference

Every list endpoint accepts `skip` and `limit` for pagination. Composite-key
resources (`orderdetails`, `payments`) take both key parts in the path.

| Resource | Endpoints |
|---|---|
| Customers | `GET/POST /customers/`, `GET/PUT/DELETE /customers/{customerNumber}`, `GET /customers/{customerNumber}/orders`, `GET /customers/{customerNumber}/payments`, `GET /customers/count` |
| Products | `GET/POST /products/`, `GET/PUT/DELETE /products/{productCode}`, `GET /products/{productCode}/orderdetails`, `GET /products/count` |
| Product Lines | `GET/POST /productlines/`, `GET/PUT/DELETE /productlines/{productLine}`, `GET /productlines/{productLine}/products`, `GET /productlines/count` |
| Offices | `GET/POST /offices/`, `GET/PUT/DELETE /offices/{officeCode}`, `GET /offices/{officeCode}/employees`, `GET /offices/count` |
| Employees | `GET/POST /employees/`, `GET/PUT/DELETE /employees/{employeeNumber}`, `GET /employees/{employeeNumber}/customers`, `GET /employees/{employeeNumber}/reports`, `GET /employees/count` |
| Orders | `GET/POST /orders/`, `GET/PUT/DELETE /orders/{orderNumber}`, `GET /orders/{orderNumber}/orderdetails`, `GET /orders/customer/{customerNumber}`, `GET /orders/count` |
| Order Details | `GET/POST /orderdetails/`, `GET/PUT/DELETE /orderdetails/{orderNumber}/{productCode}`, `GET /orderdetails/order/{orderNumber}`, `GET /orderdetails/product/{productCode}`, `GET /orderdetails/count` |
| Payments | `GET/POST /payments/`, `GET/PUT/DELETE /payments/{customerNumber}/{checkNumber}`, `GET /payments/customer/{customerNumber}`, `GET /payments/count` |
| Counts dashboard | `GET /overall_counts` — runs all 8 counts concurrently with `asyncio.gather()` |

### Error handling

- **404** : record not found on a GET/PUT/DELETE by ID.
- **422** : a foreign key on create/update points at a row that doesn't exist (e.g. a `productLine` that isn't in `productlines`), or a Pydantic validation rule fails (e.g. `MSRP < buyPrice`, `quantityOrdered <= 0`).
- **409** : delete blocked because another table still references the row (e.g. deleting an `office` that still has `employees`).
- List-by-relationship endpoints (`/orders/customer/{id}`, `/payments/customer/{id}`, `/orderdetails/order/{id}`) never 404 on an empty result — they return `[]`, since "no orders yet" isn't an error.

## Logging

`app/logger.py` configures one shared logger (console + `app.log`) used
everywhere:

- `app/main.py` has an app-wide middleware that logs every request, its
  resulting status code, response time, and any unhandled exception.
- Each router logs the specific action being requested (e.g. `GET
  /customers/103`).
- Each `app/crud/*.py` module logs query results, not-found warnings, and
  integrity errors.
- `app/database.py` logs engine creation and each session open/close.

`app.log` is gitignored — it's runtime output, not source.


