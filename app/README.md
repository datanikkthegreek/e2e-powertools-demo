# cdp-demo-web-shop ✨

> A modern full-stack application built with [`apx`](https://github.com/databricks-solutions/apx) 🚀

## 🛠️ Tech Stack

This application leverages a powerful, modern tech stack:

- **Backend** 🐍 Python + [FastAPI](https://fastapi.tiangolo.com/)
- **Frontend** ⚛️ React + [shadcn/ui](https://ui.shadcn.com/)
- **API Client** 🔄 Auto-generated TypeScript client from OpenAPI schema

## 🚀 Quick Start

### Development Mode

Start all development servers (backend, frontend, and OpenAPI watcher) in detached mode:

```bash
apx dev start
```

This will start an apx development server, which in it's turn runs backend, frontend and OpenAPI watcher.
All servers run in the background, with logs kept in-memory of the apx dev server.

### 📊 Monitoring & Logs

```bash
# View all logs
apx dev logs

# Stream logs in real-time
apx dev logs -f

# Check server status
apx dev status

# Stop all servers
apx dev stop
```

## ✅ Code Quality

Run type checking and linting for both TypeScript and Python:

```bash
apx dev check
```

## 📦 Build

Create a production-ready build:

```bash
apx build
```

## 🚢 Deployment

Deploy to Databricks:

```bash
databricks bundle deploy -p <your-profile>
```

### Deploying the Bosch Power Tools webshop onto the `techsummit` Lakebase

This app is **BUNDLE 1** and must be deployed **after** the `etl/` bundle has
provisioned the `techsummit` Lakebase project and seeded the OLTP tables
(`products` [no specs], `accounts`, `carts`, `cart_items`, `purchases`,
`purchase_lines`). The app reads that live data; it does not seed it (the
startup seed hook is idempotent and only tops up the 12-tool catalogue).

**Auth model.** The storefront connects to Lakebase and the SQL warehouse as the
**app service principal** (`WorkspaceClient()` → `w.postgres.generate_database_credential`),
not on behalf of the signed-in user. So the app SP must have a Postgres role
with table privileges in the `techsummit` project. (`user_api_scopes` are
intentionally empty — the `postgres` OBO scope is disallowed in this workspace,
and the only OBO call is the `/me` identity endpoint, which needs no scope.)

Reproducible steps (FEVM profile):

```bash
# 1. Deploy the app resource + upload built source (runs `apx build`).
databricks bundle deploy -p FEVM

# 2. Read back the app's service-principal client id.
SP=$(databricks apps get powertools-webshop -p FEVM \
       | python3 -c "import sys,json;print(json.load(sys.stdin)['service_principal_client_id'])")

# 3. Create a Postgres role for the app SP on the techsummit production branch.
#    role-id must start with a letter; postgres_role is the SP client id (the
#    login name the app uses).
databricks postgres create-role "projects/techsummit/branches/production" \
  --role-id "app-powertools-webshop" \
  --json "{\"spec\": {\"identity_type\": \"SERVICE_PRINCIPAL\", \"postgres_role\": \"$SP\", \"auth_method\": \"LAKEBASE_OAUTH_V1\"}}" \
  -p FEVM

# 4. Grant that SP role least-privilege access to the six storefront OLTP tables.
#    Connect to the Lakebase endpoint as YOUR OWN superuser Postgres role (the
#    role created for your user on this branch). No secrets are stored: the
#    endpoint host is resolved from the SDK and the DB password is a short-lived
#    OAuth credential minted on the fly via w.postgres.generate_database_credential
#    (sslmode=require). Run from the app/ dir so `uv run` has the deps:
SP="$SP" uv run python - <<'PY'
import os
from databricks.sdk import WorkspaceClient
import psycopg
SP = os.environ["SP"]
w = WorkspaceClient(profile="FEVM")
ep = "projects/techsummit/branches/production/endpoints/primary"
host = w.postgres.get_endpoint(ep).status.hosts.host           # endpoint host, from SDK
cred = w.postgres.generate_database_credential(endpoint=ep)    # short-lived OAuth token
conn = psycopg.connect(host=host, port=5432, dbname="databricks_postgres",
                       user=w.current_user.me().user_name,     # your superuser role
                       password=cred.token, sslmode="require", autocommit=True)
cur = conn.cursor()
cur.execute(f'GRANT USAGE ON SCHEMA public TO "{SP}"')
for t in ["products","accounts","carts","cart_items","purchases","purchase_lines"]:
    cur.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.{t} TO "{SP}"')
conn.close()
print("granted:", SP)
PY

# 5. Start compute + deploy the app.
databricks bundle run powertools-webshop-app -p FEVM
```

Notes on the grants:

- **Least privilege on exactly six tables.** The Lakebase `public` schema holds
  only the six OLTP tables above — no others and **no sequences** (all primary
  keys are client-generated UUIDs), so there is nothing else to grant. We
  deliberately do *not* use `GRANT … ON ALL TABLES` or `ALTER DEFAULT
  PRIVILEGES`, which would also cover any future table.
- **`product_specs` is NOT in this database.** The typed spec table is an
  analytics-layer **Delta** table (Unity Catalog, produced by IDP), not a
  Lakebase Postgres table — so it is not part of these grants and never
  surfaces in the storefront.

App URL (current `dev` target on FEVM `adb-7405607030687545`):
`https://powertools-webshop-7405607030687545.5.azure.databricksapps.com`
— on another workspace/target it follows the pattern
`https://powertools-webshop-<workspace-id>.<region>.azure.databricksapps.com`;
read the authoritative value from `databricks apps get powertools-webshop -p <profile>` (`.url`).

> **Follow-up (not required for the storefront):** behaviour-event capture via
> Zerobus is stubbed. `../app.yml` still has `REPLACE_WITH_FEVM_ZEROBUS_ENDPOINT`
> and `REPLACE_WITH_FEVM_ZEROBUS_CLIENT_ID`. Browsing / add-to-cart / checkout
> work regardless (the frontend event POST is fire-and-forget); wiring Zerobus
> is part of the ETL/funnel beat, not the storefront.

---

<p align="center">Built with ❤️ using <a href="https://github.com/databricks-solutions/apx">apx</a></p>
