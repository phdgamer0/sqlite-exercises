# 01 — SELECT, WHERE, ORDER BY — warm-up

**Database:** `shop` · **Course link:** Hafta 1 – Veriden Sorguya (SELECT, WHERE, LIKE, BETWEEN, IS NULL, ORDER BY, LIMIT)

Quick warm-up on one table at a time. Prices are stored in **kuruş** (`price_kurus`);
divide by `100.0` (not `100`!) to get TL with decimals.

Open the DB with `./drill open shop`, explore with `.schema products`, then write your answer
into a file and grade it with `./drill check 01.01 answer.sql`.

### 01.01 — Cheap things first

**Concept:** `WHERE` filters rows, `ORDER BY` sorts them. `x / 100` is *integer* division in SQLite; `x / 100.0` keeps decimals.

**Task:** List `name` and the price in TL as `price_tl` for products that cost **less than 500 TL**, most expensive first.

<details><summary>Hint</summary>

`price_kurus < 50000`, `price_kurus / 100.0 AS price_tl`, `ORDER BY ... DESC`
</details>

**Expected result:**

```text
┌─────────────────────────────┬──────────┐
│            name             │ price_tl │
├─────────────────────────────┼──────────┤
│ Watchmen                    │      450 │
│ Fast Charger                │      449 │
│ Yoga Mat                    │      399 │
│ Maus                        │      390 │
│ Wireless Mouse              │      349 │
│ Tutunamayanlar              │      340 │
│ Cosmos                      │      310 │
│ The Selfish Gene            │      295 │
│ A Brief History of Time     │      280 │
│ Saatleri Ayarlama Enstitusu │      260 │
│ Ince Memed                  │      210 │
│ Phone Case                  │      199 │
└─────────────────────────────┴──────────┘
... 15 rows total (first 12 shown)
```


### 01.02 — Who has no city?

**Concept:** `NULL` is not a value, it is the *absence* of one. `city = NULL` is never true; use `IS NULL`.

**Task:** Show `first_name`, `last_name`, `email` of customers whose `city` is unknown. Sort by `id`.

<details><summary>Hint</summary>

`WHERE city IS NULL`
</details>

**Expected result:**

```text
┌────────────┬───────────┬─────────────────────────────┐
│ first_name │ last_name │            email            │
├────────────┼───────────┼─────────────────────────────┤
│ Tolga      │ Aksoy     │ tolga.aksoy6@example.org    │
│ Pinar      │ Aksoy     │ pinar.aksoy11@mail.com      │
│ Hakan      │ Kurt      │ hakan.kurt12@mail.com       │
│ Elif       │ Erdogan   │ elif.erdogan18@mail.com     │
│ Murat      │ Aksoy     │ murat.aksoy34@omu.edu.tr    │
│ Mustafa    │ Demir     │ mustafa.demir46@example.org │
│ Elif       │ Kural     │ elif.kural54@omu.edu.tr     │
│ Onur       │ Arslan    │ onur.arslan76@example.org   │
└────────────┴───────────┴─────────────────────────────┘
```


### 01.03 — LIKE patterns

**Concept:** `%` = any number of characters, `_` = exactly one. In SQLite, `LIKE` is case-insensitive for ASCII letters only (not for İ/ı/ö…).

**Task:** Find every product whose name contains the word fragment `phone` anywhere (any case). Show `id, name`.

<details><summary>Hint</summary>

`name LIKE '%phone%'` — think about whether `Headphones NC` should match (it should).
</details>

**Expected result:**

```text
┌────┬───────────────┐
│ id │     name      │
├────┼───────────────┤
│ 13 │ Headphones NC │
│ 11 │ Phone Case    │
│ 10 │ Phone Lite    │
│  9 │ Phone X       │
└────┴───────────────┘
```


### 01.04 — The BETWEEN date trap

**Concept:** Dates here are TEXT like `2026-08-31 18:20:00`. `BETWEEN '2026-08-01' AND '2026-08-31'` silently drops everything on August 31 after midnight, because `'2026-08-31 18:20:00' > '2026-08-31'`.

**Task:** How many orders were placed in **August 2026** (the whole month)? Return one column `n`.

<details><summary>Hint</summary>

Use a half-open range: `ordered_at >= '2026-08-01' AND ordered_at < '2026-09-01'`. Then try the BETWEEN version and compare.
</details>

**Expected result:**

```text
┌────┐
│ n  │
├────┤
│ 35 │
└────┘
```


### 01.05 — DISTINCT

**Task:** List every distinct `ship_city` that appears in `orders`, alphabetically.

<details><summary>Hint</summary>

`SELECT DISTINCT ... ORDER BY ...`
</details>

**Expected result:**

```text
┌───────────┐
│ ship_city │
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


### 01.06 — Pagination with LIMIT / OFFSET

**Concept:** `LIMIT n OFFSET k` skips k rows then returns n. Without `ORDER BY` the 'pages' are not guaranteed to be stable.

**Task:** A shop page shows 10 products per page, ordered by `name`. Return `id, name` for **page 3**.

<details><summary>Hint</summary>

Page 3 starts after 20 rows.
</details>

**Expected result:**

```text
┌────┬──────────────────────┐
│ id │         name         │
├────┼──────────────────────┤
│ 16 │ Kurk Mantolu Madonna │
│  2 │ Laptop Air 13        │
│  1 │ Laptop Pro 14        │
│ 26 │ Maus                 │
│  5 │ Mechanical Keyboard  │
│ 41 │ Mystery Box          │
│ 29 │ Non-stick Pan        │
│ 31 │ Office Chair         │
│ 11 │ Phone Case           │
│ 10 │ Phone Lite           │
└────┴──────────────────────┘
```


### 01.07 — Combining conditions

**Concept:** `AND` binds tighter than `OR`. When in doubt, add parentheses.

**Task:** Top 5 most expensive products that are **not discontinued** and **in stock** (`stock > 0`). Show `name, price_kurus, stock`.

**Expected result:**

```text
┌───────────────┬─────────────┬───────┐
│     name      │ price_kurus │ stock │
├───────────────┼─────────────┼───────┤
│ Laptop Pro 14 │     4299900 │     9 │
│ Phone X       │     3899900 │    53 │
│ Laptop Air 13 │     3199900 │     1 │
│ Phone Lite    │     1299900 │    70 │
│ 27in Monitor  │      749900 │     8 │
└───────────────┴─────────────┴───────┘
```


### 01.08 — NOT and NULL — the classic trap

**Concept:** `referred_by <> 3` is *unknown* (not true) when `referred_by` is NULL, so those rows vanish. `IS NOT` treats NULL like a normal value.

**Task:** How many customers were **not** referred by customer 3? Customers with no referrer at all count too. Return `n`.

<details><summary>Hint</summary>

Compare `WHERE referred_by <> 3` with `WHERE referred_by IS NOT 3` (or `... OR referred_by IS NULL`).
</details>

**Expected result:**

```text
┌────┐
│ n  │
├────┤
│ 78 │
└────┘
```

> If you got a much smaller number, you fell into the NULL trap: `NULL <> 3` is NULL, and WHERE keeps only TRUE.


### 01.09 — Computed columns and aliases

**Task:** For each employee show `first_name || ' ' || last_name AS full_name`, `title`, and the **monthly salary in TL** as `monthly_tl` (salary_kurus is yearly; round to 2 decimals). Highest paid first.

<details><summary>Hint</summary>

`ROUND(salary_kurus / 100.0 / 12, 2)`
</details>

**Expected result:**

```text
┌───────────────┬─────────────────┬────────────┐
│   full_name   │      title      │ monthly_tl │
├───────────────┼─────────────────┼────────────┤
│ Oguz Kural    │ CEO             │   20833.33 │
│ Selin Aydin   │ Sales Director  │      10000 │
│ Burak Celik   │ Ops Director    │    9583.33 │
│ Elif Demir    │ Sales Manager   │    6666.67 │
│ Kerem Kaya    │ Sales Manager   │       6500 │
│ Derya Koc     │ Warehouse Lead  │    4333.33 │
│ Gizem Polat   │ Sales Rep       │    3833.33 │
│ Zeynep Arslan │ Sales Rep       │       3750 │
│ Emre Sahin    │ Sales Rep       │    3583.33 │
│ Can Tekin     │ Sales Rep       │    3416.67 │
│ Ufuk Kurt     │ Warehouse Staff │    2833.33 │
│ Pinar Gunes   │ Intern          │       1500 │
└───────────────┴─────────────────┴────────────┘
```


### 01.10 — IN lists

**Task:** Customers from Samsun, Trabzon or Bursa who **have** a phone number. Show `first_name, last_name, city`, ordered by city then last_name then first_name.

<details><summary>Hint</summary>

`city IN (...)` and `phone IS NOT NULL`
</details>

**Expected result:**

```text
┌────────────┬───────────┬─────────┐
│ first_name │ last_name │  city   │
├────────────┼───────────┼─────────┤
│ Kerem      │ Kilic     │ Bursa   │
│ Onur       │ Kural     │ Bursa   │
│ Murat      │ Ozturk    │ Bursa   │
│ Ahmet      │ Aydin     │ Samsun  │
│ Tolga      │ Gunes     │ Samsun  │
│ Zeynep     │ Koc       │ Samsun  │
│ Ece        │ Kurt      │ Samsun  │
│ Kerem      │ Kurt      │ Samsun  │
│ Hakan      │ Ozturk    │ Samsun  │
│ Irem       │ Ozturk    │ Samsun  │
│ Mustafa    │ Ozturk    │ Samsun  │
│ Onur       │ Kurt      │ Trabzon │
└────────────┴───────────┴─────────┘
```

