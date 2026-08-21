"""Seed the Lakebase (Postgres) OLTP source of truth for the powertools demo.

In production this data would arrive through the webshop App (products +
accounts on first connect; carts / purchases through real user clicks). This
Phase-1 deploy provisions the ETL bundle *without* the App bundle, so the OLTP
must be seeded directly — and the App seed never creates carts/purchases at all
(those come from browsing the storefront). This script fills that gap.

It creates the six OLTP tables with a schema that MATCHES the App's SQLModel
models exactly (app/src/cdp_demo_web_shop/backend/models.py), so a later App
deploy's `SQLModel.metadata.create_all` finds them already present and its
idempotent product/account seed lines up on the same names + stable UUIDs:

    products (NO specs), accounts, carts, cart_items, purchases, purchase_lines

All ids are deterministic (uuid5) so re-running is idempotent (ON CONFLICT DO
NOTHING). Connects to the `databricks_postgres` database (the App default and
the sync's logical_database_name) over the Lakebase autoscaling endpoint with a
freshly-minted OAuth token.

Usage:
    python seed_lakebase_oltp.py --profile FEVM --project techsummit
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import uuid
from datetime import date, datetime, timedelta, timezone

import psycopg

NS = uuid.UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")  # fixed namespace for uuid5

# Stable demo-account UUIDs the App pins (app/.../backend/seed.py) so a later App
# deploy's seed_accounts() finds them by id and skips (no duplicate insert).
DEFAULT_ACCOUNT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
NIKK_ACCOUNT_ID = uuid.UUID("1f8c6991-78ad-423a-ad46-921e5229bd9d")

# 12 active Bosch tools — EXACT (name, description, price_eur) from the App seed
# (_BOSCH_TOOLS). dim_product.category is built from `description`.
BOSCH_TOOLS: list[tuple[str, str, float]] = [
    ("GSR 18V-55", "Cordless 18V drill/driver with brushless motor for everyday tasks.", 189.00),
    ("GSB 18V-90 C", "Powerful cordless combi drill with hammer function for masonry.", 249.00),
    ("GSR 12V-35", "Compact 12V cordless drill/driver for tight workspaces.", 129.00),
    ("PSR 1080 LI", "Lightweight 10.8V drill driver for home DIY projects.", 79.00),
    ("PSB 1800 LI-2", "18V cordless impact drill with two-speed gearbox.", 139.00),
    ("GBH 2-26", "Rotary hammer 800W for drilling and chiselling concrete.", 219.00),
    ("GBH 18V-26 F", "Brushless cordless rotary hammer with SDS-plus quick-change.", 379.00),
    ("PBH 2100 RE", "Compact corded rotary hammer for occasional masonry work.", 99.00),
    ("GWS 18V-10", "Brushless 125mm cordless angle grinder with anti-kickback.", 199.00),
    ("PWS 700-115", "Entry-level 700W angle grinder with 115mm disc.", 59.00),
    ("GWS 22-230 JH", "Heavy-duty 2200W angle grinder with 230mm disc.", 189.00),
    ("GST 18V-LI S", "Cordless jigsaw with tool-free blade change.", 169.00),
]

# Same local-image map the App uses (_LOCAL_IMAGES) so image_url matches.
LOCAL_IMAGES = {
    "GSR 18V-55": "/products/gsr-18v-55.jpg",
    "GSB 18V-90 C": "/products/gsb-18v-90-c.jpg",
    "GSR 12V-35": "/products/gsr-12v-35.jpg",
    "PSR 1080 LI": "/products/psr-1080-li.jpg",
    "PSB 1800 LI-2": "/products/psb-1800-li-2.jpg",
    "GBH 2-26": "/products/gbh-2-26.jpg",
    "GBH 18V-26 F": "/products/gbh-18v-26-f.jpg",
    "PBH 2100 RE": "/products/pbh-2100-re.jpg",
    "GWS 18V-10": "/products/gws-18v-10.jpg",
    "PWS 700-115": "/products/pws-700-115.jpg",
    "GWS 22-230 JH": "/products/gws-22-230-jh.jpg",
    "GST 18V-LI S": "/products/gst-18v-li-s.jpg",
}

# Demo customers — DACH-weighted with a few EU neighbours for dim_customer variety.
# (first_name, surname, city, country)
CUSTOMERS: list[tuple[str, str, str, str]] = [
    ("Lukas", "Bauer", "Stuttgart", "Germany"),
    ("Anna", "Schmidt", "Munich", "Germany"),
    ("Jonas", "Fischer", "Hamburg", "Germany"),
    ("Mia", "Weber", "Berlin", "Germany"),
    ("Felix", "Wagner", "Cologne", "Germany"),
    ("Laura", "Becker", "Frankfurt", "Germany"),
    ("Tim", "Hoffmann", "Vienna", "Austria"),
    ("Sophie", "Gruber", "Graz", "Austria"),
    ("Noah", "Meier", "Zurich", "Switzerland"),
    ("Emma", "Keller", "Geneva", "Switzerland"),
    ("Daan", "de Vries", "Amsterdam", "Netherlands"),
    ("Sara", "Rossi", "Milan", "Italy"),
]

DDL = """
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    price_eur DOUBLE PRECISION NOT NULL,
    image_url VARCHAR NOT NULL,
    long_description VARCHAR
);
CREATE INDEX IF NOT EXISTS ix_products_name ON products (name);

CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY,
    first_name VARCHAR NOT NULL,
    surname VARCHAR NOT NULL,
    street VARCHAR NOT NULL,
    house_number VARCHAR NOT NULL,
    postal_code VARCHAR NOT NULL,
    city VARCHAR NOT NULL,
    country VARCHAR NOT NULL,
    date_of_birth DATE NOT NULL,
    email VARCHAR NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS carts (
    id UUID PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES accounts (id),
    status VARCHAR NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_carts_account_id ON carts (account_id);

CREATE TABLE IF NOT EXISTS cart_items (
    id UUID PRIMARY KEY,
    cart_id UUID REFERENCES carts (id),
    account_id UUID NOT NULL REFERENCES accounts (id),
    product_id UUID NOT NULL REFERENCES products (id),
    quantity INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS purchases (
    id UUID PRIMARY KEY,
    cart_id UUID REFERENCES carts (id),
    account_id UUID NOT NULL REFERENCES accounts (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    total_eur DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_purchases_account_id ON purchases (account_id);

CREATE TABLE IF NOT EXISTS purchase_lines (
    id UUID PRIMARY KEY,
    purchase_id UUID NOT NULL REFERENCES purchases (id),
    product_id UUID NOT NULL REFERENCES products (id),
    name_snapshot VARCHAR NOT NULL,
    unit_price_eur DOUBLE PRECISION NOT NULL,
    quantity INTEGER NOT NULL
);
"""

# Lakebase CDF prerequisite: every table in the feed must have REPLICA IDENTITY
# FULL so Postgres logs the full before/after row image (not just the PK) to the
# WAL — without it wal2delta can't build a complete change history and the table
# is silently skipped. Applied to the six existing tables here, plus an event
# trigger so any table created later (e.g. by the App's SQLModel on first
# connect) inherits it automatically. This is idempotent.
REPLICA_IDENTITY_DDL = """
DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT table_schema, table_name FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
  LOOP
    EXECUTE format('ALTER TABLE %I.%I REPLICA IDENTITY FULL;', r.table_schema, r.table_name);
  END LOOP;
END $$;

CREATE OR REPLACE FUNCTION public.set_full_replica_identity()
RETURNS event_trigger LANGUAGE plpgsql AS $$
DECLARE obj record;
BEGIN
  FOR obj IN
    SELECT * FROM pg_event_trigger_ddl_commands() WHERE command_tag = 'CREATE TABLE'
  LOOP
    EXECUTE format('ALTER TABLE %s REPLICA IDENTITY FULL;', obj.object_identity);
  END LOOP;
END $$;

DROP EVENT TRIGGER IF EXISTS set_full_replica_identity_on_create;
CREATE EVENT TRIGGER set_full_replica_identity_on_create
ON ddl_command_end WHEN TAG IN ('CREATE TABLE')
EXECUTE FUNCTION public.set_full_replica_identity();
"""


def _sh(args: list[str]) -> str:
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"command failed: {' '.join(args)}\n{r.stderr}")
    return r.stdout


def _connect(profile: str, project: str) -> psycopg.Connection:
    ep = f"projects/{project}/branches/production/endpoints/primary"
    host = json.loads(_sh(["databricks", "postgres", "get-endpoint", ep, "-p", profile, "-o", "json"]))["status"]["hosts"]["host"]
    token = json.loads(_sh(["databricks", "postgres", "generate-database-credential", ep, "-p", profile, "-o", "json"]))["token"]
    email = json.loads(_sh(["databricks", "current-user", "me", "-p", profile, "-o", "json"]))["userName"]
    return psycopg.connect(host=host, port=5432, dbname="databricks_postgres", user=email, password=token, sslmode="require")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--profile", default="FEVM")
    p.add_argument("--project", default="techsummit")
    p.add_argument("--n-purchases", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    # Fixed UTC base epoch so a given --seed produces byte-identical timestamps
    # on every clean run (datetime.now() would make the dataset non-deterministic
    # across runs even with the same seed). Override only if you need a different
    # anchor. All cart/purchase times are this base minus seeded offsets.
    p.add_argument("--base-time", default="2026-08-01T00:00:00+00:00")
    args = p.parse_args()
    rng = random.Random(args.seed)
    base_time = datetime.fromisoformat(args.base_time)
    if base_time.tzinfo is None:
        base_time = base_time.replace(tzinfo=timezone.utc)

    conn = _connect(args.profile, args.project)
    conn.autocommit = False
    cur = conn.cursor()
    cur.execute(DDL)

    # CDF prerequisite: REPLICA IDENTITY FULL on existing tables (essential) and
    # an event trigger for future ones (best-effort — tolerate a privilege error
    # so the seed still succeeds even if event triggers aren't grantable).
    cur.execute(
        "DO $$ DECLARE r record; BEGIN "
        "FOR r IN SELECT table_schema, table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_type='BASE TABLE' LOOP "
        "EXECUTE format('ALTER TABLE %I.%I REPLICA IDENTITY FULL;', r.table_schema, r.table_name); "
        "END LOOP; END $$;"
    )
    conn.commit()
    try:
        cur.execute(REPLICA_IDENTITY_DDL)
        conn.commit()
    except Exception as e:  # noqa: BLE001 — event trigger is a nice-to-have
        conn.rollback()
        print(json.dumps({"replica_identity_event_trigger": "skipped", "reason": str(e)}))

    # --- products ---
    product_ids: dict[str, uuid.UUID] = {}
    for name, desc, price in BOSCH_TOOLS:
        pid = uuid.uuid5(NS, f"product:{name}")
        product_ids[name] = pid
        cur.execute(
            "INSERT INTO products (id, name, description, price_eur, image_url, long_description) "
            "VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
            (pid, name, desc, price, LOCAL_IMAGES[name], None),
        )

    # --- accounts (2 stable App ids + generated) ---
    accounts: list[tuple[uuid.UUID, str, str, str, str, str]] = []  # id, first, surname, city, country, email
    stable = [
        (DEFAULT_ACCOUNT_ID, "Default", "User", "Gerlingen", "Germany", "default.user@bosch-shop.example"),
        (NIKK_ACCOUNT_ID, "Nikolaos", "Servos", "Stuttgart", "Netherlands", "nikolaos.servos@live.com"),
    ]
    for aid, fn, sn, city, country, email in stable:
        accounts.append((aid, fn, sn, city, country, email))
    for fn, sn, city, country in CUSTOMERS:
        email = f"{fn}.{sn}@example.com".lower().replace(" ", "")
        aid = uuid.uuid5(NS, f"account:{email}")
        accounts.append((aid, fn, sn, city, country, email))

    for aid, fn, sn, city, country, email in accounts:
        dob = date(rng.randint(1965, 2000), rng.randint(1, 12), rng.randint(1, 28))
        cur.execute(
            "INSERT INTO accounts (id, first_name, surname, street, house_number, postal_code, city, country, date_of_birth, email) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
            (aid, fn, sn, "Musterstr.", str(rng.randint(1, 200)), f"{rng.randint(10000,99999)}", city, country, dob, email),
        )

    # --- carts + purchases + lines ---
    # Deterministic: anchor on the fixed base epoch, not wall-clock now.
    now = base_time
    prod_list = list(product_ids.items())  # (name, id)
    prod_price = {name: price for name, _, price in BOSCH_TOOLS}

    n_active_carts = 0
    for i in range(args.n_purchases):
        acct = accounts[i % len(accounts)]
        aid = acct[0]
        created = now - timedelta(days=rng.randint(1, 40), hours=rng.randint(0, 23))

        cart_id = uuid.uuid5(NS, f"cart:{i}")
        cur.execute(
            "INSERT INTO carts (id, account_id, status, created_at, updated_at) "
            "VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
            (cart_id, aid, "purchased", created, created),
        )

        n_lines = rng.randint(1, 3)
        chosen = rng.sample(prod_list, n_lines)
        total = 0.0
        pur_id = uuid.uuid5(NS, f"purchase:{i}")
        # purchase row inserted after we know total; insert placeholder then update
        lines = []
        for j, (pname, pid) in enumerate(chosen):
            qty = rng.randint(1, 2)
            unit = prod_price[pname]
            total += unit * qty
            line_id = uuid.uuid5(NS, f"line:{i}:{j}")
            lines.append((line_id, pur_id, pid, pname, unit, qty))

        cur.execute(
            "INSERT INTO purchases (id, cart_id, account_id, created_at, total_eur) "
            "VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
            (pur_id, cart_id, aid, created, round(total, 2)),
        )
        for line_id, pur, pid, pname, unit, qty in lines:
            cur.execute(
                "INSERT INTO purchase_lines (id, purchase_id, product_id, name_snapshot, unit_price_eur, quantity) "
                "VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                (line_id, pur, pid, pname, unit, qty),
            )

    # A couple of still-open carts with items (OLTP realism; not synced to Delta).
    for k in range(2):
        acct = accounts[(k + 3) % len(accounts)]
        aid = acct[0]
        cart_id = uuid.uuid5(NS, f"opencart:{k}")
        cur.execute(
            "INSERT INTO carts (id, account_id, status, created_at, updated_at) "
            "VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
            (cart_id, aid, "active", now, now),
        )
        n_active_carts += 1
        for j in range(rng.randint(1, 2)):
            pname, pid = rng.choice(prod_list)
            item_id = uuid.uuid5(NS, f"cartitem:{k}:{j}")
            cur.execute(
                "INSERT INTO cart_items (id, cart_id, account_id, product_id, quantity) "
                "VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                (item_id, cart_id, aid, pid, rng.randint(1, 3)),
            )

    conn.commit()

    counts = {}
    for t in ["products", "accounts", "carts", "cart_items", "purchases", "purchase_lines"]:
        cur.execute(f"SELECT count(*) FROM {t}")
        counts[t] = cur.fetchone()[0]
    conn.close()
    print(json.dumps({"seeded": True, "counts": counts}, indent=2))


if __name__ == "__main__":
    main()
