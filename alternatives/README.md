# Alternative architectures

These folders are isolated demo implementations. They do not change or import the productive `app/` and `etl/` code.

| Option | Architecture | Main choice |
|---|---|---|
| 2 | Managed KA + Supervisor + Genie | Easiest managed multi-agent path |
| 3 | AI Parse + AI Prep Search + AI Search + KA + Supervisor | Custom retrieval, managed answers and routing |
| 4 | AI Parse + AI Prep Search + AI Search + UC function + Genie | Extend one Genie space with manual search |
| 5 | AI Parse + AI Prep Search + AI Search + custom Python agent | Own routing, SQL, retrieval, context, and synthesis |

Start with the `NOTES.md` inside the selected option. All setup is intentionally manual and creates new demo resources only when its scripts are run.
