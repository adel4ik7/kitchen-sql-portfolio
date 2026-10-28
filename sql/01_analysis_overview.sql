-- Sales, orders and theoretical food cost
SELECT COUNT(DISTINCT order_id) AS completed_orders,
       SUM(quantity) AS portions_sold,
       ROUND(SUM(net_sales_fils)/100.0,2) AS net_sales_aed,
       ROUND(SUM(net_sales_fils)/100.0/COUNT(DISTINCT order_id),2) AS average_order_aed,
       ROUND(SUM(recipe_cost_fils)/100.0,2) AS theoretical_food_cost_aed,
       ROUND(100.0*SUM(recipe_cost_fils)/SUM(net_sales_fils),2) AS food_cost_pct
FROM v_sales;
