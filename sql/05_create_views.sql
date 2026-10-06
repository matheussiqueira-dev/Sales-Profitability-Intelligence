CREATE OR REPLACE VIEW analytics.vw_sales_summary AS
SELECT sum(gross_revenue) AS gross_revenue, sum(discount_value) AS discount_value,
       sum(return_value) AS return_value, sum(net_revenue) AS net_revenue,
       sum(total_product_cost) AS total_product_cost, sum(freight_allocated) AS freight_allocated,
       sum(contribution_margin) AS contribution_margin,
       sum(contribution_margin)/nullif(sum(net_revenue),0) AS margin_percentage,
       count(DISTINCT order_id) AS orders, count(DISTINCT customer_key) AS customers,
       sum(net_revenue)/nullif(count(DISTINCT order_id),0) AS average_ticket,
       sum(discount_value)/nullif(sum(gross_revenue),0) AS discount_percentage,
       sum(returned_quantity)::numeric/nullif(sum(quantity),0) AS return_rate,
       sum(variable_cost_value) AS variable_cost_value
FROM analytics.fact_sales;

CREATE OR REPLACE VIEW analytics.vw_product_profitability AS
SELECT p.product_key, p.product_name, p.category,
       sum(f.quantity) AS quantity, sum(f.returned_quantity) AS returned_quantity,
       sum(f.net_revenue) AS net_revenue, sum(f.contribution_margin) AS contribution_margin,
       sum(f.contribution_margin)/nullif(sum(f.net_revenue),0) AS margin_percentage,
       sum(f.gross_revenue) AS gross_revenue, sum(f.discount_value) AS discount_value,
       sum(f.total_product_cost) AS total_product_cost, sum(f.freight_allocated) AS freight_allocated,
       sum(f.return_value) AS return_value,
       sum(f.returned_quantity)::numeric/nullif(sum(f.quantity),0) AS return_rate,
       analytics.discount_limit(
          sum((f.quantity-f.returned_quantity)*f.unit_price),
          sum((f.quantity-f.returned_quantity)*f.unit_price*f.variable_cost_rate)
            /nullif(sum((f.quantity-f.returned_quantity)*f.unit_price),0),
          sum(f.total_product_cost) + sum(f.freight_allocated) + sum(f.variable_cost_fixed), 0.15)
          AS maximum_discount_for_15pct_margin,
       sum(f.variable_cost_value) AS variable_cost_value,
       sum(f.variable_cost_fixed) AS variable_cost_fixed
FROM analytics.fact_sales f JOIN analytics.dim_product p USING(product_key)
GROUP BY p.product_key;

CREATE OR REPLACE VIEW analytics.vw_customer_profitability AS
WITH totals AS (
    SELECT c.customer_key, c.customer_name, c.segment, c.region,
           sum(f.net_revenue) AS net_revenue, sum(f.contribution_margin) AS contribution_margin,
           sum(f.contribution_margin)/nullif(sum(f.net_revenue),0) AS margin_percentage,
           sum(f.discount_value)/nullif(sum(f.gross_revenue),0) AS discount_percentage,
           count(DISTINCT f.order_id) AS orders,
           sum(f.net_revenue)/nullif(count(DISTINCT f.order_id),0) AS average_ticket,
           sum(f.return_value) AS return_value, max(d.full_date) AS last_order_date
    FROM analytics.fact_sales f JOIN analytics.dim_customer c USING(customer_key)
    JOIN analytics.dim_date d USING(date_key) GROUP BY c.customer_key
), thresholds AS (
    SELECT percentile_cont(0.75) WITHIN GROUP(ORDER BY net_revenue) AS high_revenue,
           sum(contribution_margin)/nullif(sum(net_revenue),0) AS average_margin,
           (SELECT max(full_date) FROM analytics.fact_sales JOIN analytics.dim_date USING(date_key))
             AS reference_date
    FROM totals
)
SELECT t.*, CASE
    WHEN last_order_date < reference_date - 90 THEN 'At Risk'
    WHEN net_revenue >= high_revenue AND margin_percentage >= average_margin THEN 'Champions'
    WHEN net_revenue >= high_revenue THEN 'High Revenue / Low Margin'
    WHEN margin_percentage >= average_margin THEN 'High Margin'
    ELSE 'Low Value' END AS profitability_segment
FROM totals t CROSS JOIN thresholds;

CREATE OR REPLACE VIEW analytics.vw_channel_profitability AS
SELECT c.channel_key, c.channel_name, sum(f.net_revenue) AS net_revenue,
       sum(f.contribution_margin) AS contribution_margin,
       sum(f.contribution_margin)/nullif(sum(f.net_revenue),0) AS margin_percentage,
       sum(f.discount_value)/nullif(sum(f.gross_revenue),0) AS discount_percentage,
       sum(f.freight_allocated) AS freight_allocated,
       sum(f.total_product_cost) AS total_product_cost,
       sum(f.net_revenue)/nullif(count(DISTINCT f.order_id),0) AS average_ticket,
       count(DISTINCT f.order_id) AS orders,
       sum(f.returned_quantity)::numeric/nullif(sum(f.quantity),0) AS return_rate,
       sum(f.variable_cost_value) AS variable_cost_value
FROM analytics.fact_sales f JOIN analytics.dim_channel c USING(channel_key)
GROUP BY c.channel_key;

CREATE OR REPLACE VIEW analytics.vw_monthly_performance AS
SELECT date_trunc('month', d.full_date)::date AS month,
       sum(f.net_revenue) AS net_revenue, sum(f.contribution_margin) AS contribution_margin,
       sum(f.contribution_margin)/nullif(sum(f.net_revenue),0) AS margin_percentage,
       sum(f.discount_value)/nullif(sum(f.gross_revenue),0) AS discount_percentage,
       count(DISTINCT f.order_id) AS orders,
       sum(f.variable_cost_value) AS variable_cost_value
FROM analytics.fact_sales f JOIN analytics.dim_date d USING(date_key)
GROUP BY 1;

CREATE OR REPLACE VIEW analytics.vw_return_analysis AS
SELECT p.product_key, p.product_name, sum(f.quantity) AS quantity,
       sum(f.returned_quantity) AS returned_quantity, sum(f.return_value) AS return_value,
       sum(f.returned_quantity)::numeric/nullif(sum(f.quantity),0) AS return_rate
FROM analytics.fact_sales f JOIN analytics.dim_product p USING(product_key)
GROUP BY p.product_key;

CREATE OR REPLACE VIEW analytics.vw_target_performance AS
SELECT t.month, t.channel, t.revenue_target, t.margin_target_percentage,
       coalesce(s.net_revenue,0) AS net_revenue,
       s.margin_percentage, s.net_revenue/nullif(t.revenue_target,0) AS revenue_attainment
FROM staging.targets t LEFT JOIN (
    SELECT date_trunc('month',d.full_date)::date AS month, c.channel_name AS channel,
           sum(f.net_revenue) AS net_revenue,
           sum(f.contribution_margin)/nullif(sum(f.net_revenue),0) AS margin_percentage
    FROM analytics.fact_sales f JOIN analytics.dim_date d USING(date_key)
    JOIN analytics.dim_channel c USING(channel_key) GROUP BY 1,2
) s USING(month,channel);
