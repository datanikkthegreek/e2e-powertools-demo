"""Shared constants, JSON schema, and helpers for the powertools silver pipeline.

No `@dp.table` decorators live here — this module is imported by every
transformation file in the pipeline glob.
"""

from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    BooleanType,
    DoubleType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)
from databricks.sdk.runtime import spark

TABLE_CATALOG = spark.conf.get("pipeline.table_catalog")
TABLE_SCHEMA = spark.conf.get("pipeline.table_schema")


def table_name(name: str) -> str:
    """Return a fully-qualified table name in the configured pipeline namespace."""
    return f"{TABLE_CATALOG}.{TABLE_SCHEMA}.{name}"


SOURCE_TABLE = table_name("gtm_events")

ITEM_SCHEMA = StructType([
    StructField("item_id",   StringType()),
    StructField("item_name", StringType()),
    StructField("price",     DoubleType()),
    StructField("currency",  StringType()),
    StructField("quantity",  IntegerType()),
])

EVENT_SCHEMA = StructType([
    # ---- GA4 envelope ----
    StructField("client_id",            StringType()),
    StructField("engagement_time_msec", LongType()),
    StructField("event_name",           StringType()),
    StructField("event_id",             StringType()),
    StructField("event_location", StructType([
        StructField("country", StringType()),
        StructField("region",  StringType()),
    ])),
    StructField("ga_session_id",        StringType()),
    StructField("ga_session_number",    LongType()),
    StructField("ip_override",          StringType()),
    StructField("language",             StringType()),
    StructField("page_location",        StringType()),
    StructField("page_referrer",        StringType()),
    StructField("page_title",           StringType()),
    StructField("screen_resolution",    StringType()),
    StructField("timestamp",            StringType()),
    StructField("user_agent",           StringType()),
    StructField("x-ga-gtm_version",     StringType()),
    StructField("x-ga-measurement_id",  StringType()),
    StructField("x-ga-mp2-seg",         StringType()),
    StructField("x-ga-page_id",         LongType()),
    StructField("x-ga-protocol_version", StringType()),
    StructField("x-ga-request_count",   LongType()),
    StructField("x-ga-tfd",             LongType()),
    StructField("client_hints", StructType([
        StructField("architecture",     StringType()),
        StructField("bitness",          StringType()),
        StructField("platform",         StringType()),
        StructField("platform_version", StringType()),
        StructField("mobile",           BooleanType()),
        StructField("model",            StringType()),
        StructField("wow64",            BooleanType()),
    ])),
    # ---- Common overlay ----
    StructField("user_id", StringType()),
    StructField("cart_id", StringType()),
    # ---- Ecommerce overlay (view_item / add_to_cart / purchase) ----
    StructField("currency",       StringType()),
    StructField("item_id",        StringType()),
    StructField("item_name",      StringType()),
    StructField("price",          DoubleType()),
    StructField("item_quantity",  IntegerType()),
    StructField("previous_quantity", IntegerType()),
    StructField("new_quantity",      IntegerType()),
    StructField("quantity_delta",    IntegerType()),
    StructField("cart_action",       StringType()),
    StructField("value",          DoubleType()),
    StructField("tax",            DoubleType()),
    StructField("shipping",       DoubleType()),
    StructField("transaction_id", StringType()),
    StructField("items",          ArrayType(ITEM_SCHEMA)),
    # ---- Account overlay (sign_up / account_deleted) ----
    StructField("method",         StringType()),
    StructField("email",          StringType()),
    StructField("name_surname",   StringType()),
    StructField("domain",         StringType()),
    StructField("first_name",     StringType()),
    StructField("surname",        StringType()),
    StructField("city",           StringType()),
    StructField("country",        StringType()),
    StructField("web_input_data", StringType()),
])


# Envelope columns shared by every silver table. Order matches the legacy
# per-silver `_COMMON` list so downstream consumers see the same column
# order they did when bronze was materialized.
COMMON_COLS = [
    (F.col("ingestion_time") / 1000).cast("timestamp").alias("ingest_timestamp"),
    F.col("ed.event_id").alias("event_id"),
    F.col("ed.client_id").alias("client_id"),
    F.col("ed.user_id").alias("user_id"),
    F.col("ed.ga_session_id").alias("ga_session_id"),
    F.col("ed.ga_session_number").alias("ga_session_number"),
    F.col("ed.engagement_time_msec").alias("engagement_time_msec"),
    F.col("ed.page_location").alias("page_location"),
    F.col("ed.page_referrer").alias("page_referrer"),
    F.col("ed.page_title").alias("page_title"),
    F.col("ed.event_location.country").alias("country"),
    F.col("ed.event_location.region").alias("region"),
    F.col("ed.language").alias("language"),
    F.col("ed.screen_resolution").alias("screen_resolution"),
    F.col("ed.client_hints.platform").alias("device_platform"),
    F.col("ed.client_hints.platform_version").alias("device_platform_version"),
    F.col("ed.client_hints.mobile").alias("device_mobile"),
    F.col("ed.user_agent").alias("user_agent"),
    F.col("ed.ip_override").alias("ip_override"),
    F.col("gtm_container_id"),
]
