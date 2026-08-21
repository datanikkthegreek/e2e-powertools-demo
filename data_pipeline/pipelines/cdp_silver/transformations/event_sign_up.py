"""Silver: GA4 sign_up events. Account-creation fact for the CDP.

Also projects two text columns (`subject`, `body`) used by the
`send_mail_create_account` notebook to drive the Gmail streaming sink.
Kept here so the email outbox is a 1:1 read of the silver event table —
no extra downstream join needed.
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

_WELCOME_SUBJECT = "Your registration at the Bosch Powertools Shop"

_WELCOME_BODY_TEMPLATE = (
    "Hello %s %s,\n"
    "\n"
    "Thank you for registering at the Bosch Powertools Shop!\n"
    "\n"
    "Here is the information you provided at sign-up:\n"
    "\n"
    "  Name:           %s %s\n"
    "  Email:          %s\n"
    "  City:           %s\n"
    "  Country:        %s\n"
    "  Sign-up method: %s\n"
    "\n"
    "If anything looks wrong, simply reply to this email and we will fix it.\n"
    "\n"
    "Welcome aboard,\n"
    "The Bosch Powertools Shop Team"
)


def _welcome_body():
    """Build the body text from the customer profile columns, null-safe."""
    name = F.coalesce(F.col("first_name"), F.lit(""))
    surname = F.coalesce(F.col("surname"), F.lit(""))
    email = F.coalesce(F.col("email"), F.lit(""))
    city = F.coalesce(F.col("city"), F.lit(""))
    country = F.coalesce(F.col("country"), F.lit(""))
    method = F.coalesce(F.col("method"), F.lit("form"))
    return F.format_string(
        _WELCOME_BODY_TEMPLATE,
        name, surname,
        name, surname,
        email, city, country, method,
    )


@dp.table(
    name="event_sign_up",
    comment=(
        "GA4 sign_up events. Captures the customer profile attributes at "
        "account creation plus a ready-to-send email subject and body."
    ),
    table_properties={"quality": "silver"},
)
def event_sign_up():
    return (
        parsed_events()
           .filter(F.col("event_name") == "sign_up")
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
           .withColumn("subject", F.lit(_WELCOME_SUBJECT))
           .withColumn("body",    _welcome_body())
    )
