#!/usr/bin/env python3
"""Generate + upload SYNTHETIC demo product manuals for the Bosch Power Tools demo.

Reproducible source of truth for the 12 product-manual PDFs consumed by the
`powertools-manuals-ka` Knowledge Assistant. We CANNOT legally redistribute
real Bosch manuals, so this renders realistic *synthetic* demo manuals — one
multi-page PDF per tool — grounded in each tool's real spec class (rotary
hammer / drill / grinder / jigsaw, corded vs cordless). Every page footer and
the cover carry a clear "Synthetic demo content — not an official Bosch
document" disclaimer.

Flow (idempotent, re-runnable):
  1. render one HTML manual per tool into etl/data/manuals/html/
  2. convert HTML -> PDF (weasyprint) into etl/data/manuals/*.pdf
  3. upload the PDFs to the manuals/ subfolder of the raw_docs UC Volume

The 12 tool ids match the datasheet filenames in etl/data/datasheets/. The
generated PDFs are NOT committed (see .gitignore); this script regenerates them.

Usage:
  python etl/src/generate_manuals.py                 # generate + upload (defaults)
  python etl/src/generate_manuals.py --no-upload     # generate PDFs only
  python etl/src/generate_manuals.py --force         # re-render even if up to date
  python etl/src/generate_manuals.py \
      --catalog nikks_fevm_workspace_7405607030687545 \
      --schema techsummit --volume raw_docs --profile FEVM
"""
from __future__ import annotations

import argparse
import html
import subprocess
import sys
from pathlib import Path

# ── defaults (match etl/databricks.yml vars + the demo guardrails) ─────────────
DEFAULT_CATALOG = "nikks_fevm_workspace_7405607030687545"
DEFAULT_SCHEMA = "techsummit"
DEFAULT_VOLUME = "raw_docs"
DEFAULT_PROFILE = "FEVM"
# NEW subfolder inside the existing MANAGED volume; the sibling datasheets/
# folder (IDP source) is never touched.
VOLUME_SUBFOLDER = "manuals"

DISCLAIMER = "Synthetic demo content — not an official Bosch document."

# Local output dirs (relative to repo root, resolved from this file's location).
REPO_ROOT = Path(__file__).resolve().parents[2]
MANUALS_DIR = REPO_ROOT / "etl" / "data" / "manuals"
HTML_DIR = MANUALS_DIR / "html"


# ── tool identity + specs (grounded in the real Bosch spec class; the datasheet
#    filenames in etl/data/datasheets/ are the id list) ─────────────────────────
# power: "cordless" (has Battery/Charging section) | "corded" (has Mains section)
TOOLS: list[dict] = [
    {
        "id": "gbh-18v-26-f", "model": "GBH 18V-26 F", "line": "Professional",
        "type": "Cordless Rotary Hammer", "power": "cordless",
        "tagline": "Brushless cordless SDS-plus rotary hammer for drilling and light chiselling in concrete.",
        "specs": [
            ("Voltage", "18 V"), ("Battery system", "18 V Li-Ion (2.0–8.0 Ah ProCORE18V)"),
            ("Tool holder", "SDS-plus"), ("Impact energy (EPTA)", "2.0 J"),
            ("Max. drilling dia. in concrete", "26 mm"), ("No-load speed", "0–1,000 rpm"),
            ("Impact rate", "0–3,600 bpm"), ("Motor", "Brushless"), ("Weight (excl. battery)", "2.2 kg"),
        ],
        "faults": [
            ("E01", "Tool stops, battery LED flashes 3×", "Battery over-temperature protection tripped", "Let the battery cool to 0–45 °C, then reinsert. Do not charge a hot pack."),
            ("E02", "Hammer runs but bit does not rotate", "Mode selector between drill and hammer positions", "Turn the mode selector fully to the drill+hammer symbol until it clicks."),
            ("—", "SDS-plus bit will not lock", "Debris in the tool holder", "Pull back the locking sleeve, clean the shank, apply a thin film of grease, reinsert until it seats."),
        ],
    },
    {
        "id": "gbh-2-26", "model": "GBH 2-26", "line": "Professional",
        "type": "Corded Rotary Hammer", "power": "corded",
        "tagline": "800 W corded SDS-plus rotary hammer for drilling and chiselling in concrete and masonry.",
        "specs": [
            ("Rated power input", "800 W"), ("Tool holder", "SDS-plus"), ("Impact energy (EPTA)", "2.7 J"),
            ("Max. drilling dia. in concrete", "26 mm"), ("No-load speed", "0–900 rpm"),
            ("Impact rate", "0–4,000 bpm"), ("Mains", "230 V / 50 Hz"), ("Weight", "2.7 kg"),
        ],
        "faults": [
            ("E10", "No rotation, motor hums", "Worn or stuck carbon brushes", "Have an authorised service centre replace the carbon brushes."),
            ("—", "Reduced hammer performance", "Worn SDS-plus bit or cold grease at start-up", "Fit a new bit; run the tool unloaded for 30 s in a cold room to warm the hammer grease."),
            ("—", "Tool cuts out under load", "Mains under-voltage or over-long extension lead", "Use a lead ≤ 30 m with ≥ 1.5 mm² conductors on a dedicated circuit."),
        ],
    },
    {
        "id": "gsb-18v-90-c", "model": "GSB 18V-90 C", "line": "Professional",
        "type": "Cordless Combi Drill (hammer function)", "power": "cordless",
        "tagline": "Powerful brushless cordless combi drill with hammer function for masonry, plus Bluetooth connectivity.",
        "specs": [
            ("Voltage", "18 V"), ("Max. torque (hard/soft)", "64 / 38 Nm"), ("Chuck", "1.5–13 mm keyless"),
            ("No-load speed (1st/2nd)", "0–650 / 0–2,100 rpm"), ("Impact rate", "0–34,000 bpm"),
            ("Max. dia. masonry / steel / wood", "16 / 13 / 65 mm"), ("Motor", "Brushless"),
            ("Connectivity", "Bluetooth (Bosch Toolbox app)"), ("Weight (excl. battery)", "1.1 kg"),
        ],
        "faults": [
            ("E20", "Tool disables, all LEDs on", "Electronic Motor Protection (overload)", "Release the trigger for 5 s; reduce feed pressure or drill diameter."),
            ("—", "No hammer action in masonry mode", "Mode collar not fully on the hammer symbol", "Rotate the front collar fully to the hammer icon until detented."),
            ("—", "Chuck slips on the bit", "Chuck not tightened in low gear", "Shift to 1st gear and hand-tighten the keyless chuck firmly; re-check after first hole."),
        ],
    },
    {
        "id": "gsr-12v-35", "model": "GSR 12V-35", "line": "Professional",
        "type": "Cordless Drill/Driver", "power": "cordless",
        "tagline": "Compact brushless 12 V cordless drill/driver for assembly work in tight spaces.",
        "specs": [
            ("Voltage", "12 V"), ("Max. torque (hard/soft)", "35 / 20 Nm"), ("Chuck", "1.5–10 mm keyless"),
            ("No-load speed (1st/2nd)", "0–460 / 0–1,750 rpm"), ("Max. dia. steel / wood", "10 / 27 mm"),
            ("Torque settings", "20 + drill"), ("Motor", "Brushless"), ("Weight (excl. battery)", "0.8 kg"),
        ],
        "faults": [
            ("E30", "Runtime much shorter than usual", "Battery cells aged or deep-discharged", "Charge fully; if runtime stays low, replace the battery pack."),
            ("—", "Clutch slips at low torque", "Torque collar set too low for the screw", "Increase the torque collar setting one step at a time until the screw seats."),
            ("—", "Chuck will not open", "Chuck jaws tightened under power", "Hold the chuck, set forward rotation and briefly pulse the trigger to release."),
        ],
    },
    {
        "id": "gsr-18v-55", "model": "GSR 18V-55", "line": "Professional",
        "type": "Cordless Drill/Driver", "power": "cordless",
        "tagline": "Brushless 18 V cordless drill/driver with EMP overload protection for everyday drilling and driving.",
        "specs": [
            ("Voltage", "18 V"), ("Max. torque (hard/soft)", "55 / 28 Nm"), ("Chuck", "1.5–13 mm keyless"),
            ("No-load speed (1st/2nd)", "0–500 / 0–1,900 rpm"), ("Max. dia. steel / wood", "13 / 40 mm"),
            ("Torque settings", "20 + drill"), ("Motor", "Brushless"), ("Weight (excl. battery)", "1.0 kg"),
        ],
        "faults": [
            ("E20", "Tool shuts off under heavy load", "Electronic Motor Protection (overload)", "Release the trigger, let the tool idle 5 s, then resume with less feed pressure."),
            ("—", "LED work light stays off", "Trigger not partially pressed", "The light activates on the first trigger stage; check the battery charge if still dark."),
            ("—", "Excessive run-out when drilling", "Bit not centred in the chuck", "Open the chuck fully, seat the bit against all three jaws, re-tighten."),
        ],
    },
    {
        "id": "gst-18v-li-s", "model": "GST 18V-LI S", "line": "Professional",
        "type": "Cordless Jigsaw", "power": "cordless",
        "tagline": "Cordless 18 V jigsaw with tool-free SDS blade change and 4-stage pendulum action.",
        "specs": [
            ("Voltage", "18 V"), ("Stroke rate", "0–2,700 spm"), ("Stroke length", "26 mm"),
            ("Blade fitting", "SDS tool-free, T-shank"), ("Cutting depth wood / aluminium / steel", "120 / 20 / 10 mm"),
            ("Pendulum action", "4 stages"), ("Bevel cuts", "0–45°"), ("Weight (excl. battery)", "2.3 kg"),
        ],
        "faults": [
            ("—", "Blade wanders off a straight line", "Wrong pendulum setting for the material", "Set pendulum to 0 for metal and fine cuts; increase for fast cuts in wood."),
            ("—", "Blade ejects during cutting", "SDS lever not fully engaged", "Open the SDS lever, insert the blade until it stops, release the lever and tug-test the blade."),
            ("E40", "Tool stops mid-cut", "Battery under-voltage cut-off", "Recharge the battery; avoid forcing the blade, which raises current draw."),
        ],
    },
    {
        "id": "gws-18v-10", "model": "GWS 18V-10", "line": "Professional",
        "type": "Cordless Angle Grinder", "power": "cordless",
        "tagline": "Brushless 125 mm cordless angle grinder with KickBack Control and restart protection.",
        "specs": [
            ("Voltage", "18 V"), ("Disc diameter", "125 mm"), ("No-load speed", "9,000 rpm"),
            ("Spindle thread", "M14"), ("Safety", "KickBack Control, restart protection, drop control"),
            ("Motor", "Brushless"), ("Guard", "Tool-free adjustable"), ("Weight (excl. battery)", "1.7 kg"),
        ],
        "faults": [
            ("E50", "Tool shuts off suddenly, will not restart on trigger", "KickBack Control triggered by a pinch/stall", "Release the switch fully and press again to re-enable; clear the pinch before restarting."),
            ("—", "Disc will not tighten", "SDS-clic nut cross-threaded or omitted", "Fit the disc squarely, hand-start the nut, tighten with the two-pin wrench."),
            ("—", "Restart protection blocks start", "Trigger was locked on at battery insertion", "Unlock the switch, remove and reinsert the battery, then press the trigger."),
        ],
    },
    {
        "id": "gws-22-230-jh", "model": "GWS 22-230 JH", "line": "Professional",
        "type": "Corded Angle Grinder", "power": "corded",
        "tagline": "Heavy-duty 2,200 W corded 230 mm angle grinder with restart protection and J-handle.",
        "specs": [
            ("Rated power input", "2,200 W"), ("Disc diameter", "230 mm"), ("No-load speed", "6,500 rpm"),
            ("Spindle thread", "M14"), ("Safety", "Restart protection, direct cooling"),
            ("Handle", "Vibration-damped J-handle (JH)"), ("Mains", "230 V / 50 Hz"), ("Weight", "5.1 kg"),
        ],
        "faults": [
            ("—", "Tool will not start after power returns", "Restart protection engaged after a mains interruption", "Switch off, then switch on again to restart the tool."),
            ("E10", "Sparking from the motor housing, loss of power", "Worn carbon brushes", "Have an authorised service centre replace both carbon brushes as a pair."),
            ("—", "Excessive vibration", "Out-of-round or damaged disc", "Stop immediately, inspect and replace the disc; verify max. disc rpm ≥ tool rpm."),
        ],
    },
    {
        "id": "pbh-2100-re", "model": "PBH 2100 RE", "line": "DIY / Home",
        "type": "Corded Rotary Hammer", "power": "corded",
        "tagline": "Compact 550 W corded SDS-plus rotary hammer for occasional masonry work at home.",
        "specs": [
            ("Rated power input", "550 W"), ("Tool holder", "SDS-plus"), ("Impact energy (EPTA)", "1.7 J"),
            ("Max. drilling dia. concrete", "20 mm"), ("No-load speed", "0–5,800 rpm"),
            ("Impact rate", "0–5,800 bpm"), ("Speed control", "Variable trigger (RE = reverse + electronic)"),
            ("Mains", "230 V / 50 Hz"), ("Weight", "2.4 kg"),
        ],
        "faults": [
            ("—", "Bit does not hammer", "Selector set to drill-only", "Turn the function selector to the hammer-drill symbol."),
            ("—", "Motor runs slowly and warm", "Continuous heavy use beyond DIY duty cycle", "Rest the tool for 15 min per 30 min of use; do not exceed 20 mm holes."),
            ("—", "Reverse direction will not engage", "Rotation switch moved with the motor running", "Stop the motor fully before switching rotation direction."),
        ],
    },
    {
        "id": "psb-1800-li-2", "model": "PSB 1800 LI-2", "line": "DIY / Home",
        "type": "Cordless Impact Drill", "power": "cordless",
        "tagline": "18 V cordless impact drill with a two-speed gearbox for wood, metal and light masonry.",
        "specs": [
            ("Voltage", "18 V"), ("Max. torque (hard/soft)", "38 / 22 Nm"), ("Chuck", "1.0–10 mm keyless"),
            ("No-load speed (1st/2nd)", "0–450 / 0–1,400 rpm"), ("Impact rate", "0–22,400 bpm"),
            ("Max. dia. masonry / steel / wood", "10 / 10 / 25 mm"), ("Torque settings", "20 + drill + hammer"),
            ("Battery system", "18 V 'Power for All' Li-Ion"), ("Weight (excl. battery)", "1.1 kg"),
        ],
        "faults": [
            ("—", "No impact when drilling masonry", "Mode ring not on the hammer symbol", "Rotate the mode ring to the hammer icon; use a masonry bit."),
            ("E30", "Very short runtime", "Battery aged or stored discharged", "Charge fully before use; store the pack at ~40–60 % charge."),
            ("—", "Gear will not shift", "Gear selector moved under power", "Stop the motor, then slide the 1/2 gear selector fully into position."),
        ],
    },
    {
        "id": "psr-1080-li", "model": "PSR 1080 LI", "line": "DIY / Home",
        "type": "Cordless Drill/Driver", "power": "cordless",
        "tagline": "Lightweight 10.8 V cordless drill/driver for home DIY drilling and screwdriving.",
        "specs": [
            ("Voltage", "10.8 V"), ("Max. torque (hard/soft)", "30 / 10 Nm"), ("Chuck", "1.0–10 mm keyless"),
            ("No-load speed", "0–1,300 rpm"), ("Max. dia. steel / wood", "10 / 20 mm"),
            ("Torque settings", "10 + drill"), ("Battery", "10.8 V 1.5 Ah Li-Ion (integrated)"),
            ("Charging time", "~3 h (standard charger)"), ("Weight", "0.95 kg"),
        ],
        "faults": [
            ("—", "Battery gauge shows empty after charge", "Charged below 0 °C or above 45 °C", "Charge indoors at room temperature; the LED turns green when full."),
            ("—", "Screws driven too deep", "Torque collar set too high", "Lower the torque collar until the clutch slips as the screw seats flush."),
            ("—", "No rotation in either direction", "Direction switch in the central lock position", "Push the forward/reverse slider fully to one side to unlock the trigger."),
        ],
    },
    {
        "id": "pws-700-115", "model": "PWS 700-115", "line": "DIY / Home",
        "type": "Corded Angle Grinder", "power": "corded",
        "tagline": "Entry-level 700 W corded angle grinder with a 115 mm disc for cutting and grinding at home.",
        "specs": [
            ("Rated power input", "700 W"), ("Disc diameter", "115 mm"), ("No-load speed", "11,000 rpm"),
            ("Spindle thread", "M14"), ("Guard", "Tool-free adjustable"), ("Handle", "2-position auxiliary handle"),
            ("Mains", "230 V / 50 Hz"), ("Weight", "1.9 kg"),
        ],
        "faults": [
            ("—", "Disc slows badly under light load", "Overloading a 700 W tool / blunt disc", "Reduce pressure, let the disc do the work; fit a fresh disc."),
            ("—", "Guard rotates during use", "Guard clamp not tightened", "Set the guard between work and operator and tighten the clamp screw."),
            ("—", "Burning smell from the vents", "Dust-clogged motor windings", "Unplug, blow out the vents with dry compressed air; service if the smell persists."),
        ],
    },
]


# ── HTML rendering ─────────────────────────────────────────────────────────────
CSS = """
@page {
  size: A4; margin: 20mm 18mm 24mm 18mm;
  @bottom-center {
    content: "Synthetic demo content — not an official Bosch document.";
    font-family: Arial, sans-serif; font-size: 8pt; color: #999;
  }
  @bottom-right { content: "Page " counter(page) " / " counter(pages);
    font-family: Arial, sans-serif; font-size: 8pt; color: #999; }
}
body { font-family: Arial, Helvetica, sans-serif; font-size: 10.5pt; color: #1a1a1a; line-height: 1.45; }
.cover { page-break-after: always; }
.cover .brand { font-size: 13pt; letter-spacing: 2px; color: #666; }
.cover h1 { font-size: 30pt; margin: 6px 0 2px; }
.cover .type { font-size: 15pt; color: #333; margin: 0 0 24px; }
.cover .tagline { font-size: 12pt; color: #444; max-width: 130mm; }
.cover .disclaimer { margin-top: 40mm; padding: 10px 14px; border: 2px solid #c0392b;
  color: #c0392b; font-weight: bold; font-size: 11pt; }
.meta { margin-top: 14px; color: #555; font-size: 9.5pt; }
h2 { font-size: 15pt; color: #c0392b; border-bottom: 2px solid #eee; padding-bottom: 3px;
  margin-top: 22px; page-break-after: avoid; }
h3 { font-size: 12pt; margin-top: 14px; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 10pt; }
th, td { border: 1px solid #ccc; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background: #f2f2f2; }
ul { margin: 6px 0 6px 0; padding-left: 20px; }
li { margin: 3px 0; }
.warn { background: #fdf2f2; border-left: 4px solid #c0392b; padding: 8px 12px; margin: 8px 0; }
.note { background: #f2f7fd; border-left: 4px solid #2980b9; padding: 8px 12px; margin: 8px 0; }
.small { font-size: 9pt; color: #666; }
"""


def _rows(pairs: list[tuple[str, str]]) -> str:
    return "".join(
        f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>" for k, v in pairs
    )


def _power_section(tool: dict) -> str:
    """Battery/Charging for cordless, Mains/Power supply for corded."""
    if tool["power"] == "cordless":
        return f"""
<h2>6. Battery &amp; Charging</h2>
<p>The {html.escape(tool['model'])} is powered by a Bosch Li-Ion battery pack (not always
supplied with the bare tool). Use only the charger specified for this battery system.</p>
<ul>
  <li>Insert the battery until it clicks; press the release button to remove it.</li>
  <li>Charge only at ambient temperatures between <strong>0 °C and 45 °C</strong>. Charging outside
      this range aborts and the charger LED signals a fault.</li>
  <li>A partially charged pack can be topped up at any time without harming cell life
      (no memory effect).</li>
  <li>For storage longer than a month, keep the pack at roughly <strong>40–60 %</strong> charge in a
      cool, dry place.</li>
  <li>The fuel-gauge LEDs show the state of charge when the button is pressed.</li>
</ul>
<div class="warn"><strong>Safety:</strong> never charge a damaged, swollen or wet battery, and
never short the terminals. Dispose of batteries at a collection point, not in household waste.</div>
"""
    return f"""
<h2>6. Mains Power Supply</h2>
<p>The {html.escape(tool['model'])} is a corded 230 V / 50 Hz tool. Check that the mains
voltage matches the rating plate before connecting.</p>
<ul>
  <li>Inspect the cable and plug before every use; a damaged cable must be replaced by an
      authorised service centre.</li>
  <li>Use an extension lead of <strong>≤ 30 m</strong> with a conductor cross-section of at least
      <strong>1.5 mm²</strong>; fully unwind cable reels to avoid overheating.</li>
  <li>Connect via a residual-current device (RCD) where required by local regulations.</li>
  <li>Route the cable behind the tool, away from the working area.</li>
</ul>
<div class="warn"><strong>Safety:</strong> always unplug the tool before changing accessories,
clearing a jam, or performing maintenance.</div>
"""


def render_html(tool: dict) -> str:
    faults = "".join(
        f"<tr><td>{html.escape(c)}</td><td>{html.escape(sym)}</td>"
        f"<td>{html.escape(cause)}</td><td>{html.escape(fix)}</td></tr>"
        for c, sym, cause, fix in tool["faults"]
    )
    model = html.escape(tool["model"])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{model} — Operating Manual (synthetic demo)</title>
<style>{CSS}</style></head>
<body>

<section class="cover">
  <div class="brand">BOSCH · {html.escape(tool['line'])}</div>
  <h1>{model}</h1>
  <p class="type">{html.escape(tool['type'])}</p>
  <p class="tagline">{html.escape(tool['tagline'])}</p>
  <p class="meta">Original Operating Instructions · Document ID: MAN-{html.escape(tool['id'].upper())} · Rev. A</p>
  <div class="disclaimer">{html.escape(DISCLAIMER)}<br>
  <span class="small">Generated for a Databricks demo. Specifications are representative of the
  product class and must not be used for real operation, service or purchasing decisions.</span></div>
</section>

<h2>1. Safety Warnings</h2>
<div class="warn"><strong>Read all safety warnings and instructions.</strong> Failure to follow
them may result in electric shock, fire and/or serious injury. Keep these instructions for
future reference.</div>
<h3>General power-tool safety</h3>
<ul>
  <li>Keep the work area clean and well lit; cluttered or dark areas invite accidents.</li>
  <li>Do not operate the tool in explosive atmospheres, e.g. near flammable liquids or dust.</li>
  <li>Wear eye protection, hearing protection and a dust mask appropriate to the task.</li>
  <li>Dress properly: no loose clothing or jewellery; keep hair away from moving parts.</li>
  <li>Remove any adjusting key or wrench before switching the tool on.</li>
  <li>Do not overreach; keep proper footing and balance at all times.</li>
</ul>
<h3>Tool-specific warnings</h3>
<ul>
  <li>Hold the tool by the insulated gripping surfaces; a hidden live wire can make metal
      parts live and give the operator an electric shock.</li>
  <li>Use the auxiliary handle(s) supplied; loss of control can cause injury.</li>
  <li>Wait until the tool has come to a complete stop before setting it down.</li>
</ul>

<h2>2. Technical Specifications</h2>
<p>Representative specifications for the {model} ({html.escape(tool['type'])}):</p>
<table><thead><tr><th>Specification</th><th>Value</th></tr></thead>
<tbody>{_rows(tool['specs'])}</tbody></table>
<p class="small">Noise/vibration values are omitted from this synthetic manual. Refer to the
official documentation for declared emission values.</p>

<h2>3. Intended Use</h2>
<p>The {model} is intended for {html.escape(tool['tagline'][0].lower() + tool['tagline'][1:])}
The user is responsible for any damage caused by use outside the intended purpose. Do not modify
the tool or use accessories other than those recommended for this model.</p>

<h2>4. Operating Instructions</h2>
<ol>
  <li>Fit the correct accessory and any auxiliary handle before starting work.</li>
  <li>Select the operating mode/gear appropriate to the material (see Technical Specifications).</li>
  <li>Position the tool against the workpiece <em>before</em> pressing the trigger.</li>
  <li>Apply steady, moderate pressure — let the tool do the work; excess force reduces
      performance and tool life.</li>
  <li>Release the trigger and wait for a complete stop before withdrawing the tool.</li>
</ol>
<div class="note"><strong>Tip:</strong> for the cleanest result, match speed/torque to the
material rather than forcing the feed rate.</div>

<h2>5. Maintenance &amp; Cleaning</h2>
<ul>
  <li>Disconnect the power source (unplug / remove the battery) before any maintenance.</li>
  <li>Keep the ventilation slots clear; blow out dust with dry compressed air regularly.</li>
  <li>Wipe the housing with a dry or slightly damp cloth — never use solvents.</li>
  <li>Inspect accessories (bits, discs, blades) before each use and replace worn items.</li>
  <li>Have repairs and internal service carried out only by an authorised service centre using
      genuine spare parts.</li>
</ul>

{_power_section(tool)}

<h2>7. Troubleshooting</h2>
<table><thead><tr><th>Code</th><th>Symptom</th><th>Probable cause</th><th>Remedy</th></tr></thead>
<tbody>{faults}</tbody></table>
<p class="small">Fault codes shown are synthetic and specific to this demo manual for the
{model}. If a fault persists after the remedy, stop using the tool and contact service.</p>

<h2>8. Warranty &amp; Service</h2>
<p>This synthetic demo assumes a standard manufacturer warranty against material and
manufacturing defects from the date of purchase, subject to correct use and the maintenance in
Section 5. Wear parts (carbon brushes, chuck, discs, blades, batteries) and damage from
overload or unauthorised repair are excluded.</p>
<ul>
  <li>Keep your proof of purchase; it is required for any warranty claim.</li>
  <li>For service, quote the model <strong>{model}</strong> and the document ID on the cover.</li>
  <li>Register the tool where a Professional-line extended warranty programme applies.</li>
</ul>
<p class="small">{html.escape(DISCLAIMER)} Service terms here are illustrative only.</p>

</body></html>
"""


# ── build steps ────────────────────────────────────────────────────────────────
def write_html(force: bool) -> list[Path]:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for tool in TOOLS:
        p = HTML_DIR / f"{tool['id']}.html"
        p.write_text(render_html(tool), encoding="utf-8")
        out.append(p)
    print(f"[html] wrote {len(out)} HTML manuals -> {HTML_DIR}")
    return out


def convert_pdfs(force: bool) -> list[Path]:
    try:
        from weasyprint import HTML  # noqa: WPS433 (import here to keep CLI import-light)
    except Exception as exc:  # pragma: no cover
        sys.exit(f"weasyprint is required to render PDFs ({exc}). Install with: uv pip install weasyprint")
    MANUALS_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = []
    for tool in TOOLS:
        html_path = HTML_DIR / f"{tool['id']}.html"
        pdf_path = MANUALS_DIR / f"{tool['id']}.pdf"
        if (not force and pdf_path.exists()
                and pdf_path.stat().st_mtime >= html_path.stat().st_mtime):
            pdfs.append(pdf_path)
            continue
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        pdfs.append(pdf_path)
    print(f"[pdf ] rendered {len(pdfs)} PDFs -> {MANUALS_DIR}")
    return pdfs


def upload(pdfs: list[Path], catalog: str, schema: str, volume: str, profile: str) -> None:
    base = f"dbfs:/Volumes/{catalog}/{schema}/{volume}/{VOLUME_SUBFOLDER}"
    # Upload each PDF individually (not `cp -r` on the dir) so the KA source folder
    # stays PDF-only — no local html/ scratch or .gitkeep leaking in as duplicate
    # retrieval content. This only ADDS to manuals/ and never touches the sibling
    # datasheets/ folder that IDP reads.
    print(f"[up  ] uploading {len(pdfs)} PDFs -> {base}/ (profile {profile})")
    for pdf in pdfs:
        subprocess.run(
            ["databricks", "fs", "cp", "--overwrite",
             str(pdf), f"{base}/{pdf.name}", "--profile", profile],
            check=True,
        )
    # verify
    ls = subprocess.run(
        ["databricks", "fs", "ls", base, "--profile", profile],
        check=True, capture_output=True, text=True,
    )
    listed = [ln for ln in ls.stdout.splitlines() if ln.strip()]
    print(f"[up  ] volume now lists {len(listed)} entries under {VOLUME_SUBFOLDER}/:")
    for ln in listed:
        print(f"         {ln}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate + upload synthetic Bosch demo manuals.")
    ap.add_argument("--catalog", default=DEFAULT_CATALOG)
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    ap.add_argument("--volume", default=DEFAULT_VOLUME)
    ap.add_argument("--profile", default=DEFAULT_PROFILE)
    ap.add_argument("--force", action="store_true", help="re-render PDFs even if up to date")
    ap.add_argument("--no-upload", action="store_true", help="generate PDFs locally only")
    args = ap.parse_args()

    write_html(args.force)
    pdfs = convert_pdfs(args.force)
    if args.no_upload:
        print("[done] --no-upload set; skipped Volume upload.")
        return
    upload(pdfs, args.catalog, args.schema, args.volume, args.profile)
    print(f"[done] {len(pdfs)} manuals in "
          f"/Volumes/{args.catalog}/{args.schema}/{args.volume}/{VOLUME_SUBFOLDER}/")


if __name__ == "__main__":
    main()
