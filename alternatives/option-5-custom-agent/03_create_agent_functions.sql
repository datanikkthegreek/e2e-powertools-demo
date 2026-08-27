CREATE OR REPLACE FUNCTION nikks_fevm_workspace_7405607030687545.techsummit.option5_search_manuals(
  question STRING COMMENT 'Complete product operation, safety, maintenance, or troubleshooting question'
)
RETURNS TABLE (manual_text STRING, source_path STRING, score DOUBLE)
COMMENT 'Hybrid AI Search over Bosch product manuals. Returns grounded context and citation paths.'
RETURN
  SELECT chunk_to_retrieve, source_path, search_score
  FROM VECTOR_SEARCH(
    index => 'nikks_fevm_workspace_7405607030687545.techsummit.option5_manual_index',
    query_text => question,
    num_results => 5
  );

CREATE OR REPLACE FUNCTION nikks_fevm_workspace_7405607030687545.techsummit.option5_product_performance()
RETURNS TABLE (product STRING, category STRING, views BIGINT, units_sold BIGINT, revenue_eur DOUBLE)
COMMENT 'Returns product-level webshop views, units sold, and revenue in EUR for the techsummit demo.'
RETURN
  SELECT
    p.name,
    p.category,
    count(DISTINCT v.ga_session_id),
    coalesce(sum(l.quantity), 0),
    coalesce(sum(l.quantity * l.unit_price_eur), 0)
  FROM nikks_fevm_workspace_7405607030687545.techsummit.dim_product p
  LEFT JOIN nikks_fevm_workspace_7405607030687545.techsummit.event_view_item v
    ON v.product_id = p.product_id
  LEFT JOIN nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase_line l
    ON l.product_id = p.product_id
  GROUP BY p.name, p.category;

CREATE OR REPLACE FUNCTION nikks_fevm_workspace_7405607030687545.techsummit.option5_revenue_by_country()
RETURNS TABLE (country STRING, revenue_eur DOUBLE, purchases BIGINT)
COMMENT 'Returns completed-purchase revenue and purchase count by country for the techsummit demo.'
RETURN
  SELECT c.country, sum(p.total_eur), count(*)
  FROM nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase p
  JOIN nikks_fevm_workspace_7405607030687545.techsummit.dim_customer c
    ON c.customer_id = p.customer_id
  GROUP BY c.country;

CREATE OR REPLACE FUNCTION nikks_fevm_workspace_7405607030687545.techsummit.option5_product_specs(
  model STRING COMMENT 'Full or partial Bosch model name'
)
RETURNS TABLE (
  model_name STRING,
  voltage_v DOUBLE,
  max_torque_nm DOUBLE,
  no_load_rpm STRING,
  weight_kg DOUBLE,
  battery_platform STRING
)
COMMENT 'Returns extracted technical specifications for Bosch products matching a model name.'
RETURN
  SELECT model_name, voltage_v, max_torque_nm, no_load_rpm, weight_kg, battery_platform
  FROM nikks_fevm_workspace_7405607030687545.techsummit.idp_product_specs
  WHERE lower(model_name) LIKE concat('%', lower(model), '%');
