from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound
from databricks.sdk.service.vectorsearch import (
    DeltaSyncVectorIndexSpecRequest,
    EmbeddingSourceColumn,
    EndpointType,
    PipelineType,
    VectorIndexType,
)

ENDPOINT_NAME = "powertools-option3-ai-search"
INDEX_NAME = "nikks_fevm_workspace_7405607030687545.techsummit.option3_manual_index"
SOURCE_TABLE = "nikks_fevm_workspace_7405607030687545.techsummit.option3_manual_chunks"

w = WorkspaceClient(profile="FEVM")

endpoints = list(w.vector_search_endpoints.list_endpoints())
if not any(endpoint.name == ENDPOINT_NAME for endpoint in endpoints):
    w.vector_search_endpoints.create_endpoint(name=ENDPOINT_NAME, endpoint_type=EndpointType.STANDARD)
    print(f"Created endpoint {ENDPOINT_NAME}; wait until it is ONLINE, then rerun this script.")
    raise SystemExit(0)

try:
    index = w.vector_search_indexes.get_index(index_name=INDEX_NAME)
    print(f"Reusing index {INDEX_NAME}")
except NotFound:
    index = w.vector_search_indexes.create_index(
        name=INDEX_NAME,
        endpoint_name=ENDPOINT_NAME,
        primary_key="chunk_id",
        index_type=VectorIndexType.DELTA_SYNC,
        delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
            source_table=SOURCE_TABLE,
            embedding_source_columns=[EmbeddingSourceColumn(
                name="chunk_to_embed",
                embedding_model_endpoint_name="databricks-gte-large-en",
            )],
            pipeline_type=PipelineType.TRIGGERED,
            columns_to_sync=["chunk_id", "chunk_to_retrieve", "source_path"],
        ),
    )
    print(f"Created index {INDEX_NAME}")

w.vector_search_indexes.sync_index(index_name=INDEX_NAME)
status = w.vector_search_indexes.get_index(index_name=INDEX_NAME)
print(f"AI_SEARCH_ENDPOINT={ENDPOINT_NAME}")
print(f"AI_SEARCH_INDEX={INDEX_NAME}")
print(status)
