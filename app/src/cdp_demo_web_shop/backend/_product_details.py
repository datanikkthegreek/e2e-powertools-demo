"""Long (marketing) descriptions for the active Bosch tools.

Keyed by product name (must match _BOSCH_TOOLS in seed.py).

NOTE: technical *specifications* have been removed from this demo. Specs are
no longer stored in Lakebase `products` nor rendered by the app — in the
powertools demo they are produced fresh by IDP from the datasheet PDFs into
the analytics-layer `product_specs` table. Only the free-text
`long_description` remains here.
"""

from __future__ import annotations

from typing import TypedDict


class ProductDetail(TypedDict):
    long_description: str


PRODUCT_DETAILS: dict[str, ProductDetail] = {
    # --- Drills / Combi drills ---
    "GSR 18V-55": {
        "long_description": (
            "The GSR 18V-55 is a compact professional cordless drill/driver built around "
            "Bosch's brushless EC motor. Tuned for everyday assembly, fitting and light "
            "construction work, it offers strong torque in a body small enough for repetitive "
            "overhead use. The two-speed gearbox plus 25+1 torque settings give precise control "
            "across screws and small drilling tasks. Part of the Bosch Professional 18V system."
        ),
    },
    "GSB 18V-90 C": {
        "long_description": (
            "The GSB 18V-90 C is Bosch Professional's high-torque cordless combi drill with "
            "hammer function for masonry. Built around a brushless EC motor, it delivers "
            "class-leading torque for tough drilling and fastening into wood, metal and "
            "concrete. Connectivity-enabled (Bluetooth module slot) for tool tracking and "
            "behaviour customisation through the Bosch Toolbox app."
        ),
    },
    "GSR 12V-35": {
        "long_description": (
            "Compact 12V brushless drill/driver for tight workspaces such as kitchen "
            "installation, electrical fit-out and cabinetry. Despite its short head length, "
            "it delivers torque comparable to many entry-level 18V tools. Sits inside the "
            "Bosch Professional 12V system, sharing batteries with impact drivers, lights "
            "and inspection cameras."
        ),
    },
    "PSR 1080 LI": {
        "long_description": (
            "The PSR 1080 LI is an entry-level 10.8V cordless drill driver from Bosch's DIY "
            "(green) range, designed for occasional jobs around the home: putting up shelves, "
            "tightening furniture screws, or drilling small pilot holes. Lightweight, "
            "balanced and easy to handle for first-time users, with a 20+1 torque setting "
            "clutch to prevent overdriving."
        ),
    },
    "PSB 1800 LI-2": {
        "long_description": (
            "The PSB 1800 LI-2 is an 18V cordless impact drill from the Bosch DIY range that "
            "covers a wider range of home projects than a basic drill driver: drilling into "
            "brick and lightweight concrete in addition to wood and metal. The two-speed "
            "gearbox shifts between high torque for fastening and high speed for drilling, "
            "making it a versatile single-tool choice for ambitious home users."
        ),
    },
    # --- Rotary hammers ---
    "GBH 2-26": {
        "long_description": (
            "A workhorse SDS-plus rotary hammer trusted on construction sites for over a "
            "decade. The 830W motor, robust gearbox and 2.7 J impact energy make short work "
            "of through-holes and anchor holes in concrete, while the rotation-stop mode "
            "allows light chiselling. Vibration Control reduces fatigue during sustained use."
        ),
    },
    "GBH 18V-26 F": {
        "long_description": (
            "A brushless 18V SDS-plus rotary hammer with a quick-change chuck system: swap "
            "between SDS-plus and 13mm keyless chuck in seconds, no tools required. Delivers "
            "corded-class impact energy on concrete drilling and supports light chiselling "
            "via the rotation-stop mode. Designed for installers who alternate between "
            "concrete and wood/metal drilling throughout the day."
        ),
    },
    "PBH 2100 RE": {
        "long_description": (
            "A compact corded SDS-plus rotary hammer from the Bosch DIY range, ideal for "
            "occasional masonry work in renovation or fit-out projects. Offers three modes "
            "(drilling, hammer drilling, chiselling) and a separate keyed chuck adapter for "
            "round-shank wood and metal drill bits. Good first SDS-plus tool for serious "
            "DIYers."
        ),
    },
    # --- Angle grinders ---
    "GWS 18V-10": {
        "long_description": (
            "A compact 125 mm cordless angle grinder built around Bosch's brushless EC motor "
            "and electronic safety package: KickBack Control halts the disc on sudden binding, "
            "and the brake stops the wheel in seconds after release. Ideal for cutting "
            "rebar, light steel sections and tile on installations where a power cable is "
            "impractical."
        ),
    },
    "PWS 700-115": {
        "long_description": (
            "Entry-level corded 700W angle grinder for occasional cutting, grinding and "
            "polishing tasks at home. The compact body fits comfortably in one hand and the "
            "115 mm wheel is the most common size for general DIY use. Spindle lock makes "
            "wheel changes straightforward."
        ),
    },
    "GWS 22-230 JH": {
        "long_description": (
            "Heavy-duty 2,200 W large angle grinder with a 230 mm disc for serious "
            "construction cutting and grinding: paving slabs, large steel sections, and "
            "demolition work. Direct cooling, a robust gearbox and the Vibration Control "
            "side handle make sustained use practical. Restart Protection prevents the "
            "tool from running when power is restored after an interruption."
        ),
    },
    # --- Jigsaw ---
    "GST 18V-LI S": {
        "long_description": (
            "Cordless 18V jigsaw with bow handle and SDS tool-free blade change for fast "
            "switching between wood, metal and laminate blades. The Constant Electronic "
            "system keeps the blade speed steady under load for cleaner cuts, and the "
            "four-step pendulum action lets you balance speed against finish quality. "
            "Built-in dust blower keeps the cut line visible."
        ),
    },
}
