# Deployed Genie space and benchmark executions

## Live data sources

```console
$ python - <<'PY'
from databricks.sdk import WorkspaceClient
import json
w=WorkspaceClient(profile='FEVM')
s=w.genie.get_space('01f1a09a7ae41d9987122d1fe6918bcb', include_serialized_space=True)
serialized=json.loads(s.serialized_space)
print(json.dumps({'space_id':s.space_id,'title':s.title,'warehouse_id':s.warehouse_id,'data_sources':serialized['data_sources']},indent=2))
PY
{
  "space_id": "01f1a09a7ae41d9987122d1fe6918bcb",
  "title": "Bosch Power Tools Analytics",
  "warehouse_id": "a8384833e450ec4e",
  "data_sources": {
    "tables": [
      {
        "identifier": "nikks_fevm_workspace_7405607030687545.techsummit.dim_customer",
        "description": [
          "One row per customer account (14 rows). PK customer_id. Columns: customer_id, city, country (full name), signup_date (ALL NULL \u2014 never use for cohort/tenure analysis)."
        ]
      },
      {
        "identifier": "nikks_fevm_workspace_7405607030687545.techsummit.dim_product",
        "description": [
          "One row per product in the Bosch catalog (12 rows). PK product_id. Columns: product_id (canonical UUID), name (e.g. \"GSR 18V-55\"), category (family), price_eur (current list price)."
        ]
      },
      {
        "identifier": "nikks_fevm_workspace_7405607030687545.techsummit.event_add_to_cart",
        "description": [
          "GA4 cart actions (830 rows). Columns: source_timestamp (UTC), user_id, cart_id, product_id (FK->dim_product), item_name, price, previous_quantity, new_quantity, quantity_delta, cart_action ('add'|'increase'|'decrease'|'remove'), currency."
        ]
      },
      {
        "identifier": "nikks_fevm_workspace_7405607030687545.techsummit.event_view_item",
        "description": [
          "GA4 product-detail-page views (3,012 rows). Columns: ingest_timestamp (UTC), user_id, ga_session_id, product_id (FK->dim_product)."
        ],
        "column_configs": [
          {
            "column_name": "ga_session_id",
            "exclude": true
          }
        ]
      },
      {
        "identifier": "nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase",
        "description": [
          "One row per completed checkout (11 rows). PK purchase_id, UNIQUE cart_id. Columns: purchase_id, customer_id (FK->dim_customer), cart_id (UNIQUE; the checkout cart identifier \u2014 cart<->purchase is a LOGICAL non-enforced join to event_add_to_cart.cart_id, NOT a declared FK), created_at (UTC), total_eur."
        ]
      },
      {
        "identifier": "nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase_line",
        "description": [
          "One row per product line within a purchase (18 rows). PK purchase_line_id. Columns: purchase_line_id, purchase_id (FK->fact_purchase), product_id (FK->dim_product), quantity, unit_price_eur, name_snapshot."
        ]
      },
      {
        "identifier": "nikks_fevm_workspace_7405607030687545.techsummit.idp_product_specs",
        "description": [
          "Technical specs from PDF datasheets (12 rows). Columns: model_name, voltage_v, max_torque_nm, no_load_rpm, chuck_capacity_mm, weight_kg, battery_platform."
        ]
      }
    ],
    "volumes": [
      {
        "path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/productmanuals/"
      }
    ]
  }
}
```

## Two natural-language benchmark questions

Each `COMPLETED` Genie message reports the generated SQL, statement ID, executed row count, and answer grounded in the executed result.

```console
$ python -u - <<'PY'
from databricks.sdk import WorkspaceClient
import json
w=WorkspaceClient(profile='FEVM')
sid='01f1a09a7ae41d9987122d1fe6918bcb'
questions=['Top 5 products by revenue','Which 18V tool has the highest torque, and how well is it selling?']
for question in questions:
    m=w.genie.start_conversation_and_wait(sid,question,enable_visualization=False)
    query=next(a.query for a in m.attachments if a.query is not None)
    answer=next(a.text.content for a in m.attachments if a.text is not None and str(a.text.purpose).endswith('ANSWER'))
    print(json.dumps({'question':question,'status':str(m.status),'conversation_id':m.conversation_id,'statement_id':query.statement_id,'executed_row_count':query.query_result_metadata.row_count,'generated_sql':query.query,'answer_from_executed_result':answer},indent=2,ensure_ascii=False),flush=True)
PY
{
  "question": "Top 5 products by revenue",
  "status": "MessageStatus.COMPLETED",
  "conversation_id": "01f1be762f4d1a26a9f7f8f84d4a3c98",
  "statement_id": "01f1be76-33e5-1a32-a978-8f095db2cf5d",
  "executed_row_count": 5,
  "generated_sql": "WITH product_revenue AS (\n  SELECT\n    `p`.`name`,\n    SUM(`l`.`quantity` * `l`.`unit_price_eur`) AS `revenue_eur`\n  FROM `nikks_fevm_workspace_7405607030687545`.`techsummit`.`fact_purchase_line` AS `l`\n  INNER JOIN `nikks_fevm_workspace_7405607030687545`.`techsummit`.`dim_product` AS `p`\n    ON `l`.`product_id` = `p`.`product_id`\n  WHERE `p`.`name` IS NOT NULL\n  GROUP BY `p`.`name`\n), ranked_products AS (\n  SELECT\n    `name`,\n    `revenue_eur`,\n    RANK() OVER (ORDER BY `revenue_eur` DESC) AS `product_rank`\n  FROM product_revenue\n)\nSELECT\n  `name`,\n  `revenue_eur`\nFROM ranked_products\nWHERE `product_rank` <= 5\nORDER BY `revenue_eur` DESC, `name` ASC;",
  "answer_from_executed_result": "Top 5 products by revenue in the **techsummit demo dataset** are shown below, with all figures in **EUR**.\n\n- **GBH 18V-26 F** — **EUR 14,023.0**\n- **GBH 2-26** — **EUR 1,752.0**\n- **GSB 18V-90 C** — **EUR 996.0**\n- **GWS 22-230 JH** — **EUR 945.0**\n- **GST 18V-LI S** — **EUR 845.0**\n\nAcross these 5 products, **GBH 18V-26 F** is the clear leader, generating far more revenue than the other top-selling products in the dataset."
}
{
  "question": "Which 18V tool has the highest torque, and how well is it selling?",
  "status": "MessageStatus.COMPLETED",
  "conversation_id": "01f1be763b9e13e38bdf526549da77f1",
  "statement_id": "01f1be76-40af-15ad-a26f-a6e92df68e92",
  "executed_row_count": 1,
  "generated_sql": "WITH product_sales AS (\n  SELECT\n    `p`.`name`,\n    `s`.`max_torque_nm`,\n    `s`.`battery_platform`,\n    COALESCE(SUM(`l`.`quantity`), 0) AS `units_sold`\n  FROM `nikks_fevm_workspace_7405607030687545`.`techsummit`.`idp_product_specs` AS `s`\n  INNER JOIN `nikks_fevm_workspace_7405607030687545`.`techsummit`.`dim_product` AS `p`\n    ON `s`.`model_name` = `p`.`name`\n  LEFT JOIN `nikks_fevm_workspace_7405607030687545`.`techsummit`.`fact_purchase_line` AS `l`\n    ON `l`.`product_id` = `p`.`product_id`\n  WHERE `s`.`battery_platform` IS NOT NULL\n    AND `s`.`max_torque_nm` IS NOT NULL\n    AND `s`.`battery_platform` ILIKE '%18V%'\n  GROUP BY `p`.`name`, `s`.`max_torque_nm`, `s`.`battery_platform`\n), ranked AS (\n  SELECT\n    `name`,\n    `max_torque_nm`,\n    `battery_platform`,\n    `units_sold`,\n    RANK() OVER (ORDER BY `max_torque_nm` DESC) AS `torque_rank`\n  FROM product_sales\n)\nSELECT\n  `name`,\n  `max_torque_nm`,\n  `battery_platform`,\n  `units_sold`\nFROM ranked\nWHERE `torque_rank` <= 1\nORDER BY `max_torque_nm` DESC, `name` ASC;",
  "answer_from_executed_result": "In the techsummit demo dataset, the **PSB 1800 LI-2** on the **18V Li-Ion** platform has the highest torque at **150.0 Nm**. Based on the same techsummit demo dataset, **PSB 1800 LI-2** has sold **1 unit**."
}
```

