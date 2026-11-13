# 06 — Designing schemas: CREATE TABLE, constraints, types, ALTER

**Database:** `lab` · **Course link:** Hafta 3 – Veritabanı Şeması Tasarlama (storage class, affinity, PK/FK, CHECK, ALTER TABLE)

These exercises start from an **empty** database (`./drill reset lab`, then `./drill open lab`)
and build a small library system step by step. Each exercise builds on the previous ones —
if you get lost, `./drill catchup 06.0X` puts the DB in the right state.

Grading: your script is run, then a **check script** pokes the tables (inserts good and bad
rows). If your constraints are right, the bad rows produce `Error:` lines exactly where the
expected output has them.

### 06.01 — members

_✏️ changes the DB — `./drill catchup 06.01` first if your DB is out of sync_

**Task:** Create `members`:
- `id` INTEGER primary key
- `name` TEXT, required
- `email` TEXT, required and unique
- `joined_at` TEXT, required, defaults to `CURRENT_DATE`

**After your script, this check:**

```sql
SELECT name, type, "notnull", pk FROM pragma_table_info('members');
INSERT INTO members (name, email) VALUES ('Ayse', 'ayse@omu.edu.tr');
INSERT INTO members (name, email) VALUES ('Ali',  'ayse@omu.edu.tr');
INSERT INTO members (name) VALUES ('No Mail');
SELECT id, name, joined_at IS NOT NULL AS has_date FROM members;
```

should print:

```text
┌───────────┬─────────┬─────────┬────┐
│   name    │  type   │ notnull │ pk │
├───────────┼─────────┼─────────┼────┤
│ id        │ INTEGER │       0 │  1 │
│ name      │ TEXT    │       1 │  0 │
│ email     │ TEXT    │       1 │  0 │
│ joined_at │ TEXT    │       1 │  0 │
└───────────┴─────────┴─────────┴────┘

Error: UNIQUE constraint failed: members.email

Error: NOT NULL constraint failed: members.email

┌────┬──────┬──────────┐
│ id │ name │ has_date │
├────┼──────┼──────────┤
│  1 │ Ayse │        1 │
└────┴──────┴──────────┘
```


### 06.02 — books with CHECK constraints

_✏️ changes the DB — `./drill catchup 06.02` first if your DB is out of sync_

**Task:** Create `books`:
- `id` INTEGER primary key
- `title` TEXT, required
- `isbn` TEXT, unique, must be exactly 13 characters long (may be NULL)
- `published_year` INTEGER, must be between 1450 and 2026
- `price_kurus` INTEGER, required, default 0, cannot be negative

<details><summary>Hint</summary>

`CHECK (length(isbn) = 13)` — a CHECK that evaluates to NULL counts as *passed*, so NULL isbn is allowed automatically.
</details>

**After your script, this check:**

```sql
INSERT INTO books (title, isbn, published_year, price_kurus) VALUES ('Nutuk', '9789751600000', 1927, 12000);
INSERT INTO books (title, isbn) VALUES ('Short ISBN', '12345');
INSERT INTO books (title, published_year) VALUES ('From the future', 2030);
INSERT INTO books (title, price_kurus) VALUES ('Negative', -1);
INSERT INTO books (title) VALUES ('No ISBN');
INSERT INTO books (title, isbn) VALUES ('Dup', '9789751600000');
SELECT id, title, isbn, price_kurus FROM books;
```

should print:

```text
Error: CHECK constraint failed: length(isbn) = 13

Error: CHECK constraint failed: published_year BETWEEN 1450 AND 2026

Error: CHECK constraint failed: price_kurus >= 0

Error: UNIQUE constraint failed: books.isbn

┌────┬─────────┬───────────────┬─────────────┐
│ id │  title  │     isbn      │ price_kurus │
├────┼─────────┼───────────────┼─────────────┤
│  1 │ Nutuk   │ 9789751600000 │       12000 │
│  2 │ No ISBN │ NULL          │           0 │
└────┴─────────┴───────────────┴─────────────┘
```


### 06.03 — loans: a junction table with foreign keys

_✏️ changes the DB — `./drill catchup 06.03` first if your DB is out of sync_

**Concept:** `ON DELETE CASCADE` deletes child rows with the parent; `ON DELETE RESTRICT` refuses to delete a parent that still has children. Remember: SQLite only enforces FKs after `PRAGMA foreign_keys = ON;` (`./drill open` does that for you).

**Task:** Create `loans` linking members and books (many-to-many):
- `id` INTEGER primary key
- `member_id` required, references `members(id)`, **deleting a member deletes their loans**
- `book_id` required, references `books(id)`, **a book with loans cannot be deleted**
- `loaned_at` TEXT required, default `CURRENT_TIMESTAMP`
- `returned_at` TEXT, NULL while the book is still out; when set it must not be earlier than `loaned_at`

**After your script, this check:**

```sql
INSERT INTO members (id, name, email) VALUES (1, 'Ayse', 'ayse@omu.edu.tr'), (2, 'Can', 'can@omu.edu.tr');
INSERT INTO books (id, title) VALUES (1, 'Nutuk'), (2, 'Huzur');
INSERT INTO loans (member_id, book_id, loaned_at) VALUES (1, 1, '2026-10-01'), (1, 2, '2026-10-05'), (2, 2, '2026-10-06');
INSERT INTO loans (member_id, book_id) VALUES (99, 1);
UPDATE loans SET returned_at = '2026-09-01' WHERE id = 1;
UPDATE loans SET returned_at = '2026-10-10' WHERE id = 1;
DELETE FROM books WHERE id = 2;
DELETE FROM members WHERE id = 1;
SELECT id, member_id, book_id, returned_at FROM loans;
```

should print:

```text
Error: FOREIGN KEY constraint failed

Error: CHECK constraint failed: returned_at IS NULL OR returned_at >= loaned_at

Error: FOREIGN KEY constraint failed

┌────┬───────────┬─────────┬─────────────┐
│ id │ member_id │ book_id │ returned_at │
├────┼───────────┼─────────┼─────────────┤
│  3 │         2 │       2 │ NULL        │
└────┴───────────┴─────────┴─────────────┘
```


### 06.04 — Type affinity: what actually gets stored?

_✏️ changes the DB — `./drill catchup 06.04` first if your DB is out of sync_

**Concept:** In a normal SQLite table a column's type is only a *preference* (affinity). `INTEGER` affinity converts `'25'` to 25, but stores `'yirmi bes'` as text. A column with **no type** keeps whatever you give it.

**Task:** Create `demo(a INTEGER, b TEXT, c REAL, d)` (d has no type) and insert three rows:
`('25', '25', '25', '25')`, `(25, 25, 25, 25)`, `('yirmi bes', 2.5, '2.5', 2.5)`.

**After your script, this check:**

```sql
SELECT typeof(a), typeof(b), typeof(c), typeof(d) FROM demo ORDER BY rowid;
```

should print:

```text
┌───────────┬───────────┬───────────┬───────────┐
│ typeof(a) │ typeof(b) │ typeof(c) │ typeof(d) │
├───────────┼───────────┼───────────┼───────────┤
│ integer   │ text      │ real      │ text      │
│ integer   │ text      │ real      │ integer   │
│ text      │ text      │ real      │ real      │
└───────────┴───────────┴───────────┴───────────┘
```

> Note row 1: `c REAL` turned `'25'` into the real 25.0, while untyped `d` kept the text `'25'`. Row 3: INTEGER affinity could not convert 'yirmi bes', so it is stored as text — no error!


### 06.05 — STRICT tables

_✏️ changes the DB — `./drill catchup 06.05` first if your DB is out of sync_

**Concept:** `CREATE TABLE ... ( ... ) STRICT;` (SQLite ≥ 3.37) turns types into real rules: a value that can't be losslessly converted is rejected.

**Task:** Create `strict_demo(a INTEGER, b TEXT) STRICT`.

**After your script, this check:**

```sql
INSERT INTO strict_demo VALUES ('25', 'ok');
INSERT INTO strict_demo VALUES ('yirmi bes', 'fails');
INSERT INTO strict_demo VALUES (2.5, 'fails too');
SELECT a, typeof(a), b FROM strict_demo;
```

should print:

```text
Error: cannot store TEXT value in INTEGER column strict_demo.a

Error: cannot store REAL value in INTEGER column strict_demo.a

┌────┬───────────┬────┐
│ a  │ typeof(a) │ b  │
├────┼───────────┼────┤
│ 25 │ integer   │ ok │
└────┴───────────┴────┘
```


### 06.06 — ALTER TABLE

_✏️ changes the DB — `./drill catchup 06.06` first if your DB is out of sync_

**Concept:** SQLite's ALTER TABLE can `ADD COLUMN`, `RENAME COLUMN`, `RENAME TO` and `DROP COLUMN`. Anything else (changing a type, adding a FK) needs the *create-new → copy → drop → rename* dance (exercise 07.12).

**Task:** On the library schema:
1. add `phone TEXT` to `members`,
2. rename `members.name` to `full_name`,
3. rename table `loans` to `borrowings`,
4. drop the `demo` and `strict_demo` tables.

**After your script, this check:**

```sql
SELECT name FROM pragma_table_info('members');
SELECT name FROM sqlite_schema WHERE type = 'table' ORDER BY name;
```

should print:

```text
┌───────────┐
│   name    │
├───────────┤
│ id        │
│ full_name │
│ email     │
│ joined_at │
│ phone     │
└───────────┘

┌────────────┐
│    name    │
├────────────┤
│ books      │
│ borrowings │
│ members    │
└────────────┘
```

> Renaming `loans` also rewrote the FOREIGN KEY text inside other tables' definitions automatically — check `.schema borrowings`.


### 06.07 — Why money is stored in kuruş

**Task:** Return one row: `float_ok` = `0.1 + 0.2 = 0.3`, `int_ok` = `10 + 20 = 30`, and `float_sum` = `printf('%.17f', 0.1 + 0.2)`.

**Expected result:**

```text
┌──────────┬────────┬─────────────────────┐
│ float_ok │ int_ok │      float_sum      │
├──────────┼────────┼─────────────────────┤
│        0 │      1 │ 0.30000000000000000 │
└──────────┴────────┴─────────────────────┘
```


### 06.08 — Normalise a flat table

_✏️ changes the DB — `./drill catchup 06.08` first if your DB is out of sync · starts from a fresh DB (`./drill reset lab`)_

**Concept:** One table that repeats rider and station details on every row wastes space and invites contradictions. Split entities into their own tables and keep only ids in the event table.

**Task:** Start from a fresh lab DB. Run `.read data/flat_rides.sql` (creates `flat_rides(rider, station, district, rode_at)`). Then:
1. create `riders(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)`
2. create `stations(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, district TEXT NOT NULL)`
3. create `rides(id INTEGER PRIMARY KEY, rider_id … REFERENCES riders, station_id … REFERENCES stations, rode_at TEXT NOT NULL)`
4. fill all three from `flat_rides` with `INSERT INTO … SELECT`, then `DROP TABLE flat_rides`.

<details><summary>Hint</summary>

`INSERT INTO riders (name) SELECT DISTINCT rider FROM flat_rides;` — for rides, JOIN flat_rides to riders and stations by name to look the ids up.
</details>

**After your script, this check:**

```sql
SELECT (SELECT COUNT(*) FROM riders) AS riders, (SELECT COUNT(*) FROM stations) AS stations,
       (SELECT COUNT(*) FROM rides) AS rides,
       (SELECT COUNT(*) FROM sqlite_schema WHERE name = 'flat_rides') AS flat_left;
SELECT s.district, COUNT(*) AS rides
FROM rides JOIN stations AS s ON s.id = rides.station_id
GROUP BY s.district ORDER BY s.district;
SELECT r.name, COUNT(*) AS rides
FROM rides JOIN riders AS r ON r.id = rides.rider_id
GROUP BY r.name ORDER BY r.name;
```

should print:

```text
┌────────┬──────────┬───────┬───────────┐
│ riders │ stations │ rides │ flat_left │
├────────┼──────────┼───────┼───────────┤
│      4 │        5 │    12 │         0 │
└────────┴──────────┴───────┴───────────┘

┌──────────┬───────┐
│ district │ rides │
├──────────┼───────┤
│ Atakum   │     4 │
│ Ilkadim  │     7 │
│ Tekkekoy │     1 │
└──────────┴───────┘

┌─────────────┬───────┐
│    name     │ rides │
├─────────────┼───────┤
│ Ayse Yilmaz │     4 │
│ Can Demir   │     2 │
│ Mehmet Kaya │     3 │
│ Selin Aydin │     3 │
└─────────────┴───────┘
```

