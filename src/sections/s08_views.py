SECTION = dict(
    num=8, title="Views", db="shop",
    pdf="Hafta 5 – Görünümler (CREATE VIEW, özet görünüm, TEMP VIEW, bölümleme, güvenlik, görünüme yazılamaz)",
    intro="""
A view is a **saved query with a name**. It stores no rows — every time you select from it,
the query runs against the current tables. Uses from the lecture: simplify (hide joins),
aggregate (summary), partition (one view per period), secure (hide columns).

Exercises are cumulative: start with `./drill reset shop`. Inspect views with `.schema view_name`
or `SELECT name, type FROM sqlite_schema;`.
""",
)

EX = [
    dict(
        title="A view that hides the joins",
        task="Create view `purchase_history` with columns `customer_id, customer` (first + last name), `city, ordered_at, product, quantity` for **delivered** orders only.",
        sol="""
CREATE VIEW purchase_history AS
SELECT c.id AS customer_id, c.first_name || ' ' || c.last_name AS customer, c.city,
       o.ordered_at, p.name AS product, oi.quantity
FROM customers AS c
JOIN orders AS o       ON o.customer_id = c.id
JOIN order_items AS oi ON oi.order_id = o.id
JOIN products AS p     ON p.id = oi.product_id
WHERE o.status = 'delivered';
""",
        check="""
SELECT ordered_at, product, quantity FROM purchase_history
WHERE customer_id = 13 ORDER BY ordered_at, product LIMIT 6;
SELECT COUNT(*) AS rows FROM purchase_history;
""",
    ),
    dict(
        title="Query a view like a table",
        task="Using **only** `purchase_history`: the 5 products bought by the most different customers — `product, buyers`. Ties by product name.",
        sol="""
SELECT product, COUNT(DISTINCT customer_id) AS buyers
FROM purchase_history
GROUP BY product
ORDER BY buyers DESC, product
LIMIT 5;
""",
    ),
    dict(
        title="A summary view",
        task="Create view `order_totals(order_id, customer_id, ordered_at, status, items, total_kurus)` — one row per order, `items` = number of lines, `total_kurus` = sum of quantity × unit price.",
        sol="""
CREATE VIEW order_totals AS
SELECT o.id AS order_id, o.customer_id, o.ordered_at, o.status,
       COUNT(*) AS items, SUM(oi.quantity * oi.unit_price_kurus) AS total_kurus
FROM orders AS o JOIN order_items AS oi ON oi.order_id = o.id
GROUP BY o.id;
""",
        check="""
SELECT status, COUNT(*) AS orders, SUM(total_kurus) / 100.0 AS total_tl
FROM order_totals GROUP BY status ORDER BY status;
""",
    ),
    dict(
        title="A view built on a view",
        task="Create view `customer_value(customer_id, orders, lifetime_tl)` on top of `order_totals`, counting **delivered** orders only. Then show the top 5 by lifetime_tl.",
        sol="""
CREATE VIEW customer_value AS
SELECT customer_id, COUNT(*) AS orders, SUM(total_kurus) / 100.0 AS lifetime_tl
FROM order_totals
WHERE status = 'delivered'
GROUP BY customer_id;
""",
        check="SELECT * FROM customer_value ORDER BY lifetime_tl DESC LIMIT 5;",
    ),
    dict(
        title="Partitioning views",
        concept="Like the lecture's August/September/October reports: one view per slice of the same table, so each report queries its own 'table'.",
        task="Create views `orders_2025` and `orders_2026`, each with all columns of `orders` for that year.",
        sol="""
CREATE VIEW orders_2025 AS SELECT * FROM orders WHERE ordered_at >= '2025-01-01' AND ordered_at < '2026-01-01';
CREATE VIEW orders_2026 AS SELECT * FROM orders WHERE ordered_at >= '2026-01-01' AND ordered_at < '2027-01-01';
""",
        check="""
SELECT (SELECT COUNT(*) FROM orders_2025) AS y2025, (SELECT COUNT(*) FROM orders_2026) AS y2026,
       (SELECT COUNT(*) FROM orders) AS total;
""",
    ),
    dict(
        title="A security view",
        concept="An analyst should see behaviour, not identities. Expose only safe columns. (In SQLite anyone who can open the file can still read the tables — real databases add `GRANT`/`REVOKE`; SQLite has no users.)",
        task="Create view `customers_public(id, name, city, birth_year)` where `name` is first name + last-name initial + '.' (e.g. `Ayse Y.`), no email/phone/full birth date.",
        hint="`first_name || ' ' || substr(last_name, 1, 1) || '.'`, `strftime('%Y', birth_date)`",
        sol="""
CREATE VIEW customers_public AS
SELECT id, first_name || ' ' || substr(last_name, 1, 1) || '.' AS name, city,
       strftime('%Y', birth_date) AS birth_year
FROM customers;
""",
        check="SELECT * FROM customers_public WHERE id <= 5 ORDER BY id;",
    ),
    dict(
        title="You can't write to a view (yet)",
        nocheck=True, allow_error=True,
        task="Try `DELETE FROM purchase_history WHERE customer_id = 13;` and read the error. Why can't SQLite do this? (Which table's rows should disappear — customers? orders? order_items?)",
        sol="DELETE FROM purchase_history WHERE customer_id = 13;",
        after="Section 10 fixes this with an `INSTEAD OF` trigger: you tell SQLite what a DELETE on the view should mean.",
    ),
    dict(
        title="Views are live",
        task="Insert a new delivered order for customer 13 (`id` 1000, employee NULL, `2026-11-01 10:00:00`, ship_city `Eskisehir`) with one line: 2 × product 37 (Yoga Mat) at 39900. Then look at `customer_value` for customer 13 — no refresh needed.",
        sol="""
INSERT INTO orders (id, customer_id, employee_id, ordered_at, status, ship_city)
VALUES (1000, 13, NULL, '2026-11-01 10:00:00', 'delivered', 'Eskisehir');
INSERT INTO order_items (order_id, product_id, quantity, unit_price_kurus) VALUES (1000, 37, 2, 39900);
""",
        check="SELECT * FROM customer_value WHERE customer_id = 13;",
    ),
    dict(
        title="Replacing a view",
        concept="SQLite has no `CREATE OR REPLACE VIEW`, and `CREATE VIEW IF NOT EXISTS` silently keeps the **old** definition. To change a view: `DROP VIEW` then `CREATE VIEW`.",
        task="Change `customers_public` so it also has a column `orders` (number of orders, 0 for none).",
        sol="""
DROP VIEW customers_public;
CREATE VIEW customers_public AS
SELECT c.id, c.first_name || ' ' || substr(c.last_name, 1, 1) || '.' AS name, c.city,
       strftime('%Y', c.birth_date) AS birth_year,
       (SELECT COUNT(*) FROM orders AS o WHERE o.customer_id = c.id) AS orders
FROM customers AS c;
""",
        check="SELECT * FROM customers_public WHERE id <= 5 ORDER BY id;",
    ),
    dict(
        title="TEMPORARY views",
        nocheck=True,
        concept="`CREATE TEMP VIEW` lives in the `temp` schema and disappears when you close the connection. Good for scratch work that shouldn't pollute the schema.",
        task="Create `CREATE TEMP VIEW big_orders AS SELECT * FROM order_totals WHERE total_kurus > 5000000;`, query it, list it with `SELECT name FROM sqlite_temp_schema;`, then quit (`.quit`), reopen and see that it's gone.",
        sol="""
CREATE TEMP VIEW big_orders AS SELECT * FROM order_totals WHERE total_kurus > 5000000;
SELECT COUNT(*) AS big_orders, (SELECT name FROM sqlite_temp_schema) AS lives_in_temp FROM big_orders;
""",
    ),
    dict(
        title="Which objects exist now?",
        task="List all views in the main schema with how many columns each has: `view, columns`, alphabetically.",
        hint="`sqlite_schema` has `type` and `name`; `pragma_table_info(name)` works on views too.",
        sol="""
SELECT s.name AS view, (SELECT COUNT(*) FROM pragma_table_info(s.name)) AS columns
FROM sqlite_schema AS s
WHERE s.type = 'view'
ORDER BY s.name;
""",
    ),
]
