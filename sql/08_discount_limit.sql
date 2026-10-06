CREATE OR REPLACE FUNCTION analytics.discount_limit(
    base_revenue numeric, variable_rate numeric, retained_costs numeric,
    target_margin numeric DEFAULT 0.15
) RETURNS numeric LANGUAGE SQL IMMUTABLE
RETURN CASE WHEN base_revenue > 0 AND variable_rate >= 0 AND variable_rate < 1
                 AND target_margin >= 0 AND target_margin < 1
                 AND 1-variable_rate-target_margin > 0
            THEN 1-retained_costs/(base_revenue*(1-variable_rate-target_margin))
            ELSE NULL END;
