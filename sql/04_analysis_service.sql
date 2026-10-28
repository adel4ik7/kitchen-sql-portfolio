-- Lunch versus dinner without averaging individual lines
WITH tickets AS (
 SELECT order_id, service, SUM(net_sales_fils) AS ticket_fils
 FROM v_sales GROUP BY order_id,service
)
SELECT service, COUNT(*) AS orders,
 ROUND(AVG(ticket_fils)/100.0,2) AS average_order_aed,
 ROUND(SUM(ticket_fils)/100.0,2) AS net_sales_aed
FROM tickets GROUP BY service ORDER BY net_sales_aed DESC;
