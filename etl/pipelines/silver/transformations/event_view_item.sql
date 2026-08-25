-- Silver: GA4 view_item events (product detail page views).
--
-- Streams the raw gtm_events table and decodes only the eventData fields this
-- table needs. Table + source are referenced by bare name so they resolve in
-- the pipeline's own configured catalog/schema (see etl/resources/pipeline_silver.yml).
-- Downstream (etl/src/key_normalize.sql) reads product_id / user_id /
-- ga_session_id; those are the load-bearing columns.
CREATE OR REFRESH STREAMING TABLE event_view_item (
  ingest_timestamp TIMESTAMP                                                                                           COMMENT 'Timestamp when the event was ingested into the data platform (UTC). Derived from the raw ingestion_time epoch.',
  user_id          STRING                                                                                              COMMENT 'Unique identifier for the user who viewed the product. Ties behavioral events to dim_customer via downstream key normalization.',
  ga_session_id    STRING                                                                                              COMMENT 'Google Analytics session identifier. Groups page views within a single browsing session for sessionization analysis.',
  product_id       STRING    COMMENT 'Canonical product identifier viewed on the page. Foreign key to dim_product.product_id. Extracted from the GA4 items array (always contains exactly one item per view_item event).',
  CONSTRAINT fk_event_view_item_product FOREIGN KEY (product_id) REFERENCES dim_product(product_id)
)
  COMMENT 'GA4 product detail page view event stream. One row per product page view action by a user. Grain: one user + one product view event. Use to analyze product discovery, browsing patterns, and top-of-funnel engagement. Join to dim_product on product_id for product attributes.'
AS
WITH parsed AS (
  SELECT
    ingestion_time,
    from_json(
      eventData,
      'STRUCT<user_id: STRING, ga_session_id: STRING, items: ARRAY<STRUCT<item_id: STRING, item_name: STRING, price: DOUBLE, currency: STRING, quantity: INT>>>'
    ) AS ed
  FROM STREAM(gtm_events)
  WHERE event_name = 'view_item'
)
SELECT
  CAST(ingestion_time / 1000 AS TIMESTAMP) AS ingest_timestamp,
  ed.user_id                               AS user_id,
  ed.ga_session_id                         AS ga_session_id,
  ed.items[0].item_id                      AS product_id
FROM parsed;
