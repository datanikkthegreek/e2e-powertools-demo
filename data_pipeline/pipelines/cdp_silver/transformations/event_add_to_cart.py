"""Silver: GA4 add_to_cart events."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F

from _shared import COMMON_COLS, EVENT_SCHEMA, SOURCE_TABLE


def parsed_events():
    """Stream `gtm_events` with `eventData` decoded into the `ed` struct."""
    return (
        spark.readStream.option("ignoreDeletes", "true").table(SOURCE_TABLE)
             .withColumn("ed", F.from_json("eventData", EVENT_SCHEMA))
    )


@dp.table(
    name="event_add_to_cart",
    comment="GA4 add_to_cart events. One row per item-added-to-cart action; the items array carries the SKU and quantity added.",
    table_properties={"quality": "silver"},
)
def event_add_to_cart():
    return (
        parsed_events()
           .filter(F.col("event_name") == "add_to_cart")
           .select(
               (F.col("ingestion_time") / 1000).cast("timestamp").alias("ingest_timestamp"),
               F.to_timestamp(F.col("ed.timestamp")).alias("source_timestamp"),
               F.col("ed.user_id").alias("user_id"),
               F.col("ed.cart_id").alias("cart_id"),
               F.col("ed.item_id").alias("item_id"),
               F.col("ed.item_name").alias("item_name"),
               F.col("ed.price").alias("price"),
               F.col("ed.previous_quantity").alias("previous_quantity"),
               F.col("ed.new_quantity").alias("new_quantity"),
               F.col("ed.quantity_delta").alias("quantity_delta"),
               F.col("ed.cart_action").alias("cart_action"),
               F.col("ed.currency").alias("currency")
           )
    )