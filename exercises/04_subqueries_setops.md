# 04 — Subqueries and set operations

**Database:** `shop` · **Course link:** Hafta 2 – Alt sorgular, IN, Küme işlemleri (UNION, INTERSECT, EXCEPT)

A subquery is a query used as a value (scalar), a list (`IN`), a test (`EXISTS`) or a table
(`FROM (...)`). A **correlated** subquery refers to the outer row and runs once per row.

Set operations stack two results with the **same number of columns**: `UNION` (dedup),
`UNION ALL` (keep duplicates), `INTERSECT`, `EXCEPT`.

### 04.01 — Scalar subquery

**Task:** Products priced **above the average product price**: `name, price_kurus`, most expensive first.

**Expected result:**

```text
┌──────────────────┬─────────────┐
│       name       │ price_kurus │
├──────────────────┼─────────────┤
│ Laptop Pro 14    │     4299900 │
│ Phone X          │     3899900 │
│ Laptop Air 13    │     3199900 │
│ Budget Laptop 15 │     1599900 │
│ Phone Lite       │     1299900 │
│ 27in Monitor     │      749900 │
│ Headphones NC    │      549900 │
│ Office Chair     │      499900 │
└──────────────────┴─────────────┘
```


### 04.02 — Nested IN

**Task:** `id, first_name, last_name` of customers who ordered at least one product from the **Books** top-level category or any of its sub-categories (Novels, Science, Comics). Order by id.

<details><summary>Hint</summary>

categories where `id = 2 OR parent_id = 2` → products IN that → order_items → orders.customer_id. Three nested INs, no JOIN.
</details>

**Expected result:**

```text
┌────┬────────────┬───────────┐
│ id │ first_name │ last_name │
├────┼────────────┼───────────┤
│  1 │ Onur       │ Erdogan   │
│  2 │ Ayse       │ Dogan     │
│  3 │ Ayse       │ Celik     │
│  7 │ Onur       │ Kural     │
│  8 │ Fatma      │ Kaya      │
│  9 │ Selin      │ Koc       │
│ 10 │ Selin      │ Kural     │
│ 12 │ Hakan      │ Kurt      │
│ 13 │ Oguz       │ Dogan     │
│ 14 │ Ufuk       │ Ozturk    │
│ 15 │ Fatma      │ Polat     │
│ 16 │ Irem       │ Ozturk    │
└────┴────────────┴───────────┘
... 59 rows total (first 12 shown)
```


### 04.03 — The NOT IN + NULL trap

**Concept:** `x NOT IN (1, 2, NULL)` is never true: SQL can't rule out that x equals the unknown value. If the subquery can return NULL, `NOT IN` returns **nothing**.

**Task:** How many customers have **never referred anyone**? Return `n`. (First try `WHERE id NOT IN (SELECT referred_by FROM customers)` and see what you get.)

<details><summary>Hint</summary>

Filter the NULLs out of the subquery, or use `NOT EXISTS`.
</details>

**Expected result:**

```text
┌────┐
│ n  │
├────┤
│ 64 │
└────┘
```


### 04.04 — Correlated subquery: above my category's average

**Task:** Products that cost more than the average price **of their own category**: `name, category_id, price_kurus`, by category_id then price desc. (Products without category are ignored.)

**Expected result:**

```text
┌─────────────────────────────┬─────────────┬─────────────┐
│            name             │ category_id │ price_kurus │
├─────────────────────────────┼─────────────┼─────────────┤
│ Phone X                     │           6 │     3899900 │
│ Headphones NC               │           7 │      549900 │
│ Laptop Pro 14               │           8 │     4299900 │
│ Laptop Air 13               │           8 │     3199900 │
│ Mechanical Keyboard         │           9 │      189900 │
│ Webcam HD                   │           9 │      119900 │
│ Tutunamayanlar              │          10 │       34000 │
│ Saatleri Ayarlama Enstitusu │          10 │       26000 │
│ Ince Memed                  │          10 │       21000 │
│ Database Systems            │          11 │       95000 │
│ Watchmen                    │          12 │       45000 │
│ Coffee Maker                │          13 │      289900 │
└─────────────────────────────┴─────────────┴─────────────┘
... 16 rows total (first 12 shown)
```


### 04.05 — EXISTS

**Task:** `id, first_name, last_name` of customers who have **at least one returned** order. By id.

**Expected result:**

```text
┌────┬────────────┬───────────┐
│ id │ first_name │ last_name │
├────┼────────────┼───────────┤
│  7 │ Onur       │ Kural     │
│ 13 │ Oguz       │ Dogan     │
│ 14 │ Ufuk       │ Ozturk    │
│ 21 │ Nazli      │ Kural     │
│ 24 │ Zeynep     │ Koc       │
│ 28 │ Cem        │ Tekin     │
│ 32 │ Ufuk       │ Ozdemir   │
│ 35 │ Kerem      │ Kilic     │
│ 45 │ Ece        │ Kurt      │
│ 48 │ Emre       │ Dogan     │
│ 49 │ Elif       │ Ozturk    │
│ 53 │ Burak      │ Ozdemir   │
└────┴────────────┴───────────┘
... 16 rows total (first 12 shown)
```


### 04.06 — Aggregate of an aggregate

**Concept:** You can't write `MAX(AVG(...))`. Compute the inner aggregate in a subquery in `FROM`, then aggregate that.

**Task:** Compute every customer's **average order value** (in kuruş, from order_items, all statuses). Return the highest of these averages, in TL rounded to 2, as `best_avg_tl`.

**Expected result:**

```text
┌─────────────┐
│ best_avg_tl │
├─────────────┤
│    68588.67 │
└─────────────┘
```


### 04.07 — UNION

**Task:** One column `city`: every city that appears as a customer city **or** as an order ship_city, without duplicates and without NULL, alphabetical.

**Expected result:**

```text
┌───────────┐
│   city    │
├───────────┤
│ Ankara    │
│ Antalya   │
│ Bursa     │
│ Eskisehir │
│ Istanbul  │
│ Izmir     │
│ Samsun    │
│ Trabzon   │
└───────────┘
```


### 04.08 — UNION vs UNION ALL

**Task:** One row with two columns: `union_rows` = number of rows in (customer cities UNION ship cities), `union_all_rows` = same with UNION ALL. Keep the NULL filter on customers.

**Expected result:**

```text
┌────────────┬────────────────┐
│ union_rows │ union_all_rows │
├────────────┼────────────────┤
│          8 │            492 │
└────────────┴────────────────┘
```


### 04.09 — INTERSECT

**Task:** `customer_id`s of customers who have paid **both** by `card` and by `transfer` (on any of their orders). Sorted.

**Expected result:**

```text
┌─────────────┐
│ customer_id │
├─────────────┤
│           1 │
│           3 │
│           7 │
│           8 │
│          13 │
│          15 │
│          16 │
│          18 │
│          20 │
│          23 │
│          24 │
│          25 │
└─────────────┘
... 36 rows total (first 12 shown)
```


### 04.10 — EXCEPT: churned customers

**Task:** `customer_id`s who ordered in **2025** but **not in 2026**. Sorted.

**Expected result:**

```text
┌─────────────┐
│ customer_id │
├─────────────┤
│          42 │
│          54 │
└─────────────┘
```


### 04.11 — Subquery in SELECT

**Task:** Every employee: `first_name, title, reports` where `reports` is the number of people whose `manager_id` is that employee. Most reports first, then first_name.

**Expected result:**

```text
┌────────────┬─────────────────┬─────────┐
│ first_name │      title      │ reports │
├────────────┼─────────────────┼─────────┤
│ Elif       │ Sales Manager   │       2 │
│ Kerem      │ Sales Manager   │       2 │
│ Oguz       │ CEO             │       2 │
│ Selin      │ Sales Director  │       2 │
│ Burak      │ Ops Director    │       1 │
│ Derya      │ Warehouse Lead  │       1 │
│ Zeynep     │ Sales Rep       │       1 │
│ Can        │ Sales Rep       │       0 │
│ Emre       │ Sales Rep       │       0 │
│ Gizem      │ Sales Rep       │       0 │
│ Pinar      │ Intern          │       0 │
│ Ufuk       │ Warehouse Staff │       0 │
└────────────┴─────────────────┴─────────┘
```


### 04.12 — Product never sold — three ways

**Task:** Names of products that never appear in `order_items`, alphabetically. Write it with `NOT IN`, with `NOT EXISTS`, and with `LEFT JOIN ... IS NULL`, and convince yourself all three agree here (and when `NOT IN` would break).

**Expected result:**

```text
┌───────────────┐
│     name      │
├───────────────┤
│ Gift Card 500 │
│ Kucuk Prens   │
│ Maus          │
└───────────────┘
```

