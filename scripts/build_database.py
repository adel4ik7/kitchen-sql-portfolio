from pathlib import Path
import csv
import datetime as dt
import json
import random
import sqlite3
import zipfile

ROOT = Path(__file__).resolve().parents[1]
for folder in ['sql', 'data', 'results', 'docs', 'scripts']:
    (ROOT / folder).mkdir(parents=True, exist_ok=True)

SCHEMA = '''-- SQLite. Money is stored in fils: 100 fils = 1 AED.
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
'''
(ROOT / 'sql/01_schema.sql').write_text(SCHEMA, encoding='utf-8')

QUERIES = [
('01_overview', 'Sales, orders and theoretical food cost', '''SELECT COUNT(DISTINCT order_id) AS completed_orders,
       SUM(quantity) AS portions_sold,
       ROUND(SUM(net_sales_fils)/100.0,2) AS net_sales_aed,
       ROUND(SUM(net_sales_fils)/100.0/COUNT(DISTINCT order_id),2) AS average_order_aed,
       ROUND(SUM(recipe_cost_fils)/100.0,2) AS theoretical_food_cost_aed,
       ROUND(100.0*SUM(recipe_cost_fils)/SUM(net_sales_fils),2) AS food_cost_pct
FROM v_sales;'''),
('02_monthly', 'Monthly trading performance', '''SELECT strftime('%Y-%m',sale_date) AS month,
 COUNT(DISTINCT order_id) AS orders, SUM(quantity) AS portions,
 ROUND(SUM(net_sales_fils)/100.0,2) AS net_sales_aed,
 ROUND(100.0*SUM(recipe_cost_fils)/SUM(net_sales_fils),2) AS food_cost_pct
FROM v_sales GROUP BY month ORDER BY month;'''),
('03_menu', 'Which dishes contribute most after recipe cost?', '''SELECT d.dish_name, d.category, SUM(s.quantity) AS portions,
 ROUND(SUM(s.net_sales_fils)/100.0,2) AS net_sales_aed,
 ROUND(SUM(s.recipe_cost_fils)/100.0,2) AS recipe_cost_aed,
 ROUND(SUM(s.net_sales_fils-s.recipe_cost_fils)/100.0,2) AS contribution_aed,
 ROUND(SUM(s.net_sales_fils-s.recipe_cost_fils)/SUM(s.quantity)/100.0,2) AS contribution_per_portion_aed,
 ROUND(100.0*SUM(s.recipe_cost_fils)/SUM(s.net_sales_fils),2) AS food_cost_pct
FROM v_sales s JOIN dishes d ON d.dish_id=s.dish_id
GROUP BY d.dish_id,d.dish_name,d.category ORDER BY contribution_aed DESC;'''),
('04_service', 'Lunch versus dinner without averaging individual lines', '''WITH tickets AS (
 SELECT order_id, service, SUM(net_sales_fils) AS ticket_fils
 FROM v_sales GROUP BY order_id,service
)
SELECT service, COUNT(*) AS orders,
 ROUND(AVG(ticket_fils)/100.0,2) AS average_order_aed,
 ROUND(SUM(ticket_fils)/100.0,2) AS net_sales_aed
FROM tickets GROUP BY service ORDER BY net_sales_aed DESC;'''),
('05_weekday', 'What days need more prep?', '''SELECT strftime('%w',sale_date) AS weekday_sun_0,
 COUNT(DISTINCT sale_date) AS trading_days,
 COUNT(DISTINCT order_id) AS orders,
 ROUND(1.0*SUM(quantity)/COUNT(DISTINCT sale_date),1) AS portions_per_day
FROM v_sales GROUP BY weekday_sun_0 ORDER BY weekday_sun_0;'''),
('06_waste_ingredients', 'Waste cost by ingredient', '''SELECT i.ingredient_name, i.unit,
 ROUND(SUM(w.quantity),3) AS wasted_quantity,
 ROUND(SUM(w.quantity*i.cost_fils_per_unit)/100.0,2) AS waste_cost_aed
FROM waste w JOIN ingredients i ON i.ingredient_id=w.ingredient_id
GROUP BY i.ingredient_id,i.ingredient_name,i.unit ORDER BY waste_cost_aed DESC;'''),
('07_waste_reasons', 'Where are recorded waste costs coming from?', '''SELECT w.reason, COUNT(*) AS entries,
 ROUND(SUM(w.quantity*i.cost_fils_per_unit)/100.0,2) AS waste_cost_aed
FROM waste w JOIN ingredients i ON i.ingredient_id=w.ingredient_id
GROUP BY w.reason ORDER BY waste_cost_aed DESC;'''),
('08_cost_alerts', 'Dishes above a project-specific 32% food-cost target', '''SELECT d.dish_name, SUM(s.quantity) AS portions,
 ROUND(100.0*SUM(s.recipe_cost_fils)/SUM(s.net_sales_fils),2) AS food_cost_pct
FROM v_sales s JOIN dishes d ON d.dish_id=s.dish_id
GROUP BY d.dish_id,d.dish_name
HAVING 100.0*SUM(s.recipe_cost_fils)/SUM(s.net_sales_fils)>32
ORDER BY food_cost_pct DESC;'''),
('09_ingredient_demand', 'Theoretical raw ingredient demand for sold portions', '''SELECT i.ingredient_name,i.unit,
 ROUND(SUM(s.quantity*r.qty_per_portion),3) AS theoretical_usage,
 ROUND(SUM(s.quantity*r.qty_per_portion*i.cost_fils_per_unit)/100.0,2) AS usage_cost_aed
FROM v_sales s JOIN recipes r ON r.dish_id=s.dish_id
JOIN ingredients i ON i.ingredient_id=r.ingredient_id
GROUP BY i.ingredient_id,i.ingredient_name,i.unit ORDER BY usage_cost_aed DESC;'''),
('10_daily_cost', 'Combine sales and waste only after aggregating each to a date', '''WITH sales_by_day AS (
 SELECT sale_date,SUM(net_sales_fils) AS sales,SUM(recipe_cost_fils) AS recipe_cost
 FROM v_sales GROUP BY sale_date
), waste_by_day AS (
 SELECT w.waste_date,SUM(w.quantity*i.cost_fils_per_unit) AS waste_cost
 FROM waste w JOIN ingredients i ON i.ingredient_id=w.ingredient_id GROUP BY w.waste_date
), dates AS (
 SELECT sale_date AS day FROM sales_by_day UNION SELECT waste_date FROM waste_by_day
)
SELECT d.day,ROUND(COALESCE(s.sales,0)/100.0,2) AS net_sales_aed,
 ROUND(COALESCE(w.waste_cost,0)/100.0,2) AS waste_cost_aed,
 ROUND(100.0*COALESCE(w.waste_cost,0)/NULLIF(s.sales,0),2) AS waste_to_sales_pct,
 ROUND((COALESCE(s.sales,0)-COALESCE(s.recipe_cost,0)-COALESCE(w.waste_cost,0))/100.0,2)
 AS contribution_after_recorded_waste_aed
FROM dates d LEFT JOIN sales_by_day s ON s.sale_date=d.day
LEFT JOIN waste_by_day w ON w.waste_date=d.day ORDER BY d.day;'''),
('11_channel', 'Channel sales before any unmodelled fees', '''SELECT channel,COUNT(DISTINCT order_id) AS orders,
 ROUND(SUM(net_sales_fils)/100.0,2) AS net_sales_aed,
 ROUND(SUM(net_sales_fils)/100.0/COUNT(DISTINCT order_id),2) AS average_order_aed
FROM v_sales GROUP BY channel ORDER BY net_sales_aed DESC;'''),
('12_running_sales', 'Optional window-function exercise', '''WITH daily AS (
 SELECT sale_date,SUM(net_sales_fils) AS sales FROM v_sales GROUP BY sale_date
)
SELECT sale_date,ROUND(sales/100.0,2) AS sales_aed,
 ROUND(SUM(sales) OVER (ORDER BY sale_date ROWS UNBOUNDED PRECEDING)/100.0,2)
 AS cumulative_sales_aed
FROM daily ORDER BY sale_date;''')]
for key,title,query in QUERIES:
    (ROOT / f'sql/{key[0:2]}_analysis_{key[3:]}.sql').write_text('-- '+title+'\n'+query+'\n', encoding='utf-8')

INGREDIENTS = [
 (1,'Chicken thigh','kg',3200),(2,'Sea bass fillet','kg',9800),(3,'Prawns','kg',9500),
 (4,'Rice','kg',800),(5,'Potato','kg',500),(6,'Tomato','kg',700),
 (7,'Cucumber','kg',450),(8,'Feta','kg',4800),(9,'Olive oil','litre',4200),
 (10,'Yoghurt','kg',1100),(11,'Lemon','kg',650),(12,'Lettuce','kg',1200),
 (13,'Pasta','kg',950),(14,'Cream','litre',2100),(15,'Parmesan','kg',8800),
 (16,'Bread','kg',1400),(17,'Chickpeas','kg',850),(18,'Tahini','kg',2600),
 (19,'Butter','kg',4000),(20,'Herb and spice mix','kg',6500)]
DISHES = [(1,'Chicken souvlaki','Main',6800),(2,'Grilled sea bass','Main',9800),
 (3,'Prawn linguine','Main',8200),(4,'Greek salad','Starter',4200),
 (5,'Chicken rice bowl','Main',5200),(6,'Hummus and bread','Starter',3200),
 (7,'Lemon roast potatoes','Side',2400),(8,'Creamy parmesan pasta','Main',5400),
 (9,'Tomato cucumber salad','Side',2200),(10,'Garlic prawns','Starter',5800),
 (11,'Crispy fish sandwich','Main',4900),(12,'Yoghurt herb dip','Side',1800)]
RECIPES = {
 1:{1:.22,10:.05,11:.025,9:.018,16:.08,20:.004},
 2:{2:.32,5:.18,9:.025,11:.04,20:.004},
 3:{3:.28,13:.12,6:.09,9:.02,19:.015,20:.003},
 4:{6:.15,7:.10,8:.07,9:.02,12:.04,20:.002},
 5:{1:.16,4:.10,6:.06,7:.04,10:.04,9:.01,20:.003},
 6:{17:.12,18:.035,9:.015,11:.025,16:.10,20:.002},
 7:{5:.25,9:.025,11:.025,20:.003},
 8:{13:.13,14:.09,15:.025,19:.02,20:.002},
 9:{6:.16,7:.12,9:.015,11:.015,20:.002},
 10:{3:.20,19:.025,11:.035,16:.06,20:.004},
 11:{2:.18,16:.12,12:.025,10:.03,9:.025,20:.002},
 12:{10:.13,7:.025,9:.01,20:.003}}

def generate():
    rng=random.Random(27)
    orders=[]; items=[]; waste=[]
    weights=[19,7,10,16,18,15,17,12,8,8,7,9]
    for offset in range(90):
        day=dt.date(2026,7,1)+dt.timedelta(days=offset)
        weekend=day.weekday() in (4,5)
        count=rng.randint(40,65)+(20 if weekend else 0)+offset//30*3
        for _ in range(count):
            oid=len(orders)+1
            service=rng.choices(['Lunch','Dinner'],[42,58])[0]
            hour=rng.randint(12,15) if service=='Lunch' else rng.randint(18,22)
            stamp=f'{day} {hour:02d}:{rng.randrange(60):02d}:00'
            orders.append((oid,stamp,service,rng.choices(['Dine-in','Takeaway'],[84,16])[0],
                           'Cancelled' if rng.random()<.025 else 'Completed'))
            n=rng.choices([1,2,3,4],[25,42,25,8])[0]
            pool=list(range(1,13))
            for _ in range(n):
                dish=rng.choices(pool,[weights[d-1] for d in pool])[0]
                pool.remove(dish)
                qty=rng.choices([1,2,3],[79,19,2])[0]
                price=DISHES[dish-1][3]
                discount=round(qty*price*.10) if service=='Lunch' and rng.random()<.18 else 0
                items.append((len(items)+1,oid,dish,qty,price,discount))
        for _ in range(rng.randint(4,8)):
            iid=rng.choices(range(1,21),[6,9,9,2,5,12,7,3,1,8,2,16,2,3,1,12,2,2,1,3])[0]
            reason=rng.choices(['Spoilage','Prep trim','Overproduction','Handling'],[42,18,30,10])[0]
            qty=round(rng.uniform(.07,.65)*(1.5 if weekend else 1),3)
            waste.append((len(waste)+1,str(day),iid,qty,reason))
    return {'ingredients':INGREDIENTS,'dishes':DISHES,
            'recipes':[(d,i,q) for d,recipe in RECIPES.items() for i,q in recipe.items()],
            'orders':orders,'order_items':items,'waste':waste}

def build():
    path=ROOT/'kitchen.db'
    if path.exists(): path.unlink()
    con=sqlite3.connect(path)
    con.executescript(SCHEMA)
    data=generate()
    for table,rows in data.items():
        con.executemany(f"INSERT INTO {table} VALUES ({','.join('?' for _ in rows[0])})",rows)
        headers=[r[1] for r in con.execute(f'PRAGMA table_info({table})')]
        with (ROOT/f'data/{table}.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f);w.writerow(headers);w.writerows(rows)
    con.commit()
    results={}
    for key,title,query in QUERIES:
        cur=con.execute(query);headers=[r[0] for r in cur.description]; rows=cur.fetchall()
        results[key]=[dict(zip(headers,row)) for row in rows]
        with (ROOT/f'results/{key}.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f);w.writerow(headers);w.writerows(rows)
    assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not con.execute('PRAGMA foreign_key_check').fetchall()
    assert len(results['10_daily_cost'])==90
    assert all(r[0]>0 for r in con.execute('SELECT portion_cost_fils FROM v_recipe_cost'))
    # Independent reconciliation: raw completed lines must match the sales view.
    raw=con.execute("SELECT SUM(quantity*unit_price_fils-discount_fils) FROM order_items JOIN orders USING(order_id) WHERE status='Completed'").fetchone()[0]
    assert raw==con.execute('SELECT SUM(net_sales_fils) FROM v_sales').fetchone()[0]
    raw_cost=0
    for item in data['order_items']:
        if data['orders'][item[1]-1][4]!='Completed':
            continue
        for d,iid,qty in data['recipes']:
            if item[2]==d:
                raw_cost+=qty*item[3]*INGREDIENTS[iid-1][3]
    assert abs(raw_cost-con.execute('SELECT SUM(recipe_cost_fils) FROM v_sales').fetchone()[0])<.01
    waste_cost=con.execute('SELECT SUM(quantity*cost_fils_per_unit) FROM waste JOIN ingredients USING(ingredient_id)').fetchone()[0]/100
    assert abs(sum(r['waste_cost_aed'] for r in results['10_daily_cost'])-waste_cost)<.5
    assert abs(results['12_running_sales'][-1]['cumulative_sales_aed']-raw/100)<.01
    facts={'rows':{k:len(v) for k,v in data.items()},'kpis':results['01_overview'][0],
           'waste_cost_aed':round(waste_cost,2),'cancelled_orders':sum(r[4]=='Cancelled' for r in data['orders'])}
    (ROOT/'results/summary.json').write_text(json.dumps(facts,indent=2),encoding='utf-8')
    (ROOT/'results/validation.txt').write_text('PASS: database integrity; foreign keys; 90 daily results; recipe coverage; sales reconciliation; independent recipe-cost reconciliation; waste reconciliation; cumulative sales reconciliation.\nAll 12 analysis queries executed successfully.\n',encoding='utf-8')
    con.close()
    return results,facts

if __name__=='__main__':
    results,facts=build()
    print(json.dumps(facts,indent=2))
