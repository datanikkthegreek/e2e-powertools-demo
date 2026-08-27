#!/usr/bin/env bash
set -euo pipefail

: "${KA_ID:?Run create_knowledge_assistant.py and export KA_ID}"
: "${GENIE_SPACE_ID:?Export the existing Genie space id}"

PROFILE="${DATABRICKS_CONFIG_PROFILE:-FEVM}"

SUPERVISOR=$(databricks supervisor-agents create-supervisor-agent \
  "powertools-option2-supervisor" \
  --description "Routes Bosch analytics and manual questions" \
  --instructions "Use analytics for quantitative questions, manuals for service questions, and both for blended questions." \
  --profile "$PROFILE")

SUPERVISOR_NAME=$(printf '%s' "$SUPERVISOR" | jq -r .name)

databricks supervisor-agents create-tool "$SUPERVISOR_NAME" analytics --json "{
  \"tool_type\": \"genie_space\",
  \"description\": \"Revenue, customers, funnel, purchases and product specification analytics\",
  \"genie_space\": {\"id\": \"$GENIE_SPACE_ID\"}
}" --profile "$PROFILE"

databricks supervisor-agents create-tool "$SUPERVISOR_NAME" manuals --json "{
  \"tool_type\": \"knowledge_assistant\",
  \"description\": \"Product operation, safety, maintenance and troubleshooting from Bosch manuals\",
  \"knowledge_assistant\": {\"knowledge_assistant_id\": \"$KA_ID\"}
}" --profile "$PROFILE"

printf 'SUPERVISOR_NAME=%s\n' "$SUPERVISOR_NAME"

