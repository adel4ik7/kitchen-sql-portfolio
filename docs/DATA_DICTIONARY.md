# Data dictionary

| Table | Grain | Fields and units |
|---|---|---|
| ingredients | one raw ingredient | ingredient_id (PK), ingredient_name (unique), unit (kg or litre), cost_fils_per_unit (fixed purchase-equivalent cost) |
| dishes | one menu dish | dish_id (PK), dish_name (unique), category, menu_price_fils (reference price) |
| recipes | one ingredient in one dish | dish_id + ingredient_id (composite PK / FKs), qty_per_portion in the ingredient unit, including normal raw-to-served yield loss |
| orders | one food ticket | order_id (PK), ordered_at (Dubai local text timestamp), service, channel, status |
| order_items | one dish line on a ticket | order_item_id (PK), order_id / dish_id (FKs), quantity (portions), unit_price_fils (price at sale), discount_fils (total line discount) |
| waste | one raw ingredient waste entry | waste_id (PK), waste_date (Dubai local date), ingredient_id (FK), quantity (kg/litre), reason |

## Views

- v_recipe_cost: one dish; portion_cost_fils = SUM(qty_per_portion × ingredient unit cost).
- v_sales: one completed order line; net_sales_fils = quantity × unit_price_fils − line discount; recipe_cost_fils = quantity × portion cost.

## Rules

100 fils = 1 AED. Unit costs are integer fils per kg/litre; multiplying by fractional units produces fractional fils. Keep that precision until presentation and round once in query outputs. Do not sum rounded dish totals to calculate exact account balances.

Orders include food only. No customer identities or covers are modelled. An order average is not spend per guest. Dine-in and takeaway have the same reference menu prices; some lunch lines receive a 10% discount. Cancelled order lines remain in source data but never enter v_sales.

Waste reasons: Spoilage, Overproduction, Handling, and avoidable excess Prep trim. Waste quantities are raw stock equivalents. Routine yield loss is included in recipes, so the waste log excludes routine trim already allowed there. Food prepared before cancellation is not modelled. Actual cost in a real kitchen could therefore differ.

The dataset is generated with Python random.Random(27). More Friday/Saturday orders and more dinner tickets are deliberately built into the generator. Prices, recipes and weights are assumptions, not observations or supplier quotations.
