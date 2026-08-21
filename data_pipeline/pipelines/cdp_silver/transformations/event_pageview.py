"""Silver: GA4 pageview events."""

from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from _shared import EVENT_SCHEMA, SOURCE_TABLE


def parsed_events():
    """Stream `gtm_events` with `eventData` decoded into the `ed` struct."""
    return (
        spark.readStream.option("ignoreDeletes", "true").table(SOURCE_TABLE)
             .withColumn("ed", F.from_json("eventData", EVENT_SCHEMA))
    )


@dp.table(
    name="event_pageview",
    comment="GA4 pageview events. One row per page load.",
    table_properties={"quality": "silver"},
)
def event_pageview():
    return (
        parsed_events()
           .filter(F.col("event_name") == "page_view")
           .select(
               (F.col("ingestion_time") / 1000).cast("timestamp").alias("ingest_timestamp"),
               F.to_timestamp(F.col("ed.timestamp")).alias("source_timestamp"),
               F.col("ed.event_name").alias("event_name"),
               F.col("ed.event_id").alias("event_id"),
               F.col("ed.client_id").alias("client_id"),
               F.col("ed.user_id").alias("user_id"),
               F.col("ed.ga_session_id").alias("ga_session_id"),
               F.col("ed.ga_session_number").alias("ga_session_number"),
               F.col("ed.page_location").alias("page_location"),
               F.col("ed.page_referrer").alias("page_referrer"),
               F.col("ed.page_title").alias("page_title"),
               F.col("ed.language").alias("language"),
               F.col("ed.screen_resolution").alias("screen_resolution"),
               F.col("ed.client_hints.architecture").alias("device_architecture"),
               F.col("ed.client_hints.bitness").alias("device_bitness"),
               F.col("ed.client_hints.platform").alias("device_platform"),
               F.col("ed.client_hints.platform_version").alias("device_platform_version"),
               F.col("ed.client_hints.mobile").alias("device_mobile"),
               F.col("ed.client_hints.model").alias("device_model"),
               F.col("ed.client_hints.wow64").alias("device_wow64"),
               F.col("ed.ip_override").alias("ip_override"),
               F.col("ed.user_agent").alias("user_agent"),
               F.col("ed.event_location.country").alias("event_country"),
               F.col("ed.event_location.region").alias("event_region"),
               F.col("ed.`x-ga-gtm_version`").alias("ga_gtm_version"),
               F.col("ed.`x-ga-measurement_id`").alias("ga_measurement_id"),
               F.col("ed.`x-ga-mp2-seg`").alias("ga_mp2_seg"),
               F.col("ed.`x-ga-page_id`").alias("ga_page_id"),
               F.col("ed.`x-ga-protocol_version`").alias("ga_protocol_version"),
               F.col("ed.`x-ga-request_count`").alias("ga_request_count"),
               F.col("ed.`x-ga-tfd`").alias("ga_tfd"),
               F.col("gtm_container_id"),
           )
    )
