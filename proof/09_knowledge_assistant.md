# Knowledge Assistant execution evidence

The Knowledge Assistant API returns its identity, endpoint, and files source. The serving endpoint reports `READY` (the current API's active/servable state spelling), and the source reports `UPDATED`.

## KA and source get

```console
$ python - <<'PY'
from databricks.sdk import WorkspaceClient
import json
w=WorkspaceClient(profile='FEVM')
for a in w.knowledge_assistants.list_knowledge_assistants():
    if (a.display_name or '').strip() == 'powertools-manuals-ka':
        print(json.dumps(a.as_dict(), indent=2))
        for s in w.knowledge_assistants.list_knowledge_sources(parent=a.name):
            print(json.dumps(s.as_dict(), indent=2))
PY
{
  "create_time": "2026-08-24T13:53:17.744Z",
  "creator": "nikolaos.servos@databricks.com",
  "description": "Answers questions about real Bosch power-tool operating manuals (safety, specifications, operation, battery/charging or mains, maintenance, troubleshooting, warranty) for the 12 demo power tools. RAG over the PDFs in the manuals/ Volume folder. A few tools are covered by their nearest-variant or family manual (e.g. psr-1080-li uses the Bosch PSB 1080 LI-2 booklet).",
  "display_name": "powertools-manuals-ka",
  "endpoint_name": "ka-44e78d1c-endpoint",
  "experiment_id": "1447594879287564",
  "id": "44e78d1c-c243-4def-b0e6-c27638d78c91",
  "instructions": "Answer only from the retrieved product manuals and always cite the source manual. Identify the specific tool model (e.g. GBH 2-26) the question is about. If a spec or fault code is not in the manuals, say so rather than guessing. A few tools are documented by their nearest-variant manual (e.g. psr-1080-li -> Bosch PSB 1080 LI-2); cite the actual manual retrieved.",
  "name": "knowledge-assistants/44e78d1c-c243-4def-b0e6-c27638d78c91"
}
{
  "create_time": "2026-08-25T16:48:43.786Z",
  "description": "Bosch power-tool operating manuals (PDFs) \u2014 safety, specs, operation, battery/mains, maintenance, troubleshooting, warranty.",
  "display_name": "powertools-pdf-manuals",
  "files": {
    "path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/productmanuals/"
  },
  "id": "ef383dfe-ff62-4029-92ea-7564b8f0a2c3",
  "knowledge_cutoff_time": "2026-08-25T16:48:43.786Z",
  "name": "knowledge-assistants/44e78d1c-c243-4def-b0e6-c27638d78c91/knowledge-sources/ef383dfe-ff62-4029-92ea-7564b8f0a2c3",
  "source_type": "files",
  "state": "UPDATED"
}
```

## Endpoint state

```console
$ databricks serving-endpoints get ka-44e78d1c-endpoint -p FEVM -o json | jq '{name, state}'
{
  "name": "ka-44e78d1c-endpoint",
  "state": {
    "config_update": "NOT_UPDATING",
    "ready": "READY"
  }
}
```

## Real grounded question and answer

```console
$ python - <<'PY'
from databricks.sdk import WorkspaceClient
import json
w=WorkspaceClient(profile='FEVM')
question='According to the Bosch GSB 18V-90 C operating manual, what should I do before carrying out any work on the power tool? Cite the manual.'
print('QUESTION:', question)
response=w.api_client.do('POST','/serving-endpoints/ka-44e78d1c-endpoint/invocations',body={'input':[{'role':'user','content':question}]})
print(json.dumps(response, indent=2, ensure_ascii=False))
PY
QUESTION: According to the Bosch GSB 18V-90 C operating manual, what should I do before carrying out any work on the power tool? Cite the manual.
{
  "tool_choice": null,
  "truncation": null,
  "id": null,
  "created_at": null,
  "error": null,
  "incomplete_details": null,
  "instructions": null,
  "metadata": null,
  "model": "kbqa_agent",
  "object": "response",
  "output": [
    {
      "type": "message",
      "id": "b9bc4748-9892-425e-804b-8f6039b61f3b",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "According to the ",
          "annotations": [],
          "logprobs": []
        },
        {
          "type": "output_text",
          "text": "Bosch GSB 18V-90 C operating manual, before carrying out any work on the power tool (e.g. maintenance, tool change etc.), you should remove the battery from the power tool. There is risk of injury from unintentionally pressing the on/off switch.",
          "annotations": [
            {
              "type": "url_citation",
              "url": "https://adb-7405607030687545.5.azuredatabricks.net/ajax-api/2.0/fs/files/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/productmanuals/gsb-18v-90-c.pdf#page=19:~:text=Changing%20the%20tool%20%28see%20figure%20A%29%0A%0Au%20Before%20carrying%20out%20any%20work%20on%20the%20power%20tool%20%28e.g.%0Amaintenance%2C%20tool%20change%20etc.%29%2C%20remove%20the%20battery%0Afrom%20the%20power%20tool.%20There%20is%20risk%20of%20injury%20from%20uninten-tionally%0Apressing%20the%20on/off%20switch.%0A",
              "title": "gsb-18v-90-c.pdf"
            }
          ],
          "logprobs": []
        }
      ]
    }
  ],
  "parallel_tool_calls": null,
  "temperature": null,
  "tools": null,
  "top_p": null,
  "max_output_tokens": null,
  "previous_response_id": null,
  "reasoning": null,
  "status": null,
  "text": null,
  "usage": null,
  "user": null,
  "custom_outputs": {
    "sources_used": true
  }
}
```

