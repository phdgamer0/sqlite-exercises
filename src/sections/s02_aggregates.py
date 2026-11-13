SECTION = dict(
    num=2, title="Aggregates, GROUP BY, HAVING", db="shop",
    pdf="Hafta 1 (COUNT/AVG/SUM/MIN/MAX/DISTINCT) + Hafta 2 (GROUP BY, HAVING)",
    intro="""
Aggregates collapse many rows into one. `GROUP BY` makes one group per distinct key, and
the aggregate runs **per group**. `WHERE` filters rows *before* grouping; `HAVING` filters
groups *after*.

Line revenue = `quantity * unit_price_kurus` (from `order_items`). These exercises stay on
one or two tables; joins get their own section next.
""",
)

EX = [
    dict(
        title="One-row summary",
        task="In one row: number of products `n`, average price in TL `avg_tl` (rounded to 2), cheapest `min_tl` and most expensive `max_tl` (in TL).",
        hint="`COUNT(*)`, `ROUND(AVG(price_kurus) / 100.0, 2)`, `MIN(...)/100.0`, `MAX(...)/100.0`",
        sol="""
SELECT COUNT(*) AS n,
       ROUND(AVG(price_kurus) / 100.0, 2) AS avg_tl,
       MIN(price_kurus) / 100.0 AS min_tl,
       MAX(price_kurus) / 100.0 AS max_tl
FROM products;
""",
    ),
    dict(
        title="COUNT(*) vs COUNT(col) vs COUNT(DISTINCT col)",
        concept="`COUNT(*)` counts rows. `COUNT(col)` skips NULLs. `COUNT(DISTINCT col)` counts different non-NULL values.",
        task="On `customers`, return `all_rows`, `with_phone`, `with_city`, `distinct_cities` in one row.",
        sol="""
SELECT COUNT(*) AS all_rows, COUNT(phone) AS with_phone,
       COUNT(city) AS with_city, COUNT(DISTINCT city) AS distinct_cities
FROM customers;
""",
    ),
    dict(
        title="Orders per status",
        task="How many orders are there per `status`? Columns `status, n`, biggest group first.",
        sol="SELECT status, COUNT(*) AS n FROM orders GROUP BY status ORDER BY n DESC;",
    ),
    dict(
        title="Order value",
        task="For each order compute its value in TL from `order_items` as `total_tl`. Return the **5 largest** orders: `order_id, total_tl`.",
        hint="`SUM(quantity * unit_price_kurus) / 100.0` grouped by `order_id`.",
        sol="""
SELECT order_id, SUM(quantity * unit_price_kurus) / 100.0 AS total_tl
FROM order_items
GROUP BY order_id
ORDER BY total_tl DESC
LIMIT 5;
""",
    ),
    dict(
        title="Group by an expression: months",
        concept="You can group by any expression. `strftime('%Y-%m', ordered_at)` or `substr(ordered_at, 1, 7)` turn a timestamp into a month key.",
        task="Number of orders per month **in 2026**: `month` (like `2026-01`) and `n`, chronological.",
        sol="""
SELECT strftime('%Y-%m', ordered_at) AS month, COUNT(*) AS n
FROM orders
WHERE ordered_at >= '2026-01-01'
GROUP BY month
ORDER BY month;
""",
    ),
    dict(
        title="HAVING",
        task="Which cities have **at least 10 customers**? Columns `city, n`, biggest first. Ignore customers without a city.",
        hint="`WHERE city IS NOT NULL ... GROUP BY city HAVING COUNT(*) >= 10`",
        sol="""
SELECT city, COUNT(*) AS n
FROM customers
WHERE city IS NOT NULL
GROUP BY city
HAVING COUNT(*) >= 10
ORDER BY n DESC;
""",
    ),
    dict(
        title="WHERE and HAVING together",
        task="Loyal customers: `customer_id` and `n` for customers with **at least 12 orders that were not cancelled**. Order by `n` desc, then `customer_id`.",
        hint="Cancelled orders must be removed *before* counting → WHERE. The threshold applies to the count → HAVING.",
        sol="""
SELECT customer_id, COUNT(*) AS n
FROM orders
WHERE status <> 'cancelled'
GROUP BY customer_id
HAVING COUNT(*) >= 12
ORDER BY n DESC, customer_id;
""",
    ),
    dict(
        title="Ratings that mean something",
        task="Average rating per `product_id` (rounded to 2, as `avg_rating`) and the number of reviews `n`, but only for products with **at least 5 reviews**. Best first.",
        sol="""
SELECT product_id, ROUND(AVG(rating), 2) AS avg_rating, COUNT(*) AS n
FROM reviews
GROUP BY product_id
HAVING COUNT(*) >= 5
ORDER BY avg_rating DESC;
""",
    ),
    dict(
        title="A ratio from two counts",
        concept="`COUNT(*) * 1.0 / COUNT(DISTINCT x)` = average number of rows per x — no subquery needed.",
        task="On average, how many different products (line items) does an order contain? One column `avg_lines`, rounded to 2.",
        sol="SELECT ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT order_id), 2) AS avg_lines FROM order_items;",
    ),
    dict(
        title="Grouping by two columns",
        task="Total paid in TL per **year** and **payment method**: `year, method, total_tl`. Sort by year, then total descending.",
        hint="`strftime('%Y', paid_at)` and `GROUP BY year, method`",
        sol="""
SELECT strftime('%Y', paid_at) AS year, method, SUM(amount_kurus) / 100.0 AS total_tl
FROM payments
GROUP BY year, method
ORDER BY year, total_tl DESC;
""",
    ),
    dict(
        title="Birth decades",
        task="Count customers per birth decade: `decade` (e.g. `1980`) and `n`. Skip unknown birth dates. Oldest decade first.",
        hint="`CAST(substr(birth_date, 1, 3) AS INTEGER) * 10` or `(CAST(strftime('%Y', birth_date) AS INTEGER) / 10) * 10`",
        sol="""
SELECT (CAST(strftime('%Y', birth_date) AS INTEGER) / 10) * 10 AS decade, COUNT(*) AS n
FROM customers
WHERE birth_date IS NOT NULL
GROUP BY decade
ORDER BY decade;
""",
    ),
    dict(
        title="Most recent order per customer",
        concept="`MAX()` works on text dates because ISO-8601 strings sort chronologically.",
        task="For each customer who ordered: `customer_id, last_order` (their latest `ordered_at`). Show the 5 customers whose last order is the **oldest** (the ones we're losing).",
        sol="""
SELECT customer_id, MAX(ordered_at) AS last_order
FROM orders
GROUP BY customer_id
ORDER BY last_order
LIMIT 5;
""",
        after="SQLite lets you put a non-aggregated column next to MAX() (a 'bare column') and picks the value from the max row. Other databases reject that — don't rely on it.",
    ),
    dict(
        title="Best sellers by units",
        task="Top 3 `product_id`s by total units sold (`units`), counting only order lines (all statuses).",
        sol="""
SELECT product_id, SUM(quantity) AS units
FROM order_items
GROUP BY product_id
ORDER BY units DESC
LIMIT 3;
""",
    ),
    dict(
        title="Aggregates ignore NULL",
        concept="`AVG(col)` divides by the number of **non-NULL** values, not by the number of rows.",
        task="In `reviews`, return in one row: `total` reviews, `with_comment` (comment not NULL) and `pct_with_comment` rounded to 1 decimal.",
        hint="`ROUND(100.0 * COUNT(comment) / COUNT(*), 1)`",
        sol="""
SELECT COUNT(*) AS total, COUNT(comment) AS with_comment,
       ROUND(100.0 * COUNT(comment) / COUNT(*), 1) AS pct_with_comment
FROM reviews;
""",
    ),
]
