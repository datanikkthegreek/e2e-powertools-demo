# Bosch Power Tools Analytics dashboard evidence

- Dashboard: **Bosch Power Tools Analytics**
- Dashboard ID: `01f1b65f3a751391a18496f5fe60915e`
- Published URL: https://adb-7405607030687545.5.azuredatabricks.net/dashboardsv3/01f1b65f3a751391a18496f5fe60915e/published
- Warehouse: `a8384833e450ec4e`
- Evidence captured: 2026-10-02 with the `FEVM` profile using `databricks experimental aitools tools query`

Every dataset query exported in `../etl/src/bosch_power_tools_analytics.lvdash.json`
was executed against the dashboard warehouse. Results below are the actual CLI
output rendered as tables.

## Total Orders (`total_orders`)

```sql
SELECT
  COUNT(*) AS total_orders
FROM
  nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase
```

| total_orders |
| ---: |
| 36 |

## Revenue by Product (`revenue_by_product`)

```sql
SELECT
  p.name AS product_name,
  ROUND(SUM(pl.quantity * pl.unit_price_eur), 2) AS revenue_eur
FROM
  nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase_line pl
    JOIN nikks_fevm_workspace_7405607030687545.techsummit.dim_product p
      ON pl.product_id = p.product_id
GROUP BY
  p.name
ORDER BY
  revenue_eur DESC
```

| product_name | revenue_eur |
| --- | ---: |
| GBH 18V-26 F | 14023.0 |
| GBH 2-26 | 1752.0 |
| GSB 18V-90 C | 996.0 |
| GWS 22-230 JH | 945.0 |
| GST 18V-LI S | 845.0 |
| GWS 18V-10 | 597.0 |
| GSR 18V-55 | 189.0 |
| PSB 1800 LI-2 | 139.0 |
| PWS 700-115 | 118.0 |
| PSR 1080 LI | 79.0 |

## Revenue by Country (`revenue_by_country`)

```sql
SELECT
  c.country,
  ROUND(SUM(fp.total_eur), 2) AS revenue_eur
FROM
  nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase fp
    JOIN nikks_fevm_workspace_7405607030687545.techsummit.dim_customer c
      ON fp.customer_id = c.customer_id
GROUP BY
  c.country
ORDER BY
  revenue_eur DESC
```

| country | revenue_eur |
| --- | ---: |
| Switzerland | 10548.0 |
| Germany | 6225.0 |
| Netherlands | 1963.0 |
| Austria | 947.0 |

## Total Revenue (`total_revenue`)

```sql
SELECT
  ROUND(SUM(total_eur), 2) AS total_revenue_eur
FROM
  nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase
```

| total_revenue_eur |
| ---: |
| 19683.0 |

## Total Product Views (`total_views`)

```sql
SELECT
  COUNT(*) AS total_views
FROM
  nikks_fevm_workspace_7405607030687545.techsummit.event_view_item
```

| total_views |
| ---: |
| 3030 |

## Views by Product (`views_by_product`)

```sql
SELECT
  p.name AS product_name,
  COUNT(*) AS view_count
FROM
  nikks_fevm_workspace_7405607030687545.techsummit.event_view_item ev
    JOIN nikks_fevm_workspace_7405607030687545.techsummit.dim_product p
      ON ev.product_id = p.product_id
GROUP BY
  p.name
ORDER BY
  view_count ASC
```

| product_name | view_count |
| --- | ---: |
| GSB 18V-90 C | 235 |
| GSR 12V-35 | 240 |
| PWS 700-115 | 241 |
| PSB 1800 LI-2 | 244 |
| PSR 1080 LI | 247 |
| GSR 18V-55 | 255 |
| GST 18V-LI S | 255 |
| GBH 2-26 | 259 |
| GWS 18V-10 | 262 |
| PBH 2100 RE | 263 |
| GWS 22-230 JH | 263 |
| GBH 18V-26 F | 265 |

## Total Cart Actions (`total_cart`)

```sql
SELECT
  COUNT(*) AS total_cart_actions
FROM
  nikks_fevm_workspace_7405607030687545.techsummit.event_add_to_cart
```

| total_cart_actions |
| ---: |
| 859 |

## Product Catalog (`product_catalog`)

```sql
SELECT
  p.name,
  p.category,
  p.price_eur,
  s.voltage_v,
  s.max_torque_nm,
  s.weight_kg,
  s.battery_platform
FROM
  nikks_fevm_workspace_7405607030687545.techsummit.dim_product p
    LEFT JOIN nikks_fevm_workspace_7405607030687545.techsummit.idp_product_specs s
      ON p.name = s.model_name
ORDER BY
  p.name
```

| name | category | price_eur | voltage_v | max_torque_nm | weight_kg | battery_platform |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| GBH 18V-26 F | Brushless cordless rotary hammer with SDS-plus quick-change. | 379.0 | 18.0 | 2.0 | 2.2 | 18V |
| GBH 2-26 | Rotary hammer 800W for drilling and chiselling concrete. | 219.0 |  | 2.7 | 2.6 | corded |
| GSB 18V-90 C | Powerful cordless combi drill with hammer function for masonry. | 249.0 | 18.0 | 106.0 | 2.8 | 18V |
| GSR 12V-35 | Compact 12V cordless drill/driver for tight workspaces. | 129.0 | 12.0 | 35.0 | 1.3 | 12V |
| GSR 18V-55 | Cordless 18V drill/driver with brushless motor for everyday tasks. | 189.0 | 18.0 | 63.0 | 2.2 | 18V |
| GST 18V-LI S | Cordless jigsaw with tool-free blade change. | 169.0 | 18.0 |  | 2.3 | 18V |
| GWS 18V-10 | Brushless 125mm cordless angle grinder with anti-kickback. | 199.0 | 18.0 |  | 1.9 | 18V |
| GWS 22-230 JH | Heavy-duty 2200W angle grinder with 230mm disc. | 189.0 |  |  | 6.2 | corded |
| PBH 2100 RE | Compact corded rotary hammer for occasional masonry work. | 99.0 |  | 2.2 | 2.5 | corded |
| PSB 1800 LI-2 | 18V cordless impact drill with two-speed gearbox. | 139.0 | 18.0 | 150.0 | 1.9 | 18V Li-Ion |
| PSR 1080 LI | Lightweight 10.8V drill driver for home DIY projects. | 79.0 | 10.8 | 21.0 | 0.9 | 10.8V |
| PWS 700-115 | Entry-level 700W angle grinder with 115mm disc. | 59.0 |  |  | 2.0 | corded |

## Cart by Product (`cart_by_product`)

```sql
SELECT
  p.name AS product_name,
  COUNT(*) AS cart_count
FROM
  nikks_fevm_workspace_7405607030687545.techsummit.event_add_to_cart ac
    JOIN nikks_fevm_workspace_7405607030687545.techsummit.dim_product p
      ON ac.product_id = p.product_id
GROUP BY
  p.name
ORDER BY
  cart_count ASC
```

| product_name | cart_count |
| --- | ---: |
| PWS 700-115 | 53 |
| GSB 18V-90 C | 55 |
| PSB 1800 LI-2 | 60 |
| GST 18V-LI S | 68 |
| GWS 22-230 JH | 71 |
| GSR 12V-35 | 72 |
| PBH 2100 RE | 73 |
| PSR 1080 LI | 77 |
| GWS 18V-10 | 79 |
| GSR 18V-55 | 82 |
| GBH 2-26 | 82 |
| GBH 18V-26 F | 86 |

## Purchases per Day (`purchases_per_day`)

```sql
SELECT
  DATE(created_at) AS purchase_day,
  COUNT(*) AS purchase_count,
  ROUND(SUM(total_eur), 2) AS revenue_eur
FROM
  nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase
GROUP BY
  DATE(created_at)
ORDER BY
  purchase_day
```

| purchase_day | purchase_count | revenue_eur |
| --- | ---: | ---: |
| 2026-07-14 | 1 | 896.0 |
| 2026-07-22 | 1 | 587.0 |
| 2026-07-23 | 1 | 758.0 |
| 2026-07-27 | 1 | 627.0 |
| 2026-07-29 | 1 | 577.0 |
| 2026-08-03 | 1 | 118.0 |
| 2026-08-04 | 1 | 338.0 |
| 2026-08-06 | 1 | 947.0 |
| 2026-08-17 | 2 | 627.0 |
| 2026-08-21 | 1 | 379.0 |
| 2026-09-02 | 1 | 1895.0 |
| 2026-09-26 | 4 | 2144.0 |
| 2026-09-27 | 5 | 3370.0 |
| 2026-09-28 | 5 | 2123.0 |
| 2026-09-29 | 8 | 3160.0 |
| 2026-10-02 | 2 | 1137.0 |

## Sales by Selected Date (`sales_by_date`)

```sql
SELECT
  ROUND(SUM(total_eur), 2) AS revenue_eur
FROM
  nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase
WHERE
  (
    :selected_date IS NULL
    OR array_contains(:selected_date, DATE(created_at))
  )
```

The exported dashboard defines `selected_date` as a `MULTI DATE` parameter
with default selection `2026-09-29`. The SQL Statement Execution API used by
the CLI does not accept an `ARRAY<DATE>` marker type, so the execution replaced
both `:selected_date` markers with the equivalent
`array(DATE '2026-09-29')` literal.

| revenue_eur |
| ---: |
| 3160.0 |
