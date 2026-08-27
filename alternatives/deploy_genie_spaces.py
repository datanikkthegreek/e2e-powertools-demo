import copy
import json
import uuid
from pathlib import Path

from databricks.sdk import WorkspaceClient

WAREHOUSE_ID = "a8384833e450ec4e"
SOURCE = Path(__file__).parents[1] / "etl/src/bosch_powertools_analytics.geniespace.json"
FUNCTION_NAME = "nikks_fevm_workspace_7405607030687545.techsummit.search_product_manuals"

SPACES = {
    "option2": "Bosch Power Tools — Option 2 Analytics",
    "option3": "Bosch Power Tools — Option 3 Analytics",
    "option4": "Bosch Power Tools — Option 4 Analytics + Manuals",
}


def definition(option: str) -> dict:
    payload = copy.deepcopy(json.loads(SOURCE.read_text()))
    payload["data_sources"].pop("volumes", None)
    if option == "option4":
        payload["instructions"]["sql_functions"] = [{
            "id": uuid.uuid5(uuid.NAMESPACE_URL, FUNCTION_NAME).hex,
            "identifier": FUNCTION_NAME,
        }]
    return payload


def deploy(options: list[str]) -> None:
    w = WorkspaceClient(profile="FEVM")
    existing = {space.title: space for space in w.genie.list_spaces().spaces}
    for option in options:
        title = SPACES[option]
        serialized = json.dumps(definition(option))
        current = existing.get(title)
        if current:
            space = w.genie.update_space(
                space_id=current.space_id,
                title=title,
                warehouse_id=WAREHOUSE_ID,
                serialized_space=serialized,
            )
            action = "updated"
        else:
            space = w.genie.create_space(
                warehouse_id=WAREHOUSE_ID,
                serialized_space=serialized,
                title=title,
                description=f"Alternative architecture demo: {option}",
            )
            action = "created"
        print(f"{option.upper()}_GENIE_SPACE_ID={space.space_id} ({action})")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("options", nargs="+", choices=SPACES)
    deploy(parser.parse_args().options)
