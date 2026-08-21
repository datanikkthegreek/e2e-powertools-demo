"""Silver: custom abandon_cart events. Cart-abandonment fact for the CDP."""

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
    name="event_abandon_cart",
    comment="Custom abandon_cart events. One row per user-triggered cart abandonment; items array carries cart contents at abandonment time.",
    table_properties={"quality": "silver"},
)
def event_abandon_cart():
    return (
        parsed_events()
           .filter(F.col("event_name") == "abandon_cart")
           .select(
               *COMMON_COLS,
               F.col("ed.cart_id").alias("cart_id"),
               F.col("ed.currency").alias("currency"),
               F.col("ed.value").alias("value"),
               F.col("ed.items").alias("items"),
               F.col("ed.email").alias("email"),
               F.col("ed.first_name").alias("first_name"),
               F.col("ed.surname").alias("surname"),
           )
    )
