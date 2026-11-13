# 07 — Writing data: INSERT, .import, UPDATE, DELETE, ON DELETE, upsert

**Database:** `shop` · **Course link:** Hafta 4 – Veri Yazmak: INSERT, DELETE, UPDATE (.import, geçici tablo, ON DELETE, trim/upper, yumuşak silme)

Everything here **changes** the DB. Exercises are cumulative per database: 07.01–07.08 work
on `shop`, 07.09–07.13 on `transit`. Before starting run `./drill reset shop transit`.
Broke something? `./drill catchup 07.05` rebuilds the DB as it should look right before 07.05.

Habit from the lecture: before any UPDATE/DELETE, run the same WHERE as a `SELECT COUNT(*)`.
Run `.import` lines from inside the `drills/` folder (`./drill open ...` does that).

### 07.01 — INSERT with a looked-up foreign key

_✏️ changes the DB — `./drill catchup 07.01` first if your DB is out of sync_

**Task:** Add a top-level category `Toys`, then a category `Board Games` whose parent is Toys. Don't hard-code Toys' id — look it up with a subquery.

<details><summary>Hint</summary>

`INSERT INTO categories (name, parent_id) VALUES ('Board Games', (SELECT id FROM categories WHERE name = 'Toys'));`
</details>

**After your script, this check:**

```sql
SELECT c.name, p.name AS parent
FROM categories AS c LEFT JOIN categories AS p ON p.id = c.parent_id
WHERE c.name IN ('Toys', 'Board Games') ORDER BY c.name;
```

should print:

```text
┌─────────────┬────────┐
│    name     │ parent │
├─────────────┼────────┤
│ Board Games │ Toys   │
│ Toys        │ NULL   │
└─────────────┴────────┘
```


### 07.02 — .import a messy CSV through a temp table

_✏️ changes the DB — `./drill catchup 07.02` first if your DB is out of sync_

**Concept:** `data/new_products.csv` has no id column, a category *name* instead of an id, prices in TL, and messy spacing/case. Import it into its own table first, then `INSERT INTO ... SELECT` with the cleaning and the lookup, then drop the temp table.

**Task:** Import `data/new_products.csv` into a table `new_raw`, insert its rows into `products` (trimmed name, category matched case-/space-insensitively, `price_kurus` = TL × 100, stock, `added_at = '2026-11-13'`), then `DROP TABLE new_raw`.

<details><summary>Hint</summary>

`.import --csv data/new_products.csv new_raw` (the header becomes column names, all TEXT). Match with `lower(trim(r.category)) = lower(c.name)`; `CAST(r.price_tl AS INTEGER) * 100`.
</details>

**After your script, this check:**

```sql
SELECT p.name, c.name AS category, p.price_kurus, p.stock, typeof(p.stock) AS t
FROM products AS p JOIN categories AS c ON c.id = p.category_id
WHERE p.added_at = '2026-11-13' ORDER BY p.name;
SELECT COUNT(*) AS leftover_tables FROM sqlite_schema WHERE name = 'new_raw';
```

should print:

```text
┌───────────────────┬─────────────┬─────────────┬───────┬─────────┐
│       name        │  category   │ price_kurus │ stock │    t    │
├───────────────────┼─────────────┼─────────────┼───────┼─────────┤
│ Catan             │ Board Games │      145000 │    12 │ integer │
│ Chess Set         │ Board Games │       65000 │    30 │ integer │
│ Dixit             │ Board Games │       98000 │     8 │ integer │
│ Graphic Novel Box │ Comics      │      130000 │     4 │ integer │
│ Kindle Basic      │ Electronics │      420000 │    15 │ integer │
│ Puzzle 1000pc     │ Board Games │       42000 │    25 │ integer │
└───────────────────┴─────────────┴─────────────┴───────┴─────────┘

┌─────────────────┐
│ leftover_tables │
├─────────────────┤
│               0 │
└─────────────────┘
```


### 07.03 — All or nothing

_✏️ changes the DB — `./drill catchup 07.03` first if your DB is out of sync_

**Concept:** A multi-row INSERT is one statement: if one row breaks a constraint, **none** of the rows are inserted.

**Task:** Run this and read the error:
```sql
INSERT INTO products (name, category_id, price_kurus, stock, added_at) VALUES
  ('Jenga',    (SELECT id FROM categories WHERE name = 'Board Games'), 39000, 20, '2026-11-13'),
  ('Catan',    (SELECT id FROM categories WHERE name = 'Board Games'), 99900,  5, '2026-11-13'),
  ('Monopoly', (SELECT id FROM categories WHERE name = 'Board Games'), 75000, 10, '2026-11-13');
```
Confirm nothing was added, then get **Jenga and Monopoly** in (skip the duplicate).

<details><summary>Hint</summary>

Remove the Catan row — or look up `INSERT OR IGNORE`.
</details>

**After your script, this check:**

```sql
SELECT p.name, p.price_kurus FROM products AS p JOIN categories AS c ON c.id = p.category_id
WHERE c.name = 'Board Games' ORDER BY p.name;
```

should print:

```text
┌───────────────┬─────────────┐
│     name      │ price_kurus │
├───────────────┼─────────────┤
│ Catan         │      145000 │
│ Chess Set     │       65000 │
│ Dixit         │       98000 │
│ Jenga         │       39000 │
│ Monopoly      │       75000 │
│ Puzzle 1000pc │       42000 │
└───────────────┴─────────────┘
```


### 07.04 — UPDATE with arithmetic

_✏️ changes the DB — `./drill catchup 07.04` first if your DB is out of sync_

**Task:** Raise prices of every product in **Books or any Books sub-category** by 10%, rounded to whole TL (the result must still be an INTEGER number of kuruş).

<details><summary>Hint</summary>

`price_kurus = CAST(ROUND(price_kurus * 1.10 / 100) AS INTEGER) * 100`. Category ids: `SELECT id FROM categories WHERE id = 2 OR parent_id = 2`.
</details>

**After your script, this check:**

```sql
SELECT name, price_kurus, typeof(price_kurus) AS t FROM products
WHERE category_id IN (10, 11, 12) ORDER BY name;
```

should print:

```text
┌─────────────────────────────┬─────────────┬─────────┐
│            name             │ price_kurus │    t    │
├─────────────────────────────┼─────────────┼─────────┤
│ A Brief History of Time     │       30800 │ integer │
│ Cosmos                      │       34100 │ integer │
│ Database Systems            │      104500 │ integer │
│ Graphic Novel Box           │      143000 │ integer │
│ Ince Memed                  │       23100 │ integer │
│ Kucuk Prens                 │        9900 │ integer │
│ Kurk Mantolu Madonna        │       13200 │ integer │
│ Maus                        │       42900 │ integer │
│ Saatleri Ayarlama Enstitusu │       28600 │ integer │
│ The Selfish Gene            │       32500 │ integer │
│ Tutunamayanlar              │       37400 │ integer │
│ Watchmen                    │       49500 │ integer │
└─────────────────────────────┴─────────────┴─────────┘
```


### 07.05 — UPDATE driven by a subquery

_✏️ changes the DB — `./drill catchup 07.05` first if your DB is out of sync_

**Task:** Mark as discontinued (`discontinued = 1`) every product with `added_at` before 2026 that has **no order line in an order placed since 2026-01-01**.

**After your script, this check:**

```sql
SELECT name FROM products WHERE discontinued = 1 ORDER BY name;
```

should print:

```text
┌──────────────────┐
│       name       │
├──────────────────┤
│ Budget Laptop 15 │
│ Gift Card 500    │
│ Kucuk Prens      │
│ Maus             │
│ Mystery Box      │
└──────────────────┘
```


### 07.06 — DELETE children before parents

_✏️ changes the DB — `./drill catchup 07.06` first if your DB is out of sync_

**Concept:** With foreign keys on, deleting a parent that still has children fails (`FOREIGN KEY constraint failed`) — the default action behaves like RESTRICT.

**Task:** Delete all **cancelled** orders. Try `DELETE FROM orders WHERE status = 'cancelled'` first and read the error; then remove whatever references them and try again.

<details><summary>Hint</summary>

Which tables point at orders? `order_items` and `payments`.
</details>

**After your script, this check:**

```sql
SELECT status, COUNT(*) AS n FROM orders GROUP BY status ORDER BY status;
SELECT COUNT(*) AS orphan_items FROM order_items WHERE order_id NOT IN (SELECT id FROM orders);
```

should print:

```text
┌───────────┬─────┐
│  status   │  n  │
├───────────┼─────┤
│ delivered │ 339 │
│ pending   │  13 │
│ returned  │  20 │
│ shipped   │  12 │
└───────────┴─────┘

┌──────────────┐
│ orphan_items │
├──────────────┤
│            0 │
└──────────────┘
```


### 07.07 — Upsert: INSERT ... ON CONFLICT

_✏️ changes the DB — `./drill catchup 07.07` first if your DB is out of sync_

**Concept:** `INSERT ... ON CONFLICT(col) DO UPDATE SET x = excluded.x` inserts a new row, or updates the existing one when the unique key already exists. `excluded` is the row you tried to insert.

**Task:** A sign-up form sends these two customers. Insert them so that an existing email **updates phone and city** instead of failing:
- `Nazli, Erdogan, nazli.erdogan80@mail.com, 05550000080, Samsun, joined 2026-11-13`
- `Deniz, Kural, deniz.kural@omu.edu.tr, NULL phone, Samsun, joined 2026-11-13`

**After your script, this check:**

```sql
SELECT id, first_name, email, phone, city, joined_at FROM customers
WHERE email IN ('nazli.erdogan80@mail.com', 'deniz.kural@omu.edu.tr') ORDER BY id;
SELECT COUNT(*) AS customers FROM customers;
```

should print:

```text
┌────┬────────────┬──────────────────────────┬─────────────┬────────┬────────────┐
│ id │ first_name │          email           │    phone    │  city  │ joined_at  │
├────┼────────────┼──────────────────────────┼─────────────┼────────┼────────────┤
│ 80 │ Nazli      │ nazli.erdogan80@mail.com │ 05550000080 │ Samsun │ 2025-10-03 │
│ 81 │ Deniz      │ deniz.kural@omu.edu.tr   │ NULL        │ Samsun │ 2026-11-13 │
└────┴────────────┴──────────────────────────┴─────────────┴────────┴────────────┘

┌───────────┐
│ customers │
├───────────┤
│        81 │
└───────────┘
```

> Customer 80 kept their id and original `joined_at` — only the columns listed in `DO UPDATE SET` changed.


### 07.08 — CREATE TABLE + INSERT ... SELECT (a report table)

_✏️ changes the DB — `./drill catchup 07.08` first if your DB is out of sync_

**Task:** Create `monthly_sales(month TEXT PRIMARY KEY, orders INTEGER NOT NULL, revenue_kurus INTEGER NOT NULL)` and fill it from **delivered** orders (one row per `YYYY-MM`).

**After your script, this check:**

```sql
SELECT COUNT(*) AS months, SUM(orders) AS orders FROM monthly_sales;
SELECT * FROM monthly_sales ORDER BY revenue_kurus DESC LIMIT 3;
```

should print:

```text
┌────────┬────────┐
│ months │ orders │
├────────┼────────┤
│     21 │    339 │
└────────┴────────┘

┌─────────┬────────┬───────────────┐
│  month  │ orders │ revenue_kurus │
├─────────┼────────┼───────────────┤
│ 2026-07 │     40 │      75843500 │
│ 2026-10 │     30 │      53128400 │
│ 2026-09 │     37 │      50818200 │
└─────────┴────────┴───────────────┘
```

> This table is a *snapshot*: new orders won't show up in it. A VIEW (section 08) would always be current.


### 07.09 — Clean a survey with trim / upper / LIKE

_db: `transit` · ✏️ changes the DB — `./drill catchup 07.09` first if your DB is out of sync_

**Concept:** SQLite's `upper()`/`lower()` only know ASCII: `upper('ilkadım')` gives `ILKADıM`. Leave the Turkish letters out of your LIKE patterns (`'%lkad%'`).

**Task:** Import `data/survey.csv` into a table named `survey`. Normalise `district` to exactly `İlkadım`, `Atakum`, `Tekkeköy`, `Canik`; empty cells become NULL.

<details><summary>Hint</summary>

First `UPDATE survey SET district = trim(district);` then one UPDATE per district with `LIKE`, and `SET district = NULL WHERE district = ''`. Check with `SELECT district, COUNT(*) ... GROUP BY district`.
</details>

**After your script, this check:**

```sql
SELECT district, COUNT(*) AS n, ROUND(AVG(score), 2) AS avg_score
FROM survey GROUP BY district ORDER BY district;
```

should print:

```text
┌──────────┬───┬───────────┐
│ district │ n │ avg_score │
├──────────┼───┼───────────┤
│ NULL     │ 1 │         3 │
│ Atakum   │ 3 │      3.67 │
│ Canik    │ 1 │         5 │
│ Tekkeköy │ 3 │      2.67 │
│ İlkadım  │ 4 │         4 │
└──────────┴───┴───────────┘
```


### 07.10 — Import only the rows that fit

_db: `transit` · ✏️ changes the DB — `./drill catchup 07.10` first if your DB is out of sync_

**Task:** `data/stations_extra.csv` has 5 stations. One already exists (`Gar`) and one has an empty district. Import into a temp table `extra`, insert only the valid new stations into `stations`, then drop `extra`.

<details><summary>Hint</summary>

`WHERE district <> '' AND name NOT IN (SELECT name FROM stations)` — or `INSERT OR IGNORE` for the duplicate.
</details>

**After your script, this check:**

```sql
SELECT id, name, district, line FROM stations WHERE id > 18 ORDER BY id;
```

should print:

```text
┌────┬───────────┬──────────┬──────┐
│ id │   name    │ district │ line │
├────┼───────────┼──────────┼──────┤
│ 19 │ Kurtulus  │ Ilkadim  │ Bus  │
│ 20 │ Baruthane │ Atakum   │ Bus  │
│ 21 │ Unye Yolu │ Tekkekoy │ Bus  │
└────┴───────────┴──────────┴──────┘
```


### 07.11 — Change ON DELETE behaviour (rebuild a table)

_db: `transit` · ✏️ changes the DB — `./drill catchup 07.11` first if your DB is out of sync_

**Concept:** SQLite can't ALTER a foreign key. The recipe: create a new table with the right definition, copy the rows, drop the old table, rename the new one.

**Task:** Rebuild `swipes` so that:
- deleting a **card** deletes its swipes (`ON DELETE CASCADE`)
- deleting a **station** keeps the swipes but sets `station_id` to NULL (`ON DELETE SET NULL`)

Keep every other column, CHECK and default exactly as before (`.schema swipes`).

<details><summary>Hint</summary>

`CREATE TABLE swipes_new (...); INSERT INTO swipes_new SELECT * FROM swipes; DROP TABLE swipes; ALTER TABLE swipes_new RENAME TO swipes;`
</details>

**After your script, this check:**

```sql
SELECT COUNT(*) AS swipes FROM swipes;
DELETE FROM stations WHERE name = 'Sanayi';
SELECT COUNT(*) AS swipes_without_station FROM swipes WHERE station_id IS NULL AND type = 'boarding';
DELETE FROM cards WHERE id = 30;
SELECT COUNT(*) AS swipes_after, (SELECT COUNT(*) FROM swipes WHERE card_id = 30) AS card30_left FROM swipes;
INSERT INTO swipes (card_id, type, amount_kurus) VALUES (1, 'boarding', 500);
```

should print:

```text
┌────────┐
│ swipes │
├────────┤
│   2193 │
└────────┘

┌────────────────────────┐
│ swipes_without_station │
├────────────────────────┤
│                     77 │
└────────────────────────┘

┌──────────────┬─────────────┐
│ swipes_after │ card30_left │
├──────────────┼─────────────┤
│         2161 │           0 │
└──────────────┴─────────────┘

Error: CHECK constraint failed: (type = 'boarding' AND amount_kurus < 0) OR
        (type = 'refund'   AND amount_kurus > 0) OR
        (type = 'topup'    AND amount_kurus > 0)
```

> The last check line must fail: the CHECK constraints survived the rebuild.


### 07.12 — Soft delete with a flag column

_db: `transit` · ✏️ changes the DB — `./drill catchup 07.12` first if your DB is out of sync_

**Concept:** Instead of DELETE (which loses history and fights foreign keys) add a flag and filter on it.

**Task:** Add `cancelled INTEGER NOT NULL DEFAULT 0` (only 0/1 allowed) to `cards`. Then mark as cancelled every card with **no boarding since 2026-10-25**.

**After your script, this check:**

```sql
SELECT id, owner FROM cards WHERE cancelled = 1 ORDER BY id;
UPDATE cards SET cancelled = 2 WHERE id = 1;
```

should print:

```text
┌────┬─────────────┐
│ id │    owner    │
├────┼─────────────┤
│  6 │ Mustafa Y.  │
│ 31 │ Unused Card │
│ 32 │ Topup Only  │
└────┴─────────────┘

Error: CHECK constraint failed: cancelled IN (0, 1)
```


### 07.13 — Repair data after a bad UPDATE

_db: `transit` · ✏️ changes the DB — `./drill catchup 07.13` first if your DB is out of sync_

**Task:** Someone ran `UPDATE cards SET balance_kurus = 0;` (run it yourself). Rebuild every card's balance from its swipes with **one** UPDATE (cards with no swipes → 0).

<details><summary>Hint</summary>

Correlated subquery: `SET balance_kurus = (SELECT COALESCE(SUM(amount_kurus), 0) FROM swipes WHERE swipes.card_id = cards.id)`.
</details>

**After your script, this check:**

```sql
SELECT COUNT(*) AS wrong_balances FROM cards AS c
WHERE balance_kurus <> (SELECT COALESCE(SUM(amount_kurus), 0) FROM swipes WHERE card_id = c.id);
SELECT SUM(balance_kurus) AS total_balance, COUNT(*) AS cards FROM cards;
```

should print:

```text
┌────────────────┐
│ wrong_balances │
├────────────────┤
│              0 │
└────────────────┘

┌───────────────┬───────┐
│ total_balance │ cards │
├───────────────┼───────┤
│        220000 │    32 │
└───────────────┴───────┘
```

