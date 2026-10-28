-- SQLite. Money is stored in fils: 100 fils = 1 AED.
PRAGMA foreign_keys = ON;
CREATE TABLE ingredients (
 ingredient_id INTEGER PRIMARY KEY,
 ingredient_name TEXT NOT NULL UNIQUE,
 unit TEXT NOT NULL CHECK(unit IN ('kg','litre')),
 cost_fils_per_unit INTEGER NOT NULL CHECK(cost_fils_per_unit > 0)
);
CREATE TABLE dishes (
 dish_id INTEGER PRIMARY KEY,
 dish_name TEXT NOT NULL UNIQUE,
 category TEXT NOT NULL,
 menu_price_fils INTEGER NOT NULL CHECK(menu_price_fils > 0)
);
CREATE TABLE recipes (
 dish_id INTEGER NOT NULL REFERENCES dishes,
 ingredient_id INTEGER NOT NULL REFERENCES ingredients,
 qty_per_portion REAL NOT NULL CHECK(qty_per_portion > 0),
 PRIMARY KEY(dish_id, ingredient_id)
);
CREATE TABLE orders (
 order_id INTEGER PRIMARY KEY,
 ordered_at TEXT NOT NULL,
 service TEXT NOT NULL CHECK(service IN ('Lunch','Dinner')),
 channel TEXT NOT NULL CHECK(channel IN ('Dine-in','Takeaway')),
 status TEXT NOT NULL CHECK(status IN ('Completed','Cancelled'))
);
CREATE TABLE order_items (
 order_item_id INTEGER PRIMARY KEY,
 order_id INTEGER NOT NULL REFERENCES orders,
 dish_id INTEGER NOT NULL REFERENCES dishes,
 quantity INTEGER NOT NULL CHECK(quantity > 0),
 unit_price_fils INTEGER NOT NULL CHECK(unit_price_fils > 0),
 discount_fils INTEGER NOT NULL DEFAULT 0,
 CHECK(discount_fils >= 0 AND discount_fils <= quantity * unit_price_fils)
);
CREATE TABLE waste (
 waste_id INTEGER PRIMARY KEY,
 waste_date TEXT NOT NULL,
 ingredient_id INTEGER NOT NULL REFERENCES ingredients,
 quantity REAL NOT NULL CHECK(quantity > 0),
 reason TEXT NOT NULL CHECK(reason IN ('Spoilage','Prep trim','Overproduction','Handling'))
);
CREATE INDEX idx_orders_date ON orders(ordered_at);
CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_waste_date ON waste(waste_date);

-- Recipe quantities are purchased/raw equivalents, including normal yield loss.
CREATE VIEW v_recipe_cost AS
SELECT r.dish_id, SUM(r.qty_per_portion * i.cost_fils_per_unit) AS portion_cost_fils
FROM recipes r JOIN ingredients i ON i.ingredient_id = r.ingredient_id
GROUP BY r.dish_id;

-- One row per completed order line. Cancelled orders never enter sales KPIs.
CREATE VIEW v_sales AS
SELECT o.order_id, date(o.ordered_at) AS sale_date,
       o.service, o.channel, oi.dish_id, oi.quantity,
       oi.quantity * oi.unit_price_fils - oi.discount_fils AS net_sales_fils,
       oi.quantity * rc.portion_cost_fils AS recipe_cost_fils
FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
JOIN v_recipe_cost rc ON rc.dish_id = oi.dish_id
WHERE o.status = 'Completed';
