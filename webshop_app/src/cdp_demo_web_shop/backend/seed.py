from __future__ import annotations

from datetime import date
from urllib.parse import quote
from uuid import UUID

from sqlmodel import Session, col, select

from ._product_details import PRODUCT_DETAILS
from .core._config import logger
from .models import Account, CartItem, Product, Purchase, PurchaseLine

DEFAULT_ACCOUNT_EMAIL = "default.user@bosch-shop.example"
# Stable UUID for the seeded default account so the frontend's cached
# `bosch_shop_active_account_id` in localStorage survives `apx dev restart`
# (the in-memory PGLite DB is wiped on every restart in dev mode).
DEFAULT_ACCOUNT_ID = UUID("00000000-0000-0000-0000-000000000001")

# Locally hosted product photos under ui/public/products/<slug>.jpg
# (served by Vite at /products/<slug>.jpg). Add entries here as you
# download more images; the rest fall back to a placehold.co URL.
_LOCAL_IMAGES: dict[str, str] = {
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


def _img(name: str) -> str:
    """Resolve a product image URL: prefer a locally hosted file, else a placeholder."""
    local = _LOCAL_IMAGES.get(name)
    if local:
        return local
    label = quote(name.replace(" ", "+"))
    return f"https://placehold.co/400x300/0a3d62/ffffff?text={label}"


# Only products with a real local image (entry in _LOCAL_IMAGES) are active.
# Products without a downloaded picture are commented out below; uncomment a
# line and add the slug to _LOCAL_IMAGES when its image becomes available.
_BOSCH_TOOLS: list[tuple[str, str, float]] = [
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
    # ("PST 900 PEL", "Corded 620W jigsaw with LED lighting.", 109.00),
    # ("GKS 18V-57 G", "Cordless circular saw with guide rail compatibility.", 259.00),
    # ("PKS 66 AF", "Corded 1600W circular saw with parallel guide.", 149.00),
    # ("GTS 635-216", "Compact table saw with 216mm blade for precision cuts.", 449.00),
    # ("PTS 10", "Versatile table saw with sliding carriage.", 379.00),
    # ("GCM 8 SJL", "Sliding mitre saw 1600W with laser cut line.", 419.00),
    # ("PCM 8 S", "Compact sliding mitre saw for trim and panels.", 219.00),
    # ("GOP 18V-28", "StarlockPlus cordless multi-tool with high oscillation rate.", 229.00),
    # ("PMF 350 CES", "Multi-tool 350W with Starlock accessory mount.", 129.00),
    # ("GEX 18V-125", "Cordless random orbit sander with PROtection low-vibration.", 219.00),
    # ("PEX 220 A", "Compact 220W random orbit sander for fine finishing.", 79.00),
    # ("PSS 250 AE", "Orbital sander 250W with microfilter dust box.", 89.00),
    # ("PBS 75 AE", "Belt sander 750W for fast stock removal.", 159.00),
    # ("GHO 18V-LI", "Cordless planer with brushless motor and woodruff knives.", 269.00),
    # ("PHO 2000", "Corded 680W planer with 82mm planing width.", 109.00),
    # ("POF 1400 ACE", "Plunge router 1400W with depth fine adjustment.", 219.00),
    # ("GKF 12V-8", "12V cordless palm router for trimming and chamfering.", 169.00),
    # ("GBM 13-2 RE", "Two-speed drill 750W for metal and wood drilling.", 159.00),
    # ("PSM 18 LI", "18V cordless detail sander for corners and edges.", 99.00),
    # ("UniversalImpact 800", "800W impact drill for occasional masonry use.", 89.00),
    # ("AdvancedImpact 18", "18V cordless impact drill with kickback control.", 179.00),
    # ("EasyDrill 1200", "Lightweight 12V drill driver for quick jobs.", 69.00),
    # ("AdvancedDrill 18V-60", "Cordless drill driver with brushless motor.", 169.00),
    # ("UniversalLevel 360", "Self-levelling cross-line laser with 360 horizontal line.", 199.00),
    # ("GLL 3-80", "Professional three-plane line laser for tiling and framing.", 379.00),
    # ("GLM 50-27 C", "Bluetooth-connected 50m laser distance measurer.", 179.00),
    # ("GLM 100-25 C", "Premium 100m laser measure with camera viewfinder.", 269.00),
    # ("EasyHedgeCut 12-450", "12V cordless hedge cutter with 450mm blade.", 99.00),
    # ("AdvancedHedgeCut 36V-65-28", "36V hedge cutter with anti-blocking system.", 219.00),
    # ("EasyGrassCut 18-26", "18V cordless grass trimmer with semi-automatic spool.", 119.00),
    # ("AdvancedGrassCut 36V-33", "36V grass trimmer with adjustable cutting head.", 179.00),
    # ("UniversalLeafBlower 18V-130", "Cordless leaf blower with two air-flow speeds.", 149.00),
    # ("UniversalChain 18", "Cordless 18V chainsaw with 25cm bar for branch trimming.", 179.00),
    # ("AdvancedRotak 36-750", "36V cordless lawnmower with 46cm cutting width.", 499.00),
    # ("EasyAquatak 120", "High-pressure washer with 1500W motor for cars and patios.", 119.00),
    # ("UniversalAquatak 135", "Mid-range pressure washer with quick-connect lance.", 169.00),
    # ("AdvancedAquatak 150", "Premium pressure washer with rotating brush head.", 229.00),
    # ("PFS 5000 E", "Paint spray system with PaintControl for walls and ceilings.", 339.00),
]


def seed_products(session: Session) -> tuple[int, int, int]:
    """Sync product table to the active _BOSCH_TOOLS list.

    For each row in _BOSCH_TOOLS: insert if missing, update if changed.
    Any product in the DB whose name is NOT in _BOSCH_TOOLS is removed,
    cascading through cart items, purchase lines, and orphan purchases.
    Returns (inserted, updated, removed).
    """
    active_names = {name for name, _, _ in _BOSCH_TOOLS}
    existing = session.exec(select(Product)).all()
    existing_by_name = {p.name: p for p in existing}

    # --- Remove products no longer in the active list ---
    to_remove = [p for p in existing if p.name not in active_names]
    removed = 0
    if to_remove:
        remove_ids = [p.id for p in to_remove]

        cart_items = session.exec(
            select(CartItem).where(col(CartItem.product_id).in_(remove_ids))
        ).all()
        for ci in cart_items:
            session.delete(ci)

        purchase_lines = session.exec(
            select(PurchaseLine).where(col(PurchaseLine.product_id).in_(remove_ids))
        ).all()
        affected_purchase_ids = {pl.purchase_id for pl in purchase_lines}
        for pl in purchase_lines:
            session.delete(pl)

        for p in to_remove:
            session.delete(p)
        removed = len(to_remove)

        session.flush()

        # Drop purchases that lost all their lines
        for pid in affected_purchase_ids:
            remaining = session.exec(
                select(PurchaseLine).where(col(PurchaseLine.purchase_id) == pid)
            ).first()
            if remaining is None:
                purchase = session.get(Purchase, pid)
                if purchase is not None:
                    session.delete(purchase)

    # --- Insert/update active products ---
    inserted = 0
    updated = 0
    for name, description, price in _BOSCH_TOOLS:
        url = _img(name)
        detail = PRODUCT_DETAILS.get(name)
        long_description = detail["long_description"] if detail else None
        specs = detail["specs"] if detail else None

        current = existing_by_name.get(name)
        if current is None:
            session.add(
                Product(
                    name=name,
                    description=description,
                    price_eur=price,
                    image_url=url,
                    long_description=long_description,
                    specs=specs,
                )
            )
            inserted += 1
        else:
            if (
                current.description != description
                or current.price_eur != price
                or current.image_url != url
                or current.long_description != long_description
                or current.specs != specs
            ):
                current.description = description
                current.price_eur = price
                current.image_url = url
                current.long_description = long_description
                current.specs = specs
                session.add(current)
                updated += 1

    session.commit()
    logger.info(
        f"Seeded Bosch products: {inserted} inserted, {updated} updated, {removed} removed"
    )
    return inserted, updated, removed


# Demo accounts seeded with STABLE, deterministic UUIDs. Stable ids let the
# browser's cached `bosch_shop_active_account_id` (localStorage) keep resolving
# to a real account across an `apx dev restart`, which wipes the ephemeral dev
# DB. Without this, an API-created account gets a fresh random UUID on every
# restart, the cached id 404s on its first account-scoped request, and the
# global error handler snaps the account picker back to the first account.
_DEMO_ACCOUNTS: list[dict] = [
    {
        "id": DEFAULT_ACCOUNT_ID,
        "first_name": "Default",
        "surname": "User",
        "street": "Robert-Bosch-Platz",
        "house_number": "1",
        "postal_code": "70839",
        "city": "Gerlingen",
        "country": "Germany",
        "date_of_birth": date(1990, 1, 1),
        "email": DEFAULT_ACCOUNT_EMAIL,
    },
    {
        # Pin the existing demo account's current id so it survives DB wipes
        # and the browser's cached selection keeps resolving with no snap-back.
        "id": UUID("1f8c6991-78ad-423a-ad46-921e5229bd9d"),
        "first_name": "Nikolaos",
        "surname": "Servos",
        "street": "Foehrichstr.",
        "house_number": "48",
        "postal_code": "70469",
        "city": "Stuttgart",
        "country": "Netherlands",
        "date_of_birth": date(1991, 6, 11),
        "email": "nikolaos.servos@live.com",
    },
]


def seed_accounts(session: Session) -> int:
    """Idempotently ensure the demo accounts exist with their stable UUIDs.

    Inserts any demo account whose stable id is missing. If an account with the
    same email already exists under a *different* id (a legacy random-UUID row),
    it is left untouched to avoid violating the unique-email constraint, and a
    note is logged. Returns the number of accounts inserted.
    """
    inserted = 0
    for spec in _DEMO_ACCOUNTS:
        if session.get(Account, spec["id"]) is not None:
            continue

        email_taken = session.exec(
            select(Account).where(col(Account.email) == spec["email"])
        ).first()
        if email_taken is not None:
            logger.info(
                f"Account email '{spec['email']}' already present under id "
                f"{email_taken.id}; skipping stable-id seed for it."
            )
            continue

        session.add(Account(**spec))
        inserted += 1

    session.commit()
    logger.info(f"Seeded demo accounts: {inserted} inserted")
    return inserted
