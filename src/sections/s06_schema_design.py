SECTION = dict(
    num=6, title="Designing schemas: CREATE TABLE, constraints, types, ALTER", db="lab",
    pdf="Hafta 3 – Veritabanı Şeması Tasarlama (storage class, affinity, PK/FK, CHECK, ALTER TABLE)",
    intro="""
These exercises start from an **empty** database (`./drill reset lab`, then `./drill open lab`)
and build a small library system step by step. Each exercise builds on the previous ones —
if you get lost, `./drill catchup 06.0X` puts the DB in the right state.

Grading: your script is run, then a **check script** pokes the tables (inserts good and bad
rows). If your constraints are right, the bad rows produce `Error:` lines exactly where the
expected output has them.
""",
)

EX = [
    dict(
        title="members",
        task="""Create `members`:
- `id` INTEGER primary key
- `name` TEXT, required
- `email` TEXT, required and unique
- `joined_at` TEXT, required, defaults to `CURRENT_DATE`""",
        sol="""
CREATE TABLE members (
    id        INTEGER PRIMARY KEY,
    name      TEXT NOT NULL,
    email     TEXT NOT NULL UNIQUE,
    joined_at TEXT NOT NULL DEFAULT CURRENT_DATE
);
""",
        check="""
SELECT name, type, "notnull", pk FROM pragma_table_info('members');
INSERT INTO members (name, email) VALUES ('Ayse', 'ayse@omu.edu.tr');
INSERT INTO members (name, email) VALUES ('Ali',  'ayse@omu.edu.tr');
INSERT INTO members (name) VALUES ('No Mail');
SELECT id, name, joined_at IS NOT NULL AS has_date FROM members;
""",
    ),
    dict(
        title="books with CHECK constraints",
        task="""Create `books`:
- `id` INTEGER primary key
- `title` TEXT, required
- `isbn` TEXT, unique, must be exactly 13 characters long (may be NULL)
- `published_year` INTEGER, must be between 1450 and 2026
- `price_kurus` INTEGER, required, default 0, cannot be negative""",
        hint="`CHECK (length(isbn) = 13)` — a CHECK that evaluates to NULL counts as *passed*, so NULL isbn is allowed automatically.",
        sol="""
CREATE TABLE books (
    id             INTEGER PRIMARY KEY,
    title          TEXT NOT NULL,
    isbn           TEXT UNIQUE CHECK (length(isbn) = 13),
    published_year INTEGER CHECK (published_year BETWEEN 1450 AND 2026),
    price_kurus    INTEGER NOT NULL DEFAULT 0 CHECK (price_kurus >= 0)
);
""",
        check="""
INSERT INTO books (title, isbn, published_year, price_kurus) VALUES ('Nutuk', '9789751600000', 1927, 12000);
INSERT INTO books (title, isbn) VALUES ('Short ISBN', '12345');
INSERT INTO books (title, published_year) VALUES ('From the future', 2030);
INSERT INTO books (title, price_kurus) VALUES ('Negative', -1);
INSERT INTO books (title) VALUES ('No ISBN');
INSERT INTO books (title, isbn) VALUES ('Dup', '9789751600000');
SELECT id, title, isbn, price_kurus FROM books;
""",
    ),
    dict(
        title="loans: a junction table with foreign keys",
        concept="`ON DELETE CASCADE` deletes child rows with the parent; `ON DELETE RESTRICT` refuses to delete a parent that still has children. Remember: SQLite only enforces FKs after `PRAGMA foreign_keys = ON;` (`./drill open` does that for you).",
        task="""Create `loans` linking members and books (many-to-many):
- `id` INTEGER primary key
- `member_id` required, references `members(id)`, **deleting a member deletes their loans**
- `book_id` required, references `books(id)`, **a book with loans cannot be deleted**
- `loaned_at` TEXT required, default `CURRENT_TIMESTAMP`
- `returned_at` TEXT, NULL while the book is still out; when set it must not be earlier than `loaned_at`""",
        sol="""
CREATE TABLE loans (
    id          INTEGER PRIMARY KEY,
    member_id   INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    book_id     INTEGER NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
    loaned_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    returned_at TEXT CHECK (returned_at IS NULL OR returned_at >= loaned_at)
);
""",
        check="""
INSERT INTO members (id, name, email) VALUES (1, 'Ayse', 'ayse@omu.edu.tr'), (2, 'Can', 'can@omu.edu.tr');
INSERT INTO books (id, title) VALUES (1, 'Nutuk'), (2, 'Huzur');
INSERT INTO loans (member_id, book_id, loaned_at) VALUES (1, 1, '2026-10-01'), (1, 2, '2026-10-05'), (2, 2, '2026-10-06');
INSERT INTO loans (member_id, book_id) VALUES (99, 1);
UPDATE loans SET returned_at = '2026-09-01' WHERE id = 1;
UPDATE loans SET returned_at = '2026-10-10' WHERE id = 1;
DELETE FROM books WHERE id = 2;
DELETE FROM members WHERE id = 1;
SELECT id, member_id, book_id, returned_at FROM loans;
""",
    ),
    dict(
        title="Type affinity: what actually gets stored?",
        concept="In a normal SQLite table a column's type is only a *preference* (affinity). `INTEGER` affinity converts `'25'` to 25, but stores `'yirmi bes'` as text. A column with **no type** keeps whatever you give it.",
        task="""Create `demo(a INTEGER, b TEXT, c REAL, d)` (d has no type) and insert three rows:
`('25', '25', '25', '25')`, `(25, 25, 25, 25)`, `('yirmi bes', 2.5, '2.5', 2.5)`.""",
        sol="""
CREATE TABLE demo (a INTEGER, b TEXT, c REAL, d);
INSERT INTO demo VALUES ('25', '25', '25', '25'), (25, 25, 25, 25), ('yirmi bes', 2.5, '2.5', 2.5);
""",
        check="SELECT typeof(a), typeof(b), typeof(c), typeof(d) FROM demo ORDER BY rowid;",
        after="Note row 1: `c REAL` turned `'25'` into the real 25.0, while untyped `d` kept the text `'25'`. Row 3: INTEGER affinity could not convert 'yirmi bes', so it is stored as text — no error!",
    ),
    dict(
        title="STRICT tables",
        concept="`CREATE TABLE ... ( ... ) STRICT;` (SQLite ≥ 3.37) turns types into real rules: a value that can't be losslessly converted is rejected.",
        task="Create `strict_demo(a INTEGER, b TEXT) STRICT`.",
        sol="CREATE TABLE strict_demo (a INTEGER, b TEXT) STRICT;",
        check="""
INSERT INTO strict_demo VALUES ('25', 'ok');
INSERT INTO strict_demo VALUES ('yirmi bes', 'fails');
INSERT INTO strict_demo VALUES (2.5, 'fails too');
SELECT a, typeof(a), b FROM strict_demo;
""",
    ),
    dict(
        title="ALTER TABLE",
        concept="SQLite's ALTER TABLE can `ADD COLUMN`, `RENAME COLUMN`, `RENAME TO` and `DROP COLUMN`. Anything else (changing a type, adding a FK) needs the *create-new → copy → drop → rename* dance (exercise 07.12).",
        task="""On the library schema:
1. add `phone TEXT` to `members`,
2. rename `members.name` to `full_name`,
3. rename table `loans` to `borrowings`,
4. drop the `demo` and `strict_demo` tables.""",
        sol="""
ALTER TABLE members ADD COLUMN phone TEXT;
ALTER TABLE members RENAME COLUMN name TO full_name;
ALTER TABLE loans RENAME TO borrowings;
DROP TABLE demo;
DROP TABLE strict_demo;
""",
        check="""
SELECT name FROM pragma_table_info('members');
SELECT name FROM sqlite_schema WHERE type = 'table' ORDER BY name;
""",
        after="Renaming `loans` also rewrote the FOREIGN KEY text inside other tables' definitions automatically — check `.schema borrowings`.",
    ),
    dict(
        title="Why money is stored in kuruş",
        task="Return one row: `float_ok` = `0.1 + 0.2 = 0.3`, `int_ok` = `10 + 20 = 30`, and `float_sum` = `printf('%.17f', 0.1 + 0.2)`.",
        sol="SELECT 0.1 + 0.2 = 0.3 AS float_ok, 10 + 20 = 30 AS int_ok, printf('%.17f', 0.1 + 0.2) AS float_sum;",
    ),
    dict(
        title="Normalise a flat table",
        fresh=True,
        concept="One table that repeats rider and station details on every row wastes space and invites contradictions. Split entities into their own tables and keep only ids in the event table.",
        task="""Start from a fresh lab DB. Run `.read data/flat_rides.sql` (creates `flat_rides(rider, station, district, rode_at)`). Then:
1. create `riders(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)`
2. create `stations(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, district TEXT NOT NULL)`
3. create `rides(id INTEGER PRIMARY KEY, rider_id … REFERENCES riders, station_id … REFERENCES stations, rode_at TEXT NOT NULL)`
4. fill all three from `flat_rides` with `INSERT INTO … SELECT`, then `DROP TABLE flat_rides`.""",
        hint="`INSERT INTO riders (name) SELECT DISTINCT rider FROM flat_rides;` — for rides, JOIN flat_rides to riders and stations by name to look the ids up.",
        sol="""
.read data/flat_rides.sql
CREATE TABLE riders (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE stations (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, district TEXT NOT NULL);
CREATE TABLE rides (
    id         INTEGER PRIMARY KEY,
    rider_id   INTEGER NOT NULL REFERENCES riders(id),
    station_id INTEGER NOT NULL REFERENCES stations(id),
    rode_at    TEXT NOT NULL
);
INSERT INTO riders (name) SELECT DISTINCT rider FROM flat_rides;
INSERT INTO stations (name, district) SELECT DISTINCT station, district FROM flat_rides;
INSERT INTO rides (rider_id, station_id, rode_at)
SELECT r.id, s.id, f.rode_at
FROM flat_rides AS f
JOIN riders AS r ON r.name = f.rider
JOIN stations AS s ON s.name = f.station;
DROP TABLE flat_rides;
""",
        check="""
SELECT (SELECT COUNT(*) FROM riders) AS riders, (SELECT COUNT(*) FROM stations) AS stations,
       (SELECT COUNT(*) FROM rides) AS rides,
       (SELECT COUNT(*) FROM sqlite_schema WHERE name = 'flat_rides') AS flat_left;
SELECT s.district, COUNT(*) AS rides
FROM rides JOIN stations AS s ON s.id = rides.station_id
GROUP BY s.district ORDER BY s.district;
SELECT r.name, COUNT(*) AS rides
FROM rides JOIN riders AS r ON r.id = rides.rider_id
GROUP BY r.name ORDER BY r.name;
""",
    ),
]
