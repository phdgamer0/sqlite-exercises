SECTION = dict(
    num=4, title="Subqueries and set operations", db="shop",
    pdf="Hafta 2 – Alt sorgular, IN, Küme işlemleri (UNION, INTERSECT, EXCEPT)",
    intro="""
A subquery is a query used as a value (scalar), a list (`IN`), a test (`EXISTS`) or a table
(`FROM (...)`). A **correlated** subquery refers to the outer row and runs once per row.

Set operations stack two results with the **same number of columns**: `UNION` (dedup),
`UNION ALL` (keep duplicates), `INTERSECT`, `EXCEPT`.
""",
)

EX = [
    dict(
        title="Scalar subquery",
        task="Products priced **above the average product price**: `name, price_kurus`, most expensive first.",
        sol="""
SELECT name, price_kurus FROM products
WHERE price_kurus > (SELECT AVG(price_kurus) FROM products)
ORDER BY price_kurus DESC;
""",
    ),
    dict(
        title="Nested IN",
        task="`id, first_name, last_name` of customers who ordered at least one product from the **Books** top-level category or any of its sub-categories (Novels, Science, Comics). Order by id.",
        hint="categories where `id = 2 OR parent_id = 2` → products IN that → order_items → orders.customer_id. Three nested INs, no JOIN.",
        sol="""
SELECT id, first_name, last_name FROM customers
WHERE id IN (
  SELECT customer_id FROM orders WHERE id IN (
    SELECT order_id FROM order_items WHERE product_id IN (
      SELECT id FROM products WHERE category_id IN (
        SELECT id FROM categories WHERE id = 2 OR parent_id = 2))))
ORDER BY id;
""",
    ),
    dict(
        title="The NOT IN + NULL trap",
        concept="`x NOT IN (1, 2, NULL)` is never true: SQL can't rule out that x equals the unknown value. If the subquery can return NULL, `NOT IN` returns **nothing**.",
        task="How many customers have **never referred anyone**? Return `n`. (First try `WHERE id NOT IN (SELECT referred_by FROM customers)` and see what you get.)",
        hint="Filter the NULLs out of the subquery, or use `NOT EXISTS`.",
        sol="""
SELECT COUNT(*) AS n FROM customers AS c
WHERE NOT EXISTS (SELECT 1 FROM customers AS x WHERE x.referred_by = c.id);
""",
    ),
    dict(
        title="Correlated subquery: above my category's average",
        task="Products that cost more than the average price **of their own category**: `name, category_id, price_kurus`, by category_id then price desc. (Products without category are ignored.)",
        sol="""
SELECT p.name, p.category_id, p.price_kurus
FROM products AS p
WHERE p.price_kurus > (SELECT AVG(x.price_kurus) FROM products AS x WHERE x.category_id = p.category_id)
ORDER BY p.category_id, p.price_kurus DESC;
""",
    ),
    dict(
        title="EXISTS",
        task="`id, first_name, last_name` of customers who have **at least one returned** order. By id.",
        sol="""
SELECT id, first_name, last_name FROM customers AS c
WHERE EXISTS (SELECT 1 FROM orders AS o WHERE o.customer_id = c.id AND o.status = 'returned')
ORDER BY id;
""",
    ),
    dict(
        title="Aggregate of an aggregate",
        concept="You can't write `MAX(AVG(...))`. Compute the inner aggregate in a subquery in `FROM`, then aggregate that.",
        task="Compute every customer's **average order value** (in kuruş, from order_items, all statuses). Return the highest of these averages, in TL rounded to 2, as `best_avg_tl`.",
        sol="""
SELECT ROUND(MAX(avg_kurus) / 100.0, 2) AS best_avg_tl
FROM (
  SELECT o.customer_id, AVG(t.total) AS avg_kurus
  FROM orders AS o
  JOIN (SELECT order_id, SUM(quantity * unit_price_kurus) AS total
        FROM order_items GROUP BY order_id) AS t ON t.order_id = o.id
  GROUP BY o.customer_id
);
""",
    ),
    dict(
        title="UNION",
        task="One column `city`: every city that appears as a customer city **or** as an order ship_city, without duplicates and without NULL, alphabetical.",
        sol="""
SELECT city FROM customers WHERE city IS NOT NULL
UNION
SELECT ship_city FROM orders
ORDER BY city;
""",
    ),
    dict(
        title="UNION vs UNION ALL",
        task="One row with two columns: `union_rows` = number of rows in (customer cities UNION ship cities), `union_all_rows` = same with UNION ALL. Keep the NULL filter on customers.",
        sol="""
SELECT
 (SELECT COUNT(*) FROM (SELECT city FROM customers WHERE city IS NOT NULL UNION SELECT ship_city FROM orders)) AS union_rows,
 (SELECT COUNT(*) FROM (SELECT city FROM customers WHERE city IS NOT NULL UNION ALL SELECT ship_city FROM orders)) AS union_all_rows;
""",
    ),
    dict(
        title="INTERSECT",
        task="`customer_id`s of customers who have paid **both** by `card` and by `transfer` (on any of their orders). Sorted.",
        sol="""
SELECT o.customer_id FROM payments AS p JOIN orders AS o ON o.id = p.order_id WHERE p.method = 'card'
INTERSECT
SELECT o.customer_id FROM payments AS p JOIN orders AS o ON o.id = p.order_id WHERE p.method = 'transfer'
ORDER BY 1;
""",
    ),
    dict(
        title="EXCEPT: churned customers",
        task="`customer_id`s who ordered in **2025** but **not in 2026**. Sorted.",
        sol="""
SELECT customer_id FROM orders WHERE ordered_at < '2026-01-01'
EXCEPT
SELECT customer_id FROM orders WHERE ordered_at >= '2026-01-01'
ORDER BY 1;
""",
    ),
    dict(
        title="Subquery in SELECT",
        task="Every employee: `first_name, title, reports` where `reports` is the number of people whose `manager_id` is that employee. Most reports first, then first_name.",
        sol="""
SELECT e.first_name, e.title,
       (SELECT COUNT(*) FROM employees AS x WHERE x.manager_id = e.id) AS reports
FROM employees AS e
ORDER BY reports DESC, e.first_name;
""",
    ),
    dict(
        title="Product never sold — three ways",
        task="Names of products that never appear in `order_items`, alphabetically. Write it with `NOT IN`, with `NOT EXISTS`, and with `LEFT JOIN ... IS NULL`, and convince yourself all three agree here (and when `NOT IN` would break).",
        sol="""
SELECT name FROM products AS p
WHERE NOT EXISTS (SELECT 1 FROM order_items AS oi WHERE oi.product_id = p.id)
ORDER BY name;
""",
    ),
]
