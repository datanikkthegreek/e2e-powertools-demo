import sys
import time
from pathlib import Path

from databricks.sdk import WorkspaceClient

WAREHOUSE_ID = "a8384833e450ec4e"


def run(statement: str) -> None:
    w = WorkspaceClient(profile="FEVM")
    response = w.statement_execution.execute_statement(
        statement=statement,
        warehouse_id=WAREHOUSE_ID,
        wait_timeout="50s",
    )
    while response.status.state.value in {"PENDING", "RUNNING"}:
        print(f"{response.statement_id}: {response.status.state.value}", flush=True)
        time.sleep(10)
        response = w.statement_execution.get_statement(response.statement_id)
    if response.status.state.value != "SUCCEEDED":
        raise RuntimeError(f"{response.status.state}: {response.status.error}")
    print(f"{response.statement_id}: SUCCEEDED")


for filename in sys.argv[1:]:
    print(f"Running {filename}")
    text = Path(filename).read_text()
    for statement in (part.strip() for part in text.split(";")):
        if statement:
            run(statement)
