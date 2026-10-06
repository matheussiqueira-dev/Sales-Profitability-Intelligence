-- Existing V1 snapshot retains rows and monetary totals, with explicit zero legacy costs.
ALTER TABLE analytics.fact_sales
  ADD COLUMN variable_cost_rate numeric(8,4) NOT NULL DEFAULT 0,
  ADD COLUMN variable_cost_fixed numeric(18,2) NOT NULL DEFAULT 0,
  ADD COLUMN variable_cost_value numeric(18,2) NOT NULL DEFAULT 0;
ALTER TABLE analytics.fact_sales DROP CONSTRAINT fact_sales_check2;
ALTER TABLE analytics.fact_sales ADD CONSTRAINT fact_sales_contribution_v2
  CHECK(contribution_margin = net_revenue - total_product_cost - freight_allocated - variable_cost_value);
ALTER TABLE analytics.fact_sales ADD CONSTRAINT fact_sales_variable_v2
  CHECK(variable_cost_value = round(net_revenue * variable_cost_rate + variable_cost_fixed,2));
ALTER TABLE analytics.fact_sales ADD CONSTRAINT fact_sales_variable_ranges
  CHECK(variable_cost_rate >= 0 AND variable_cost_rate < 1 AND variable_cost_fixed >= 0
        AND variable_cost_value >= 0 AND discount_value >= 0);
ALTER TABLE analytics.pipeline_metadata DROP CONSTRAINT pipeline_metadata_contract_version_check;
ALTER TABLE analytics.pipeline_metadata ADD CONSTRAINT pipeline_metadata_contract_version_check
  CHECK(contract_version IN (1,2));
UPDATE analytics.pipeline_metadata SET contract_version = 2;
