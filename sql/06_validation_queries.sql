-- Independent SQL source totals, excluding cancelled orders.
WITH lines AS (
    SELECT i.*, p.unit_cost,
           coalesce(r.returned_quantity,0) AS returned_quantity,
           round(i.quantity*i.unit_price,2) AS gross,
           round(i.quantity*i.unit_price*i.discount_percentage,2) AS discount
    FROM staging.order_items i JOIN staging.orders o USING(order_id)
    JOIN staging.products p USING(product_id)
    LEFT JOIN (SELECT order_item_id,sum(quantity_returned) AS returned_quantity
               FROM staging.returns GROUP BY order_item_id) r USING(order_item_id)
    WHERE o.status <> 'cancelled'
)
SELECT sum(gross) AS gross_revenue, sum(discount) AS discount_value,
       sum(round((gross-discount)*returned_quantity/quantity,2)) AS return_value,
       sum(round((quantity-returned_quantity)*unit_cost,2)) AS total_product_cost
FROM lines;
