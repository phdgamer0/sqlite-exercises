# 08 — Views

**Database:** `shop` · **Course link:** Hafta 5 – Görünümler (CREATE VIEW, özet görünüm, TEMP VIEW, bölümleme, güvenlik, görünüme yazılamaz)

A view is a **saved query with a name**. It stores no rows — every time you select from it,
the query runs against the current tables. Uses from the lecture: simplify (hide joins),
aggregate (summary), partition (one view per period), secure (hide columns).

Exercises are cumulative: start with `./drill reset shop`. Inspect views with `.schema view_name`
or `SELECT name, type FROM sqlite_schema;`.

### 08.01 — A view that hides the joins

_✏️ changes the DB — `./drill catchup 08.01` first if your DB is out of sync_

**Task:** Create view `purchase_history` with columns `customer_id, customer` (first + last name), `city, ordered_at, product, quantity` for **delivered** orders only.

**After your script, this check:**

```sql
SELECT ordered_at, product, quantity FROM purchase_history
WHERE customer_id = 13 ORDER BY ordered_at, product LIMIT 6;
SELECT COUNT(*) AS rows FROM purchase_history;
```

should print:

```text
┌─────────────────────┬──────────────────────┬──────────┐
│     ordered_at      │       product        │ quantity │
├─────────────────────┼──────────────────────┼──────────┤
│ 2026-04-17 20:32:22 │ Database Systems     │        5 │
│ 2026-04-17 20:32:22 │ Jump Rope            │        1 │
│ 2026-04-17 20:32:22 │ Kurk Mantolu Madonna │        1 │
│ 2026-04-17 20:32:22 │ Mystery Box          │        1 │
│ 2026-04-17 20:32:22 │ Wireless Mouse       │        1 │
│ 2026-05-03 06:17:19 │ Blender              │        1 │
└─────────────────────┴──────────────────────┴──────────┘

┌──────┐
│ rows │
├──────┤
│  716 │
└──────┘
```


### 08.02 — Query a view like a table

**Task:** Using **only** `purchase_history`: the 5 products bought by the most different customers — `product, buyers`. Ties by product name.

**Expected result:**

```text
┌───────────────┬────────┐
│    product    │ buyers │
├───────────────┼────────┤
│ Coffee Maker  │     24 │
│ Laptop Air 13 │     21 │
│ Watchmen      │     20 │
│ Webcam HD     │     19 │
│ Mystery Box   │     18 │
└───────────────┴────────┘
```


### 08.03 — A summary view

_✏️ changes the DB — `./drill catchup 08.03` first if your DB is out of sync_

**Task:** Create view `order_totals(order_id, customer_id, ordered_at, status, items, total_kurus)` — one row per order, `items` = number of lines, `total_kurus` = sum of quantity × unit price.

**After your script, this check:**

```sql
SELECT status, COUNT(*) AS orders, SUM(total_kurus) / 100.0 AS total_tl
FROM order_totals GROUP BY status ORDER BY status;
```

should print:

```text
┌───────────┬────────┬──────────┐
│  status   │ orders │ total_tl │
├───────────┼────────┼──────────┤
│ cancelled │     36 │   568790 │
│ delivered │    339 │  5150383 │
│ pending   │     13 │   128058 │
│ returned  │     20 │   209945 │
│ shipped   │     12 │   191215 │
└───────────┴────────┴──────────┘
```


### 08.04 — A view built on a view

_✏️ changes the DB — `./drill catchup 08.04` first if your DB is out of sync_

**Task:** Create view `customer_value(customer_id, orders, lifetime_tl)` on top of `order_totals`, counting **delivered** orders only. Then show the top 5 by lifetime_tl.

**After your script, this check:**

```sql
SELECT * FROM customer_value ORDER BY lifetime_tl DESC LIMIT 5;
```

should print:

```text
┌─────────────┬────────┬─────────────┐
│ customer_id │ orders │ lifetime_tl │
├─────────────┼────────┼─────────────┤
│          53 │     14 │      379793 │
│           1 │     12 │      312396 │
│          80 │     14 │      305109 │
│          79 │      7 │      226209 │
│          14 │     16 │      223174 │
└─────────────┴────────┴─────────────┘
```


### 08.05 — Partitioning views

_✏️ changes the DB — `./drill catchup 08.05` first if your DB is out of sync_

**Concept:** Like the lecture's August/September/October reports: one view per slice of the same table, so each report queries its own 'table'.

**Task:** Create views `orders_2025` and `orders_2026`, each with all columns of `orders` for that year.

**After your script, this check:**

```sql
SELECT (SELECT COUNT(*) FROM orders_2025) AS y2025, (SELECT COUNT(*) FROM orders_2026) AS y2026,
       (SELECT COUNT(*) FROM orders) AS total;
```

should print:

```text
┌───────┬───────┬───────┐
│ y2025 │ y2026 │ total │
├───────┼───────┼───────┤
│   100 │   320 │   420 │
└───────┴───────┴───────┘
```


### 08.06 — A security view

_✏️ changes the DB — `./drill catchup 08.06` first if your DB is out of sync_

**Concept:** An analyst should see behaviour, not identities. Expose only safe columns. (In SQLite anyone who can open the file can still read the tables — real databases add `GRANT`/`REVOKE`; SQLite has no users.)

**Task:** Create view `customers_public(id, name, city, birth_year)` where `name` is first name + last-name initial + '.' (e.g. `Ayse Y.`), no email/phone/full birth date.

<details><summary>Hint</summary>

`first_name || ' ' || substr(last_name, 1, 1) || '.'`, `strftime('%Y', birth_date)`
</details>

**After your script, this check:**

```sql
SELECT * FROM customers_public WHERE id <= 5 ORDER BY id;
```

should print:

```text
┌────┬──────────┬──────────┬────────────┐
│ id │   name   │   city   │ birth_year │
├────┼──────────┼──────────┼────────────┤
│  1 │ Onur E.  │ Izmir    │ NULL       │
│  2 │ Ayse D.  │ Istanbul │ 1972       │
│  3 │ Ayse C.  │ Istanbul │ NULL       │
│  4 │ Fatma T. │ Istanbul │ 1987       │
│  5 │ Baris Y. │ Samsun   │ 1993       │
└────┴──────────┴──────────┴────────────┘
```


### 08.07 — You can't write to a view (yet)

**Task:** Try `DELETE FROM purchase_history WHERE customer_id = 13;` and read the error. Why can't SQLite do this? (Which table's rows should disappear — customers? orders? order_items?)

**Expected result:**

```text
Error: cannot modify purchase_history because it is a view
```

> Section 10 fixes this with an `INSTEAD OF` trigger: you tell SQLite what a DELETE on the view should mean.


### 08.08 — Views are live

_✏️ changes the DB — `./drill catchup 08.08` first if your DB is out of sync_

**Task:** Insert a new delivered order for customer 13 (`id` 1000, employee NULL, `2026-11-01 10:00:00`, ship_city `Eskisehir`) with one line: 2 × product 37 (Yoga Mat) at 39900. Then look at `customer_value` for customer 13 — no refresh needed.

**After your script, this check:**

```sql
SELECT * FROM customer_value WHERE customer_id = 13;
```

should print:

```text
┌─────────────┬────────┬─────────────┐
│ customer_id │ orders │ lifetime_tl │
├─────────────┼────────┼─────────────┤
│          13 │     14 │       68718 │
└─────────────┴────────┴─────────────┘
```


### 08.09 — Replacing a view

_✏️ changes the DB — `./drill catchup 08.09` first if your DB is out of sync_

**Concept:** SQLite has no `CREATE OR REPLACE VIEW`, and `CREATE VIEW IF NOT EXISTS` silently keeps the **old** definition. To change a view: `DROP VIEW` then `CREATE VIEW`.

**Task:** Change `customers_public` so it also has a column `orders` (number of orders, 0 for none).

**After your script, this check:**

```sql
SELECT * FROM customers_public WHERE id <= 5 ORDER BY id;
```

should print:

```text
┌────┬──────────┬──────────┬────────────┬────────┐
│ id │   name   │   city   │ birth_year │ orders │
├────┼──────────┼──────────┼────────────┼────────┤
│  1 │ Onur E.  │ Izmir    │ NULL       │     13 │
│  2 │ Ayse D.  │ Istanbul │ 1972       │      3 │
│  3 │ Ayse C.  │ Istanbul │ NULL       │     10 │
│  4 │ Fatma T. │ Istanbul │ 1987       │      0 │
│  5 │ Baris Y. │ Samsun   │ 1993       │      2 │
└────┴──────────┴──────────┴────────────┴────────┘
```


### 08.10 — TEMPORARY views

**Concept:** `CREATE TEMP VIEW` lives in the `temp` schema and disappears when you close the connection. Good for scratch work that shouldn't pollute the schema.

**Task:** Create `CREATE TEMP VIEW big_orders AS SELECT * FROM order_totals WHERE total_kurus > 5000000;`, query it, list it with `SELECT name FROM sqlite_temp_schema;`, then quit (`.quit`), reopen and see that it's gone.

**Expected result:**

```text
┌────────────┬───────────────┐
│ big_orders │ lives_in_temp │
├────────────┼───────────────┤
│         28 │ big_orders    │
└────────────┴───────────────┘
```


### 08.11 — Which objects exist now?

**Task:** List all views in the main schema with how many columns each has: `view, columns`, alphabetically.

<details><summary>Hint</summary>

`sqlite_schema` has `type` and `name`; `pragma_table_info(name)` works on views too.
</details>

**Expected result:**

```text
┌──────────────────┬─────────┐
│       view       │ columns │
├──────────────────┼─────────┤
│ customer_value   │       3 │
│ customers_public │       5 │
│ order_totals     │       6 │
│ orders_2025      │       6 │
│ orders_2026      │       6 │
│ purchase_history │       6 │
└──────────────────┴─────────┘
```

