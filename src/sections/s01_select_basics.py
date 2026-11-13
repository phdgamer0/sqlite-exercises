SECTION = dict(
    num=1, title="SELECT, WHERE, ORDER BY — warm-up", db="shop",
    pdf="Hafta 1 – Veriden Sorguya (SELECT, WHERE, LIKE, BETWEEN, IS NULL, ORDER BY, LIMIT)",
    intro="""
Quick warm-up on one table at a time. Prices are stored in **kuruş** (`price_kurus`);
divide by `100.0` (not `100`!) to get TL with decimals.

Open the DB with `./drill open shop`, explore with `.schema products`, then write your answer
into a file and grade it with `./drill check 01.01 answer.sql`.
""",
)

EX = [
    dict(
        title="Cheap things first",
        concept="`WHERE` filters rows, `ORDER BY` sorts them. `x / 100` is *integer* division in SQLite; `x / 100.0` keeps decimals.",
        task="List `name` and the price in TL as `price_tl` for products that cost **less than 500 TL**, most expensive first.",
        hint="`price_kurus < 50000`, `price_kurus / 100.0 AS price_tl`, `ORDER BY ... DESC`",
        sol="""
SELECT name, price_kurus / 100.0 AS price_tl
FROM products
WHERE price_kurus < 50000
ORDER BY price_kurus DESC;
""",
    ),
    dict(
        title="Who has no city?",
        concept="`NULL` is not a value, it is the *absence* of one. `city = NULL` is never true; use `IS NULL`.",
        task="Show `first_name`, `last_name`, `email` of customers whose `city` is unknown. Sort by `id`.",
        hint="`WHERE city IS NULL`",
        sol="SELECT first_name, last_name, email FROM customers WHERE city IS NULL ORDER BY id;",
    ),
    dict(
        title="LIKE patterns",
        concept="`%` = any number of characters, `_` = exactly one. In SQLite, `LIKE` is case-insensitive for ASCII letters only (not for İ/ı/ö…).",
        task="Find every product whose name contains the word fragment `phone` anywhere (any case). Show `id, name`.",
        hint="`name LIKE '%phone%'` — think about whether `Headphones NC` should match (it should).",
        sol="SELECT id, name FROM products WHERE name LIKE '%phone%';",
    ),
    dict(
        title="The BETWEEN date trap",
        concept="Dates here are TEXT like `2026-08-31 18:20:00`. `BETWEEN '2026-08-01' AND '2026-08-31'` silently drops everything on August 31 after midnight, because `'2026-08-31 18:20:00' > '2026-08-31'`.",
        task="How many orders were placed in **August 2026** (the whole month)? Return one column `n`.",
        hint="Use a half-open range: `ordered_at >= '2026-08-01' AND ordered_at < '2026-09-01'`. Then try the BETWEEN version and compare.",
        sol="SELECT COUNT(*) AS n FROM orders WHERE ordered_at >= '2026-08-01' AND ordered_at < '2026-09-01';",
    ),
    dict(
        title="DISTINCT",
        task="List every distinct `ship_city` that appears in `orders`, alphabetically.",
        hint="`SELECT DISTINCT ... ORDER BY ...`",
        sol="SELECT DISTINCT ship_city FROM orders ORDER BY ship_city;",
    ),
    dict(
        title="Pagination with LIMIT / OFFSET",
        concept="`LIMIT n OFFSET k` skips k rows then returns n. Without `ORDER BY` the 'pages' are not guaranteed to be stable.",
        task="A shop page shows 10 products per page, ordered by `name`. Return `id, name` for **page 3**.",
        hint="Page 3 starts after 20 rows.",
        sol="SELECT id, name FROM products ORDER BY name LIMIT 10 OFFSET 20;",
    ),
    dict(
        title="Combining conditions",
        concept="`AND` binds tighter than `OR`. When in doubt, add parentheses.",
        task="Top 5 most expensive products that are **not discontinued** and **in stock** (`stock > 0`). Show `name, price_kurus, stock`.",
        sol="""
SELECT name, price_kurus, stock
FROM products
WHERE discontinued = 0 AND stock > 0
ORDER BY price_kurus DESC
LIMIT 5;
""",
    ),
    dict(
        title="NOT and NULL — the classic trap",
        concept="`referred_by <> 3` is *unknown* (not true) when `referred_by` is NULL, so those rows vanish. `IS NOT` treats NULL like a normal value.",
        task="How many customers were **not** referred by customer 3? Customers with no referrer at all count too. Return `n`.",
        hint="Compare `WHERE referred_by <> 3` with `WHERE referred_by IS NOT 3` (or `... OR referred_by IS NULL`).",
        sol="SELECT COUNT(*) AS n FROM customers WHERE referred_by IS NOT 3;",
        after="If you got a much smaller number, you fell into the NULL trap: `NULL <> 3` is NULL, and WHERE keeps only TRUE.",
    ),
    dict(
        title="Computed columns and aliases",
        task="For each employee show `first_name || ' ' || last_name AS full_name`, `title`, and the **monthly salary in TL** as `monthly_tl` (salary_kurus is yearly; round to 2 decimals). Highest paid first.",
        hint="`ROUND(salary_kurus / 100.0 / 12, 2)`",
        sol="""
SELECT first_name || ' ' || last_name AS full_name, title,
       ROUND(salary_kurus / 100.0 / 12, 2) AS monthly_tl
FROM employees
ORDER BY salary_kurus DESC;
""",
    ),
    dict(
        title="IN lists",
        task="Customers from Samsun, Trabzon or Bursa who **have** a phone number. Show `first_name, last_name, city`, ordered by city then last_name then first_name.",
        hint="`city IN (...)` and `phone IS NOT NULL`",
        sol="""
SELECT first_name, last_name, city
FROM customers
WHERE city IN ('Samsun', 'Trabzon', 'Bursa') AND phone IS NOT NULL
ORDER BY city, last_name, first_name;
""",
    ),
]
