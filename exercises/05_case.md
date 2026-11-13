# 05 — CASE, COALESCE, NULLIF, conditional aggregation

**Database:** `shop` · **Course link:** Not a separate lecture — used everywhere (labels, pivots, safe division, CASE in UPDATE)

`CASE` is SQL's if/else **expression** — it returns a value, so it can go anywhere a value can:
SELECT list, WHERE, ORDER BY, GROUP BY, inside aggregates, inside UPDATE ... SET.

```sql
CASE WHEN cond1 THEN a WHEN cond2 THEN b ELSE c END   -- searched CASE (use this one)
CASE col WHEN 1 THEN 'x' WHEN 2 THEN 'y' END          -- simple CASE (equality only)
```
No ELSE → NULL. The first matching WHEN wins.

### 05.01 — Price bands

**Task:** Label every product `cheap` (< 500 TL), `mid` (< 5000 TL) or `premium`, and count products per band: `band, n`. Order the bands cheap, mid, premium.

<details><summary>Hint</summary>

GROUP BY the CASE expression (or its alias). For the order, `ORDER BY MIN(price_kurus)` is a neat trick.
</details>

**Expected result:**

```text
┌─────────┬────┐
│  band   │ n  │
├─────────┼────┤
│ cheap   │ 15 │
│ mid     │ 19 │
│ premium │  7 │
└─────────┴────┘
```


### 05.02 — Custom sort order

**Concept:** `ORDER BY CASE ... END` lets you sort by any business rule instead of alphabetically.

**Task:** Count orders per status (`status, n`) but list them in workflow order: pending, shipped, delivered, returned, cancelled.

**Expected result:**

```text
┌───────────┬─────┐
│  status   │  n  │
├───────────┼─────┤
│ pending   │  13 │
│ shipped   │  12 │
│ delivered │ 339 │
│ returned  │  20 │
│ cancelled │  36 │
└───────────┴─────┘
```


### 05.03 — Pivot with conditional aggregation

**Concept:** `SUM(CASE WHEN cond THEN 1 ELSE 0 END)` counts rows matching `cond` inside each group. One such column per value = a pivot table.

**Task:** For each month of **2026**: `month, delivered, cancelled, returned, other` (counts). Chronological.

**Expected result:**

```text
┌─────────┬───────────┬───────────┬──────────┬───────┐
│  month  │ delivered │ cancelled │ returned │ other │
├─────────┼───────────┼───────────┼──────────┼───────┤
│ 2026-01 │        11 │         2 │        2 │     0 │
│ 2026-02 │        11 │         0 │        0 │     0 │
│ 2026-03 │        20 │         0 │        2 │     0 │
│ 2026-04 │        22 │         3 │        1 │     0 │
│ 2026-05 │        25 │         2 │        3 │     0 │
│ 2026-06 │        26 │         1 │        0 │     0 │
│ 2026-07 │        40 │         2 │        1 │     0 │
│ 2026-08 │        31 │         3 │        1 │     0 │
│ 2026-09 │        37 │         7 │        4 │     0 │
│ 2026-10 │        30 │         7 │        1 │    25 │
└─────────┴───────────┴───────────┴──────────┴───────┘
```


### 05.04 — Money pivot

**Task:** Per year (`year`), total paid in TL by method as three columns `card_tl, cash_tl, transfer_tl`. Use `SUM(CASE ... THEN amount ...)`.

**Expected result:**

```text
┌──────┬─────────┬─────────┬─────────────┐
│ year │ card_tl │ cash_tl │ transfer_tl │
├──────┼─────────┼─────────┼─────────────┤
│ 2025 │ 1017389 │  186519 │      168015 │
│ 2026 │ 3348557 │  286141 │      582530 │
└──────┴─────────┴─────────┴─────────────┘
```


### 05.05 — COALESCE: first non-NULL wins

**Task:** For customers 1–10: `id`, `contact` = phone if known, otherwise email; `city` = city or `'Unknown'`. By id.

**Expected result:**

```text
┌────┬───────────────────────────┬──────────┐
│ id │          contact          │   city   │
├────┼───────────────────────────┼──────────┤
│  1 │ onur.erdogan1@omu.edu.tr  │ Izmir    │
│  2 │ ayse.dogan2@mail.com      │ Istanbul │
│  3 │ 05569882389               │ Istanbul │
│  4 │ 05441044863               │ Istanbul │
│  5 │ baris.yilmaz5@example.org │ Samsun   │
│  6 │ 05528341313               │ Unknown  │
│  7 │ 05324679185               │ Bursa    │
│  8 │ fatma.kaya8@mail.com      │ Ankara   │
│  9 │ selin.koc9@example.org    │ Antalya  │
│ 10 │ selin.kural10@omu.edu.tr  │ Istanbul │
└────┴───────────────────────────┴──────────┘
```


### 05.06 — NULLIF: safe division

**Concept:** `NULLIF(a, b)` returns NULL when a = b. `x / NULLIF(y, 0)` gives NULL instead of a divide-by-zero surprise. (SQLite returns NULL for /0 anyway, but most databases throw an error.)

**Task:** Return rate per product: `name`, `sold` (units in delivered+returned orders), `returned` (units in returned orders), `return_pct` = 100 × returned / sold rounded to 1. Only products with `returned > 0`, highest rate first.

**Expected result:**

```text
┌─────────────────────────┬──────┬──────────┬────────────┐
│          name           │ sold │ returned │ return_pct │
├─────────────────────────┼──────┼──────────┼────────────┤
│ Dumbbell Set            │   32 │        7 │       21.9 │
│ The Selfish Gene        │   28 │        5 │       17.9 │
│ Kurk Mantolu Madonna    │   25 │        4 │         16 │
│ Ince Memed              │   33 │        4 │       12.1 │
│ Hiking Boots            │   25 │        3 │         12 │
│ Tutunamayanlar          │   26 │        3 │       11.5 │
│ Blender                 │   27 │        3 │       11.1 │
│ Phone X                 │   19 │        2 │       10.5 │
│ Office Chair            │   29 │        3 │       10.3 │
│ A Brief History of Time │   31 │        3 │        9.7 │
│ Bookshelf               │   31 │        3 │        9.7 │
│ Tent 2P                 │   32 │        3 │        9.4 │
└─────────────────────────┴──────┴──────────┴────────────┘
... 21 rows total (first 12 shown)
```


### 05.07 — CASE and NULL

**Concept:** `CASE city WHEN NULL THEN ...` never matches (it tests `city = NULL`). Use the searched form `CASE WHEN city IS NULL THEN ...`.

**Task:** Count customers per `region`: `Black Sea` (Samsun, Trabzon), `Marmara` (Istanbul, Bursa, Eskisehir), `Other` (any other known city), `No city` (NULL). Columns `region, n`, biggest first.

**Expected result:**

```text
┌───────────┬────┐
│  region   │ n  │
├───────────┼────┤
│ Other     │ 31 │
│ Marmara   │ 28 │
│ Black Sea │ 13 │
│ No city   │  8 │
└───────────┴────┘
```


### 05.08 — Age groups

**Task:** Using the date `2026-11-13` as 'today', put customers into `under 25`, `25-39`, `40-59`, `60+`, `unknown` and count them: `age_group, n`, in that order.

<details><summary>Hint</summary>

Age ≈ `(julianday('2026-11-13') - julianday(birth_date)) / 365.25`, truncated with `CAST(... AS INTEGER)`.
</details>

**Expected result:**

```text
┌───────────┬────┐
│ age_group │ n  │
├───────────┼────┤
│ under 25  │  9 │
│ 25-39     │ 21 │
│ 40-59     │ 32 │
│ 60+       │  6 │
│ unknown   │ 12 │
└───────────┴────┘
```


### 05.09 — Customer segments

**Task:** Segment **every** customer by delivered spend: `VIP` (≥ 50 000 TL), `regular` (> 0), `inactive` (nothing delivered). Count per segment: `segment, n`, biggest first.

<details><summary>Hint</summary>

LEFT JOIN customers to a per-customer delivered-spend subquery; `COALESCE(spend, 0)`. SQLite's `iif(cond, a, b)` is a 2-way CASE shortcut.
</details>

**Expected result:**

```text
┌──────────┬────┐
│ segment  │ n  │
├──────────┼────┤
│ VIP      │ 34 │
│ regular  │ 31 │
│ inactive │ 15 │
└──────────┴────┘
```


### 05.10 — Percentages per group

**Task:** Per year: `year`, `orders`, `web_pct` = % of that year's orders with no sales rep (`employee_id IS NULL`), rounded to 1.

**Expected result:**

```text
┌──────┬────────┬─────────┐
│ year │ orders │ web_pct │
├──────┼────────┼─────────┤
│ 2025 │    100 │      33 │
│ 2026 │    320 │    34.1 │
└──────┴────────┴─────────┘
```


### 05.11 — CASE inside UPDATE

_✏️ changes the DB — `./drill catchup 05.11` first if your DB is out of sync_

**Concept:** One UPDATE with a CASE can apply different rules to different rows in a single pass.

**Task:** Restock: products with `stock = 0` get stock **50**; products with stock below 10 get **+20**; others unchanged. Do it in **one** UPDATE statement.

<details><summary>Hint</summary>

`UPDATE products SET stock = CASE WHEN ... END WHERE stock < 10;` — or keep `ELSE stock` and no WHERE.
</details>

**After your script, this check:**

```sql
SELECT id, name, stock FROM products WHERE id IN (1, 2, 3, 7, 12, 28, 34, 35, 36) ORDER BY id;
```

should print:

```text
┌────┬──────────────────┬───────┐
│ id │       name       │ stock │
├────┼──────────────────┼───────┤
│  1 │ Laptop Pro 14    │    29 │
│  2 │ Laptop Air 13    │    21 │
│  3 │ Budget Laptop 15 │    50 │
│  7 │ 27in Monitor     │    28 │
│ 12 │ Fast Charger     │    50 │
│ 28 │ Chef Knife       │    26 │
│ 34 │ Tent 2P          │    27 │
│ 35 │ Sleeping Bag     │    50 │
│ 36 │ Hiking Boots     │    73 │
└────┴──────────────────┴───────┘
```

