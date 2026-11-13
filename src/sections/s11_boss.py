SECTION = dict(
    num=11, title="Boss level: window functions, gaps & islands, big data, indexes", db="shop",
    pdf="Beyond Hafta 5 — window functions and indexes (likely coming soon in the course; standard interview material)",
    intro="""
**Window functions** compute over a set of rows *related to the current row* without collapsing
them like GROUP BY does:

```sql
fn(...) OVER (PARTITION BY group_cols ORDER BY sort_cols [ROWS BETWEEN ...])
```
`ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LAG(x)`, `LEAD(x)`, `SUM(x) OVER (...)`,
`FIRST_VALUE(x)`. You can't use them in WHERE — wrap the query in a CTE and filter outside.

The last exercises run on your **scenario.db** (600k students, 1.2M registrations). Read-only
exercises are graded against `../scenario/scenario.db` opened read-only; your playground copy is
`db/scenario.db` (`./drill reset scenario`).
""",
)

EX = [
    dict(
        title="Top 3 per group (ROW_NUMBER)",
        task="For each category (by name), the 3 products with the highest delivered revenue: `category, product, revenue_tl, rn`. Skip uncategorised products. Order by category, rn.",
        sol="""
WITH rev AS (
  SELECT c.name AS category, p.name AS product,
         SUM(oi.quantity * oi.unit_price_kurus) / 100.0 AS revenue_tl
  FROM order_items AS oi
  JOIN orders AS o ON o.id = oi.order_id AND o.status = 'delivered'
  JOIN products AS p ON p.id = oi.product_id
  JOIN categories AS c ON c.id = p.category_id
  GROUP BY p.id
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue_tl DESC) AS rn FROM rev
)
SELECT category, product, revenue_tl, rn FROM ranked WHERE rn <= 3 ORDER BY category, rn;
""",
    ),
    dict(
        title="RANK vs DENSE_RANK vs ROW_NUMBER",
        task="Rank customers by number of orders: `customer_id, n, row_number, rank, dense_rank` (all ordered by n desc; ROW_NUMBER ties broken by customer_id). Show only rows with `dense_rank <= 4`, ordered by row_number.",
        sol="""
WITH c AS (SELECT customer_id, COUNT(*) AS n FROM orders GROUP BY customer_id),
r AS (
  SELECT customer_id, n,
         ROW_NUMBER() OVER (ORDER BY n DESC, customer_id) AS "row_number",
         RANK()       OVER (ORDER BY n DESC) AS "rank",
         DENSE_RANK() OVER (ORDER BY n DESC) AS "dense_rank"
  FROM c
)
SELECT * FROM r WHERE "dense_rank" <= 4 ORDER BY "row_number";
""",
    ),
    dict(
        title="Running total",
        task="Delivered revenue per month of 2026 (`month, revenue_tl`) and the year-to-date running total `ytd_tl`. Chronological.",
        sol="""
WITH m AS (
  SELECT strftime('%Y-%m', o.ordered_at) AS month, SUM(oi.quantity * oi.unit_price_kurus) / 100.0 AS revenue_tl
  FROM orders AS o JOIN order_items AS oi ON oi.order_id = o.id
  WHERE o.status = 'delivered' AND o.ordered_at >= '2026-01-01'
  GROUP BY month
)
SELECT month, revenue_tl, SUM(revenue_tl) OVER (ORDER BY month) AS ytd_tl FROM m ORDER BY month;
""",
    ),
    dict(
        title="Share of total",
        task="Revenue share per payment method across all payments: `method, total_tl, pct` (pct of the grand total, 1 decimal), biggest first. Use `SUM(...) OVER ()`.",
        sol="""
SELECT method, SUM(amount_kurus) / 100.0 AS total_tl,
       ROUND(100.0 * SUM(amount_kurus) / SUM(SUM(amount_kurus)) OVER (), 1) AS pct
FROM payments
GROUP BY method
ORDER BY total_tl DESC;
""",
        after="`SUM(SUM(x)) OVER ()`: the inner SUM is the GROUP BY aggregate, the outer is a window over the grouped rows.",
    ),
    dict(
        title="Time between orders (LAG)",
        task="For customers with at least 10 orders: `customer_id, orders, avg_gap_days` = average number of days between consecutive orders (1 decimal). Shortest gap first.",
        hint="`julianday(ordered_at) - julianday(LAG(ordered_at) OVER (PARTITION BY customer_id ORDER BY ordered_at))`",
        sol="""
WITH g AS (
  SELECT customer_id,
         julianday(ordered_at) - julianday(LAG(ordered_at) OVER (PARTITION BY customer_id ORDER BY ordered_at)) AS gap
  FROM orders
)
SELECT customer_id, COUNT(*) AS orders, ROUND(AVG(gap), 1) AS avg_gap_days
FROM g
GROUP BY customer_id
HAVING COUNT(*) >= 10
ORDER BY avg_gap_days, customer_id;
""",
    ),
    dict(
        title="What do people buy first?",
        task="For each customer take their **first** order (earliest `ordered_at`). Over all those first orders, which products appear most? `product, first_orders`, top 5, ties by name.",
        sol="""
WITH firsts AS (
  SELECT id, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY ordered_at) AS rn FROM orders
)
SELECT p.name AS product, COUNT(*) AS first_orders
FROM firsts AS f
JOIN order_items AS oi ON oi.order_id = f.id
JOIN products AS p ON p.id = oi.product_id
WHERE f.rn = 1
GROUP BY p.id
ORDER BY first_orders DESC, product
LIMIT 5;
""",
    ),
    dict(
        title="Cohorts",
        task="Group customers by the quarter they joined (`cohort` like `2025-Q3`). Per cohort: `customers`, `quick_buyers` = customers whose first order came within 30 days of joining, `pct` (1 decimal). Chronological.",
        hint="Quarter: `strftime('%Y', d) || '-Q' || ((CAST(strftime('%m', d) AS INTEGER) + 2) / 3)`. First order per customer with MIN.",
        sol="""
WITH f AS (SELECT customer_id, MIN(ordered_at) AS first_at FROM orders GROUP BY customer_id),
c AS (
  SELECT c.id,
         strftime('%Y', c.joined_at) || '-Q' || ((CAST(strftime('%m', c.joined_at) AS INTEGER) + 2) / 3) AS cohort,
         CASE WHEN julianday(f.first_at) - julianday(c.joined_at) <= 30 THEN 1 ELSE 0 END AS quick
  FROM customers AS c LEFT JOIN f ON f.customer_id = c.id
)
SELECT cohort, COUNT(*) AS customers, SUM(quick) AS quick_buyers,
       ROUND(100.0 * SUM(quick) / COUNT(*), 1) AS pct
FROM c GROUP BY cohort ORDER BY cohort;
""",
    ),
    dict(
        title="Transfers (transit)",
        db="transit",
        task="A *transfer* is a boarding that happens within 60 minutes of the same card's previous boarding. Top 5 cards by number of transfers: `card_id, owner, transfers` (ties by card_id).",
        sol="""
WITH b AS (
  SELECT card_id, datetime,
         LAG(datetime) OVER (PARTITION BY card_id ORDER BY datetime) AS prev
  FROM swipes WHERE type = 'boarding'
)
SELECT b.card_id, c.owner, COUNT(*) AS transfers
FROM b JOIN cards AS c ON c.id = b.card_id
WHERE prev IS NOT NULL AND (julianday(datetime) - julianday(prev)) * 24 * 60 <= 60
GROUP BY b.card_id
ORDER BY transfers DESC, b.card_id
LIMIT 5;
""",
    ),
    dict(
        title="Gaps and islands: longest riding streak (transit)",
        db="transit",
        concept="Classic trick: for consecutive days, `day - ROW_NUMBER()` is constant. Group by that difference and each group is one unbroken streak (an *island*).",
        task="For each card, its longest run of **consecutive days with at least one boarding**. Top 5: `card_id, streak_days, from_day, to_day` (ties by card_id).",
        hint="1) distinct (card_id, date(datetime)); 2) `julianday(day) - ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY day)` as grp; 3) GROUP BY card_id, grp.",
        sol="""
WITH d AS (SELECT DISTINCT card_id, date(datetime) AS day FROM swipes WHERE type = 'boarding'),
g AS (SELECT card_id, day, julianday(day) - ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY day) AS grp FROM d),
s AS (SELECT card_id, COUNT(*) AS streak_days, MIN(day) AS from_day, MAX(day) AS to_day FROM g GROUP BY card_id, grp),
best AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY streak_days DESC, from_day) AS rn FROM s)
SELECT card_id, streak_days, from_day, to_day FROM best WHERE rn = 1
ORDER BY streak_days DESC, card_id
LIMIT 5;
""",
    ),
    dict(
        title="Busiest station per district (transit)",
        db="transit",
        task="For each district, the station with the most boardings: `district, station, boardings`. By district.",
        sol="""
WITH c AS (
  SELECT st.district, st.name AS station, COUNT(*) AS boardings,
         RANK() OVER (PARTITION BY st.district ORDER BY COUNT(*) DESC) AS r
  FROM swipes AS s JOIN stations AS st ON st.id = s.station_id
  WHERE s.type = 'boarding'
  GROUP BY st.id
)
SELECT district, station, boardings FROM c WHERE r = 1 ORDER BY district;
""",
    ),
    dict(
        title="Six-table join at scale (scenario)",
        db="scenario",
        task="Top 5 countries by number of students: `country, students`. Path: students → department → university → city → state → country.",
        sol="""
SELECT co.name AS country, COUNT(*) AS students
FROM students AS s
JOIN department AS d ON d.id = s.department_id
JOIN university AS u ON u.id = d.uni_id
JOIN city AS c ON c.id = u.city_id
JOIN state AS st ON st.id = c.state_id
JOIN country AS co ON co.id = st.country_id
GROUP BY co.id
ORDER BY students DESC
LIMIT 5;
""",
    ),
    dict(
        title="Overbooked events (scenario)",
        db="scenario",
        task="How many events have more registrations than `capacity`? Return `overbooked`. **Don't** use a correlated subquery per event (try it with LIMIT and see why) — aggregate `register` once, then join.",
        sol="""
SELECT COUNT(*) AS overbooked
FROM event AS e
JOIN (SELECT event_id, COUNT(*) AS n FROM register GROUP BY event_id) AS r ON r.event_id = e.id
WHERE r.n > e.capacity;
""",
    ),
    dict(
        title="Data integrity audit (scenario)",
        db="scenario",
        task="One row with three counts: `richer_than_manager` (teachers paid more than their own department's manager), `manager_elsewhere` (departments whose manager belongs to a different department), `closed_clubs_with_members` (closed clubs that still have member rows).",
        sol="""
SELECT
 (SELECT COUNT(*) FROM teacher AS t
    JOIN department AS d ON d.id = t.department_id
    JOIN teacher AS m ON m.id = d.manager_id
  WHERE t.paycheck > m.paycheck) AS richer_than_manager,
 (SELECT COUNT(*) FROM department AS d JOIN teacher AS m ON m.id = d.manager_id
  WHERE m.department_id IS NOT d.id) AS manager_elsewhere,
 (SELECT COUNT(*) FROM club WHERE closed = 1 AND id IN (SELECT club_id FROM members)) AS closed_clubs_with_members;
""",
    ),
    dict(
        title="Students per year, pivoted (scenario)",
        db="scenario",
        task="For the 5 universities with the most students: `university` (name + ' #' + id, since names repeat), `total`, and counts for `y1`..`y6` (study year) as columns. Biggest first.",
        sol="""
SELECT u.name || ' #' || u.id AS university, COUNT(*) AS total,
       SUM(s.year = 1) AS y1, SUM(s.year = 2) AS y2, SUM(s.year = 3) AS y3,
       SUM(s.year = 4) AS y4, SUM(s.year = 5) AS y5, SUM(s.year = 6) AS y6
FROM students AS s
JOIN department AS d ON d.id = s.department_id
JOIN university AS u ON u.id = d.uni_id
GROUP BY u.id
ORDER BY total DESC, u.id
LIMIT 5;
""",
        after="`SUM(s.year = 1)` works because a comparison is 1 or 0 in SQLite — a shortcut for `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`.",
    ),
    dict(
        title="Why was it slow? EXPLAIN QUERY PLAN (scenario)",
        db="scenario", nocheck=True,
        concept="`EXPLAIN QUERY PLAN <query>` shows how SQLite will run it. `SCAN t` = read every row; `SEARCH t USING INDEX ...` = jump straight to the matches. `register`'s primary key is `(student_id, event_id)`, which helps lookups by student, **not** by event.",
        task="Show the plan for `SELECT COUNT(*) FROM register WHERE event_id = 123;` and for `... WHERE student_id = 123;`. Return the second one's plan.",
        sol="EXPLAIN QUERY PLAN SELECT COUNT(*) FROM register WHERE student_id = 123;",
        after="The `event_id` version says `SCAN register` — 1.2M rows per lookup. Inside a correlated subquery that's 60 000 × 1.2M row reads.",
    ),
    dict(
        title="Add an index (scenario)",
        db="scenario",
        task="On your scenario copy, create an index `register_event` on `register(event_id)`. Then the plan for `WHERE event_id = 123` changes. (Bonus: rerun the correlated version of 11.12 and time it with `.timer on`.)",
        sol="CREATE INDEX register_event ON register(event_id);",
        check="EXPLAIN QUERY PLAN SELECT COUNT(*) FROM register WHERE event_id = 123;",
        after="Indexes speed up reads but cost disk space and slow down every INSERT/UPDATE/DELETE on that table. Check the file size before/after.",
    ),
]
