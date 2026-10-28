-- Which dishes contribute most after recipe cost?
SELECT d.dish_name, d.category, SUM(s.quantity) AS portions,
 ROUND(SUM(s.net_sales_fils)/100.0,2) AS net_sales_aed,
 ROUND(SUM(s.recipe_cost_fils)/100.0,2) AS recipe_cost_aed,
 ROUND(SUM(s.net_sales_fils-s.recipe_cost_fils)/100.0,2) AS contribution_aed,
 ROUND(SUM(s.net_sales_fils-s.recipe_cost_fils)/SUM(s.quantity)/100.0,2) AS contribution_per_portion_aed,
 ROUND(100.0*SUM(s.recipe_cost_fils)/SUM(s.net_sales_fils),2) AS food_cost_pct
FROM v_sales s JOIN dishes d ON d.dish_id=s.dish_id
GROUP BY d.dish_id,d.dish_name,d.category ORDER BY contribution_aed DESC;
