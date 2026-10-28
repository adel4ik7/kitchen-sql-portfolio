-- Combine sales and waste only after aggregating each to a date
WITH sales_by_day AS (
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
LEFT JOIN waste_by_day w ON w.waste_date=d.day ORDER BY d.day;
