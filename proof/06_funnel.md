# View → add-to-cart → purchase funnel and IDP join

The add-to-cart stage includes the observed canonical values `add`, `increase`, and `added`. Counts are event/record counts plus distinct actors; stages are not asserted to be a cohort conversion rate.

```console
$ databricks experimental aitools tools query "WITH stages AS (SELECT 'view' AS stage, COUNT(*) AS event_or_record_count, COUNT(DISTINCT user_id) AS distinct_users FROM nikks_fevm_workspace_7405607030687545.techsummit.event_view_item UNION ALL SELECT 'add_to_cart', COUNT(*), COUNT(DISTINCT user_id) FROM nikks_fevm_workspace_7405607030687545.techsummit.event_add_to_cart WHERE cart_action IN ('add','increase','added') UNION ALL SELECT 'purchase', COUNT(*), COUNT(DISTINCT customer_id) FROM nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase), spec_join AS (SELECT COUNT(*) AS joined_rows, COUNT(DISTINCT p.product_id) AS matched_products, (SELECT COUNT(*) FROM nikks_fevm_workspace_7405607030687545.techsummit.dim_product) AS product_rows, (SELECT COUNT(*) FROM nikks_fevm_workspace_7405607030687545.techsummit.idp_product_specs) AS spec_rows FROM nikks_fevm_workspace_7405607030687545.techsummit.dim_product p JOIN nikks_fevm_workspace_7405607030687545.techsummit.idp_product_specs s ON p.name = s.model_name) SELECT 'funnel' AS result_set, stage AS label, event_or_record_count AS value_1, distinct_users AS value_2 FROM stages UNION ALL SELECT 'spec_join', 'dim_product.name = idp_product_specs.model_name', joined_rows, matched_products FROM spec_join UNION ALL SELECT 'spec_join_inputs', 'product_rows / spec_rows', product_rows, spec_rows FROM spec_join" -p FEVM
[
  {
    "label": "view",
    "result_set": "funnel",
    "value_1": "3031",
    "value_2": "104"
  },
  {
    "label": "add_to_cart",
    "result_set": "funnel",
    "value_1": "860",
    "value_2": "104"
  },
  {
    "label": "purchase",
    "result_set": "funnel",
    "value_1": "36",
    "value_2": "11"
  },
  {
    "label": "dim_product.name = idp_product_specs.model_name",
    "result_set": "spec_join",
    "value_1": "12",
    "value_2": "12"
  },
  {
    "label": "product_rows / spec_rows",
    "result_set": "spec_join_inputs",
    "value_1": "12",
    "value_2": "12"
  }
]
```

