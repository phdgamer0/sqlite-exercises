# 09 — CTEs (WITH) and recursive CTEs

**Database:** `shop` · **Course link:** Hafta 5 – CTE ile geçici ara sonuçlar (+ WITH RECURSIVE, beyond the slides)

A CTE is a view that lives for **one statement**:

```sql
WITH spend AS (SELECT ...), big AS (SELECT ... FROM spend ...)
SELECT ... FROM big;
```
CTEs make long queries readable top-to-bottom and let you reuse one intermediate result twice.

`WITH RECURSIVE` adds a loop: an anchor query, `UNION ALL`, and a recursive query that refers
to the CTE itself, repeated until it produces no new rows. Trees (categories, org charts,
referrals) and generated series (calendars) are the classic uses.

### 09.01 — Rewrite a subquery as a CTE

**Task:** Customers whose delivered spend is **above the average delivered spend** of customers who bought something. `customer_id, spend_tl`, biggest first. Use a CTE `spend`.

**Expected result:**

```text
┌─────────────┬──────────┐
│ customer_id │ spend_tl │
├─────────────┼──────────┤
│          53 │   379793 │
│           1 │   312396 │
│          80 │   305109 │
│          79 │   226209 │
│          14 │   223174 │
│          74 │   213296 │
│          78 │   202546 │
│          73 │   196570 │
│          35 │   155602 │
│          46 │   142991 │
│          24 │   136577 │
│          37 │   135214 │
└─────────────┴──────────┘
... 24 rows total (first 12 shown)
```


### 09.02 — Month over month (CTE joined to itself)

**Task:** Delivered revenue per month (`month`, `revenue_tl`) and the previous month's revenue (`prev_tl`) and the change in percent (`change_pct`, 1 decimal). 2026 months only, chronological. Do it with a CTE joined to itself — no window functions.

<details><summary>Hint</summary>

Join `m AS cur` to `m AS prev` on `prev.month = strftime('%Y-%m', cur.month || '-01', '-1 month')`.
</details>

**Expected result:**

```text
┌─────────┬────────────┬─────────┬────────────┐
│  month  │ revenue_tl │ prev_tl │ change_pct │
├─────────┼────────────┼─────────┼────────────┤
│ 2026-01 │     413990 │  141441 │      192.7 │
│ 2026-02 │     136538 │  413990 │        -67 │
│ 2026-03 │     220014 │  136538 │       61.1 │
│ 2026-04 │     307657 │  220014 │       39.8 │
│ 2026-05 │     131719 │  307657 │      -57.2 │
│ 2026-06 │     310804 │  131719 │        136 │
│ 2026-07 │     758435 │  310804 │        144 │
│ 2026-08 │     415348 │  758435 │      -45.2 │
│ 2026-09 │     508182 │  415348 │       22.4 │
│ 2026-10 │     531284 │  508182 │        4.5 │
└─────────┴────────────┴─────────┴────────────┘
```


### 09.03 — Two CTEs, one answer

**Task:** Per city (customer city, known only): `city`, `customers`, `buyers` (customers with ≥1 delivered order) and `conversion_pct` (1 decimal). Use a CTE for buyers and one for customers per city. Best conversion first.

**Expected result:**

```text
┌───────────┬───────────┬────────┬────────────────┐
│   city    │ customers │ buyers │ conversion_pct │
├───────────┼───────────┼────────┼────────────────┤
│ Antalya   │         9 │      9 │            100 │
│ Bursa     │         3 │      3 │            100 │
│ Eskisehir │         8 │      8 │            100 │
│ Izmir     │         8 │      8 │            100 │
│ Trabzon   │         1 │      1 │            100 │
│ Samsun    │        12 │     11 │           91.7 │
│ Istanbul  │        17 │     12 │           70.6 │
│ Ankara    │        14 │      8 │           57.1 │
└───────────┴───────────┴────────┴────────────────┘
```


### 09.04 — A lookup table from VALUES

**Concept:** `WITH bands(name, lo, hi) AS (VALUES ('cheap', 0, 50000), ...)` creates a tiny inline table — then join on a **range** (`price >= lo AND price < hi`).

**Task:** Using a VALUES CTE with bands cheap [0, 500 TL), mid [500, 5000 TL), premium [5000 TL, ∞): units sold per band in delivered orders — `band, units`, ordered cheap → premium.

**Expected result:**

```text
┌─────────┬───────┐
│  band   │ units │
├─────────┼───────┤
│ cheap   │   359 │
│ mid     │   507 │
│ premium │   188 │
└─────────┴───────┘
```


### 09.05 — Recursive warm-up: 1 to 10

**Task:** Produce one column `n` with the numbers 1..10 using `WITH RECURSIVE`.

**Expected result:**

```text
┌────┐
│ n  │
├────┤
│  1 │
│  2 │
│  3 │
│  4 │
│  5 │
│  6 │
│  7 │
│  8 │
│  9 │
│ 10 │
└────┘
```


### 09.06 — A calendar with zero days

**Task:** Orders per day for every day of **October 2026** — days without orders show 0. Columns `day, orders`; return only the days with 0 orders.

<details><summary>Hint</summary>

Recursive CTE of dates: `SELECT date(day, '+1 day') ... WHERE day < '2026-10-31'`, LEFT JOIN orders on `date(ordered_at) = day`.
</details>

**Expected result:**

```text
┌────────────┬────────┐
│    day     │ orders │
├────────────┼────────┤
│ 2026-10-05 │      0 │
│ 2026-10-14 │      0 │
│ 2026-10-17 │      0 │
└────────────┴────────┘
```


### 09.07 — Category paths

**Task:** For every category show its full path like `Electronics > Computers > Laptops`: columns `id, path, depth` (top level = 1). Order by path.

**Expected result:**

```text
┌────┬───────────────────────────────────────┬───────┐
│ id │                 path                  │ depth │
├────┼───────────────────────────────────────┼───────┤
│  2 │ Books                                 │     1 │
│ 12 │ Books > Comics                        │     2 │
│ 10 │ Books > Novels                        │     2 │
│ 11 │ Books > Science                       │     2 │
│  1 │ Electronics                           │     1 │
│  7 │ Electronics > Audio                   │     2 │
│  5 │ Electronics > Computers               │     2 │
│  9 │ Electronics > Computers > Accessories │     3 │
│  8 │ Electronics > Computers > Laptops     │     3 │
│  6 │ Electronics > Phones                  │     2 │
│  3 │ Home                                  │     1 │
│ 14 │ Home > Furniture                      │     2 │
└────┴───────────────────────────────────────┴───────┘
... 17 rows total (first 12 shown)
```


### 09.08 — Revenue of a whole subtree

**Task:** Total delivered revenue in TL (`revenue_tl`) of **Electronics including all its descendants** (Computers, Laptops, Accessories, Phones, Audio...).

**Expected result:**

```text
┌────────────┐
│ revenue_tl │
├────────────┤
│    4344772 │
└────────────┘
```


### 09.09 — Org chart

**Task:** Print the org chart: `chart` = name indented by 4 spaces per level (CEO not indented), `level` (CEO = 0). Order so that each person appears directly under their manager (depth-first).

<details><summary>Hint</summary>

Carry a sort key: the path of ids, e.g. `printf('%03d', id)` concatenated per level, then `ORDER BY sort_key`. Indent with `substr('                        ', 1, level * 4)`.
</details>

**Expected result:**

```text
┌─────────────────────────────────────────┬───────┐
│                  chart                  │ level │
├─────────────────────────────────────────┼───────┤
│ Oguz Kural (CEO)                        │     0 │
│     Selin Aydin (Sales Director)        │     1 │
│         Elif Demir (Sales Manager)      │     2 │
│             Zeynep Arslan (Sales Rep)   │     3 │
│                 Pinar Gunes (Intern)    │     4 │
│             Emre Sahin (Sales Rep)      │     3 │
│         Kerem Kaya (Sales Manager)      │     2 │
│             Gizem Polat (Sales Rep)     │     3 │
│             Can Tekin (Sales Rep)       │     3 │
│     Burak Celik (Ops Director)          │     1 │
│         Derya Koc (Warehouse Lead)      │     2 │
│             Ufuk Kurt (Warehouse Staff) │     3 │
└─────────────────────────────────────────┴───────┘
```


### 09.10 — Walk up a chain

**Task:** Customer 70 was referred by someone, who was referred by someone, ... List the chain from 70 up to the first customer who has no referrer: `step` (70 itself is 0), `id`, `first_name`, `last_name`.

**Expected result:**

```text
┌──────┬────┬────────────┬───────────┐
│ step │ id │ first_name │ last_name │
├──────┼────┼────────────┼───────────┤
│    0 │ 70 │ Emre       │ Kurt      │
│    1 │ 50 │ Selin      │ Gunes     │
│    2 │ 25 │ Mustafa    │ Ozturk    │
│    3 │ 10 │ Selin      │ Kural     │
│    4 │  3 │ Ayse       │ Celik     │
└──────┴────┴────────────┴───────────┘
```


### 09.11 — Managers' total team salary

**Task:** For each employee who manages anyone: `manager` (first name) and `team_tl` = total yearly salary in TL of **everyone below them** (direct and indirect reports, not themselves). Biggest first.

<details><summary>Hint</summary>

Recursive CTE of (manager_id, employee_id) pairs: start with direct reports, then extend each pair one level down.
</details>

**Expected result:**

```text
┌─────────┬─────────┐
│ manager │ team_tl │
├─────────┼─────────┤
│ Oguz    │  672000 │
│ Selin   │  351000 │
│ Elif    │  106000 │
│ Kerem   │   87000 │
│ Burak   │   86000 │
│ Derya   │   34000 │
│ Zeynep  │   18000 │
└─────────┴─────────┘
```


### 09.12 — CTE in a write statement

_✏️ changes the DB — `./drill catchup 09.12` first if your DB is out of sync_

**Concept:** A CTE can sit in front of INSERT / UPDATE / DELETE too.

**Task:** Using a CTE `top_buyers` (the 3 customers with the highest delivered spend), insert one review per top buyer for product 37 (Yoga Mat), rating 5, comment `Thanks for being a top customer`, created_at `2026-11-13`.

**After your script, this check:**

```sql
SELECT customer_id, rating, comment FROM reviews WHERE created_at = '2026-11-13' ORDER BY customer_id;
```

should print:

```text
┌─────────────┬────────┬─────────────────────────────────┐
│ customer_id │ rating │             comment             │
├─────────────┼────────┼─────────────────────────────────┤
│           1 │      5 │ Thanks for being a top customer │
│          53 │      5 │ Thanks for being a top customer │
│          80 │      5 │ Thanks for being a top customer │
└─────────────┴────────┴─────────────────────────────────┘
```

