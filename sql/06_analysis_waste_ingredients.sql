-- Waste cost by ingredient
SELECT i.ingredient_name, i.unit,
 ROUND(SUM(w.quantity),3) AS wasted_quantity,
 ROUND(SUM(w.quantity*i.cost_fils_per_unit)/100.0,2) AS waste_cost_aed
FROM waste w JOIN ingredients i ON i.ingredient_id=w.ingredient_id
GROUP BY i.ingredient_id,i.ingredient_name,i.unit ORDER BY waste_cost_aed DESC;
