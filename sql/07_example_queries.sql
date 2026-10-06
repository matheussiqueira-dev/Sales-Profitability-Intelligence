-- Products with the highest total contribution, percentage is weighted.
SELECT * FROM analytics.vw_product_profitability ORDER BY contribution_margin DESC LIMIT 10;
SELECT * FROM analytics.vw_customer_profitability ORDER BY contribution_margin DESC LIMIT 10;
-- Commercial concentration with a margin below the portfolio average.
SELECT p.* FROM analytics.vw_product_profitability p
CROSS JOIN analytics.vw_sales_summary s
WHERE p.net_revenue >= (SELECT percentile_cont(0.75) WITHIN GROUP(ORDER BY net_revenue)
                       FROM analytics.vw_product_profitability)
AND p.margin_percentage < s.margin_percentage ORDER BY p.net_revenue DESC;
-- Discount policy for retained units, freight remains fixed, target = 15%.
SELECT product_name, maximum_discount_for_15pct_margin
FROM analytics.vw_product_profitability ORDER BY maximum_discount_for_15pct_margin;
