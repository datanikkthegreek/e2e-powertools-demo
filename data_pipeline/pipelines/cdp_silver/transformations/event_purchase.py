"""Silver: GA4 purchase events. The transaction fact table for the CDP.

Also projects two text columns (`subject`, `body`) used by the
`purchase_email_sink` in `sinks.py` to drive the order-confirmation Gmail
sink. Same pattern as `event_sign_up` — the email outbox is a 1:1 read of
the silver event table.
"""

from pyspark import pipelines as dp
from pyspark.sql import functions as F

from _shared import COMMON_COLS, EVENT_SCHEMA, SOURCE_TABLE


def parsed_events():
    """Stream `gtm_events` with `eventData` decoded into the `ed` struct."""
    return (
        spark.readStream.option("ignoreDeletes", "true").table(SOURCE_TABLE)
             .withColumn("ed", F.from_json("eventData", EVENT_SCHEMA))
    )

_ORDER_SUBJECT = "Your order at the Bosch Powertools Shop"

_ORDER_BODY_TEMPLATE = (
    "Hello %s %s,\n"
    "\n"
    "Thank you for your order at the Bosch Powertools Shop!\n"
    "\n"
    "Order ID:  %s\n"
    "Total:     %.2f %s\n"
    "\n"
    "Items:\n"
    "%s\n"
    "\n"
    "If anything looks wrong, simply reply to this email and we will fix it.\n"
    "\n"
    "Thanks for shopping with us,\n"
    "The Bosch Powertools Shop Team"
)


def _items_summary():
    """Render the `items` array as a newline-separated list of order lines."""
    return F.array_join(
        F.transform(
            F.col("items"),
            lambda item: F.format_string(
                "  - %d x %s @ %.2f %s",
                item.quantity,
                item.item_name,
                item.price,
                item.currency,
            ),
        ),
        "\n",
    )


def _order_body():
    """Build the order-confirmation body, null-safe."""
    return F.format_string(
        _ORDER_BODY_TEMPLATE,
        F.coalesce(F.col("first_name"),     F.lit("")),
        F.coalesce(F.col("surname"),        F.lit("")),
        F.coalesce(F.col("transaction_id"), F.lit("")),
        F.coalesce(F.col("value"),          F.lit(0.0)),
        F.coalesce(F.col("currency"),       F.lit("EUR")),
        F.coalesce(_items_summary(),        F.lit("")),
    )


@dp.table(
    name="event_purchase",
    comment="GA4 purchase events. Order-level transaction fact; line items are nested in the items array. Carries a ready-to-send order-confirmation subject and body.",
    table_properties={"quality": "silver"},
)
def event_purchase():
    return (
        parsed_events()
           .filter(F.col("event_name") == "purchase")
           .select(
               (F.col("ingestion_time") / 1000).cast("timestamp").alias("ingest_timestamp"),
               F.to_timestamp(F.col("ed.timestamp")).alias("source_timestamp"),
               F.col("ed.user_id").alias("user_id"),
               F.col("ed.cart_id").alias("cart_id"),
               F.col("ed.transaction_id").alias("transaction_id"),
               F.col("ed.currency").alias("currency"),
               F.col("ed.value").alias("value"),
               F.col("ed.items").alias("items"),
               F.concat(F.coalesce(F.col("ed.name_surname"), F.lit("")),F.coalesce(F.col("ed.domain"), F.lit("")),).alias("email"),
               F.col("ed.first_name").alias("first_name"),
               F.col("ed.surname").alias("surname"),
           )
           .withColumn("subject", F.lit(_ORDER_SUBJECT))
           .withColumn("body",    _order_body())
    )
