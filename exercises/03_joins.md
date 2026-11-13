# 03 — JOINs — inner, outer, self, anti, and the fan-out trap

**Database:** `shop` · **Course link:** Hafta 2 – Tablolar Arasındaki İlişkiler (PK/FK, INNER/LEFT/RIGHT/FULL/NATURAL JOIN)

Every join links a **primary key** to a **foreign key**. Draw the path first:

```
customers ─< orders ─< order_items >─ products >─ categories ─┐ (parent_id)
     │ (referred_by)    │       └─< payments                   └─ categories
     └─ customers       └─> employees ─ (manager_id) ─> employees
reviews >─ products, reviews >─ customers
```

`─<` means "one to many". When you go *down* a one-to-many link, rows multiply.

### 03.01 — Order 42, with product names

**Task:** Show `product` (name), `quantity`, `unit_price_kurus` for every line of **order 42**.

<details><summary>Hint</summary>

`order_items JOIN products ON products.id = order_items.product_id`
</details>

**Expected result:**

```text
┌────────────┬──────────┬──────────────────┐
│  product   │ quantity │ unit_price_kurus │
├────────────┼──────────┼──────────────────┤
│ Phone Lite │        1 │          1299900 │
└────────────┴──────────┴──────────────────┘
```


### 03.02 — What did Nazli Erdogan buy?

**Concept:** Chain joins along the FK path: customers → orders → order_items → products.

**Task:** Distinct product names that customer **id 80** received (status `delivered`), alphabetically. Column `product`.

**Expected result:**

```text
┌─────────────────────────┐
│         product         │
├─────────────────────────┤
│ 27in Monitor            │
│ A Brief History of Time │
│ Cosmos                  │
│ Desk Lamp               │
│ Headphones NC           │
│ Hiking Boots            │
│ Ince Memed              │
│ Kurk Mantolu Madonna    │
│ Laptop Air 13           │
│ Laptop Pro 14           │
│ Mechanical Keyboard     │
│ Mystery Box             │
└─────────────────────────┘
... 17 rows total (first 12 shown)
```


### 03.03 — Anti-join: customers who never ordered

**Concept:** `LEFT JOIN` keeps every left row; where nothing matched, the right side is NULL. Filtering on `right.id IS NULL` keeps only the unmatched ones.

**Task:** `id, first_name, last_name` of customers with **no orders at all**, by id.

**Expected result:**

```text
┌────┬────────────┬───────────┐
│ id │ first_name │ last_name │
├────┼────────────┼───────────┤
│  4 │ Fatma      │ Tekin     │
│  6 │ Tolga      │ Aksoy     │
│ 11 │ Pinar      │ Aksoy     │
│ 19 │ Ufuk       │ Kural     │
│ 27 │ Ahmet      │ Erdogan   │
│ 30 │ Pinar      │ Ozturk    │
│ 31 │ Can        │ Polat     │
│ 41 │ Murat      │ Kurt      │
│ 43 │ Merve      │ Demir     │
│ 47 │ Irem       │ Arslan    │
│ 57 │ Nazli      │ Kaya      │
│ 58 │ Onur       │ Kaya      │
└────┴────────────┴───────────┘
... 13 rows total (first 12 shown)
```


### 03.04 — Counting zeros: COUNT(*) vs COUNT(col)

**Concept:** After a LEFT JOIN an unmatched row still exists (with NULLs), so `COUNT(*)` says 1. `COUNT(oi.order_id)` says 0.

**Task:** Every product with the number of order lines it appears in, as `name, times_ordered` — products never ordered must show **0**. Fewest first, then by name.

**Expected result:**

```text
┌──────────────────┬───────────────┐
│       name       │ times_ordered │
├──────────────────┼───────────────┤
│ Gift Card 500    │             0 │
│ Kucuk Prens      │             0 │
│ Maus             │             0 │
│ Non-stick Pan    │            11 │
│ Chef Knife       │            17 │
│ Cosmos           │            18 │
│ Earbuds          │            18 │
│ Jump Rope        │            18 │
│ Budget Laptop 15 │            19 │
│ Tutunamayanlar   │            19 │
│ Laptop Pro 14    │            20 │
│ Sleeping Bag     │            20 │
└──────────────────┴───────────────┘
... 41 rows total (first 12 shown)
```


### 03.05 — LEFT JOIN + filter: ON vs WHERE

**Concept:** A condition on the *right* table placed in `WHERE` throws away the NULL rows and turns your LEFT JOIN back into an INNER JOIN. Put it in `ON` instead.

**Task:** For **every** product in category 16 (Fitness), how many units were sold in orders placed in **2026**? Columns `name, units_2026`; products without 2026 sales show 0.

<details><summary>Hint</summary>

Join `order_items` and `orders` inside the LEFT JOIN (or join to a subquery), put the 2026 condition in `ON`, use `COALESCE(SUM(...), 0)`.
</details>

**Expected result:**

```text
┌──────────────┬────────────┐
│     name     │ units_2026 │
├──────────────┼────────────┤
│ Dumbbell Set │         29 │
│ Jump Rope    │         28 │
│ Yoga Mat     │         41 │
└──────────────┴────────────┘
```


### 03.06 — Self join: who is my manager?

**Concept:** A table can be joined to itself with two aliases. Use LEFT JOIN so the boss (manager_id NULL) stays.

**Task:** `employee` (first + last name), `title`, `manager` (first + last name, NULL for the CEO), ordered by employee id.

**Expected result:**

```text
┌───────────────┬─────────────────┬───────────────┐
│   employee    │      title      │    manager    │
├───────────────┼─────────────────┼───────────────┤
│ Oguz Kural    │ CEO             │ NULL          │
│ Selin Aydin   │ Sales Director  │ Oguz Kural    │
│ Burak Celik   │ Ops Director    │ Oguz Kural    │
│ Elif Demir    │ Sales Manager   │ Selin Aydin   │
│ Kerem Kaya    │ Sales Manager   │ Selin Aydin   │
│ Zeynep Arslan │ Sales Rep       │ Elif Demir    │
│ Emre Sahin    │ Sales Rep       │ Elif Demir    │
│ Gizem Polat   │ Sales Rep       │ Kerem Kaya    │
│ Can Tekin     │ Sales Rep       │ Kerem Kaya    │
│ Derya Koc     │ Warehouse Lead  │ Burak Celik   │
│ Ufuk Kurt     │ Warehouse Staff │ Derya Koc     │
│ Pinar Gunes   │ Intern          │ Zeynep Arslan │
└───────────────┴─────────────────┴───────────────┘
```


### 03.07 — Self join: referrals across cities

**Task:** Pairs where a customer was referred by someone living in a **different** city (both cities known). Columns `customer_id, customer_city, referrer_id, referrer_city`, by customer_id.

**Expected result:**

```text
┌─────────────┬───────────────┬─────────────┬───────────────┐
│ customer_id │ customer_city │ referrer_id │ referrer_city │
├─────────────┼───────────────┼─────────────┼───────────────┤
│           9 │ Antalya       │           1 │ Izmir         │
│          14 │ Izmir         │           3 │ Istanbul      │
│          25 │ Samsun        │          10 │ Istanbul      │
│          26 │ Izmir         │          21 │ Eskisehir     │
│          36 │ Trabzon       │          22 │ Antalya       │
│          41 │ Ankara        │           4 │ Istanbul      │
│          42 │ Samsun        │          23 │ Eskisehir     │
│          50 │ Istanbul      │          25 │ Samsun        │
│          68 │ Ankara        │          22 │ Antalya       │
│          70 │ Ankara        │          50 │ Istanbul      │
│          79 │ Eskisehir     │          16 │ Samsun        │
└─────────────┴───────────────┴─────────────┴───────────────┘
```

> `c.city <> r.city` is NULL when either city is NULL, so those pairs are dropped automatically — check that this is what you wanted.


### 03.08 — Revenue per category (with an 'Uncategorised' bucket)

**Task:** Delivered revenue in TL per category name: `category, revenue_tl`. Products with no category go into a bucket named `Uncategorised`. Biggest first.

<details><summary>Hint</summary>

products → categories must be a LEFT JOIN; `COALESCE(c.name, 'Uncategorised')`.
</details>

**Expected result:**

```text
┌───────────────┬────────────┐
│   category    │ revenue_tl │
├───────────────┼────────────┤
│ Laptops       │    2825156 │
│ Phones        │    1020611 │
│ Audio         │     223626 │
│ Furniture     │     218627 │
│ Kitchen       │     194843 │
│ Computers     │     158228 │
│ Camping       │     138675 │
│ Accessories   │     117151 │
│ Fitness       │      65541 │
│ Outdoor       │      60318 │
│ Science       │      56927 │
│ Uncategorised │      31318 │
└───────────────┴────────────┘
... 14 rows total (first 12 shown)
```


### 03.09 — The fan-out trap (double counting)

**Concept:** Joining an order to its items (many) **and** its payments (many) gives items × payments rows; every SUM is then inflated. Aggregate each child table **separately first**, then join the small results.

**Task:** Orders whose paid total differs from their item total. Columns `order_id, items_kurus, paid_kurus` (paid = 0 if no payment), only for statuses `delivered`, `shipped`, `returned`. Order by `order_id`.

<details><summary>Hint</summary>

Two subqueries in FROM: one `GROUP BY order_id` over order_items, one over payments; LEFT JOIN the payments one.
</details>

**Expected result:**

```text
┌──────────┬─────────────┬────────────┐
│ order_id │ items_kurus │ paid_kurus │
├──────────┼─────────────┼────────────┤
│        2 │       19900 │      14900 │
│       57 │      159800 │     154800 │
│       94 │      499800 │     494800 │
│      113 │    15069500 │   15064500 │
│      115 │      349900 │     344900 │
│      139 │      324900 │     319900 │
│      151 │      207800 │     202800 │
│      206 │      499900 │     494900 │
│      300 │      379800 │     374800 │
│      353 │      573700 │     568700 │
│      359 │      555700 │     550700 │
└──────────┴─────────────┴────────────┘
```

> Try the naive version (join items and payments directly, SUM both) and look at an order paid in two installments — its item total doubles.


### 03.10 — CROSS JOIN to fill in the zeros

**Concept:** `CROSS JOIN` pairs every row with every row. Useful to build a complete grid, then LEFT JOIN the real counts onto it.

**Task:** For every combination of `method` (card/cash/transfer) and year (2025, 2026), the number of payments — combinations with no payments show 0. Columns `method, year, n`, sorted by method then year.

<details><summary>Hint</summary>

`(SELECT DISTINCT method FROM payments) CROSS JOIN (SELECT '2025' AS year UNION SELECT '2026')`, then LEFT JOIN payments on both keys.
</details>

**Expected result:**

```text
┌──────────┬──────┬─────┐
│  method  │ year │  n  │
├──────────┼──────┼─────┤
│ card     │ 2025 │  78 │
│ card     │ 2026 │ 253 │
│ cash     │ 2025 │   9 │
│ cash     │ 2026 │  28 │
│ transfer │ 2025 │  18 │
│ transfer │ 2026 │  68 │
└──────────┴──────┴─────┘
```


### 03.11 — NATURAL JOIN gone wrong

**Concept:** `NATURAL JOIN` joins on **every column with the same name**. `products` and `categories` share both `id` and `name`, so it compares product.id = category.id AND product.name = category.name.

**Task:** How many rows does `products NATURAL JOIN categories` return? Then write the correct join with `ON` and count those rows too. Return one row: `natural_rows, correct_rows`.

**Expected result:**

```text
┌──────────────┬──────────────┐
│ natural_rows │ correct_rows │
├──────────────┼──────────────┤
│            0 │           39 │
└──────────────┴──────────────┘
```


### 03.12 — FULL OUTER JOIN: reviewers vs. recent buyers

**Concept:** `FULL JOIN` keeps unmatched rows from **both** sides (SQLite ≥ 3.39). Handy for comparing two lists where each side has members the other lacks.

**Task:** Marketing wants one list of customers who either wrote reviews **or** ordered since `2026-09-01`. Columns `customer_id`, `reviews` (how many reviews they wrote) and `recent_orders` (orders since 2026-09-01); missing counts show 0. Sort by customer_id.

<details><summary>Hint</summary>

FULL JOIN two grouped subqueries; `COALESCE(a.customer_id, b.customer_id)`.
</details>

**Expected result:**

```text
┌─────────────┬─────────┬───────────────┐
│ customer_id │ reviews │ recent_orders │
├─────────────┼─────────┼───────────────┤
│           1 │       7 │             1 │
│           2 │       1 │             1 │
│           3 │       2 │             2 │
│           4 │       1 │             0 │
│           5 │       1 │             0 │
│           6 │       1 │             0 │
│           7 │       5 │             2 │
│           8 │       2 │             0 │
│           9 │       0 │             2 │
│          10 │       1 │             1 │
│          11 │       1 │             0 │
│          12 │       3 │             0 │
└─────────────┴─────────┴───────────────┘
... 63 rows total (first 12 shown)
```

> Rows with `reviews = 0` came only from the right side, rows with `recent_orders = 0` only from the left. A LEFT JOIN would have lost one of those groups.


### 03.13 — Reviews from people who never bought the product

**Task:** Suspicious reviews: `review_id, product_id, customer_id` for reviews where that customer has **no** order line for that product. By review_id.

<details><summary>Hint</summary>

LEFT JOIN `orders` + `order_items` on *both* customer and product, keep rows where the join found nothing.
</details>

**Expected result:**

```text
┌───────────┬────────────┬─────────────┐
│ review_id │ product_id │ customer_id │
├───────────┼────────────┼─────────────┤
│       151 │          1 │           4 │
│       152 │          1 │           6 │
│       153 │          1 │          11 │
└───────────┴────────────┴─────────────┘
```


### 03.14 — Sales reps leaderboard (including people with no sales)

**Task:** Every employee with `name` (first + last), `orders` (number of **delivered** orders they handled) and `revenue_tl`. People without sales show 0 and 0. Biggest revenue first, then name.

<details><summary>Hint</summary>

Pre-aggregate delivered revenue per employee in a subquery, then LEFT JOIN employees to it.
</details>

**Expected result:**

```text
┌───────────────┬────────┬────────────┐
│     name      │ orders │ revenue_tl │
├───────────────┼────────┼────────────┤
│ Elif Demir    │     45 │     637244 │
│ Emre Sahin    │     42 │     629604 │
│ Kerem Kaya    │     40 │     517389 │
│ Can Tekin     │     33 │     451359 │
│ Gizem Polat   │     30 │     375282 │
│ Zeynep Arslan │     29 │     340517 │
│ Burak Celik   │      0 │          0 │
│ Derya Koc     │      0 │          0 │
│ Oguz Kural    │      0 │          0 │
│ Pinar Gunes   │      0 │          0 │
│ Selin Aydin   │      0 │          0 │
│ Ufuk Kurt     │      0 │          0 │
└───────────────┴────────┴────────────┘
```


### 03.15 — GROUP BY name vs GROUP BY id

**Concept:** Two different customers can share a name. Grouping by the name silently merges them.

**Task:** Top 5 customers by number of orders, showing `id, first_name, last_name, n`. Ties broken by id. (Then try grouping by name only and look at *Hakan Kurt*.)

**Expected result:**

```text
┌────┬────────────┬───────────┬────┐
│ id │ first_name │ last_name │ n  │
├────┼────────────┼───────────┼────┤
│ 80 │ Nazli      │ Erdogan   │ 19 │
│ 53 │ Burak      │ Ozdemir   │ 18 │
│ 13 │ Oguz       │ Dogan     │ 17 │
│ 14 │ Ufuk       │ Ozturk    │ 17 │
│ 67 │ Hakan      │ Kurt      │ 17 │
└────┴────────────┴───────────┴────┘
```

