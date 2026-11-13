# SQL drills — BİL309 companion

136 graded exercises covering everything in the Oğuz Kural slides (weeks 1–5) and then some:
SELECT/filtering → aggregates/GROUP BY/HAVING → JOINs → subqueries & set ops → CASE →
schema design → INSERT/UPDATE/DELETE/.import → views → CTEs (incl. recursive) → triggers
(incl. INSTEAD OF) → window functions, gaps & islands, indexes on a 600k-row DB.

## Setup (once)

```bash
cd ~/Desktop/SqlStuff/Learning/drills
./reset.sh            # builds db/shop.db, db/transit.db, db/lab.db, copies ../scenario/scenario.db
```
Only needs `sqlite3` and `python3` (no pip packages).

`db/` is not in the repo — it is rebuilt from `schemas/`. The 127 MB `scenario` DB ships
xz-compressed as `schemas/scenario.db.xz` (32 MB) and is unpacked automatically on first use.
`scenario/` holds its schema and the Faker-based generator (`seed.py`) for reference.
To grade against a different copy: `SCENARIO_DB=/path/to/scenario.db ./drill ...`.

## Workflow

```bash
./drill list                 # all exercises (✏️ = changes the DB)
./drill show 03.05           # task + hint in the terminal (or read exercises/03_joins.md)
./drill open shop            # sqlite3 shell: box mode, PRAGMA foreign_keys = ON, cwd = drills/
# ...experiment, then put your final answer in a file...
./drill check 03.05 a.sql    # ✓ / ✗ with your result vs the expected one
./drill solution 03.05       # when stuck (try first!)
```
You can also pipe: `echo "SELECT ..." | ./drill check 03.05 -`

**Grading never touches your `db/*.db`** — it runs your answer on a throw-away copy. So break
your working DBs as much as you like:

| Broke it? | Command |
|---|---|
| start over | `./reset.sh shop` (or `transit`, `lab`, `scenario`, nothing = all) |
| jump into the middle of a cumulative section | `./drill catchup 10.06` → your DB now has the official results of 10.01–10.05 applied |

How checks work:
- **SELECT exercises:** the last result set of your file is compared with the official one
  (values only, column names don't matter; row order matters only if the task asks for it).
- **✏️ exercises** (DDL, DML, triggers): your whole script runs (dot-commands like `.import` are
  fine), then a *check script* shown in the .md runs, and its output must match. Errors count as
  output too, so a missing constraint/trigger shows up as a missing `Error:` line.

## Databases

| db | what | used in |
|---|---|---|
| `shop` | online store: categories (tree), products, customers (referral chain), employees (org chart), orders, order_items, payments, reviews. Money in kuruş. Deliberate edge cases: NULL cities/phones, duplicate names, never-sold products, underpaid orders, fake reviews | 01–05, 07–11 |
| `transit` | SAMULAŞ-style cards / stations / swipes + fares, no triggers installed | 07, 10, 11 |
| `lab` | empty — you design the tables | 06 |
| `scenario` | bundled `schemas/scenario.db.xz` (universities, 600k students, 1.2M registrations) | 11 |

## Sections ↔ lectures

| file | topic | slides |
|---|---|---|
| `exercises/01_select_basics.md` | SELECT, WHERE, LIKE, BETWEEN, NULL, ORDER BY, LIMIT | Hafta 1 |
| `exercises/02_aggregates.md` | COUNT/SUM/AVG/MIN/MAX, GROUP BY, HAVING | Hafta 1–2 |
| `exercises/03_joins.md` | INNER/LEFT/FULL/CROSS/NATURAL/self joins, anti-join, fan-out trap | Hafta 2 |
| `exercises/04_subqueries_setops.md` | scalar/IN/EXISTS/correlated, UNION/INTERSECT/EXCEPT, NOT IN + NULL | Hafta 2 |
| `exercises/05_case.md` | CASE, pivots, COALESCE, NULLIF, CASE in UPDATE | (everywhere) |
| `exercises/06_schema_design.md` | CREATE TABLE, constraints, FKs, affinity, STRICT, ALTER, normalisation | Hafta 3 |
| `exercises/07_writing_data.md` | INSERT, .import via temp table, UPDATE/DELETE, ON DELETE, upsert, cleanup, soft delete | Hafta 4 |
| `exercises/08_views.md` | views: simplify, aggregate, partition, secure, temp, replace | Hafta 5 |
| `exercises/09_cte.md` | WITH, multiple CTEs, VALUES tables, WITH RECURSIVE (calendar, trees, chains) | Hafta 5 + |
| `exercises/10_triggers.md` | AFTER/BEFORE, OLD/NEW, RAISE, audit log, soft delete, INSTEAD OF | Hafta 4–5 |
| `exercises/11_boss.md` | window functions, cohorts, gaps & islands, big joins, EXPLAIN, indexes | beyond |

Sections 06, 07, 08, 10 are **cumulative** — do them in order (or use `catchup`).

## Files

```
drill, reset.sh          the tool
exercises/*.md           generated exercise sheets with expected outputs
src/sections/*.py        exercise source (task, hint, solution, check) — solutions are in here, don't peek
src/gen_*.py             deterministic generators for schemas/*.sql (fixed seeds)
schemas/*.sql            the mock DBs
data/*.csv, *.sql        files for .import / .read exercises
db/                      your working DBs (disposable)
```
Add your own exercise: append a dict to a section file, run `./drill build`.
