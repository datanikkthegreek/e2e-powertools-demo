from databricks.sdk import WorkspaceClient
from databricks.sdk.service.knowledgeassistants import FilesSpec, KnowledgeAssistant, KnowledgeSource

CATALOG = "nikks_fevm_workspace_7405607030687545"
SCHEMA = "techsummit"
VOLUME = "productmanuals"
DISPLAY_NAME = "powertools-option2-manuals-ka"

w = WorkspaceClient(profile="FEVM")
volume_path = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}/"

existing = next(
    (a for a in w.knowledge_assistants.list_knowledge_assistants() if a.display_name == DISPLAY_NAME),
    None,
)

if existing:
    ka_id = existing.name.split("/", 1)[-1]
else:
    ka = w.knowledge_assistants.create_knowledge_assistant(
        knowledge_assistant=KnowledgeAssistant(
            display_name=DISPLAY_NAME,
            description="Answers Bosch Power Tools service questions from product manuals.",
            instructions="Answer only from retrieved manuals. Cite the actual manual and do not guess.",
        )
    )
    ka_id = ka.name.split("/", 1)[-1]
    w.knowledge_assistants.create_knowledge_source(
        parent=f"knowledge-assistants/{ka_id}",
        knowledge_source=KnowledgeSource(
            display_name="powertools-manuals",
            description="Bosch operating manuals for the demo tools.",
            source_type="files",
            files=FilesSpec(path=volume_path),
        ),
    )

w.knowledge_assistants.sync_knowledge_sources(name=f"knowledge-assistants/{ka_id}")
print(f"KA_ID={ka_id}")
