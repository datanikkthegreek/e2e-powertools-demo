"""Silver: GA4 account_deleted events. Account-deletion fact for the CDP."""

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
    name="event_account_deleted",
    comment="GA4 account_deleted events. Self-service account deletions; mirrors event_sign_up shape.",
    table_properties={"quality": "silver"},
)
def event_account_deleted():
    return (
        parsed_events()
           .filter(F.col("event_name") == "account_deleted")
           .select(
               (F.col("ingestion_time") / 1000).cast("timestamp").alias("ingest_timestamp"),
               F.to_timestamp(F.col("ed.timestamp")).alias("source_timestamp"),
               F.col("ed.user_id").alias("user_id"),
               F.col("ed.method").alias("method"),
               F.concat(F.coalesce(F.col("ed.name_surname"), F.lit("")),F.coalesce(F.col("ed.domain"), F.lit("")),).alias("email"),
               F.col("ed.first_name").alias("first_name"),
               F.col("ed.surname").alias("surname"),
               F.col("ed.city").alias("city"),
               F.col("ed.country").alias("country"),
           )
    )
