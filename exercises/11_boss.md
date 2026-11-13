# 11 — Boss level: window functions, gaps & islands, big data, indexes

**Database:** `shop` · **Course link:** Beyond Hafta 5 — window functions and indexes (likely coming soon in the course; standard interview material)

**Window functions** compute over a set of rows *related to the current row* without collapsing
them like GROUP BY does:

```sql
fn(...) OVER (PARTITION BY group_cols ORDER BY sort_cols [ROWS BETWEEN ...])
```
`ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LAG(x)`, `LEAD(x)`, `SUM(x) OVER (...)`,
`FIRST_VALUE(x)`. You can't use them in WHERE — wrap the query in a CTE and filter outside.

The last exercises run on your **scenario.db** (600k students, 1.2M registrations). Read-only
exercises are graded against `../scenario/scenario.db` opened read-only; your playground copy is
`db/scenario.db` (`./drill reset scenario`).

### 11.01 — Top 3 per group (ROW_NUMBER)

**Task:** For each category (by name), the 3 products with the highest delivered revenue: `category, product, revenue_tl, rn`. Skip uncategorised products. Order by category, rn.

**Expected result:**

```text
┌─────────────┬─────────────────────┬────────────┬────┐
│  category   │       product       │ revenue_tl │ rn │
├─────────────┼─────────────────────┼────────────┼────┤
│ Accessories │ Mechanical Keyboard │      54691 │  1 │
│ Accessories │ Webcam HD           │      28296 │  2 │
│ Accessories │ USB-C Hub           │      23449 │  3 │
│ Audio       │ Headphones NC       │     123177 │  1 │
│ Audio       │ Bluetooth Speaker   │      58084 │  2 │
│ Audio       │ Earbuds             │      42365 │  3 │
│ Camping     │ Tent 2P             │      99021 │  1 │
│ Camping     │ Sleeping Bag        │      39654 │  2 │
│ Comics      │ Watchmen            │      14129 │  1 │
│ Computers   │ 27in Monitor        │     158228 │  1 │
│ Fitness     │ Dumbbell Set        │      47190 │  1 │
│ Fitness     │ Yoga Mat            │      14842 │  2 │
└─────────────┴─────────────────────┴────────────┴────┘
... 32 rows total (first 12 shown)
```


### 11.02 — RANK vs DENSE_RANK vs ROW_NUMBER

**Task:** Rank customers by number of orders: `customer_id, n, row_number, rank, dense_rank` (all ordered by n desc; ROW_NUMBER ties broken by customer_id). Show only rows with `dense_rank <= 4`, ordered by row_number.

**Expected result:**

```text
┌─────────────┬────┬────────────┬──────┬────────────┐
│ customer_id │ n  │ row_number │ rank │ dense_rank │
├─────────────┼────┼────────────┼──────┼────────────┤
│          80 │ 19 │          1 │    1 │          1 │
│          53 │ 18 │          2 │    2 │          2 │
│          13 │ 17 │          3 │    3 │          3 │
│          14 │ 17 │          4 │    3 │          3 │
│          67 │ 17 │          5 │    3 │          3 │
│          23 │ 15 │          6 │    6 │          4 │
│          24 │ 15 │          7 │    6 │          4 │
│          78 │ 15 │          8 │    6 │          4 │
└─────────────┴────┴────────────┴──────┴────────────┘
```


### 11.03 — Running total

**Task:** Delivered revenue per month of 2026 (`month, revenue_tl`) and the year-to-date running total `ytd_tl`. Chronological.

**Expected result:**

```text
┌─────────┬────────────┬─────────┐
│  month  │ revenue_tl │ ytd_tl  │
├─────────┼────────────┼─────────┤
│ 2026-01 │     413990 │  413990 │
│ 2026-02 │     136538 │  550528 │
│ 2026-03 │     220014 │  770542 │
│ 2026-04 │     307657 │ 1078199 │
│ 2026-05 │     131719 │ 1209918 │
│ 2026-06 │     310804 │ 1520722 │
│ 2026-07 │     758435 │ 2279157 │
│ 2026-08 │     415348 │ 2694505 │
│ 2026-09 │     508182 │ 3202687 │
│ 2026-10 │     531284 │ 3733971 │
└─────────┴────────────┴─────────┘
```


### 11.04 — Share of total

**Task:** Revenue share per payment method across all payments: `method, total_tl, pct` (pct of the grand total, 1 decimal), biggest first. Use `SUM(...) OVER ()`.

**Expected result:**

```text
┌──────────┬──────────┬──────┐
│  method  │ total_tl │ pct  │
├──────────┼──────────┼──────┤
│ card     │  4365946 │ 78.1 │
│ transfer │   750545 │ 13.4 │
│ cash     │   472660 │  8.5 │
└──────────┴──────────┴──────┘
```

> `SUM(SUM(x)) OVER ()`: the inner SUM is the GROUP BY aggregate, the outer is a window over the grouped rows.


### 11.05 — Time between orders (LAG)

**Task:** For customers with at least 10 orders: `customer_id, orders, avg_gap_days` = average number of days between consecutive orders (1 decimal). Shortest gap first.

<details><summary>Hint</summary>

`julianday(ordered_at) - julianday(LAG(ordered_at) OVER (PARTITION BY customer_id ORDER BY ordered_at))`
</details>

**Expected result:**

```text
┌─────────────┬────────┬──────────────┐
│ customer_id │ orders │ avg_gap_days │
├─────────────┼────────┼──────────────┤
│          26 │     12 │          4.9 │
│          14 │     17 │         10.8 │
│          24 │     15 │         10.8 │
│          13 │     17 │           12 │
│          77 │     10 │         13.8 │
│          15 │     13 │         18.8 │
│          80 │     19 │         21.1 │
│          28 │     13 │         22.1 │
│          53 │     18 │         24.5 │
│          67 │     17 │         35.9 │
│          12 │     13 │         39.7 │
│          23 │     15 │         43.6 │
└─────────────┴────────┴──────────────┘
... 18 rows total (first 12 shown)
```


### 11.06 — What do people buy first?

**Task:** For each customer take their **first** order (earliest `ordered_at`). Over all those first orders, which products appear most? `product, first_orders`, top 5, ties by name.

**Expected result:**

```text
┌─────────────────────────────┬──────────────┐
│           product           │ first_orders │
├─────────────────────────────┼──────────────┤
│ Coffee Maker                │            8 │
│ Bluetooth Speaker           │            7 │
│ Mystery Box                 │            7 │
│ Saatleri Ayarlama Enstitusu │            7 │
│ Office Chair                │            6 │
└─────────────────────────────┴──────────────┘
```


### 11.07 — Cohorts

**Task:** Group customers by the quarter they joined (`cohort` like `2025-Q3`). Per cohort: `customers`, `quick_buyers` = customers whose first order came within 30 days of joining, `pct` (1 decimal). Chronological.

<details><summary>Hint</summary>

Quarter: `strftime('%Y', d) || '-Q' || ((CAST(strftime('%m', d) AS INTEGER) + 2) / 3)`. First order per customer with MIN.
</details>

**Expected result:**

```text
┌─────────┬───────────┬──────────────┬──────┐
│ cohort  │ customers │ quick_buyers │ pct  │
├─────────┼───────────┼──────────────┼──────┤
│ 2024-Q3 │         2 │            0 │    0 │
│ 2024-Q4 │         4 │            0 │    0 │
│ 2025-Q1 │        10 │            3 │   30 │
│ 2025-Q2 │         8 │            1 │ 12.5 │
│ 2025-Q3 │        10 │            2 │   20 │
│ 2025-Q4 │        11 │            2 │ 18.2 │
│ 2026-Q1 │        11 │            5 │ 45.5 │
│ 2026-Q2 │        11 │            5 │ 45.5 │
│ 2026-Q3 │        10 │            6 │   60 │
│ 2026-Q4 │         3 │            3 │  100 │
└─────────┴───────────┴──────────────┴──────┘
```


### 11.08 — Transfers (transit)

_db: `transit`_

**Task:** A *transfer* is a boarding that happens within 60 minutes of the same card's previous boarding. Top 5 cards by number of transfers: `card_id, owner, transfers` (ties by card_id).

**Expected result:**

```text
┌─────────┬─────────┬───────────┐
│ card_id │  owner  │ transfers │
├─────────┼─────────┼───────────┤
│      17 │ Irem P. │        14 │
│      13 │ Ece K.  │        12 │
│       1 │ Ayse Y. │        11 │
│      21 │ Esra Y. │        11 │
│      23 │ Seda D. │        11 │
└─────────┴─────────┴───────────┘
```


### 11.09 — Gaps and islands: longest riding streak (transit)

_db: `transit`_

**Concept:** Classic trick: for consecutive days, `day - ROW_NUMBER()` is constant. Group by that difference and each group is one unbroken streak (an *island*).

**Task:** For each card, its longest run of **consecutive days with at least one boarding**. Top 5: `card_id, streak_days, from_day, to_day` (ties by card_id).

<details><summary>Hint</summary>

1) distinct (card_id, date(datetime)); 2) `julianday(day) - ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY day)` as grp; 3) GROUP BY card_id, grp.
</details>

**Expected result:**

```text
┌─────────┬─────────────┬────────────┬────────────┐
│ card_id │ streak_days │  from_day  │   to_day   │
├─────────┼─────────────┼────────────┼────────────┤
│      13 │          22 │ 2026-09-30 │ 2026-10-21 │
│       5 │          19 │ 2026-09-24 │ 2026-10-12 │
│      26 │          19 │ 2026-10-09 │ 2026-10-27 │
│      22 │          15 │ 2026-10-16 │ 2026-10-30 │
│      17 │          13 │ 2026-10-02 │ 2026-10-14 │
└─────────┴─────────────┴────────────┴────────────┘
```


### 11.10 — Busiest station per district (transit)

_db: `transit`_

**Task:** For each district, the station with the most boardings: `district, station, boardings`. By district.

**Expected result:**

```text
┌──────────┬─────────────────┬───────────┐
│ district │     station     │ boardings │
├──────────┼─────────────────┼───────────┤
│ Atakum   │ Cakirlar        │       228 │
│ Canik    │ Kalkanca        │       110 │
│ Ilkadim  │ Hastane         │       249 │
│ Tekkekoy │ Tekkekoy Merkez │       132 │
└──────────┴─────────────────┴───────────┘
```


### 11.11 — Six-table join at scale (scenario)

_db: `scenario`_

**Task:** Top 5 countries by number of students: `country, students`. Path: students → department → university → city → state → country.

**Expected result:**

```text
┌──────────────────────────┬──────────┐
│         country          │ students │
├──────────────────────────┼──────────┤
│ Kiribati                 │    10722 │
│ Trinidad and Tobago      │     9761 │
│ Finland                  │     9519 │
│ United States of America │     9301 │
│ Norway                   │     9028 │
└──────────────────────────┴──────────┘
```


### 11.12 — Overbooked events (scenario)

_db: `scenario`_

**Task:** How many events have more registrations than `capacity`? Return `overbooked`. **Don't** use a correlated subquery per event (try it with LIMIT and see why) — aggregate `register` once, then join.

**Expected result:**

```text
┌────────────┐
│ overbooked │
├────────────┤
│        110 │
└────────────┘
```


### 11.13 — Data integrity audit (scenario)

_db: `scenario`_

**Task:** One row with three counts: `richer_than_manager` (teachers paid more than their own department's manager), `manager_elsewhere` (departments whose manager belongs to a different department), `closed_clubs_with_members` (closed clubs that still have member rows).

**Expected result:**

```text
┌─────────────────────┬───────────────────┬───────────────────────────┐
│ richer_than_manager │ manager_elsewhere │ closed_clubs_with_members │
├─────────────────────┼───────────────────┼───────────────────────────┤
│               11992 │              2032 │                      1219 │
└─────────────────────┴───────────────────┴───────────────────────────┘
```


### 11.14 — Students per year, pivoted (scenario)

_db: `scenario`_

**Task:** For the 5 universities with the most students: `university` (name + ' #' + id, since names repeat), `total`, and counts for `y1`..`y6` (study year) as columns. Biggest first.

**Expected result:**

```text
┌─────────────────────────┬───────┬────┬────┬────┬────┬────┬────┐
│       university        │ total │ y1 │ y2 │ y3 │ y4 │ y5 │ y6 │
├─────────────────────────┼───────┼────┼────┼────┼────┼────┼────┤
│ Hester University #3872 │   141 │ 23 │ 24 │ 25 │ 25 │ 24 │ 20 │
│ Jackson College #4073   │   138 │ 15 │ 20 │ 24 │ 15 │ 38 │ 26 │
│ Wilkerson Academy #1247 │   133 │ 23 │ 30 │ 33 │ 14 │ 17 │ 16 │
│ Tanner Academy #5012    │   132 │ 14 │ 20 │ 24 │ 24 │ 29 │ 21 │
│ Morrison Institute #44  │   131 │ 22 │ 23 │ 28 │ 24 │ 16 │ 18 │
└─────────────────────────┴───────┴────┴────┴────┴────┴────┴────┘
```

> `SUM(s.year = 1)` works because a comparison is 1 or 0 in SQLite — a shortcut for `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`.


### 11.15 — Why was it slow? EXPLAIN QUERY PLAN (scenario)

_db: `scenario`_

**Concept:** `EXPLAIN QUERY PLAN <query>` shows how SQLite will run it. `SCAN t` = read every row; `SEARCH t USING INDEX ...` = jump straight to the matches. `register`'s primary key is `(student_id, event_id)`, which helps lookups by student, **not** by event.

**Task:** Show the plan for `SELECT COUNT(*) FROM register WHERE event_id = 123;` and for `... WHERE student_id = 123;`. Return the second one's plan.

**Expected result:**

```text
┌────┬────────┬─────────┬─────────────────────────────────────────────────────────────────────────────────┐
│ id │ parent │ notused │                                     detail                                      │
├────┼────────┼─────────┼─────────────────────────────────────────────────────────────────────────────────┤
│  3 │      0 │      56 │ SEARCH register USING COVERING INDEX sqlite_autoindex_register_1 (student_id=?) │
└────┴────────┴─────────┴─────────────────────────────────────────────────────────────────────────────────┘
```

> The `event_id` version says `SCAN register` — 1.2M rows per lookup. Inside a correlated subquery that's 60 000 × 1.2M row reads.


### 11.16 — Add an index (scenario)

_db: `scenario` · ✏️ changes the DB — `./drill catchup 11.16` first if your DB is out of sync_

**Task:** On your scenario copy, create an index `register_event` on `register(event_id)`. Then the plan for `WHERE event_id = 123` changes. (Bonus: rerun the correlated version of 11.12 and time it with `.timer on`.)

**After your script, this check:**

```sql
EXPLAIN QUERY PLAN SELECT COUNT(*) FROM register WHERE event_id = 123;
```

should print:

```text
┌────┬────────┬─────────┬──────────────────────────────────────────────────────────────────┐
│ id │ parent │ notused │                              detail                              │
├────┼────────┼─────────┼──────────────────────────────────────────────────────────────────┤
│  3 │      0 │      55 │ SEARCH register USING COVERING INDEX register_event (event_id=?) │
└────┴────────┴─────────┴──────────────────────────────────────────────────────────────────┘
```

> Indexes speed up reads but cost disk space and slow down every INSERT/UPDATE/DELETE on that table. Check the file size before/after.

