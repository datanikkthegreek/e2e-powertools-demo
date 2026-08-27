from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound
from databricks.sdk.service.vectorsearch import (
    DeltaSyncVectorIndexSpecRequest,
    EmbeddingSourceColumn,
    EndpointType,
    PipelineType,
    VectorIndexType,
)

ENDPOINT_NAME = "powertools-option5-ai-search"
INDEX_NAME = "nikks_fevm_workspace_7405607030687545.techsummit.option5_manual_index"
SOURCE_TABLE = "nikks_fevm_workspace_7405607030687545.techsummit.option5_manual_chunks"

w = WorkspaceClient(profile="FEVM")

if not any(e.name == ENDPOINT_NAME for e in w.vector_search_endpoints.list_endpoints()):
    w.vector_search_endpoints.create_endpoint(name=ENDPOINT_NAME, endpoint_type=EndpointType.STANDARD)
    print(f"Created endpoint {ENDPOINT_NAME}; wait until ONLINE, then rerun.")
    raise SystemExit(0)

try:
    w.vector_search_indexes.get_index(index_name=INDEX_NAME)
except NotFound:
    w.vector_search_indexes.create_index(
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

w.vector_search_indexes.sync_index(index_name=INDEX_NAME)
print(f"AI_SEARCH_INDEX={INDEX_NAME}")
print(w.vector_search_indexes.get_index(index_name=INDEX_NAME))
