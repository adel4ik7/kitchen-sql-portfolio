-- Where are recorded waste costs coming from?
SELECT w.reason, COUNT(*) AS entries,
 ROUND(SUM(w.quantity*i.cost_fils_per_unit)/100.0,2) AS waste_cost_aed
FROM waste w JOIN ingredients i ON i.ingredient_id=w.ingredient_id
GROUP BY w.reason ORDER BY waste_cost_aed DESC;
