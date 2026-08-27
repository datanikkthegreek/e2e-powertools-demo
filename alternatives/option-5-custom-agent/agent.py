import argparse
import json
import os
import re

from databricks.sdk import WorkspaceClient

CATALOG_SCHEMA = "nikks_fevm_workspace_7405607030687545.techsummit"
INDEX_NAME = f"{CATALOG_SCHEMA}.option5_manual_index"
MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct")
WAREHOUSE_ID = os.environ["WAREHOUSE_ID"]

w = WorkspaceClient()

SCHEMA = """
dim_product(product_id, name, category, price_eur)
dim_customer(customer_id, city, country, signup_date)
fact_purchase(purchase_id, customer_id, cart_id, created_at, total_eur)
fact_purchase_line(purchase_line_id, purchase_id, product_id, quantity, unit_price_eur)
event_view_item(ingest_timestamp, user_id, ga_session_id, product_id)
event_add_to_cart(source_timestamp, user_id, cart_id, product_id, cart_action, quantity_delta)
idp_product_specs(model_name, voltage_v, max_torque_nm, no_load_rpm, weight_kg, battery_platform)
"""


def ask_model(system: str, user: str) -> str:
    response = w.serving_endpoints.query(
        name=MODEL_ENDPOINT,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return response.choices[0].message.content


def analytics(question: str) -> dict:
    sql = ask_model(
        f"Write one read-only Databricks SQL query over {CATALOG_SCHEMA}.\nSchema:\n{SCHEMA}\n"
        "Return SQL only. Use fully qualified table names. Limit detail results to 20 rows.",
        question,
    )
    sql = re.sub(r"^```(?:sql)?|```$", "", sql.strip(), flags=re.IGNORECASE).strip()
    if not re.match(r"^(SELECT|WITH)\b", sql, re.IGNORECASE) or ";" in sql:
        raise ValueError("Model did not return one read-only query")
    result = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=sql,
        wait_timeout="30s",
    )
    return {"sql": sql, "rows": result.result.data_array if result.result else []}


def manuals(question: str) -> list:
    result = w.vector_search_indexes.query_index(
        index_name=INDEX_NAME,
        columns=["chunk_to_retrieve", "source_path"],
        query_text=question,
        query_type="HYBRID",
        num_results=5,
    )
    return result.result.data_array if result.result else []


def business_context() -> dict:
    return {
        "currency": "EUR",
        "dataset": "small techsummit demo dataset",
        "signup_date": "unavailable; all values are null",
    }


def answer(question: str) -> str:
    service_words = {"how", "safety", "maintain", "maintenance", "error", "repair", "warranty", "bit"}
    analytics_words = {"revenue", "sales", "sold", "purchase", "conversion", "customer", "country", "top"}
    words = set(re.findall(r"[a-z]+", question.lower()))
    evidence = {"business_context": business_context()}

    if words & analytics_words:
        evidence["analytics"] = analytics(question)
    if words & service_words or not words & analytics_words:
        evidence["manuals"] = manuals(question)

    return ask_model(
        "You are a Bosch Power Tools demo assistant. Answer only from the supplied tool evidence. "
        "Cite manual source paths, label demo analytics as EUR, and say when evidence is insufficient.",
        f"Question: {question}\nTool evidence:\n{json.dumps(evidence, default=str)}",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    args = parser.parse_args()
    print(answer(args.question))

