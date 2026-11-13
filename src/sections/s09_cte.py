SECTION = dict(
    num=9, title="CTEs (WITH) and recursive CTEs", db="shop",
    pdf="Hafta 5 – CTE ile geçici ara sonuçlar (+ WITH RECURSIVE, beyond the slides)",
    intro="""
A CTE is a view that lives for **one statement**:

```sql
WITH spend AS (SELECT ...), big AS (SELECT ... FROM spend ...)
SELECT ... FROM big;
```
CTEs make long queries readable top-to-bottom and let you reuse one intermediate result twice.

`WITH RECURSIVE` adds a loop: an anchor query, `UNION ALL`, and a recursive query that refers
to the CTE itself, repeated until it produces no new rows. Trees (categories, org charts,
referrals) and generated series (calendars) are the classic uses.
""",
)

EX = [
    dict(
        title="Rewrite a subquery as a CTE",
        task="Customers whose delivered spend is **above the average delivered spend** of customers who bought something. `customer_id, spend_tl`, biggest first. Use a CTE `spend`.",
        sol="""
WITH spend AS (
  SELECT o.customer_id, SUM(oi.quantity * oi.unit_price_kurus) AS kurus
  FROM orders AS o JOIN order_items AS oi ON oi.order_id = o.id
  WHERE o.status = 'delivered'
  GROUP BY o.customer_id
)
SELECT customer_id, kurus / 100.0 AS spend_tl
FROM spend
WHERE kurus > (SELECT AVG(kurus) FROM spend)
ORDER BY kurus DESC;
""",
    ),
    dict(
        title="Month over month (CTE joined to itself)",
        task="Delivered revenue per month (`month`, `revenue_tl`) and the previous month's revenue (`prev_tl`) and the change in percent (`change_pct`, 1 decimal). 2026 months only, chronological. Do it with a CTE joined to itself — no window functions.",
        hint="Join `m AS cur` to `m AS prev` on `prev.month = strftime('%Y-%m', cur.month || '-01', '-1 month')`.",
        sol="""
WITH m AS (
  SELECT strftime('%Y-%m', o.ordered_at) AS month, SUM(oi.quantity * oi.unit_price_kurus) AS kurus
  FROM orders AS o JOIN order_items AS oi ON oi.order_id = o.id
  WHERE o.status = 'delivered'
  GROUP BY month
)
SELECT cur.month, cur.kurus / 100.0 AS revenue_tl, prev.kurus / 100.0 AS prev_tl,
       ROUND(100.0 * (cur.kurus - prev.kurus) / prev.kurus, 1) AS change_pct
FROM m AS cur
LEFT JOIN m AS prev ON prev.month = strftime('%Y-%m', cur.month || '-01', '-1 month')
WHERE cur.month >= '2026-01'
ORDER BY cur.month;
""",
    ),
    dict(
        title="Two CTEs, one answer",
        task="Per city (customer city, known only): `city`, `customers`, `buyers` (customers with ≥1 delivered order) and `conversion_pct` (1 decimal). Use a CTE for buyers and one for customers per city. Best conversion first.",
        sol="""
WITH buyers AS (
  SELECT DISTINCT customer_id FROM orders WHERE status = 'delivered'
),
per_city AS (
  SELECT c.city, COUNT(*) AS customers, COUNT(b.customer_id) AS buyers
  FROM customers AS c LEFT JOIN buyers AS b ON b.customer_id = c.id
  WHERE c.city IS NOT NULL
  GROUP BY c.city
)
SELECT city, customers, buyers, ROUND(100.0 * buyers / customers, 1) AS conversion_pct
FROM per_city
ORDER BY conversion_pct DESC, city;
""",
    ),
    dict(
        title="A lookup table from VALUES",
        concept="`WITH bands(name, lo, hi) AS (VALUES ('cheap', 0, 50000), ...)` creates a tiny inline table — then join on a **range** (`price >= lo AND price < hi`).",
        task="Using a VALUES CTE with bands cheap [0, 500 TL), mid [500, 5000 TL), premium [5000 TL, ∞): units sold per band in delivered orders — `band, units`, ordered cheap → premium.",
        sol="""
WITH bands(band, lo, hi) AS (
  VALUES ('cheap', 0, 50000), ('mid', 50000, 500000), ('premium', 500000, 1e18)
)
SELECT b.band, SUM(oi.quantity) AS units
FROM bands AS b
JOIN products AS p ON p.price_kurus >= b.lo AND p.price_kurus < b.hi
JOIN order_items AS oi ON oi.product_id = p.id
JOIN orders AS o ON o.id = oi.order_id AND o.status = 'delivered'
GROUP BY b.band
ORDER BY MIN(b.lo);
""",
    ),
    dict(
        title="Recursive warm-up: 1 to 10",
        task="Produce one column `n` with the numbers 1..10 using `WITH RECURSIVE`.",
        sol="""
WITH RECURSIVE nums(n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM nums WHERE n < 10
)
SELECT n FROM nums;
""",
    ),
    dict(
        title="A calendar with zero days",
        task="Orders per day for every day of **October 2026** — days without orders show 0. Columns `day, orders`; return only the days with 0 orders.",
        hint="Recursive CTE of dates: `SELECT date(day, '+1 day') ... WHERE day < '2026-10-31'`, LEFT JOIN orders on `date(ordered_at) = day`.",
        sol="""
WITH RECURSIVE days(day) AS (
  SELECT '2026-10-01'
  UNION ALL
  SELECT date(day, '+1 day') FROM days WHERE day < '2026-10-31'
)
SELECT d.day, COUNT(o.id) AS orders
FROM days AS d LEFT JOIN orders AS o ON date(o.ordered_at) = d.day
GROUP BY d.day
HAVING COUNT(o.id) = 0
ORDER BY d.day;
""",
    ),
    dict(
        title="Category paths",
        task="For every category show its full path like `Electronics > Computers > Laptops`: columns `id, path, depth` (top level = 1). Order by path.",
        sol="""
WITH RECURSIVE tree(id, path, depth) AS (
  SELECT id, name, 1 FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, t.path || ' > ' || c.name, t.depth + 1
  FROM categories AS c JOIN tree AS t ON c.parent_id = t.id
)
SELECT id, path, depth FROM tree ORDER BY path;
""",
    ),
    dict(
        title="Revenue of a whole subtree",
        task="Total delivered revenue in TL (`revenue_tl`) of **Electronics including all its descendants** (Computers, Laptops, Accessories, Phones, Audio...).",
        sol="""
WITH RECURSIVE sub(id) AS (
  SELECT id FROM categories WHERE name = 'Electronics'
  UNION ALL
  SELECT c.id FROM categories AS c JOIN sub ON c.parent_id = sub.id
)
SELECT SUM(oi.quantity * oi.unit_price_kurus) / 100.0 AS revenue_tl
FROM order_items AS oi
JOIN orders AS o ON o.id = oi.order_id AND o.status = 'delivered'
JOIN products AS p ON p.id = oi.product_id
WHERE p.category_id IN (SELECT id FROM sub);
""",
    ),
    dict(
        title="Org chart",
        task="Print the org chart: `chart` = name indented by 4 spaces per level (CEO not indented), `level` (CEO = 0). Order so that each person appears directly under their manager (depth-first).",
        hint="Carry a sort key: the path of ids, e.g. `printf('%03d', id)` concatenated per level, then `ORDER BY sort_key`. Indent with `substr('                        ', 1, level * 4)`.",
        sol="""
WITH RECURSIVE org(id, name, level, sort_key) AS (
  SELECT id, first_name || ' ' || last_name || ' (' || title || ')', 0, printf('%03d', id)
  FROM employees WHERE manager_id IS NULL
  UNION ALL
  SELECT e.id, e.first_name || ' ' || e.last_name || ' (' || e.title || ')', org.level + 1,
         org.sort_key || '.' || printf('%03d', e.id)
  FROM employees AS e JOIN org ON e.manager_id = org.id
)
SELECT substr('                        ', 1, level * 4) || name AS chart, level
FROM org ORDER BY sort_key;
""",
    ),
    dict(
        title="Walk up a chain",
        task="Customer 70 was referred by someone, who was referred by someone, ... List the chain from 70 up to the first customer who has no referrer: `step` (70 itself is 0), `id`, `first_name`, `last_name`.",
        sol="""
WITH RECURSIVE chain(step, id) AS (
  SELECT 0, 70
  UNION ALL
  SELECT chain.step + 1, c.referred_by
  FROM chain JOIN customers AS c ON c.id = chain.id
  WHERE c.referred_by IS NOT NULL
)
SELECT chain.step, c.id, c.first_name, c.last_name
FROM chain JOIN customers AS c ON c.id = chain.id
ORDER BY chain.step;
""",
    ),
    dict(
        title="Managers' total team salary",
        task="For each employee who manages anyone: `manager` (first name) and `team_tl` = total yearly salary in TL of **everyone below them** (direct and indirect reports, not themselves). Biggest first.",
        hint="Recursive CTE of (manager_id, employee_id) pairs: start with direct reports, then extend each pair one level down.",
        sol="""
WITH RECURSIVE below(boss, emp) AS (
  SELECT manager_id, id FROM employees WHERE manager_id IS NOT NULL
  UNION ALL
  SELECT below.boss, e.id FROM below JOIN employees AS e ON e.manager_id = below.emp
)
SELECT m.first_name AS manager, SUM(e.salary_kurus) / 100.0 AS team_tl
FROM below
JOIN employees AS m ON m.id = below.boss
JOIN employees AS e ON e.id = below.emp
GROUP BY m.id
ORDER BY team_tl DESC;
""",
    ),
    dict(
        title="CTE in a write statement",
        concept="A CTE can sit in front of INSERT / UPDATE / DELETE too.",
        task="Using a CTE `top_buyers` (the 3 customers with the highest delivered spend), insert one review per top buyer for product 37 (Yoga Mat), rating 5, comment `Thanks for being a top customer`, created_at `2026-11-13`.",
        sol="""
WITH top_buyers AS (
  SELECT o.customer_id
  FROM orders AS o JOIN order_items AS oi ON oi.order_id = o.id
  WHERE o.status = 'delivered'
  GROUP BY o.customer_id
  ORDER BY SUM(oi.quantity * oi.unit_price_kurus) DESC
  LIMIT 3
)
INSERT INTO reviews (product_id, customer_id, rating, comment, created_at)
SELECT 37, customer_id, 5, 'Thanks for being a top customer', '2026-11-13' FROM top_buyers;
""",
        check="SELECT customer_id, rating, comment FROM reviews WHERE created_at = '2026-11-13' ORDER BY customer_id;",
    ),
]
