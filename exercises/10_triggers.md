# 10 — Triggers (AFTER, BEFORE + RAISE, audit logs, soft delete, INSTEAD OF)

**Database:** `transit` · **Course link:** Hafta 4 (tetikleyici, OLD/NEW, yumuşak silme) + Hafta 5 (INSTEAD OF tetikleyicisi ile görünüme yazmak)

```sql
CREATE TRIGGER name
{BEFORE | AFTER | INSTEAD OF} {INSERT | DELETE | UPDATE [OF col, ...]} ON table_or_view
FOR EACH ROW
[WHEN condition]
BEGIN
    statement; statement; ...
END;
```
`NEW.col` = the row being inserted / the row after an update. `OLD.col` = the row being
deleted / the row before an update. `SELECT RAISE(ABORT, 'msg')` cancels the statement with an
error; `SELECT RAISE(IGNORE)` silently skips the current row.

10.01–10.10 run on `transit` (`./drill reset transit` first), 10.11–10.14 on `shop`
(`./drill reset shop`). Triggers stack up exercise after exercise, just like in a real system.
List them with `SELECT name FROM sqlite_schema WHERE type = 'trigger';`.

### 10.01 — Keep the balance in sync (AFTER INSERT)

_✏️ changes the DB — `./drill catchup 10.01` first if your DB is out of sync_

**Task:** Write trigger `swipe_insert`: whenever a row is inserted into `swipes`, add its `amount_kurus` to that card's `balance_kurus`.

**After your script, this check:**

```sql
SELECT balance_kurus AS before FROM cards WHERE id = 5;
INSERT INTO swipes (card_id, station_id, type, datetime, amount_kurus) VALUES
  (5, NULL, 'topup', '2026-11-01 08:00:00', 5000),
  (5, 1, 'boarding', '2026-11-01 08:10:00', -1500);
SELECT balance_kurus AS after FROM cards WHERE id = 5;
```

should print:

```text
┌────────┐
│ before │
├────────┤
│   7500 │
└────────┘

┌───────┐
│ after │
├───────┤
│ 11000 │
└───────┘
```

> One INSERT with two rows fired the trigger twice — `FOR EACH ROW`.


### 10.02 — Undo on delete (AFTER DELETE)

_✏️ changes the DB — `./drill catchup 10.02` first if your DB is out of sync_

**Task:** Write trigger `swipe_delete`: when a swipe is deleted, reverse its effect on the card's balance.

<details><summary>Hint</summary>

Only `OLD` exists in a DELETE trigger.
</details>

**After your script, this check:**

```sql
SELECT balance_kurus AS before FROM cards WHERE id = 8;
DELETE FROM swipes WHERE card_id = 8 AND type = 'boarding' AND datetime >= '2026-10-30';
SELECT balance_kurus AS after FROM cards WHERE id = 8;
```

should print:

```text
┌────────┐
│ before │
├────────┤
│  10000 │
└────────┘

┌───────┐
│ after │
├───────┤
│ 14000 │
└───────┘
```


### 10.03 — Fix on update (AFTER UPDATE OF)

_✏️ changes the DB — `./drill catchup 10.03` first if your DB is out of sync_

**Task:** Write trigger `swipe_update`: when `amount_kurus` of a swipe changes, adjust the card's balance by the difference.

<details><summary>Hint</summary>

`balance_kurus - OLD.amount_kurus + NEW.amount_kurus`. (Bonus thought: what if someone changes `card_id`?)
</details>

**After your script, this check:**

```sql
SELECT balance_kurus AS before FROM cards WHERE id = 1;
UPDATE swipes SET amount_kurus = -2500
WHERE card_id = 1 AND type = 'boarding' AND datetime >= '2026-10-28';
SELECT balance_kurus AS after FROM cards WHERE id = 1;
SELECT COUNT(*) AS wrong_balances FROM cards AS c
WHERE balance_kurus <> (SELECT COALESCE(SUM(amount_kurus), 0) FROM swipes WHERE card_id = c.id);
```

should print:

```text
┌────────┐
│ before │
├────────┤
│  18000 │
└────────┘

┌───────┐
│ after │
├───────┤
│ 13500 │
└───────┘

┌────────────────┐
│ wrong_balances │
├────────────────┤
│              0 │
└────────────────┘
```


### 10.04 — Refuse a boarding without money (BEFORE INSERT + RAISE)

_✏️ changes the DB — `./drill catchup 10.04` first if your DB is out of sync_

**Concept:** A BEFORE trigger runs before the row is written; `RAISE(ABORT, '...')` cancels the whole statement, so nothing is written and the AFTER trigger never fires.

**Task:** Write trigger `no_negative_balance`: refuse (ABORT with the message `insufficient balance`) any **boarding** that would make the card's balance negative.

<details><summary>Hint</summary>

`BEFORE INSERT ON swipes FOR EACH ROW WHEN NEW.type = 'boarding' AND (SELECT balance_kurus FROM cards WHERE id = NEW.card_id) + NEW.amount_kurus < 0 BEGIN SELECT RAISE(ABORT, 'insufficient balance'); END;`
</details>

**After your script, this check:**

```sql
SELECT balance_kurus AS before FROM cards WHERE id = 9;
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (9, 1, 'boarding', -1000);
SELECT balance_kurus AS still FROM cards WHERE id = 9;
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (9, NULL, 'topup', 1000);
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (9, 1, 'boarding', -1000);
SELECT balance_kurus AS after FROM cards WHERE id = 9;
```

should print:

```text
┌────────┐
│ before │
├────────┤
│      0 │
└────────┘

Error: insufficient balance

┌───────┐
│ still │
├───────┤
│     0 │
└───────┘

┌───────┐
│ after │
├───────┤
│     0 │
└───────┘
```


### 10.05 — No boarding at a closed station

_✏️ changes the DB — `./drill catchup 10.05` first if your DB is out of sync_

**Task:** Write trigger `no_closed_station`: ABORT with `station is closed` when someone boards at a station whose `closed = 1`.

**After your script, this check:**

```sql
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (1, (SELECT id FROM stations WHERE name = 'Sanayi'), 'boarding', -2000);
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (1, (SELECT id FROM stations WHERE name = 'Gar'), 'boarding', -2000);
SELECT COUNT(*) AS boardings_today FROM swipes WHERE card_id = 1 AND datetime >= '2026-11-01';
```

should print:

```text
Error: station is closed

┌─────────────────┐
│ boardings_today │
├─────────────────┤
│               1 │
└─────────────────┘
```


### 10.06 — Audit log (a trigger fired by a trigger)

_✏️ changes the DB — `./drill catchup 10.06` first if your DB is out of sync_

**Task:** Create `balance_log(id INTEGER PRIMARY KEY, card_id INTEGER NOT NULL, old_kurus INTEGER, new_kurus INTEGER, logged_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`
and trigger `log_balance`: every time a card's `balance_kurus` actually **changes**, write a row.

<details><summary>Hint</summary>

`AFTER UPDATE OF balance_kurus ON cards ... WHEN OLD.balance_kurus <> NEW.balance_kurus`
</details>

**After your script, this check:**

```sql
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (2, NULL, 'topup', 2000);
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (2, 1, 'boarding', -500);
UPDATE cards SET balance_kurus = balance_kurus WHERE id = 2;
SELECT card_id, old_kurus, new_kurus FROM balance_log ORDER BY id;
```

should print:

```text
┌─────────┬───────────┬───────────┐
│ card_id │ old_kurus │ new_kurus │
├─────────┼───────────┼───────────┤
│       2 │     19000 │     21000 │
│       2 │     21000 │     20500 │
└─────────┴───────────┴───────────┘
```

> The INSERT on swipes fired `swipe_insert`, whose UPDATE on cards fired `log_balance`. The no-op UPDATE logged nothing thanks to WHEN.


### 10.07 — Soft delete with BEFORE DELETE + RAISE(IGNORE)

_✏️ changes the DB — `./drill catchup 10.07` first if your DB is out of sync_

**Concept:** `RAISE(IGNORE)` inside a BEFORE trigger skips the current row: the DELETE 'succeeds' but the row stays. Combined with an UPDATE, every DELETE becomes a soft delete.

**Task:** Write trigger `stations_soft_delete`: `DELETE FROM stations ...` should set `closed = 1` instead of removing the row.

**After your script, this check:**

```sql
DELETE FROM stations WHERE district = 'Canik';
SELECT COUNT(*) AS stations, SUM(closed) AS closed FROM stations;
SELECT name, closed FROM stations WHERE district = 'Canik' ORDER BY name;
```

should print:

```text
┌──────────┬────────┐
│ stations │ closed │
├──────────┼────────┤
│       18 │      4 │
└──────────┴────────┘

┌──────────────┬────────┐
│     name     │ closed │
├──────────────┼────────┤
│ Canik Merkez │      1 │
│ Kalkanca     │      1 │
│ Stadyum      │      1 │
└──────────────┴────────┘
```


### 10.08 — INSTEAD OF DELETE on a view

_✏️ changes the DB — `./drill catchup 10.08` first if your DB is out of sync_

**Concept:** Views can't be written to (08.07) — unless you define an `INSTEAD OF` trigger that says what the write *means*.

**Task:** Create view `active_stations` (`id, name, district, line` of stations with `closed = 0`) and an INSTEAD OF DELETE trigger `active_stations_delete` that closes the station instead.

**After your script, this check:**

```sql
SELECT COUNT(*) AS active_before FROM active_stations;
DELETE FROM active_stations WHERE name IN ('Hastane', 'Pazar');
SELECT COUNT(*) AS active_after FROM active_stations;
SELECT COUNT(*) AS rows_in_table FROM stations;
```

should print:

```text
┌───────────────┐
│ active_before │
├───────────────┤
│            17 │
└───────────────┘

┌──────────────┐
│ active_after │
├──────────────┤
│           15 │
└──────────────┘

┌───────────────┐
│ rows_in_table │
├───────────────┤
│            18 │
└───────────────┘
```


### 10.09 — INSTEAD OF INSERT: a friendly API view

_✏️ changes the DB — `./drill catchup 10.09` first if your DB is out of sync_

**Task:** Create view `boardings(card_id, station_name)` (one row per boarding swipe: card id + station name)
and an INSTEAD OF INSERT trigger so that `INSERT INTO boardings VALUES (4, 'Gar');` records a boarding at that station
with the **correct fare for the card's type** (from `fares`). If the station name doesn't exist, ABORT with `unknown station`.

<details><summary>Hint</summary>

Inside the trigger: `INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (NEW.card_id, (SELECT id FROM stations WHERE name = NEW.station_name), 'boarding', -(SELECT f.fare_kurus FROM cards AS c JOIN fares AS f ON f.card_type = c.card_type WHERE c.id = NEW.card_id));` — the existing swipes triggers still run.
</details>

**After your script, this check:**

```sql
SELECT card_type, balance_kurus AS before FROM cards WHERE id = 4;
INSERT INTO boardings VALUES (4, 'Gar');
INSERT INTO boardings VALUES (4, 'Atlantis');
SELECT balance_kurus AS after FROM cards WHERE id = 4;
SELECT type, amount_kurus FROM swipes WHERE id = (SELECT MAX(id) FROM swipes);
```

should print:

```text
┌───────────┬────────┐
│ card_type │ before │
├───────────┼────────┤
│ student   │  10000 │
└───────────┴────────┘

Error: unknown station

┌───────┐
│ after │
├───────┤
│  9000 │
└───────┘

┌──────────┬──────────────┐
│   type   │ amount_kurus │
├──────────┼──────────────┤
│ boarding │        -1000 │
└──────────┴──────────────┘
```


### 10.10 — INSTEAD OF UPDATE

_✏️ changes the DB — `./drill catchup 10.10` first if your DB is out of sync_

**Task:** Create view `card_overview(id, owner, card_type, balance_tl)` (`balance_tl` = balance / 100.0) and an INSTEAD OF UPDATE trigger that lets people change **owner** and **card_type** through the view (balance must not be editable — just ignore it).

**After your script, this check:**

```sql
UPDATE card_overview SET owner = 'Hakki T.', card_type = 'student' WHERE id = 31;
UPDATE card_overview SET balance_tl = 1000000 WHERE id = 31;
SELECT * FROM card_overview WHERE id = 31;
```

should print:

```text
┌────┬──────────┬───────────┬────────────┐
│ id │  owner   │ card_type │ balance_tl │
├────┼──────────┼───────────┼────────────┤
│ 31 │ Hakki T. │ student   │          0 │
└────┴──────────┴───────────┴────────────┘
```


### 10.11 — Stock control (shop)

_db: `shop` · ✏️ changes the DB — `./drill catchup 10.11` first if your DB is out of sync_

**Task:** On `shop`: trigger `reserve_stock` — inserting an order line reduces the product's `stock` by the quantity.
Plus trigger `check_stock`, which ABORTs with `out of stock` **before** the insert if there isn't enough stock.

<details><summary>Hint</summary>

Without `check_stock` the `CHECK (stock >= 0)` on products would also stop it — but with a vaguer error. Try both.
</details>

**After your script, this check:**

```sql
INSERT INTO orders (id, customer_id, ordered_at, status, ship_city) VALUES (1001, 1, '2026-11-13 10:00:00', 'pending', 'Izmir');
SELECT stock AS before FROM products WHERE id = 2;
INSERT INTO order_items VALUES (1001, 2, 2, 3199900);
INSERT INTO order_items VALUES (1001, 2, 1, 3199900);
SELECT stock AS after FROM products WHERE id = 2;
```

should print:

```text
┌────────┐
│ before │
├────────┤
│      1 │
└────────┘

Error: out of stock

┌───────┐
│ after │
├───────┤
│     0 │
└───────┘
```


### 10.12 — Price history with WHEN

_db: `shop` · ✏️ changes the DB — `./drill catchup 10.12` first if your DB is out of sync_

**Task:** Create `price_history(id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id), old_kurus INTEGER NOT NULL, new_kurus INTEGER NOT NULL, changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)` and trigger `track_price` that records **real** price changes only.

**After your script, this check:**

```sql
UPDATE products SET price_kurus = price_kurus + 1000 WHERE category_id = 16;
UPDATE products SET price_kurus = price_kurus WHERE category_id = 13;
SELECT product_id, old_kurus, new_kurus FROM price_history ORDER BY product_id;
```

should print:

```text
┌────────────┬───────────┬───────────┐
│ product_id │ old_kurus │ new_kurus │
├────────────┼───────────┼───────────┤
│         37 │     39900 │     40900 │
│         38 │    189900 │    190900 │
│         39 │     14900 │     15900 │
└────────────┴───────────┴───────────┘
```


### 10.13 — Cancel through a view

_db: `shop` · ✏️ changes the DB — `./drill catchup 10.13` first if your DB is out of sync_

**Task:** Create view `open_orders` (all columns of orders with status `pending`) and an INSTEAD OF DELETE trigger: deleting from the view sets the order's status to `cancelled` and **puts the stock back** for its lines.

<details><summary>Hint</summary>

Two statements in the trigger body: `UPDATE products SET stock = stock + (SELECT quantity FROM order_items WHERE order_id = OLD.id AND product_id = products.id) WHERE id IN (SELECT product_id FROM order_items WHERE order_id = OLD.id);` then the status UPDATE.
</details>

**After your script, this check:**

```sql
SELECT COUNT(*) AS open_before FROM open_orders;
CREATE TEMP TABLE probe AS
SELECT oi.product_id, oi.quantity, p.stock AS stock_before
FROM order_items AS oi JOIN products AS p ON p.id = oi.product_id
WHERE oi.order_id = (SELECT MIN(id) FROM open_orders);
DELETE FROM open_orders WHERE id = (SELECT MIN(id) FROM open_orders);
SELECT pr.product_id, pr.quantity, pr.stock_before, p.stock AS stock_after
FROM probe AS pr JOIN products AS p ON p.id = pr.product_id ORDER BY pr.product_id;
SELECT COUNT(*) AS open_after, (SELECT COUNT(*) FROM orders) AS orders_rows FROM open_orders;
```

should print:

```text
┌─────────────┐
│ open_before │
├─────────────┤
│          13 │
└─────────────┘

┌────────────┬──────────┬──────────────┬─────────────┐
│ product_id │ quantity │ stock_before │ stock_after │
├────────────┼──────────┼──────────────┼─────────────┤
│          5 │        5 │           27 │          32 │
│         19 │        2 │          102 │         104 │
│         35 │        2 │            0 │           2 │
└────────────┴──────────┴──────────────┴─────────────┘

┌────────────┬─────────────┐
│ open_after │ orders_rows │
├────────────┼─────────────┤
│         12 │         420 │
└────────────┴─────────────┘
```


### 10.14 — Inventory of triggers

_db: `shop`_

**Task:** List every trigger in the shop DB: `name, on_object` (the table/view it is attached to), alphabetically. Then remember: `DROP TRIGGER name;` removes one.

**Expected result:**

```text
┌────────────────────┬─────────────┐
│        name        │  on_object  │
├────────────────────┼─────────────┤
│ check_stock        │ order_items │
│ open_orders_delete │ open_orders │
│ reserve_stock      │ order_items │
│ track_price        │ products    │
└────────────────────┴─────────────┘
```

