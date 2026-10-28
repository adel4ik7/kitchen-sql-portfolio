-- Optional window-function exercise
WITH daily AS (
 SELECT sale_date,SUM(net_sales_fils) AS sales FROM v_sales GROUP BY sale_date
)
SELECT sale_date,ROUND(sales/100.0,2) AS sales_aed,
 ROUND(SUM(sales) OVER (ORDER BY sale_date ROWS UNBOUNDED PRECEDING)/100.0,2)
 AS cumulative_sales_aed
FROM daily ORDER BY sale_date;
