-- Monthly trading performance
SELECT strftime('%Y-%m',sale_date) AS month,
 COUNT(DISTINCT order_id) AS orders, SUM(quantity) AS portions,
 ROUND(SUM(net_sales_fils)/100.0,2) AS net_sales_aed,
 ROUND(100.0*SUM(recipe_cost_fils)/SUM(net_sales_fils),2) AS food_cost_pct
FROM v_sales GROUP BY month ORDER BY month;
