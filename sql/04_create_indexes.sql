CREATE INDEX IF NOT EXISTS ix_fact_date ON analytics.fact_sales(date_key);
CREATE INDEX IF NOT EXISTS ix_fact_customer ON analytics.fact_sales(customer_key);
CREATE INDEX IF NOT EXISTS ix_fact_product ON analytics.fact_sales(product_key);
CREATE INDEX IF NOT EXISTS ix_fact_channel ON analytics.fact_sales(channel_key);
CREATE INDEX IF NOT EXISTS ix_fact_seller ON analytics.fact_sales(seller_key);
CREATE INDEX IF NOT EXISTS ix_fact_order ON analytics.fact_sales(order_id);
