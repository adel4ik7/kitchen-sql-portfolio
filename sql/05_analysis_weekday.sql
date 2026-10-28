-- What days need more prep?
SELECT strftime('%w',sale_date) AS weekday_sun_0,
 COUNT(DISTINCT sale_date) AS trading_days,
 COUNT(DISTINCT order_id) AS orders,
 ROUND(1.0*SUM(quantity)/COUNT(DISTINCT sale_date),1) AS portions_per_day
FROM v_sales GROUP BY weekday_sun_0 ORDER BY weekday_sun_0;
