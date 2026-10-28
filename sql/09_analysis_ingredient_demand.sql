-- Theoretical raw ingredient demand for sold portions
SELECT i.ingredient_name,i.unit,
 ROUND(SUM(s.quantity*r.qty_per_portion),3) AS theoretical_usage,
 ROUND(SUM(s.quantity*r.qty_per_portion*i.cost_fils_per_unit)/100.0,2) AS usage_cost_aed
FROM v_sales s JOIN recipes r ON r.dish_id=s.dish_id
JOIN ingredients i ON i.ingredient_id=r.ingredient_id
GROUP BY i.ingredient_id,i.ingredient_name,i.unit ORDER BY usage_cost_aed DESC;
