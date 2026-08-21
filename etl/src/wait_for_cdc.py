"""CDC readiness gate for the powertools build job.

The wal2delta sync (../resources/sync.yml) is a CONTINUOUS resource, so it can't
be a task in this job — but every downstream task reads what it produces. Both
`seed_gtm_events` (reads `lb_products_history`) and `cdc_to_current` (reads all
four `lb_*_history` change-logs) will silently produce empty/partial output if
they run before the sync has landed its first rows.

This task is the job's first node: it polls until ALL required history tables
both EXIST and are POPULATED (at least one row), or fails after a timeout so the
run stops loudly instead of building empty Genie tables.

Run as a Databricks job task (the wait_for_cdc task in ../resources/job_build.yml):
    wait_for_cdc.py --catalog <cat> --schema <schema>
"""

from __future__ import annotations

import argparse
import json
import time

from pyspark.sql import SparkSession

# The four Lakebase change-logs the downstream tasks read (see sync.yml).
REQUIRED_HISTORY_TABLES = [
    "lb_products_history",
    "lb_accounts_history",
    "lb_purchases_history",
    "lb_purchase_lines_history",
]


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Wait until the CDC history tables are populated.")
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--timeout-seconds", type=int, default=1800)
    p.add_argument("--poll-interval-seconds", type=int, default=30)
    return p.parse_args()


def _is_populated(spark: SparkSession, fqn: str) -> bool:
    """True when the table exists AND has at least one row.

    A missing table raises (AnalysisException on classic, its Spark Connect
    equivalent on serverless); treat any read failure as not-yet-ready rather
    than an error, since the continuous sync may not have created it yet.
    """
    try:
        return spark.table(fqn).limit(1).count() > 0
    except Exception:
        return False


def main() -> None:
    args = _parse_args()
    spark = SparkSession.builder.getOrCreate()

    targets = [f"{args.catalog}.{args.schema}.{t}" for t in REQUIRED_HISTORY_TABLES]
    deadline = time.monotonic() + args.timeout_seconds

    while True:
        pending = [fqn for fqn in targets if not _is_populated(spark, fqn)]
        if not pending:
            print(json.dumps({"status": "ready", "tables": targets}))
            return
        if time.monotonic() >= deadline:
            raise SystemExit(
                "CDC readiness gate timed out after "
                f"{args.timeout_seconds}s. Not yet populated: {pending}. "
                "Ensure the continuous sync (../resources/sync.yml) is running "
                "and the Lakebase OLTP tables have been seeded (open the webshop once)."
            )
        print(
            json.dumps(
                {"status": "waiting", "pending": pending, "poll_in_seconds": args.poll_interval_seconds}
            )
        )
        time.sleep(args.poll_interval_seconds)


if __name__ == "__main__":
    main()
