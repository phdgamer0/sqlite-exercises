SECTION = dict(
    num=5, title="CASE, COALESCE, NULLIF, conditional aggregation", db="shop",
    pdf="Not a separate lecture — used everywhere (labels, pivots, safe division, CASE in UPDATE)",
    intro="""
`CASE` is SQL's if/else **expression** — it returns a value, so it can go anywhere a value can:
SELECT list, WHERE, ORDER BY, GROUP BY, inside aggregates, inside UPDATE ... SET.

```sql
CASE WHEN cond1 THEN a WHEN cond2 THEN b ELSE c END   -- searched CASE (use this one)
CASE col WHEN 1 THEN 'x' WHEN 2 THEN 'y' END          -- simple CASE (equality only)
```
No ELSE → NULL. The first matching WHEN wins.
""",
)

EX = [
    dict(
        title="Price bands",
        task="Label every product `cheap` (< 500 TL), `mid` (< 5000 TL) or `premium`, and count products per band: `band, n`. Order the bands cheap, mid, premium.",
        hint="GROUP BY the CASE expression (or its alias). For the order, `ORDER BY MIN(price_kurus)` is a neat trick.",
        sol="""
SELECT CASE WHEN price_kurus < 50000 THEN 'cheap'
            WHEN price_kurus < 500000 THEN 'mid'
            ELSE 'premium' END AS band,
       COUNT(*) AS n
FROM products
GROUP BY band
ORDER BY MIN(price_kurus);
""",
    ),
    dict(
        title="Custom sort order",
        concept="`ORDER BY CASE ... END` lets you sort by any business rule instead of alphabetically.",
        task="Count orders per status (`status, n`) but list them in workflow order: pending, shipped, delivered, returned, cancelled.",
        sol="""
SELECT status, COUNT(*) AS n
FROM orders
GROUP BY status
ORDER BY CASE status WHEN 'pending' THEN 1 WHEN 'shipped' THEN 2 WHEN 'delivered' THEN 3
                     WHEN 'returned' THEN 4 ELSE 5 END;
""",
    ),
    dict(
        title="Pivot with conditional aggregation",
        concept="`SUM(CASE WHEN cond THEN 1 ELSE 0 END)` counts rows matching `cond` inside each group. One such column per value = a pivot table.",
        task="For each month of **2026**: `month, delivered, cancelled, returned, other` (counts). Chronological.",
        sol="""
SELECT strftime('%Y-%m', ordered_at) AS month,
       SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) AS delivered,
       SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
       SUM(CASE WHEN status = 'returned'  THEN 1 ELSE 0 END) AS returned,
       SUM(CASE WHEN status NOT IN ('delivered', 'cancelled', 'returned') THEN 1 ELSE 0 END) AS other
FROM orders
WHERE ordered_at >= '2026-01-01'
GROUP BY month
ORDER BY month;
""",
    ),
    dict(
        title="Money pivot",
        task="Per year (`year`), total paid in TL by method as three columns `card_tl, cash_tl, transfer_tl`. Use `SUM(CASE ... THEN amount ...)`.",
        sol="""
SELECT strftime('%Y', paid_at) AS year,
       SUM(CASE WHEN method = 'card'     THEN amount_kurus ELSE 0 END) / 100.0 AS card_tl,
       SUM(CASE WHEN method = 'cash'     THEN amount_kurus ELSE 0 END) / 100.0 AS cash_tl,
       SUM(CASE WHEN method = 'transfer' THEN amount_kurus ELSE 0 END) / 100.0 AS transfer_tl
FROM payments
GROUP BY year
ORDER BY year;
""",
    ),
    dict(
        title="COALESCE: first non-NULL wins",
        task="For customers 1–10: `id`, `contact` = phone if known, otherwise email; `city` = city or `'Unknown'`. By id.",
        sol="""
SELECT id, COALESCE(phone, email) AS contact, COALESCE(city, 'Unknown') AS city
FROM customers WHERE id <= 10 ORDER BY id;
""",
    ),
    dict(
        title="NULLIF: safe division",
        concept="`NULLIF(a, b)` returns NULL when a = b. `x / NULLIF(y, 0)` gives NULL instead of a divide-by-zero surprise. (SQLite returns NULL for /0 anyway, but most databases throw an error.)",
        task="Return rate per product: `name`, `sold` (units in delivered+returned orders), `returned` (units in returned orders), `return_pct` = 100 × returned / sold rounded to 1. Only products with `returned > 0`, highest rate first.",
        sol="""
SELECT p.name,
       SUM(oi.quantity) AS sold,
       SUM(CASE WHEN o.status = 'returned' THEN oi.quantity ELSE 0 END) AS returned,
       ROUND(100.0 * SUM(CASE WHEN o.status = 'returned' THEN oi.quantity ELSE 0 END)
             / NULLIF(SUM(oi.quantity), 0), 1) AS return_pct
FROM products AS p
JOIN order_items AS oi ON oi.product_id = p.id
JOIN orders AS o ON o.id = oi.order_id
WHERE o.status IN ('delivered', 'returned')
GROUP BY p.id
HAVING returned > 0
ORDER BY return_pct DESC, p.name;
""",
    ),
    dict(
        title="CASE and NULL",
        concept="`CASE city WHEN NULL THEN ...` never matches (it tests `city = NULL`). Use the searched form `CASE WHEN city IS NULL THEN ...`.",
        task="Count customers per `region`: `Black Sea` (Samsun, Trabzon), `Marmara` (Istanbul, Bursa, Eskisehir), `Other` (any other known city), `No city` (NULL). Columns `region, n`, biggest first.",
        sol="""
SELECT CASE WHEN city IS NULL THEN 'No city'
            WHEN city IN ('Samsun', 'Trabzon') THEN 'Black Sea'
            WHEN city IN ('Istanbul', 'Bursa', 'Eskisehir') THEN 'Marmara'
            ELSE 'Other' END AS region,
       COUNT(*) AS n
FROM customers
GROUP BY region
ORDER BY n DESC;
""",
    ),
    dict(
        title="Age groups",
        task="Using the date `2026-11-13` as 'today', put customers into `under 25`, `25-39`, `40-59`, `60+`, `unknown` and count them: `age_group, n`, in that order.",
        hint="Age ≈ `(julianday('2026-11-13') - julianday(birth_date)) / 365.25`, truncated with `CAST(... AS INTEGER)`.",
        sol="""
WITH a AS (
  SELECT CAST((julianday('2026-11-13') - julianday(birth_date)) / 365.25 AS INTEGER) AS age
  FROM customers
)
SELECT CASE WHEN age IS NULL THEN 'unknown'
            WHEN age < 25 THEN 'under 25'
            WHEN age < 40 THEN '25-39'
            WHEN age < 60 THEN '40-59'
            ELSE '60+' END AS age_group,
       COUNT(*) AS n
FROM a
GROUP BY age_group
ORDER BY CASE age_group WHEN 'under 25' THEN 1 WHEN '25-39' THEN 2 WHEN '40-59' THEN 3
                        WHEN '60+' THEN 4 ELSE 5 END;
""",
    ),
    dict(
        title="Customer segments",
        task="Segment **every** customer by delivered spend: `VIP` (≥ 50 000 TL), `regular` (> 0), `inactive` (nothing delivered). Count per segment: `segment, n`, biggest first.",
        hint="LEFT JOIN customers to a per-customer delivered-spend subquery; `COALESCE(spend, 0)`. SQLite's `iif(cond, a, b)` is a 2-way CASE shortcut.",
        sol="""
SELECT CASE WHEN COALESCE(s.spend, 0) >= 5000000 THEN 'VIP'
            WHEN COALESCE(s.spend, 0) > 0 THEN 'regular'
            ELSE 'inactive' END AS segment,
       COUNT(*) AS n
FROM customers AS c
LEFT JOIN (SELECT o.customer_id, SUM(oi.quantity * oi.unit_price_kurus) AS spend
           FROM orders AS o JOIN order_items AS oi ON oi.order_id = o.id
           WHERE o.status = 'delivered' GROUP BY o.customer_id) AS s
       ON s.customer_id = c.id
GROUP BY segment
ORDER BY n DESC;
""",
    ),
    dict(
        title="Percentages per group",
        task="Per year: `year`, `orders`, `web_pct` = % of that year's orders with no sales rep (`employee_id IS NULL`), rounded to 1.",
        sol="""
SELECT strftime('%Y', ordered_at) AS year, COUNT(*) AS orders,
       ROUND(100.0 * SUM(CASE WHEN employee_id IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS web_pct
FROM orders
GROUP BY year
ORDER BY year;
""",
    ),
    dict(
        title="CASE inside UPDATE",
        concept="One UPDATE with a CASE can apply different rules to different rows in a single pass.",
        task="Restock: products with `stock = 0` get stock **50**; products with stock below 10 get **+20**; others unchanged. Do it in **one** UPDATE statement.",
        hint="`UPDATE products SET stock = CASE WHEN ... END WHERE stock < 10;` — or keep `ELSE stock` and no WHERE.",
        sol="""
UPDATE products
SET stock = CASE WHEN stock = 0 THEN 50 ELSE stock + 20 END
WHERE stock < 10;
""",
        check="SELECT id, name, stock FROM products WHERE id IN (1, 2, 3, 7, 12, 28, 34, 35, 36) ORDER BY id;",
    ),
]
