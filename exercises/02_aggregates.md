# 02 — Aggregates, GROUP BY, HAVING

**Database:** `shop` · **Course link:** Hafta 1 (COUNT/AVG/SUM/MIN/MAX/DISTINCT) + Hafta 2 (GROUP BY, HAVING)

Aggregates collapse many rows into one. `GROUP BY` makes one group per distinct key, and
the aggregate runs **per group**. `WHERE` filters rows *before* grouping; `HAVING` filters
groups *after*.

Line revenue = `quantity * unit_price_kurus` (from `order_items`). These exercises stay on
one or two tables; joins get their own section next.

### 02.01 — One-row summary

**Task:** In one row: number of products `n`, average price in TL `avg_tl` (rounded to 2), cheapest `min_tl` and most expensive `max_tl` (in TL).

<details><summary>Hint</summary>

`COUNT(*)`, `ROUND(AVG(price_kurus) / 100.0, 2)`, `MIN(...)/100.0`, `MAX(...)/100.0`
</details>

**Expected result:**

```text
┌────┬─────────┬────────┬────────┐
│ n  │ avg_tl  │ min_tl │ max_tl │
├────┼─────────┼────────┼────────┤
│ 41 │ 4760.15 │     90 │  42999 │
└────┴─────────┴────────┴────────┘
```


### 02.02 — COUNT(*) vs COUNT(col) vs COUNT(DISTINCT col)

**Concept:** `COUNT(*)` counts rows. `COUNT(col)` skips NULLs. `COUNT(DISTINCT col)` counts different non-NULL values.

**Task:** On `customers`, return `all_rows`, `with_phone`, `with_city`, `distinct_cities` in one row.

**Expected result:**

```text
┌──────────┬────────────┬───────────┬─────────────────┐
│ all_rows │ with_phone │ with_city │ distinct_cities │
├──────────┼────────────┼───────────┼─────────────────┤
│       80 │         62 │        72 │               8 │
└──────────┴────────────┴───────────┴─────────────────┘
```


### 02.03 — Orders per status

**Task:** How many orders are there per `status`? Columns `status, n`, biggest group first.

**Expected result:**

```text
┌───────────┬─────┐
│  status   │  n  │
├───────────┼─────┤
│ delivered │ 339 │
│ cancelled │  36 │
│ returned  │  20 │
│ pending   │  13 │
│ shipped   │  12 │
└───────────┴─────┘
```


### 02.04 — Order value

**Task:** For each order compute its value in TL from `order_items` as `total_tl`. Return the **5 largest** orders: `order_id, total_tl`.

<details><summary>Hint</summary>

`SUM(quantity * unit_price_kurus) / 100.0` grouped by `order_id`.
</details>

**Expected result:**

```text
┌──────────┬──────────┐
│ order_id │ total_tl │
├──────────┼──────────┤
│      326 │   162644 │
│       83 │   161194 │
│      113 │   150695 │
│      245 │   133315 │
│      410 │   128945 │
└──────────┴──────────┘
```


### 02.05 — Group by an expression: months

**Concept:** You can group by any expression. `strftime('%Y-%m', ordered_at)` or `substr(ordered_at, 1, 7)` turn a timestamp into a month key.

**Task:** Number of orders per month **in 2026**: `month` (like `2026-01`) and `n`, chronological.

**Expected result:**

```text
┌─────────┬────┐
│  month  │ n  │
├─────────┼────┤
│ 2026-01 │ 15 │
│ 2026-02 │ 11 │
│ 2026-03 │ 22 │
│ 2026-04 │ 26 │
│ 2026-05 │ 30 │
│ 2026-06 │ 27 │
│ 2026-07 │ 43 │
│ 2026-08 │ 35 │
│ 2026-09 │ 48 │
│ 2026-10 │ 63 │
└─────────┴────┘
```


### 02.06 — HAVING

**Task:** Which cities have **at least 10 customers**? Columns `city, n`, biggest first. Ignore customers without a city.

<details><summary>Hint</summary>

`WHERE city IS NOT NULL ... GROUP BY city HAVING COUNT(*) >= 10`
</details>

**Expected result:**

```text
┌──────────┬────┐
│   city   │ n  │
├──────────┼────┤
│ Istanbul │ 17 │
│ Ankara   │ 14 │
│ Samsun   │ 12 │
└──────────┴────┘
```


### 02.07 — WHERE and HAVING together

**Task:** Loyal customers: `customer_id` and `n` for customers with **at least 12 orders that were not cancelled**. Order by `n` desc, then `customer_id`.

<details><summary>Hint</summary>

Cancelled orders must be removed *before* counting → WHERE. The threshold applies to the count → HAVING.
</details>

**Expected result:**

```text
┌─────────────┬────┐
│ customer_id │ n  │
├─────────────┼────┤
│          80 │ 18 │
│          14 │ 17 │
│          53 │ 17 │
│          67 │ 17 │
│          13 │ 15 │
│          78 │ 14 │
│          23 │ 13 │
│          24 │ 13 │
│          45 │ 13 │
│           1 │ 12 │
│          15 │ 12 │
│          28 │ 12 │
└─────────────┴────┘
```


### 02.08 — Ratings that mean something

**Task:** Average rating per `product_id` (rounded to 2, as `avg_rating`) and the number of reviews `n`, but only for products with **at least 5 reviews**. Best first.

**Expected result:**

```text
┌────────────┬────────────┬───┐
│ product_id │ avg_rating │ n │
├────────────┼────────────┼───┤
│         41 │        4.2 │ 5 │
│         16 │        4.2 │ 5 │
│         10 │          4 │ 5 │
│          4 │       3.86 │ 7 │
│         33 │       3.83 │ 6 │
│         31 │       3.83 │ 6 │
│         37 │        3.6 │ 5 │
│          6 │        3.6 │ 5 │
│         11 │        3.5 │ 6 │
│          8 │       3.43 │ 7 │
│          5 │        3.4 │ 5 │
│         27 │        3.2 │ 5 │
└────────────┴────────────┴───┘
... 16 rows total (first 12 shown)
```


### 02.09 — A ratio from two counts

**Concept:** `COUNT(*) * 1.0 / COUNT(DISTINCT x)` = average number of rows per x — no subquery needed.

**Task:** On average, how many different products (line items) does an order contain? One column `avg_lines`, rounded to 2.

**Expected result:**

```text
┌───────────┐
│ avg_lines │
├───────────┤
│       2.1 │
└───────────┘
```


### 02.10 — Grouping by two columns

**Task:** Total paid in TL per **year** and **payment method**: `year, method, total_tl`. Sort by year, then total descending.

<details><summary>Hint</summary>

`strftime('%Y', paid_at)` and `GROUP BY year, method`
</details>

**Expected result:**

```text
┌──────┬──────────┬──────────┐
│ year │  method  │ total_tl │
├──────┼──────────┼──────────┤
│ 2025 │ card     │  1017389 │
│ 2025 │ cash     │   186519 │
│ 2025 │ transfer │   168015 │
│ 2026 │ card     │  3348557 │
│ 2026 │ transfer │   582530 │
│ 2026 │ cash     │   286141 │
└──────┴──────────┴──────────┘
```


### 02.11 — Birth decades

**Task:** Count customers per birth decade: `decade` (e.g. `1980`) and `n`. Skip unknown birth dates. Oldest decade first.

<details><summary>Hint</summary>

`CAST(substr(birth_date, 1, 3) AS INTEGER) * 10` or `(CAST(strftime('%Y', birth_date) AS INTEGER) / 10) * 10`
</details>

**Expected result:**

```text
┌────────┬────┐
│ decade │ n  │
├────────┼────┤
│   1960 │ 11 │
│   1970 │ 16 │
│   1980 │ 17 │
│   1990 │ 13 │
│   2000 │ 11 │
└────────┴────┘
```


### 02.12 — Most recent order per customer

**Concept:** `MAX()` works on text dates because ISO-8601 strings sort chronologically.

**Task:** For each customer who ordered: `customer_id, last_order` (their latest `ordered_at`). Show the 5 customers whose last order is the **oldest** (the ones we're losing).

**Expected result:**

```text
┌─────────────┬─────────────────────┐
│ customer_id │     last_order      │
├─────────────┼─────────────────────┤
│          42 │ 2025-06-12 18:52:58 │
│          54 │ 2025-10-15 01:16:35 │
│          73 │ 2026-01-14 13:24:54 │
│          17 │ 2026-02-28 11:28:04 │
│          51 │ 2026-04-01 23:08:13 │
└─────────────┴─────────────────────┘
```

> SQLite lets you put a non-aggregated column next to MAX() (a 'bare column') and picks the value from the max row. Other databases reject that — don't rely on it.


### 02.13 — Best sellers by units

**Task:** Top 3 `product_id`s by total units sold (`units`), counting only order lines (all statuses).

**Expected result:**

```text
┌────────────┬───────┐
│ product_id │ units │
├────────────┼───────┤
│         37 │    54 │
│         19 │    45 │
│         27 │    44 │
└────────────┴───────┘
```


### 02.14 — Aggregates ignore NULL

**Concept:** `AVG(col)` divides by the number of **non-NULL** values, not by the number of rows.

**Task:** In `reviews`, return in one row: `total` reviews, `with_comment` (comment not NULL) and `pct_with_comment` rounded to 1 decimal.

<details><summary>Hint</summary>

`ROUND(100.0 * COUNT(comment) / COUNT(*), 1)`
</details>

**Expected result:**

```text
┌───────┬──────────────┬──────────────────┐
│ total │ with_comment │ pct_with_comment │
├───────┼──────────────┼──────────────────┤
│   153 │          107 │             69.9 │
└───────┴──────────────┴──────────────────┘
```

