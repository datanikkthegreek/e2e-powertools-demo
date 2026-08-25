-- Silver: GA4 add_to_cart events.
--
-- Streams the raw gtm_events table and decodes only the eventData fields this
-- table needs. Table + source are referenced by bare name so they resolve in
-- the pipeline's own configured catalog/schema (see etl/resources/pipeline_silver.yml).
-- Downstream (etl/src/key_normalize.sql) reads source_timestamp / user_id /
-- cart_id / product_id / quantity_delta / cart_action; the rest round out the
-- cart action for analytics.
CREATE OR REFRESH STREAMING TABLE event_add_to_cart (
  source_timestamp   TIMESTAMP COMMENT 'Original event timestamp from the GA4 client (UTC). When the add-to-cart action actually occurred on the user device.',
  user_id            STRING    COMMENT 'Unique identifier for the user who performed the cart action. Ties behavioral events to dim_customer (via downstream key normalization).',
  cart_id            STRING    COMMENT 'Unique identifier for the shopping cart. Links to fact_purchase.cart_id to connect browsing behavior to completed purchases.',
  product_id         STRING    COMMENT 'Canonical product identifier added to cart. Foreign key to dim_product.product_id. Sourced from the GA4 item_id field.',
  item_name          STRING    COMMENT 'Display name of the product at the time it was added to cart.',
  price              DOUBLE    COMMENT 'Unit price of the item in the transaction currency at time of cart addition.',
  previous_quantity  INT       COMMENT 'Quantity of this item in the cart before this action (0 if item was not previously in cart).',
  new_quantity       INT       COMMENT 'Quantity of this item in the cart after this action.',
  quantity_delta     INT       COMMENT 'Change in quantity (new_quantity minus previous_quantity). Positive = items added, negative = items removed.',
  cart_action        STRING    COMMENT 'Type of cart modification: add (new item), increase (more units), decrease (fewer units), or remove (item dropped).',
  currency           STRING    COMMENT 'ISO 4217 currency code for the price (e.g. EUR).'
)
  COMMENT 'GA4 add-to-cart event stream. One row per cart modification action (add, increase, decrease, or remove an item). Grain: one user + one item + one cart action timestamp. Use to analyze cart behavior, conversion funnels, and abandonment patterns. Joins downstream to fact_purchase via cart_id for purchase attribution.'
AS
WITH parsed AS (
  SELECT
    ingestion_time,
    from_json(
      eventData,
      'STRUCT<timestamp: STRING, user_id: STRING, cart_id: STRING, item_id: STRING, item_name: STRING, price: DOUBLE, previous_quantity: INT, new_quantity: INT, quantity_delta: INT, cart_action: STRING, currency: STRING>'
    ) AS ed
  FROM STREAM(gtm_events)
  WHERE event_name = 'add_to_cart'
)
SELECT
  to_timestamp(ed.timestamp)               AS source_timestamp,
  ed.user_id                               AS user_id,
  ed.cart_id                               AS cart_id,
  ed.item_id                               AS product_id,
  ed.item_name                             AS item_name,
  ed.price                                 AS price,
  ed.previous_quantity                     AS previous_quantity,
  ed.new_quantity                          AS new_quantity,
  ed.quantity_delta                        AS quantity_delta,
  ed.cart_action                           AS cart_action,
  ed.currency                              AS currency
FROM parsed;
