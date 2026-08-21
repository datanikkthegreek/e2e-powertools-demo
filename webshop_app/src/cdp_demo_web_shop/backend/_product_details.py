"""Long descriptions and technical specifications for the active Bosch tools.

Keyed by product name (must match _BOSCH_TOOLS in seed.py). Specs are
preserved in insertion order, so the frontend can render them as-is.

Values are authored from publicly known Bosch product family data and
are representative for the model line; treat them as demo-quality, not
as a Bosch spec sheet.
"""

from __future__ import annotations

from typing import TypedDict


class ProductDetail(TypedDict):
    long_description: str
    specs: dict[str, str]


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
        "specs": {
            "Voltage": "18 V",
            "Max torque (hard / soft)": "55 / 28 Nm",
            "No-load speed": "0 - 460 / 0 - 1,800 rpm",
            "Chuck capacity": "1.5 - 13 mm",
            "Max drilling Ø wood": "40 mm",
            "Max drilling Ø steel": "13 mm",
            "Weight (excl. battery)": "1.0 kg",
            "Battery system": "Bosch Professional 18V",
            "Brushless motor": "Yes",
        },
    },
    "GSB 18V-90 C": {
        "long_description": (
            "The GSB 18V-90 C is Bosch Professional's high-torque cordless combi drill with "
            "hammer function for masonry. Built around a brushless EC motor, it delivers "
            "class-leading torque for tough drilling and fastening into wood, metal and "
            "concrete. Connectivity-enabled (Bluetooth module slot) for tool tracking and "
            "behaviour customisation through the Bosch Toolbox app."
        ),
        "specs": {
            "Voltage": "18 V",
            "Max torque (hard / soft)": "90 / 39 Nm",
            "No-load speed": "0 - 530 / 0 - 2,100 rpm",
            "Impact rate": "0 - 31,500 bpm",
            "Chuck capacity": "1.5 - 13 mm",
            "Max drilling Ø concrete": "16 mm",
            "Max drilling Ø wood": "82 mm",
            "Max drilling Ø steel": "15 mm",
            "Weight (excl. battery)": "1.3 kg",
            "Battery system": "Bosch Professional 18V",
            "Brushless motor": "Yes",
            "Connectivity": "Bluetooth (module ready)",
        },
    },
    "GSR 12V-35": {
        "long_description": (
            "Compact 12V brushless drill/driver for tight workspaces such as kitchen "
            "installation, electrical fit-out and cabinetry. Despite its short head length, "
            "it delivers torque comparable to many entry-level 18V tools. Sits inside the "
            "Bosch Professional 12V system, sharing batteries with impact drivers, lights "
            "and inspection cameras."
        ),
        "specs": {
            "Voltage": "12 V",
            "Max torque (hard / soft)": "35 / 21 Nm",
            "No-load speed": "0 - 460 / 0 - 1,750 rpm",
            "Chuck capacity": "1.5 - 10 mm",
            "Max drilling Ø wood": "30 mm",
            "Max drilling Ø steel": "10 mm",
            "Weight (excl. battery)": "0.7 kg",
            "Battery system": "Bosch Professional 12V",
            "Brushless motor": "Yes",
        },
    },
    "PSR 1080 LI": {
        "long_description": (
            "The PSR 1080 LI is an entry-level 10.8V cordless drill driver from Bosch's DIY "
            "(green) range, designed for occasional jobs around the home: putting up shelves, "
            "tightening furniture screws, or drilling small pilot holes. Lightweight, "
            "balanced and easy to handle for first-time users, with a 20+1 torque setting "
            "clutch to prevent overdriving."
        ),
        "specs": {
            "Voltage": "10.8 V",
            "Max torque (soft)": "20 Nm",
            "No-load speed": "0 - 600 rpm",
            "Chuck capacity": "0.8 - 10 mm",
            "Torque settings": "20 + 1",
            "Max drilling Ø wood": "20 mm",
            "Max drilling Ø steel": "8 mm",
            "Weight (incl. battery)": "0.9 kg",
            "Battery system": "Bosch Home & Garden 10.8V",
            "LED light": "Yes",
        },
    },
    "PSB 1800 LI-2": {
        "long_description": (
            "The PSB 1800 LI-2 is an 18V cordless impact drill from the Bosch DIY range that "
            "covers a wider range of home projects than a basic drill driver: drilling into "
            "brick and lightweight concrete in addition to wood and metal. The two-speed "
            "gearbox shifts between high torque for fastening and high speed for drilling, "
            "making it a versatile single-tool choice for ambitious home users."
        ),
        "specs": {
            "Voltage": "18 V",
            "Max torque (soft)": "38 Nm",
            "No-load speed": "0 - 400 / 0 - 1,400 rpm",
            "Impact rate": "0 - 21,000 bpm",
            "Chuck capacity": "1.5 - 13 mm",
            "Max drilling Ø masonry": "10 mm",
            "Max drilling Ø wood": "30 mm",
            "Max drilling Ø steel": "10 mm",
            "Weight (incl. battery)": "1.4 kg",
            "Battery system": "Bosch Home & Garden 18V (Power For All)",
        },
    },
    # --- Rotary hammers ---
    "GBH 2-26": {
        "long_description": (
            "A workhorse SDS-plus rotary hammer trusted on construction sites for over a "
            "decade. The 830W motor, robust gearbox and 2.7 J impact energy make short work "
            "of through-holes and anchor holes in concrete, while the rotation-stop mode "
            "allows light chiselling. Vibration Control reduces fatigue during sustained use."
        ),
        "specs": {
            "Power input": "830 W",
            "Tool holder": "SDS-plus",
            "Impact energy (EPTA)": "2.7 J",
            "Impact rate": "4,000 bpm",
            "No-load speed": "0 - 900 rpm",
            "Max drilling Ø concrete (hammer)": "26 mm",
            "Max drilling Ø wood": "30 mm",
            "Max drilling Ø steel": "13 mm",
            "Modes": "Drilling / Hammer drilling / Chiselling",
            "Weight": "2.7 kg",
        },
    },
    "GBH 18V-26 F": {
        "long_description": (
            "A brushless 18V SDS-plus rotary hammer with a quick-change chuck system: swap "
            "between SDS-plus and 13mm keyless chuck in seconds, no tools required. Delivers "
            "corded-class impact energy on concrete drilling and supports light chiselling "
            "via the rotation-stop mode. Designed for installers who alternate between "
            "concrete and wood/metal drilling throughout the day."
        ),
        "specs": {
            "Voltage": "18 V",
            "Tool holder": "SDS-plus + quick-change 13 mm keyless chuck",
            "Impact energy (EPTA)": "2.6 J",
            "Impact rate": "0 - 4,350 bpm",
            "No-load speed": "0 - 980 rpm",
            "Max drilling Ø concrete": "26 mm",
            "Max drilling Ø wood": "30 mm",
            "Max drilling Ø steel": "13 mm",
            "Modes": "Drilling / Hammer drilling / Chiselling",
            "Weight (excl. battery)": "2.9 kg",
            "Battery system": "Bosch Professional 18V",
            "Brushless motor": "Yes",
        },
    },
    "PBH 2100 RE": {
        "long_description": (
            "A compact corded SDS-plus rotary hammer from the Bosch DIY range, ideal for "
            "occasional masonry work in renovation or fit-out projects. Offers three modes "
            "(drilling, hammer drilling, chiselling) and a separate keyed chuck adapter for "
            "round-shank wood and metal drill bits. Good first SDS-plus tool for serious "
            "DIYers."
        ),
        "specs": {
            "Power input": "550 W",
            "Tool holder": "SDS-plus",
            "Impact energy (EPTA)": "1.7 J",
            "Impact rate": "0 - 5,800 bpm",
            "No-load speed": "0 - 1,500 rpm",
            "Max drilling Ø concrete": "20 mm",
            "Max drilling Ø wood": "30 mm",
            "Max drilling Ø steel": "13 mm",
            "Modes": "Drilling / Hammer drilling / Chiselling",
            "Weight": "2.0 kg",
        },
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
        "specs": {
            "Voltage": "18 V",
            "Disc diameter": "125 mm",
            "No-load speed": "9,000 rpm",
            "Spindle thread": "M14",
            "Safety features": "KickBack Control, Brake, Restart Protection",
            "Weight (excl. battery)": "1.6 kg",
            "Battery system": "Bosch Professional 18V",
            "Brushless motor": "Yes",
        },
    },
    "PWS 700-115": {
        "long_description": (
            "Entry-level corded 700W angle grinder for occasional cutting, grinding and "
            "polishing tasks at home. The compact body fits comfortably in one hand and the "
            "115 mm wheel is the most common size for general DIY use. Spindle lock makes "
            "wheel changes straightforward."
        ),
        "specs": {
            "Power input": "700 W",
            "Disc diameter": "115 mm",
            "No-load speed": "12,000 rpm",
            "Spindle thread": "M14",
            "Auxiliary handle": "2-position",
            "Spindle lock": "Yes",
            "Weight": "1.9 kg",
        },
    },
    "GWS 22-230 JH": {
        "long_description": (
            "Heavy-duty 2,200 W large angle grinder with a 230 mm disc for serious "
            "construction cutting and grinding: paving slabs, large steel sections, and "
            "demolition work. Direct cooling, a robust gearbox and the Vibration Control "
            "side handle make sustained use practical. Restart Protection prevents the "
            "tool from running when power is restored after an interruption."
        ),
        "specs": {
            "Power input": "2,200 W",
            "Disc diameter": "230 mm",
            "No-load speed": "6,600 rpm",
            "Spindle thread": "M14",
            "Auxiliary handle": "Vibration Control",
            "Safety features": "Restart Protection, Soft start",
            "Weight": "5.3 kg",
        },
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
        "specs": {
            "Voltage": "18 V",
            "Stroke length": "26 mm",
            "Strokes at no load": "0 - 2,700 spm",
            "Max cutting depth wood": "120 mm",
            "Max cutting depth aluminium": "20 mm",
            "Max cutting depth steel": "10 mm",
            "Bevel cuts": "0 - 45°",
            "Pendulum action": "4 settings",
            "Blade change": "SDS tool-free",
            "Weight (excl. battery)": "2.3 kg",
            "Battery system": "Bosch Professional 18V",
        },
    },
}
