-- Channel sales before any unmodelled fees
SELECT channel,COUNT(DISTINCT order_id) AS orders,
 ROUND(SUM(net_sales_fils)/100.0,2) AS net_sales_aed,
 ROUND(SUM(net_sales_fils)/100.0/COUNT(DISTINCT order_id),2) AS average_order_aed
FROM v_sales GROUP BY channel ORDER BY net_sales_aed DESC;
