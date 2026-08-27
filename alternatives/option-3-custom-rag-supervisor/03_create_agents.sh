#!/usr/bin/env bash
set -euo pipefail

: "${AI_SEARCH_INDEX:?Run 02_create_ai_search_index.py first}"
: "${GENIE_SPACE_ID:?Export the existing Genie space id}"

PROFILE="${DATABRICKS_CONFIG_PROFILE:-FEVM}"

KA=$(databricks knowledge-assistants create-knowledge-assistant \
  "powertools-option3-search-ka" \
  "Answers Bosch service questions using the custom AI Search index" \
  --profile "$PROFILE")
KA_NAME=$(printf '%s' "$KA" | jq -r .name)
KA_ID=${KA_NAME#knowledge-assistants/}

databricks knowledge-assistants create-knowledge-source "$KA_NAME" --json "{
  \"display_name\": \"custom-manual-search\",
  \"description\": \"Parsed and context-enriched Bosch manual chunks\",
  \"source_type\": \"index\",
  \"index\": {
    \"index_name\": \"$AI_SEARCH_INDEX\",
    \"text_col\": \"chunk_to_retrieve\",
    \"doc_uri_col\": \"source_path\"
  }
}" --profile "$PROFILE"

databricks knowledge-assistants sync-knowledge-sources "$KA_NAME" --profile "$PROFILE"

SUPERVISOR=$(databricks supervisor-agents create-supervisor-agent \
  "powertools-option3-supervisor" \
  --description "Routes analytics and custom-index manual questions" \
  --instructions "Use analytics for quantitative questions, manuals for service questions, and both for blended questions." \
  --profile "$PROFILE")
SUPERVISOR_NAME=$(printf '%s' "$SUPERVISOR" | jq -r .name)

databricks supervisor-agents create-tool "$SUPERVISOR_NAME" analytics --json "{
  \"tool_type\": \"genie_space\",
  \"description\": \"Revenue, funnel, purchase and product specification analytics\",
  \"genie_space\": {\"id\": \"$GENIE_SPACE_ID\"}
}" --profile "$PROFILE"

databricks supervisor-agents create-tool "$SUPERVISOR_NAME" manuals --json "{
  \"tool_type\": \"knowledge_assistant\",
  \"description\": \"Operation, safety, maintenance and troubleshooting from the custom manual index\",
  \"knowledge_assistant\": {\"knowledge_assistant_id\": \"$KA_ID\"}
}" --profile "$PROFILE"

printf 'KA_ID=%s\nSUPERVISOR_NAME=%s\n' "$KA_ID" "$SUPERVISOR_NAME"

