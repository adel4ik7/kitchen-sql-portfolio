-- Dishes above a project-specific 32% food-cost target
SELECT d.dish_name, SUM(s.quantity) AS portions,
 ROUND(100.0*SUM(s.recipe_cost_fils)/SUM(s.net_sales_fils),2) AS food_cost_pct
FROM v_sales s JOIN dishes d ON d.dish_id=s.dish_id
GROUP BY d.dish_id,d.dish_name
HAVING 100.0*SUM(s.recipe_cost_fils)/SUM(s.net_sales_fils)>32
ORDER BY food_cost_pct DESC;
