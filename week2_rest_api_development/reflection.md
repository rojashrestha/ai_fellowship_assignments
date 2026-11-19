# Reflection

## Task 1 — Database & Docker (Config, Backing Services, Dev/Prod Parity)

**Config (Factor III):** Keeping credentials in `.env` instead of hardcoding
them means the password never lives in source control, and the exact same
code can run against a different database just by changing environment
variables -- no code edits between a laptop, a teammate's machine, or a
production server.

**Backing Services (Factor IV):** Running Postgres as its own Docker
container, reached only through a connection URL, means the database is
an attached resource rather than something baked into the app. It can be
restarted, moved to a different host, or swapped for a managed service
like AWS RDS by changing config, without touching `database.py`.

**Dev/Prod Parity (Factor X):** `docker-compose.yml` pins the exact same
`postgres:16` image and runs the exact same `seed.sql` everywhere it's
used. That means "works on my machine" actually means "works," since the
database engine, version, and starting schema are identical in
development and in whatever environment the project is eventually
deployed to.

## Task 2 — Customer API (Dependencies, Backing Services, Config)

**Factor II — Dependencies:** `requirements.txt` pins exact library
versions (e.g. `fastapi==0.115.6`), and a virtual environment isolates
those packages from the system Python. Anyone who clones the repo and
runs `pip install -r requirements.txt` ends up with the identical
dependency set, so "it works on my machine" can't happen from a version
mismatch.

**Factor IV — Backing Services:** Because all database access goes
through SQLAlchemy in `database.py`, the rest of the app (schemas, crud,
routers) never talks to Postgres directly. Switching to MySQL or SQLite
later would mean changing one connection string, not rewriting the
business logic in `crud/`.

**Factor III — Config Management:** `.env` keeps the database username,
password, host, and port out of the codebase entirely. That makes it safe
to push this project to GitHub, and lets a development machine use a
throwaway local password while a real deployment uses a strong one --
without either value ever appearing in a commit.
