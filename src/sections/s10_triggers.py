SECTION = dict(
    num=10, title="Triggers (AFTER, BEFORE + RAISE, audit logs, soft delete, INSTEAD OF)", db="transit",
    pdf="Hafta 4 (tetikleyici, OLD/NEW, yumuşak silme) + Hafta 5 (INSTEAD OF tetikleyicisi ile görünüme yazmak)",
    intro="""
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
""",
)

EX = [
    dict(
        title="Keep the balance in sync (AFTER INSERT)",
        task="Write trigger `swipe_insert`: whenever a row is inserted into `swipes`, add its `amount_kurus` to that card's `balance_kurus`.",
        sol="""
CREATE TRIGGER swipe_insert
AFTER INSERT ON swipes
FOR EACH ROW
BEGIN
    UPDATE cards SET balance_kurus = balance_kurus + NEW.amount_kurus WHERE id = NEW.card_id;
END;
""",
        check="""
SELECT balance_kurus AS before FROM cards WHERE id = 5;
INSERT INTO swipes (card_id, station_id, type, datetime, amount_kurus) VALUES
  (5, NULL, 'topup', '2026-11-01 08:00:00', 5000),
  (5, 1, 'boarding', '2026-11-01 08:10:00', -1500);
SELECT balance_kurus AS after FROM cards WHERE id = 5;
""",
        after="One INSERT with two rows fired the trigger twice — `FOR EACH ROW`.",
    ),
    dict(
        title="Undo on delete (AFTER DELETE)",
        task="Write trigger `swipe_delete`: when a swipe is deleted, reverse its effect on the card's balance.",
        hint="Only `OLD` exists in a DELETE trigger.",
        sol="""
CREATE TRIGGER swipe_delete
AFTER DELETE ON swipes
FOR EACH ROW
BEGIN
    UPDATE cards SET balance_kurus = balance_kurus - OLD.amount_kurus WHERE id = OLD.card_id;
END;
""",
        check="""
SELECT balance_kurus AS before FROM cards WHERE id = 8;
DELETE FROM swipes WHERE card_id = 8 AND type = 'boarding' AND datetime >= '2026-10-30';
SELECT balance_kurus AS after FROM cards WHERE id = 8;
""",
    ),
    dict(
        title="Fix on update (AFTER UPDATE OF)",
        task="Write trigger `swipe_update`: when `amount_kurus` of a swipe changes, adjust the card's balance by the difference.",
        hint="`balance_kurus - OLD.amount_kurus + NEW.amount_kurus`. (Bonus thought: what if someone changes `card_id`?)",
        sol="""
CREATE TRIGGER swipe_update
AFTER UPDATE OF amount_kurus ON swipes
FOR EACH ROW
BEGIN
    UPDATE cards SET balance_kurus = balance_kurus - OLD.amount_kurus + NEW.amount_kurus
    WHERE id = NEW.card_id;
END;
""",
        check="""
SELECT balance_kurus AS before FROM cards WHERE id = 1;
UPDATE swipes SET amount_kurus = -2500
WHERE card_id = 1 AND type = 'boarding' AND datetime >= '2026-10-28';
SELECT balance_kurus AS after FROM cards WHERE id = 1;
SELECT COUNT(*) AS wrong_balances FROM cards AS c
WHERE balance_kurus <> (SELECT COALESCE(SUM(amount_kurus), 0) FROM swipes WHERE card_id = c.id);
""",
    ),
    dict(
        title="Refuse a boarding without money (BEFORE INSERT + RAISE)",
        concept="A BEFORE trigger runs before the row is written; `RAISE(ABORT, '...')` cancels the whole statement, so nothing is written and the AFTER trigger never fires.",
        task="Write trigger `no_negative_balance`: refuse (ABORT with the message `insufficient balance`) any **boarding** that would make the card's balance negative.",
        hint="`BEFORE INSERT ON swipes FOR EACH ROW WHEN NEW.type = 'boarding' AND (SELECT balance_kurus FROM cards WHERE id = NEW.card_id) + NEW.amount_kurus < 0 BEGIN SELECT RAISE(ABORT, 'insufficient balance'); END;`",
        sol="""
CREATE TRIGGER no_negative_balance
BEFORE INSERT ON swipes
FOR EACH ROW
WHEN NEW.type = 'boarding'
 AND (SELECT balance_kurus FROM cards WHERE id = NEW.card_id) + NEW.amount_kurus < 0
BEGIN
    SELECT RAISE(ABORT, 'insufficient balance');
END;
""",
        check="""
SELECT balance_kurus AS before FROM cards WHERE id = 9;
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (9, 1, 'boarding', -1000);
SELECT balance_kurus AS still FROM cards WHERE id = 9;
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (9, NULL, 'topup', 1000);
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (9, 1, 'boarding', -1000);
SELECT balance_kurus AS after FROM cards WHERE id = 9;
""",
    ),
    dict(
        title="No boarding at a closed station",
        task="Write trigger `no_closed_station`: ABORT with `station is closed` when someone boards at a station whose `closed = 1`.",
        sol="""
CREATE TRIGGER no_closed_station
BEFORE INSERT ON swipes
FOR EACH ROW
WHEN NEW.type = 'boarding' AND (SELECT closed FROM stations WHERE id = NEW.station_id) = 1
BEGIN
    SELECT RAISE(ABORT, 'station is closed');
END;
""",
        check="""
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (1, (SELECT id FROM stations WHERE name = 'Sanayi'), 'boarding', -2000);
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (1, (SELECT id FROM stations WHERE name = 'Gar'), 'boarding', -2000);
SELECT COUNT(*) AS boardings_today FROM swipes WHERE card_id = 1 AND datetime >= '2026-11-01';
""",
    ),
    dict(
        title="Audit log (a trigger fired by a trigger)",
        task="""Create `balance_log(id INTEGER PRIMARY KEY, card_id INTEGER NOT NULL, old_kurus INTEGER, new_kurus INTEGER, logged_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`
and trigger `log_balance`: every time a card's `balance_kurus` actually **changes**, write a row.""",
        hint="`AFTER UPDATE OF balance_kurus ON cards ... WHEN OLD.balance_kurus <> NEW.balance_kurus`",
        sol="""
CREATE TABLE balance_log (
    id        INTEGER PRIMARY KEY,
    card_id   INTEGER NOT NULL,
    old_kurus INTEGER,
    new_kurus INTEGER,
    logged_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TRIGGER log_balance
AFTER UPDATE OF balance_kurus ON cards
FOR EACH ROW
WHEN OLD.balance_kurus <> NEW.balance_kurus
BEGIN
    INSERT INTO balance_log (card_id, old_kurus, new_kurus) VALUES (NEW.id, OLD.balance_kurus, NEW.balance_kurus);
END;
""",
        check="""
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (2, NULL, 'topup', 2000);
INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (2, 1, 'boarding', -500);
UPDATE cards SET balance_kurus = balance_kurus WHERE id = 2;
SELECT card_id, old_kurus, new_kurus FROM balance_log ORDER BY id;
""",
        after="The INSERT on swipes fired `swipe_insert`, whose UPDATE on cards fired `log_balance`. The no-op UPDATE logged nothing thanks to WHEN.",
    ),
    dict(
        title="Soft delete with BEFORE DELETE + RAISE(IGNORE)",
        concept="`RAISE(IGNORE)` inside a BEFORE trigger skips the current row: the DELETE 'succeeds' but the row stays. Combined with an UPDATE, every DELETE becomes a soft delete.",
        task="Write trigger `stations_soft_delete`: `DELETE FROM stations ...` should set `closed = 1` instead of removing the row.",
        sol="""
CREATE TRIGGER stations_soft_delete
BEFORE DELETE ON stations
FOR EACH ROW
BEGIN
    UPDATE stations SET closed = 1 WHERE id = OLD.id;
    SELECT RAISE(IGNORE);
END;
""",
        check="""
DELETE FROM stations WHERE district = 'Canik';
SELECT COUNT(*) AS stations, SUM(closed) AS closed FROM stations;
SELECT name, closed FROM stations WHERE district = 'Canik' ORDER BY name;
""",
    ),
    dict(
        title="INSTEAD OF DELETE on a view",
        concept="Views can't be written to (08.07) — unless you define an `INSTEAD OF` trigger that says what the write *means*.",
        task="Create view `active_stations` (`id, name, district, line` of stations with `closed = 0`) and an INSTEAD OF DELETE trigger `active_stations_delete` that closes the station instead.",
        sol="""
CREATE VIEW active_stations AS
SELECT id, name, district, line FROM stations WHERE closed = 0;
CREATE TRIGGER active_stations_delete
INSTEAD OF DELETE ON active_stations
FOR EACH ROW
BEGIN
    UPDATE stations SET closed = 1 WHERE id = OLD.id;
END;
""",
        check="""
SELECT COUNT(*) AS active_before FROM active_stations;
DELETE FROM active_stations WHERE name IN ('Hastane', 'Pazar');
SELECT COUNT(*) AS active_after FROM active_stations;
SELECT COUNT(*) AS rows_in_table FROM stations;
""",
    ),
    dict(
        title="INSTEAD OF INSERT: a friendly API view",
        task="""Create view `boardings(card_id, station_name)` (one row per boarding swipe: card id + station name)
and an INSTEAD OF INSERT trigger so that `INSERT INTO boardings VALUES (4, 'Gar');` records a boarding at that station
with the **correct fare for the card's type** (from `fares`). If the station name doesn't exist, ABORT with `unknown station`.""",
        hint="Inside the trigger: `INSERT INTO swipes (card_id, station_id, type, amount_kurus) VALUES (NEW.card_id, (SELECT id FROM stations WHERE name = NEW.station_name), 'boarding', -(SELECT f.fare_kurus FROM cards AS c JOIN fares AS f ON f.card_type = c.card_type WHERE c.id = NEW.card_id));` — the existing swipes triggers still run.",
        sol="""
CREATE VIEW boardings AS
SELECT s.card_id, st.name AS station_name
FROM swipes AS s JOIN stations AS st ON st.id = s.station_id
WHERE s.type = 'boarding';
CREATE TRIGGER boardings_insert
INSTEAD OF INSERT ON boardings
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'unknown station')
    WHERE NOT EXISTS (SELECT 1 FROM stations WHERE name = NEW.station_name);
    INSERT INTO swipes (card_id, station_id, type, amount_kurus)
    VALUES (NEW.card_id,
            (SELECT id FROM stations WHERE name = NEW.station_name),
            'boarding',
            -(SELECT f.fare_kurus FROM cards AS c JOIN fares AS f ON f.card_type = c.card_type
              WHERE c.id = NEW.card_id));
END;
""",
        check="""
SELECT card_type, balance_kurus AS before FROM cards WHERE id = 4;
INSERT INTO boardings VALUES (4, 'Gar');
INSERT INTO boardings VALUES (4, 'Atlantis');
SELECT balance_kurus AS after FROM cards WHERE id = 4;
SELECT type, amount_kurus FROM swipes WHERE id = (SELECT MAX(id) FROM swipes);
""",
    ),
    dict(
        title="INSTEAD OF UPDATE",
        task="Create view `card_overview(id, owner, card_type, balance_tl)` (`balance_tl` = balance / 100.0) and an INSTEAD OF UPDATE trigger that lets people change **owner** and **card_type** through the view (balance must not be editable — just ignore it).",
        sol="""
CREATE VIEW card_overview AS
SELECT id, owner, card_type, balance_kurus / 100.0 AS balance_tl FROM cards;
CREATE TRIGGER card_overview_update
INSTEAD OF UPDATE ON card_overview
FOR EACH ROW
BEGIN
    UPDATE cards SET owner = NEW.owner, card_type = NEW.card_type WHERE id = OLD.id;
END;
""",
        check="""
UPDATE card_overview SET owner = 'Hakki T.', card_type = 'student' WHERE id = 31;
UPDATE card_overview SET balance_tl = 1000000 WHERE id = 31;
SELECT * FROM card_overview WHERE id = 31;
""",
    ),
    dict(
        title="Stock control (shop)",
        db="shop",
        task="""On `shop`: trigger `reserve_stock` — inserting an order line reduces the product's `stock` by the quantity.
Plus trigger `check_stock`, which ABORTs with `out of stock` **before** the insert if there isn't enough stock.""",
        hint="Without `check_stock` the `CHECK (stock >= 0)` on products would also stop it — but with a vaguer error. Try both.",
        sol="""
CREATE TRIGGER check_stock
BEFORE INSERT ON order_items
FOR EACH ROW
WHEN (SELECT stock FROM products WHERE id = NEW.product_id) < NEW.quantity
BEGIN
    SELECT RAISE(ABORT, 'out of stock');
END;
CREATE TRIGGER reserve_stock
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE products SET stock = stock - NEW.quantity WHERE id = NEW.product_id;
END;
""",
        check="""
INSERT INTO orders (id, customer_id, ordered_at, status, ship_city) VALUES (1001, 1, '2026-11-13 10:00:00', 'pending', 'Izmir');
SELECT stock AS before FROM products WHERE id = 2;
INSERT INTO order_items VALUES (1001, 2, 2, 3199900);
INSERT INTO order_items VALUES (1001, 2, 1, 3199900);
SELECT stock AS after FROM products WHERE id = 2;
""",
    ),
    dict(
        title="Price history with WHEN",
        db="shop",
        task="Create `price_history(id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id), old_kurus INTEGER NOT NULL, new_kurus INTEGER NOT NULL, changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)` and trigger `track_price` that records **real** price changes only.",
        sol="""
CREATE TABLE price_history (
    id         INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    old_kurus  INTEGER NOT NULL,
    new_kurus  INTEGER NOT NULL,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TRIGGER track_price
AFTER UPDATE OF price_kurus ON products
FOR EACH ROW
WHEN NEW.price_kurus <> OLD.price_kurus
BEGIN
    INSERT INTO price_history (product_id, old_kurus, new_kurus) VALUES (NEW.id, OLD.price_kurus, NEW.price_kurus);
END;
""",
        check="""
UPDATE products SET price_kurus = price_kurus + 1000 WHERE category_id = 16;
UPDATE products SET price_kurus = price_kurus WHERE category_id = 13;
SELECT product_id, old_kurus, new_kurus FROM price_history ORDER BY product_id;
""",
    ),
    dict(
        title="Cancel through a view",
        db="shop",
        task="Create view `open_orders` (all columns of orders with status `pending`) and an INSTEAD OF DELETE trigger: deleting from the view sets the order's status to `cancelled` and **puts the stock back** for its lines.",
        hint="Two statements in the trigger body: `UPDATE products SET stock = stock + (SELECT quantity FROM order_items WHERE order_id = OLD.id AND product_id = products.id) WHERE id IN (SELECT product_id FROM order_items WHERE order_id = OLD.id);` then the status UPDATE.",
        sol="""
CREATE VIEW open_orders AS SELECT * FROM orders WHERE status = 'pending';
CREATE TRIGGER open_orders_delete
INSTEAD OF DELETE ON open_orders
FOR EACH ROW
BEGIN
    UPDATE products
    SET stock = stock + (SELECT quantity FROM order_items WHERE order_id = OLD.id AND product_id = products.id)
    WHERE id IN (SELECT product_id FROM order_items WHERE order_id = OLD.id);
    UPDATE orders SET status = 'cancelled' WHERE id = OLD.id;
END;
""",
        check="""
SELECT COUNT(*) AS open_before FROM open_orders;
CREATE TEMP TABLE probe AS
SELECT oi.product_id, oi.quantity, p.stock AS stock_before
FROM order_items AS oi JOIN products AS p ON p.id = oi.product_id
WHERE oi.order_id = (SELECT MIN(id) FROM open_orders);
DELETE FROM open_orders WHERE id = (SELECT MIN(id) FROM open_orders);
SELECT pr.product_id, pr.quantity, pr.stock_before, p.stock AS stock_after
FROM probe AS pr JOIN products AS p ON p.id = pr.product_id ORDER BY pr.product_id;
SELECT COUNT(*) AS open_after, (SELECT COUNT(*) FROM orders) AS orders_rows FROM open_orders;
""",
    ),
    dict(
        title="Inventory of triggers",
        db="shop",
        task="List every trigger in the shop DB: `name, on_object` (the table/view it is attached to), alphabetically. Then remember: `DROP TRIGGER name;` removes one.",
        sol="SELECT name, tbl_name AS on_object FROM sqlite_schema WHERE type = 'trigger' ORDER BY name;",
    ),
]
