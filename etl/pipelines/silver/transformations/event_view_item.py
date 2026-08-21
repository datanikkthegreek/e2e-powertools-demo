"""Silver: GA4 view_item events (product detail page views)."""

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
    name="event_view_item",
    comment="GA4 view_item events. One row per product detail page view.",
    table_properties={"quality": "silver"},
)
def event_view_item():
    return (
        parsed_events()
           .filter(F.col("event_name") == "view_item")
           .select(
               *COMMON_COLS,
               F.col("ed.currency").alias("currency"),
               F.col("ed.value").alias("value"),
               F.col("ed.items").alias("items"),
           )
    )
