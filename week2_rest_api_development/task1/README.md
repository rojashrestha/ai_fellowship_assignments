# Task 1 — Build a Database and API with Docker Containerisation

This stage covered setting up PostgreSQL in Docker and getting it to seed
itself automatically.

What was built at this stage:

- `docker-compose.yml` — defines the `db` service, pinned to `postgres:16`,
  reading credentials from `.env`, with a healthcheck and a persistent
  named volume.
- `seed.sql` — creates all 8 tables and loads the sample data, mounted to
  `/docker-entrypoint-initdb.d/` so it runs automatically on first
  container start.
- `.env.template` — documents the required config variables
  (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`,
  `POSTGRES_PORT`) without committing real secrets.

The written reflection for this task (Config, Backing Services, Dev/Prod
Parity) is in [`/reflection.md`](../reflection.md).

This folder is a marker for where Task 1 sits in the overall project —
the actual `docker-compose.yml`, `seed.sql`, and `.env.template` live at
the project root, since the project was built as one cumulative app
rather than a separate copy per task. See the root
[`README.md`](../README.md) for full setup and verification steps.
