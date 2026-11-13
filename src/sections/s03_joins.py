SECTION = dict(
    num=3, title="JOINs — inner, outer, self, anti, and the fan-out trap", db="shop",
    pdf="Hafta 2 – Tablolar Arasındaki İlişkiler (PK/FK, INNER/LEFT/RIGHT/FULL/NATURAL JOIN)",
    intro="""
Every join links a **primary key** to a **foreign key**. Draw the path first:

```
customers ─< orders ─< order_items >─ products >─ categories ─┐ (parent_id)
     │ (referred_by)    │       └─< payments                   └─ categories
     └─ customers       └─> employees ─ (manager_id) ─> employees
reviews >─ products, reviews >─ customers
```

`─<` means "one to many". When you go *down* a one-to-many link, rows multiply.
""",
)

EX = [
    dict(
        title="Order 42, with product names",
        task="Show `product` (name), `quantity`, `unit_price_kurus` for every line of **order 42**.",
        hint="`order_items JOIN products ON products.id = order_items.product_id`",
        sol="""
SELECT p.name AS product, oi.quantity, oi.unit_price_kurus
FROM order_items AS oi
JOIN products AS p ON p.id = oi.product_id
WHERE oi.order_id = 42;
""",
    ),
    dict(
        title="What did Nazli Erdogan buy?",
        concept="Chain joins along the FK path: customers → orders → order_items → products.",
        task="Distinct product names that customer **id 80** received (status `delivered`), alphabetically. Column `product`.",
        sol="""
SELECT DISTINCT p.name AS product
FROM customers AS c
JOIN orders AS o       ON o.customer_id = c.id
JOIN order_items AS oi ON oi.order_id = o.id
JOIN products AS p     ON p.id = oi.product_id
WHERE c.id = 80 AND o.status = 'delivered'
ORDER BY product;
""",
    ),
    dict(
        title="Anti-join: customers who never ordered",
        concept="`LEFT JOIN` keeps every left row; where nothing matched, the right side is NULL. Filtering on `right.id IS NULL` keeps only the unmatched ones.",
        task="`id, first_name, last_name` of customers with **no orders at all**, by id.",
        sol="""
SELECT c.id, c.first_name, c.last_name
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.id
WHERE o.id IS NULL
ORDER BY c.id;
""",
    ),
    dict(
        title="Counting zeros: COUNT(*) vs COUNT(col)",
        concept="After a LEFT JOIN an unmatched row still exists (with NULLs), so `COUNT(*)` says 1. `COUNT(oi.order_id)` says 0.",
        task="Every product with the number of order lines it appears in, as `name, times_ordered` — products never ordered must show **0**. Fewest first, then by name.",
        sol="""
SELECT p.name, COUNT(oi.order_id) AS times_ordered
FROM products AS p
LEFT JOIN order_items AS oi ON oi.product_id = p.id
GROUP BY p.id
ORDER BY times_ordered, p.name;
""",
    ),
    dict(
        title="LEFT JOIN + filter: ON vs WHERE",
        concept="A condition on the *right* table placed in `WHERE` throws away the NULL rows and turns your LEFT JOIN back into an INNER JOIN. Put it in `ON` instead.",
        task="For **every** product in category 16 (Fitness), how many units were sold in orders placed in **2026**? Columns `name, units_2026`; products without 2026 sales show 0.",
        hint="Join `order_items` and `orders` inside the LEFT JOIN (or join to a subquery), put the 2026 condition in `ON`, use `COALESCE(SUM(...), 0)`.",
        sol="""
SELECT p.name, COALESCE(SUM(oi.quantity), 0) AS units_2026
FROM products AS p
LEFT JOIN (order_items AS oi JOIN orders AS o ON o.id = oi.order_id)
       ON oi.product_id = p.id AND o.ordered_at >= '2026-01-01'
WHERE p.category_id = 16
GROUP BY p.id
ORDER BY p.name;
""",
    ),
    dict(
        title="Self join: who is my manager?",
        concept="A table can be joined to itself with two aliases. Use LEFT JOIN so the boss (manager_id NULL) stays.",
        task="`employee` (first + last name), `title`, `manager` (first + last name, NULL for the CEO), ordered by employee id.",
        sol="""
SELECT e.first_name || ' ' || e.last_name AS employee, e.title,
       m.first_name || ' ' || m.last_name AS manager
FROM employees AS e
LEFT JOIN employees AS m ON m.id = e.manager_id
ORDER BY e.id;
""",
    ),
    dict(
        title="Self join: referrals across cities",
        task="Pairs where a customer was referred by someone living in a **different** city (both cities known). Columns `customer_id, customer_city, referrer_id, referrer_city`, by customer_id.",
        sol="""
SELECT c.id AS customer_id, c.city AS customer_city, r.id AS referrer_id, r.city AS referrer_city
FROM customers AS c
JOIN customers AS r ON r.id = c.referred_by
WHERE c.city <> r.city
ORDER BY c.id;
""",
        after="`c.city <> r.city` is NULL when either city is NULL, so those pairs are dropped automatically — check that this is what you wanted.",
    ),
    dict(
        title="Revenue per category (with an 'Uncategorised' bucket)",
        task="Delivered revenue in TL per category name: `category, revenue_tl`. Products with no category go into a bucket named `Uncategorised`. Biggest first.",
        hint="products → categories must be a LEFT JOIN; `COALESCE(c.name, 'Uncategorised')`.",
        sol="""
SELECT COALESCE(c.name, 'Uncategorised') AS category,
       SUM(oi.quantity * oi.unit_price_kurus) / 100.0 AS revenue_tl
FROM order_items AS oi
JOIN orders AS o ON o.id = oi.order_id
JOIN products AS p ON p.id = oi.product_id
LEFT JOIN categories AS c ON c.id = p.category_id
WHERE o.status = 'delivered'
GROUP BY category
ORDER BY revenue_tl DESC;
""",
    ),
    dict(
        title="The fan-out trap (double counting)",
        concept="Joining an order to its items (many) **and** its payments (many) gives items × payments rows; every SUM is then inflated. Aggregate each child table **separately first**, then join the small results.",
        task="Orders whose paid total differs from their item total. Columns `order_id, items_kurus, paid_kurus` (paid = 0 if no payment), only for statuses `delivered`, `shipped`, `returned`. Order by `order_id`.",
        hint="Two subqueries in FROM: one `GROUP BY order_id` over order_items, one over payments; LEFT JOIN the payments one.",
        sol="""
SELECT i.order_id, i.items_kurus, COALESCE(p.paid_kurus, 0) AS paid_kurus
FROM (SELECT order_id, SUM(quantity * unit_price_kurus) AS items_kurus
      FROM order_items GROUP BY order_id) AS i
JOIN orders AS o ON o.id = i.order_id
LEFT JOIN (SELECT order_id, SUM(amount_kurus) AS paid_kurus
           FROM payments GROUP BY order_id) AS p ON p.order_id = i.order_id
WHERE o.status IN ('delivered', 'shipped', 'returned')
  AND i.items_kurus <> COALESCE(p.paid_kurus, 0)
ORDER BY i.order_id;
""",
        after="Try the naive version (join items and payments directly, SUM both) and look at an order paid in two installments — its item total doubles.",
    ),
    dict(
        title="CROSS JOIN to fill in the zeros",
        concept="`CROSS JOIN` pairs every row with every row. Useful to build a complete grid, then LEFT JOIN the real counts onto it.",
        task="For every combination of `method` (card/cash/transfer) and year (2025, 2026), the number of payments — combinations with no payments show 0. Columns `method, year, n`, sorted by method then year.",
        hint="`(SELECT DISTINCT method FROM payments) CROSS JOIN (SELECT '2025' AS year UNION SELECT '2026')`, then LEFT JOIN payments on both keys.",
        sol="""
SELECT m.method, y.year, COUNT(p.id) AS n
FROM (SELECT DISTINCT method FROM payments) AS m
CROSS JOIN (SELECT '2025' AS year UNION SELECT '2026') AS y
LEFT JOIN payments AS p ON p.method = m.method AND strftime('%Y', p.paid_at) = y.year
GROUP BY m.method, y.year
ORDER BY m.method, y.year;
""",
    ),
    dict(
        title="NATURAL JOIN gone wrong",
        concept="`NATURAL JOIN` joins on **every column with the same name**. `products` and `categories` share both `id` and `name`, so it compares product.id = category.id AND product.name = category.name.",
        task="How many rows does `products NATURAL JOIN categories` return? Then write the correct join with `ON` and count those rows too. Return one row: `natural_rows, correct_rows`.",
        sol="""
SELECT (SELECT COUNT(*) FROM products NATURAL JOIN categories) AS natural_rows,
       (SELECT COUNT(*) FROM products AS p JOIN categories AS c ON c.id = p.category_id) AS correct_rows;
""",
    ),
    dict(
        title="FULL OUTER JOIN: reviewers vs. recent buyers",
        concept="`FULL JOIN` keeps unmatched rows from **both** sides (SQLite ≥ 3.39). Handy for comparing two lists where each side has members the other lacks.",
        task="Marketing wants one list of customers who either wrote reviews **or** ordered since `2026-09-01`. Columns `customer_id`, `reviews` (how many reviews they wrote) and `recent_orders` (orders since 2026-09-01); missing counts show 0. Sort by customer_id.",
        hint="FULL JOIN two grouped subqueries; `COALESCE(a.customer_id, b.customer_id)`.",
        sol="""
SELECT COALESCE(a.customer_id, b.customer_id) AS customer_id,
       COALESCE(a.n, 0) AS reviews,
       COALESCE(b.n, 0) AS recent_orders
FROM (SELECT customer_id, COUNT(*) AS n FROM reviews GROUP BY customer_id) AS a
FULL JOIN (SELECT customer_id, COUNT(*) AS n FROM orders
           WHERE ordered_at >= '2026-09-01' GROUP BY customer_id) AS b
       ON a.customer_id = b.customer_id
ORDER BY customer_id;
""",
        after="Rows with `reviews = 0` came only from the right side, rows with `recent_orders = 0` only from the left. A LEFT JOIN would have lost one of those groups.",
    ),
    dict(
        title="Reviews from people who never bought the product",
        task="Suspicious reviews: `review_id, product_id, customer_id` for reviews where that customer has **no** order line for that product. By review_id.",
        hint="LEFT JOIN `orders` + `order_items` on *both* customer and product, keep rows where the join found nothing.",
        sol="""
SELECT r.id AS review_id, r.product_id, r.customer_id
FROM reviews AS r
LEFT JOIN (orders AS o JOIN order_items AS oi ON oi.order_id = o.id)
       ON o.customer_id = r.customer_id AND oi.product_id = r.product_id
WHERE o.id IS NULL
ORDER BY r.id;
""",
    ),
    dict(
        title="Sales reps leaderboard (including people with no sales)",
        task="Every employee with `name` (first + last), `orders` (number of **delivered** orders they handled) and `revenue_tl`. People without sales show 0 and 0. Biggest revenue first, then name.",
        hint="Pre-aggregate delivered revenue per employee in a subquery, then LEFT JOIN employees to it.",
        sol="""
SELECT e.first_name || ' ' || e.last_name AS name,
       COALESCE(s.orders, 0) AS orders,
       COALESCE(s.revenue_kurus, 0) / 100.0 AS revenue_tl
FROM employees AS e
LEFT JOIN (
    SELECT o.employee_id, COUNT(DISTINCT o.id) AS orders,
           SUM(oi.quantity * oi.unit_price_kurus) AS revenue_kurus
    FROM orders AS o JOIN order_items AS oi ON oi.order_id = o.id
    WHERE o.status = 'delivered'
    GROUP BY o.employee_id
) AS s ON s.employee_id = e.id
ORDER BY revenue_tl DESC, name;
""",
    ),
    dict(
        title="GROUP BY name vs GROUP BY id",
        concept="Two different customers can share a name. Grouping by the name silently merges them.",
        task="Top 5 customers by number of orders, showing `id, first_name, last_name, n`. Ties broken by id. (Then try grouping by name only and look at *Hakan Kurt*.)",
        sol="""
SELECT c.id, c.first_name, c.last_name, COUNT(*) AS n
FROM customers AS c JOIN orders AS o ON o.customer_id = c.id
GROUP BY c.id
ORDER BY n DESC, c.id
LIMIT 5;
""",
    ),
]
