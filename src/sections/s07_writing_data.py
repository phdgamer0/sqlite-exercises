SECTION = dict(
    num=7, title="Writing data: INSERT, .import, UPDATE, DELETE, ON DELETE, upsert", db="shop",
    pdf="Hafta 4 – Veri Yazmak: INSERT, DELETE, UPDATE (.import, geçici tablo, ON DELETE, trim/upper, yumuşak silme)",
    intro="""
Everything here **changes** the DB. Exercises are cumulative per database: 07.01–07.08 work
on `shop`, 07.09–07.13 on `transit`. Before starting run `./drill reset shop transit`.
Broke something? `./drill catchup 07.05` rebuilds the DB as it should look right before 07.05.

Habit from the lecture: before any UPDATE/DELETE, run the same WHERE as a `SELECT COUNT(*)`.
Run `.import` lines from inside the `drills/` folder (`./drill open ...` does that).
""",
)

EX = [
    dict(
        title="INSERT with a looked-up foreign key",
        task="Add a top-level category `Toys`, then a category `Board Games` whose parent is Toys. Don't hard-code Toys' id — look it up with a subquery.",
        hint="`INSERT INTO categories (name, parent_id) VALUES ('Board Games', (SELECT id FROM categories WHERE name = 'Toys'));`",
        sol="""
INSERT INTO categories (name) VALUES ('Toys');
INSERT INTO categories (name, parent_id)
VALUES ('Board Games', (SELECT id FROM categories WHERE name = 'Toys'));
""",
        check="""
SELECT c.name, p.name AS parent
FROM categories AS c LEFT JOIN categories AS p ON p.id = c.parent_id
WHERE c.name IN ('Toys', 'Board Games') ORDER BY c.name;
""",
    ),
    dict(
        title=".import a messy CSV through a temp table",
        concept="`data/new_products.csv` has no id column, a category *name* instead of an id, prices in TL, and messy spacing/case. Import it into its own table first, then `INSERT INTO ... SELECT` with the cleaning and the lookup, then drop the temp table.",
        task="Import `data/new_products.csv` into a table `new_raw`, insert its rows into `products` (trimmed name, category matched case-/space-insensitively, `price_kurus` = TL × 100, stock, `added_at = '2026-11-13'`), then `DROP TABLE new_raw`.",
        hint="`.import --csv data/new_products.csv new_raw` (the header becomes column names, all TEXT). Match with `lower(trim(r.category)) = lower(c.name)`; `CAST(r.price_tl AS INTEGER) * 100`.",
        sol="""
.import --csv data/new_products.csv new_raw
INSERT INTO products (name, category_id, price_kurus, stock, added_at)
SELECT trim(r.name), c.id, CAST(r.price_tl AS INTEGER) * 100, CAST(r.stock AS INTEGER), '2026-11-13'
FROM new_raw AS r
JOIN categories AS c ON lower(trim(r.category)) = lower(c.name);
DROP TABLE new_raw;
""",
        check="""
SELECT p.name, c.name AS category, p.price_kurus, p.stock, typeof(p.stock) AS t
FROM products AS p JOIN categories AS c ON c.id = p.category_id
WHERE p.added_at = '2026-11-13' ORDER BY p.name;
SELECT COUNT(*) AS leftover_tables FROM sqlite_schema WHERE name = 'new_raw';
""",
    ),
    dict(
        title="All or nothing",
        concept="A multi-row INSERT is one statement: if one row breaks a constraint, **none** of the rows are inserted.",
        task="""Run this and read the error:
```sql
INSERT INTO products (name, category_id, price_kurus, stock, added_at) VALUES
  ('Jenga',    (SELECT id FROM categories WHERE name = 'Board Games'), 39000, 20, '2026-11-13'),
  ('Catan',    (SELECT id FROM categories WHERE name = 'Board Games'), 99900,  5, '2026-11-13'),
  ('Monopoly', (SELECT id FROM categories WHERE name = 'Board Games'), 75000, 10, '2026-11-13');
```
Confirm nothing was added, then get **Jenga and Monopoly** in (skip the duplicate).""",
        hint="Remove the Catan row — or look up `INSERT OR IGNORE`.",
        sol="""
INSERT INTO products (name, category_id, price_kurus, stock, added_at) VALUES
  ('Jenga',    (SELECT id FROM categories WHERE name = 'Board Games'), 39000, 20, '2026-11-13'),
  ('Monopoly', (SELECT id FROM categories WHERE name = 'Board Games'), 75000, 10, '2026-11-13');
""",
        check="""
SELECT p.name, p.price_kurus FROM products AS p JOIN categories AS c ON c.id = p.category_id
WHERE c.name = 'Board Games' ORDER BY p.name;
""",
    ),
    dict(
        title="UPDATE with arithmetic",
        task="Raise prices of every product in **Books or any Books sub-category** by 10%, rounded to whole TL (the result must still be an INTEGER number of kuruş).",
        hint="`price_kurus = CAST(ROUND(price_kurus * 1.10 / 100) AS INTEGER) * 100`. Category ids: `SELECT id FROM categories WHERE id = 2 OR parent_id = 2`.",
        sol="""
UPDATE products
SET price_kurus = CAST(ROUND(price_kurus * 1.10 / 100) AS INTEGER) * 100
WHERE category_id IN (SELECT id FROM categories WHERE id = 2 OR parent_id = 2);
""",
        check="""
SELECT name, price_kurus, typeof(price_kurus) AS t FROM products
WHERE category_id IN (10, 11, 12) ORDER BY name;
""",
    ),
    dict(
        title="UPDATE driven by a subquery",
        task="Mark as discontinued (`discontinued = 1`) every product with `added_at` before 2026 that has **no order line in an order placed since 2026-01-01**.",
        sol="""
UPDATE products SET discontinued = 1
WHERE added_at < '2026-01-01'
  AND id NOT IN (SELECT oi.product_id FROM order_items AS oi
                 JOIN orders AS o ON o.id = oi.order_id
                 WHERE o.ordered_at >= '2026-01-01');
""",
        check="SELECT name FROM products WHERE discontinued = 1 ORDER BY name;",
    ),
    dict(
        title="DELETE children before parents",
        concept="With foreign keys on, deleting a parent that still has children fails (`FOREIGN KEY constraint failed`) — the default action behaves like RESTRICT.",
        task="Delete all **cancelled** orders. Try `DELETE FROM orders WHERE status = 'cancelled'` first and read the error; then remove whatever references them and try again.",
        hint="Which tables point at orders? `order_items` and `payments`.",
        sol="""
DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE status = 'cancelled');
DELETE FROM payments    WHERE order_id IN (SELECT id FROM orders WHERE status = 'cancelled');
DELETE FROM orders WHERE status = 'cancelled';
""",
        check="""
SELECT status, COUNT(*) AS n FROM orders GROUP BY status ORDER BY status;
SELECT COUNT(*) AS orphan_items FROM order_items WHERE order_id NOT IN (SELECT id FROM orders);
""",
    ),
    dict(
        title="Upsert: INSERT ... ON CONFLICT",
        concept="`INSERT ... ON CONFLICT(col) DO UPDATE SET x = excluded.x` inserts a new row, or updates the existing one when the unique key already exists. `excluded` is the row you tried to insert.",
        task="""A sign-up form sends these two customers. Insert them so that an existing email **updates phone and city** instead of failing:
- `Nazli, Erdogan, nazli.erdogan80@mail.com, 05550000080, Samsun, joined 2026-11-13`
- `Deniz, Kural, deniz.kural@omu.edu.tr, NULL phone, Samsun, joined 2026-11-13`""",
        sol="""
INSERT INTO customers (first_name, last_name, email, phone, city, joined_at) VALUES
  ('Nazli', 'Erdogan', 'nazli.erdogan80@mail.com', '05550000080', 'Samsun', '2026-11-13'),
  ('Deniz', 'Kural', 'deniz.kural@omu.edu.tr', NULL, 'Samsun', '2026-11-13')
ON CONFLICT(email) DO UPDATE SET phone = excluded.phone, city = excluded.city;
""",
        check="""
SELECT id, first_name, email, phone, city, joined_at FROM customers
WHERE email IN ('nazli.erdogan80@mail.com', 'deniz.kural@omu.edu.tr') ORDER BY id;
SELECT COUNT(*) AS customers FROM customers;
""",
        after="Customer 80 kept their id and original `joined_at` — only the columns listed in `DO UPDATE SET` changed.",
    ),
    dict(
        title="CREATE TABLE + INSERT ... SELECT (a report table)",
        task="Create `monthly_sales(month TEXT PRIMARY KEY, orders INTEGER NOT NULL, revenue_kurus INTEGER NOT NULL)` and fill it from **delivered** orders (one row per `YYYY-MM`).",
        sol="""
CREATE TABLE monthly_sales (
    month         TEXT PRIMARY KEY,
    orders        INTEGER NOT NULL,
    revenue_kurus INTEGER NOT NULL
);
INSERT INTO monthly_sales (month, orders, revenue_kurus)
SELECT strftime('%Y-%m', o.ordered_at), COUNT(DISTINCT o.id), SUM(oi.quantity * oi.unit_price_kurus)
FROM orders AS o JOIN order_items AS oi ON oi.order_id = o.id
WHERE o.status = 'delivered'
GROUP BY 1;
""",
        check="""
SELECT COUNT(*) AS months, SUM(orders) AS orders FROM monthly_sales;
SELECT * FROM monthly_sales ORDER BY revenue_kurus DESC LIMIT 3;
""",
        after="This table is a *snapshot*: new orders won't show up in it. A VIEW (section 08) would always be current.",
    ),
    dict(
        title="Clean a survey with trim / upper / LIKE",
        db="transit",
        concept="SQLite's `upper()`/`lower()` only know ASCII: `upper('ilkadım')` gives `ILKADıM`. Leave the Turkish letters out of your LIKE patterns (`'%lkad%'`).",
        task="Import `data/survey.csv` into a table named `survey`. Normalise `district` to exactly `İlkadım`, `Atakum`, `Tekkeköy`, `Canik`; empty cells become NULL.",
        hint="First `UPDATE survey SET district = trim(district);` then one UPDATE per district with `LIKE`, and `SET district = NULL WHERE district = ''`. Check with `SELECT district, COUNT(*) ... GROUP BY district`.",
        sol="""
.import --csv data/survey.csv survey
UPDATE survey SET district = trim(district);
UPDATE survey SET district = NULL WHERE district = '';
UPDATE survey SET district = 'İlkadım'  WHERE district LIKE '%lkad%';
UPDATE survey SET district = 'Atakum'   WHERE district LIKE 'atakum';
UPDATE survey SET district = 'Tekkeköy' WHERE district LIKE 'tekke%';
""",
        check="""
SELECT district, COUNT(*) AS n, ROUND(AVG(score), 2) AS avg_score
FROM survey GROUP BY district ORDER BY district;
""",
    ),
    dict(
        title="Import only the rows that fit",
        db="transit",
        task="`data/stations_extra.csv` has 5 stations. One already exists (`Gar`) and one has an empty district. Import into a temp table `extra`, insert only the valid new stations into `stations`, then drop `extra`.",
        hint="`WHERE district <> '' AND name NOT IN (SELECT name FROM stations)` — or `INSERT OR IGNORE` for the duplicate.",
        sol="""
.import --csv data/stations_extra.csv extra
INSERT INTO stations (name, district, line)
SELECT name, district, line FROM extra
WHERE district <> '' AND name NOT IN (SELECT name FROM stations);
DROP TABLE extra;
""",
        check="SELECT id, name, district, line FROM stations WHERE id > 18 ORDER BY id;",
    ),
    dict(
        title="Change ON DELETE behaviour (rebuild a table)",
        db="transit",
        concept="SQLite can't ALTER a foreign key. The recipe: create a new table with the right definition, copy the rows, drop the old table, rename the new one.",
        task="""Rebuild `swipes` so that:
- deleting a **card** deletes its swipes (`ON DELETE CASCADE`)
- deleting a **station** keeps the swipes but sets `station_id` to NULL (`ON DELETE SET NULL`)

Keep every other column, CHECK and default exactly as before (`.schema swipes`).""",
        hint="`CREATE TABLE swipes_new (...); INSERT INTO swipes_new SELECT * FROM swipes; DROP TABLE swipes; ALTER TABLE swipes_new RENAME TO swipes;`",
        sol="""
CREATE TABLE swipes_new (
    id           INTEGER PRIMARY KEY,
    card_id      INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    station_id   INTEGER REFERENCES stations(id) ON DELETE SET NULL,
    type         TEXT NOT NULL CHECK (type IN ('boarding', 'refund', 'topup')),
    datetime     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    amount_kurus INTEGER NOT NULL CHECK (typeof(amount_kurus) = 'integer'),
    CHECK (
        (type = 'boarding' AND amount_kurus < 0) OR
        (type = 'refund'   AND amount_kurus > 0) OR
        (type = 'topup'    AND amount_kurus > 0)
    )
);
INSERT INTO swipes_new SELECT * FROM swipes;
DROP TABLE swipes;
ALTER TABLE swipes_new RENAME TO swipes;
""",
        check="""
SELECT COUNT(*) AS swipes FROM swipes;
DELETE FROM stations WHERE name = 'Sanayi';
SELECT COUNT(*) AS swipes_without_station FROM swipes WHERE station_id IS NULL AND type = 'boarding';
DELETE FROM cards WHERE id = 30;
SELECT COUNT(*) AS swipes_after, (SELECT COUNT(*) FROM swipes WHERE card_id = 30) AS card30_left FROM swipes;
INSERT INTO swipes (card_id, type, amount_kurus) VALUES (1, 'boarding', 500);
""",
        after="The last check line must fail: the CHECK constraints survived the rebuild.",
    ),
    dict(
        title="Soft delete with a flag column",
        db="transit",
        concept="Instead of DELETE (which loses history and fights foreign keys) add a flag and filter on it.",
        task="Add `cancelled INTEGER NOT NULL DEFAULT 0` (only 0/1 allowed) to `cards`. Then mark as cancelled every card with **no boarding since 2026-10-25**.",
        sol="""
ALTER TABLE cards ADD COLUMN cancelled INTEGER NOT NULL DEFAULT 0 CHECK (cancelled IN (0, 1));
UPDATE cards SET cancelled = 1
WHERE id NOT IN (SELECT card_id FROM swipes WHERE type = 'boarding' AND datetime >= '2026-10-25');
""",
        check="""
SELECT id, owner FROM cards WHERE cancelled = 1 ORDER BY id;
UPDATE cards SET cancelled = 2 WHERE id = 1;
""",
    ),
    dict(
        title="Repair data after a bad UPDATE",
        db="transit",
        task="""Someone ran `UPDATE cards SET balance_kurus = 0;` (run it yourself). Rebuild every card's balance from its swipes with **one** UPDATE (cards with no swipes → 0).""",
        hint="Correlated subquery: `SET balance_kurus = (SELECT COALESCE(SUM(amount_kurus), 0) FROM swipes WHERE swipes.card_id = cards.id)`.",
        sol="""
UPDATE cards SET balance_kurus = 0;
UPDATE cards SET balance_kurus = (SELECT COALESCE(SUM(amount_kurus), 0) FROM swipes WHERE swipes.card_id = cards.id);
""",
        check="""
SELECT COUNT(*) AS wrong_balances FROM cards AS c
WHERE balance_kurus <> (SELECT COALESCE(SUM(amount_kurus), 0) FROM swipes WHERE card_id = c.id);
SELECT SUM(balance_kurus) AS total_balance, COUNT(*) AS cards FROM cards;
""",
    ),
]
