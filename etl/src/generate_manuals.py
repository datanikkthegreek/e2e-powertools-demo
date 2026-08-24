#!/usr/bin/env python3
"""Download + upload REAL Bosch product manuals for the Knowledge Assistant demo.

Sources genuine, downloadable manual PDFs for the 12 demo tools and lands them in
the ``manuals/`` subfolder of the ``raw_docs`` UC Volume. **Real manuals only** —
nothing is synthesized. If a tool's real manual cannot be sourced, it is left out
and reported as unsourced (see the run summary at the end).

Sources, in priority order, per tool:

  1. EXPLICIT URL (``MANUAL_URLS`` below, preferred) — the tool's genuine Bosch
     operating-instructions PDF on Bosch's own hosts (``bosch-professional.com``
     and regional ``media.*.bosch-pt.*`` CDNs, under ``/binary/manualsmedia/
     o<NNNNNN>v21_<docnum>_<YYYYMM>.pdf``). These are the real multilingual
     operating booklets; each was located from the tool's official Bosch product
     page. A couple of user-supplied URLs point at other public manual hosts
     (e.g. device.report) — those are fetched with browser-style headers.
  2. INTERNET ARCHIVE fallback (archive.org) — only for tools with no explicit
     URL. Query the IA advanced-search JSON API, STRICT-match the candidate item's
     title against the tool's exact model designation (spaces ignored, so a
     "GST 18 V-LI" manual is NOT accepted for "GST 18V-LI S"), pick its PDF.

Every candidate PDF — explicit or archive.org — is then verified (``%PDF`` header,
non-trivial size, > 1 page) before it is allowed to be uploaded, and each verified
PDF is uploaded individually to the manuals/ Volume subfolder.

Idempotent / additive: a tool whose verified PDF is already present locally AND
in the Volume is skipped; ``--overwrite`` on upload only replaces same-named PDFs
in manuals/ (never deletes anything, never touches the sibling datasheets/ folder
or the Volume root). Downloaded PDFs are git-ignored (etl/data/manuals/*.pdf).

Note on coverage: the demo tool list is deliberately modern (18 V ProCORE / recent
DIY). Several models legitimately resolve to "unsourced" — a US-only model whose
public copy is bot-walled, or discontinued DIY tools Bosch now serves only as
HTML / a 1-page Declaration of Conformity (no multi-page PDF). That is reported,
not faked.

Usage:
  python etl/src/generate_manuals.py                 # download + upload (defaults)
  python etl/src/generate_manuals.py --no-upload     # download + verify only
  python etl/src/generate_manuals.py --force         # re-download even if present
  python etl/src/generate_manuals.py --only gbh-2-26 # one tool (repeatable)
  python etl/src/generate_manuals.py \
      --catalog nikks_fevm_workspace_7405607030687545 \
      --schema techsummit --volume raw_docs --profile FEVM
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# ── defaults (match etl/databricks.yml vars + the demo guardrails) ─────────────
DEFAULT_CATALOG = "nikks_fevm_workspace_7405607030687545"
DEFAULT_SCHEMA = "techsummit"
DEFAULT_VOLUME = "raw_docs"
DEFAULT_PROFILE = "FEVM"
# NEW subfolder inside the existing MANAGED volume; the sibling datasheets/
# folder (IDP source) is never touched.
VOLUME_SUBFOLDER = "manuals"

# Local output dir (relative to repo root, resolved from this file's location).
REPO_ROOT = Path(__file__).resolve().parents[2]
MANUALS_DIR = REPO_ROOT / "etl" / "data" / "manuals"

# Polite networking. USER_AGENT is used for the archive.org JSON API; PDF
# downloads use a browser-style UA + Accept/Referer so Bosch CDNs and other
# public manual hosts (e.g. device.report behind Cloudflare) serve the file.
USER_AGENT = (
    "powertools-demo-manual-fetcher/1.0 "
    "(Databricks demo; sourcing public Bosch manuals)"
)
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_DELAY_S = 0.6  # small delay between network calls
MIN_PDF_BYTES = 50_000  # a real multi-page manual is well above this

ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"
ARCHIVE_METADATA = "https://archive.org/metadata"
ARCHIVE_DOWNLOAD = "https://archive.org/download"


# ── tool identity + search mapping ─────────────────────────────────────────────
# id: output filename stem (matches the datasheet filenames in etl/data/datasheets/)
# model: the exact Bosch model designation used both to query and to STRICT-match
#        candidate titles (see _matches()).
# type: human label, for the run summary only.
TOOLS: list[dict] = [
    {"id": "gbh-18v-26-f", "model": "GBH 18V-26 F", "type": "Cordless Rotary Hammer"},
    {"id": "gbh-2-26", "model": "GBH 2-26", "type": "Corded Rotary Hammer"},
    {"id": "gsb-18v-90-c", "model": "GSB 18V-90 C", "type": "Cordless Combi Drill"},
    {"id": "gsr-12v-35", "model": "GSR 12V-35", "type": "Cordless Drill/Driver"},
    {"id": "gsr-18v-55", "model": "GSR 18V-55", "type": "Cordless Drill/Driver"},
    {"id": "gst-18v-li-s", "model": "GST 18V-LI S", "type": "Cordless Jigsaw"},
    {"id": "gws-18v-10", "model": "GWS 18V-10", "type": "Cordless Angle Grinder"},
    {"id": "gws-22-230-jh", "model": "GWS 22-230 JH", "type": "Corded Angle Grinder"},
    {"id": "pbh-2100-re", "model": "PBH 2100 RE", "type": "Corded Rotary Hammer"},
    {"id": "psb-1800-li-2", "model": "PSB 1800 LI-2", "type": "Cordless Impact Drill"},
    {"id": "psr-1080-li", "model": "PSR 1080 LI", "type": "Cordless Drill/Driver"},
    {"id": "pws-700-115", "model": "PWS 700-115", "type": "Corded Angle Grinder"},
]

# ── explicit URL map (source of truth; checked BEFORE the archive.org fallback) ──
# Each URL is the tool's genuine Bosch operating-instructions PDF, located from the
# tool's official Bosch product page. Most are the real multilingual operating
# booklets on Bosch's own hosts (bosch-professional.com + regional media.*.bosch-pt.*
# CDNs, /binary/manualsmedia/o<NNNNNN>v21_<docnum>_<YYYYMM>.pdf — docnum series
# 160992A… = operating instructions). Verified downloadable + > 1 page:
#   gbh-18v-26-f    o431771…934  ~13 MB      gsb-18v-90-c   o482410…9RL  ~11 MB
#   gsr-12v-35      o518746…9UY  ~3.9 MB     gst-18v-li-s   o394849…861  ~7.4 MB
#   gws-18v-10      o398946…7ZT  142 pages   gws-22-230-jh  o612481…D4D  355 pages
# gsr-18v-55 is a US-market model absent from the EU Bosch catalog; the only public
# copy found (device.report) sits behind Cloudflare and 403s even with browser
# headers — it is wired in here so the attempt is genuine, but it verifies as
# unsourced live (never faked). Tools with NO entry fall back to archive.org:
#   gbh-2-26 sources there (real 139-page booklet); the discontinued DIY tools
#   (pbh-2100-re, psb-1800-li-2, psr-1080-li, pws-700-115) have no multi-page PDF
#   on Bosch's site and correctly resolve to unsourced.
MANUAL_URLS: dict[str, str] = {
    "gbh-18v-26-f": "https://www.bosch-professional.com/binary/manualsmedia/o431771v21_160992A934_202309.pdf",
    "gsb-18v-90-c": "https://www.bosch-professional.com/binary/manualsmedia/o482410v21_160992A9RL_202409.pdf",
    "gsr-12v-35": "https://media.bosch-pt.com.my/binary/manualsmedia/o518746v21_160992A9UY_202412.pdf",
    "gst-18v-li-s": "https://www.bosch-professional.com/binary/manualsmedia/o394849v21_160992A861_202207.pdf",
    "gws-18v-10": "https://media.vn.bosch-pt.com/binary/manualsmedia/o398946v21_160992A7ZT_202209.pdf",
    "gws-22-230-jh": "https://www.bosch-professional.com/binary/manualsmedia/o612481v21_160992AD4D_202510.pdf",
    "gsr-18v-55": "https://device.report/m/512aebc6e0d13e92aa9c018dd2bcbe76e6622e7ff879918a8d6837548591c97a.pdf",
}


# ── matching ───────────────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    """Uppercase and strip spaces so 'GBH 2-26' == 'GBH2-26' for substring tests."""
    return "".join((s or "").upper().split())


def _matches(model: str, title: str) -> bool:
    """True iff the exact model designation appears in the candidate title.

    Space-insensitive substring test on the full model. This is deliberately
    strict: it accepts an official multi-model family booklet whose title lists
    the exact model (e.g. 'GBH 2-26' inside 'GBH 2-26 E … DFR Professional …')
    but rejects a different variant ('GST 18 V-LI' for 'GST 18V-LI S').
    """
    return _norm(model) in _norm(title)


# ── Internet Archive access ─────────────────────────────────────────────────────
def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _search_identifiers(model: str, rows: int = 8) -> list[dict]:
    """Return candidate IA items ({identifier, title}) for a Bosch model query."""
    query = f'title:("Bosch {model}") AND mediatype:texts'
    url = ARCHIVE_SEARCH + "?" + urllib.parse.urlencode(
        [("q", query), ("fl[]", "identifier"), ("fl[]", "title"),
         ("rows", rows), ("output", "json")]
    )
    docs = _get_json(url).get("response", {}).get("docs", [])
    return [{"identifier": d.get("identifier"), "title": d.get("title", "")} for d in docs]


def _pick_pdf(identifier: str) -> tuple[str, int] | None:
    """Return (download_url, size) of the largest PDF in an IA item, or None."""
    meta = _get_json(f"{ARCHIVE_METADATA}/{identifier}")
    best = None
    for f in meta.get("files", []):
        name = f.get("name", "")
        if name.lower().endswith(".pdf"):
            size = int(f.get("size", 0) or 0)
            if best is None or size > best[1]:
                enc = urllib.parse.quote(name)
                best = (f"{ARCHIVE_DOWNLOAD}/{identifier}/{enc}", size)
    return best


def _download(url: str, dest: Path) -> int:
    """Fetch a PDF with browser-style headers (UA + Accept + same-host Referer)."""
    parsed = urllib.parse.urlparse(url)
    headers = {
        "User-Agent": BROWSER_UA,
        "Accept": "application/pdf,application/octet-stream,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"{parsed.scheme}://{parsed.netloc}/",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return len(data)


# ── PDF verification (real PDF, >1 page) ────────────────────────────────────────
def verify_pdf(path: Path) -> tuple[bool, str]:
    """Return (ok, detail). Requires %PDF header, non-trivial size, and > 1 page."""
    try:
        size = path.stat().st_size
    except OSError as exc:
        return False, f"stat failed: {exc}"
    if size < MIN_PDF_BYTES:
        return False, f"too small ({size} bytes)"
    with path.open("rb") as fh:
        head = fh.read(5)
    if head != b"%PDF-":
        return False, f"not a PDF (header {head!r})"
    try:
        from pypdf import PdfReader  # lazy import; verification-only dependency

        pages = len(PdfReader(str(path)).pages)
        if pages <= 1:
            return False, f"only {pages} page(s)"
        return True, f"{size} bytes, {pages} pages"
    except ModuleNotFoundError:
        # pypdf not installed — fall back to a structural check.
        tail = path.read_bytes()[-1024:]
        if b"%%EOF" not in tail:
            return False, "missing %%EOF trailer"
        return True, f"{size} bytes (page count unverified: install pypdf)"
    except Exception as exc:  # corrupt/encrypted PDF
        return False, f"unreadable PDF: {exc}"


# ── download step ────────────────────────────────────────────────────────────────
def source_manual(tool: dict, force: bool) -> dict:
    """Try to source one tool's real manual. Returns a result dict for reporting."""
    tid, model = tool["id"], tool["model"]
    dest = MANUALS_DIR / f"{tid}.pdf"

    if not force and dest.exists():
        ok, detail = verify_pdf(dest)
        if ok:
            print(f"[skip] {tid}: already have a verified PDF ({detail})")
            return {"id": tid, "status": "present", "path": dest, "detail": detail}

    # 1) explicit URL (preferred). On success we are done; on failure we fall
    #    through to the archive.org search below.
    explicit = MANUAL_URLS.get(tid)
    if explicit:
        print(f"[url ] {tid}: fetching explicit Bosch URL {explicit}")
        try:
            MANUALS_DIR.mkdir(parents=True, exist_ok=True)
            _download(explicit, dest)
            ok, detail = verify_pdf(dest)
            if ok:
                print(f"[ok  ] {tid}: verified real manual ({detail}) from explicit URL")
                return {"id": tid, "status": "sourced", "path": dest,
                        "detail": detail, "source": explicit}
            print(f"[warn] {tid}: explicit URL PDF failed verification ({detail})")
            dest.unlink(missing_ok=True)
        except Exception as exc:
            print(f"[warn] {tid}: explicit URL failed: {exc}")
            dest.unlink(missing_ok=True)
        time.sleep(REQUEST_DELAY_S)

    print(f"[find] {tid}: searching archive.org for 'Bosch {model}'")
    try:
        candidates = _search_identifiers(model)
    except Exception as exc:
        print(f"[warn] {tid}: search failed: {exc}")
        return {"id": tid, "status": "unsourced", "detail": f"search error: {exc}"}
    time.sleep(REQUEST_DELAY_S)

    matched = [c for c in candidates if c["identifier"] and _matches(model, c["title"])]
    if not matched:
        titles = ", ".join(c["title"] for c in candidates[:4]) or "no results"
        print(f"[miss] {tid}: no exact-model match (saw: {titles})")
        return {"id": tid, "status": "unsourced", "detail": f"no exact match; saw: {titles}"}

    for cand in matched:
        ident, title = cand["identifier"], cand["title"]
        try:
            pdf = _pick_pdf(ident)
            time.sleep(REQUEST_DELAY_S)
            if not pdf:
                print(f"[miss] {tid}: item {ident} has no PDF file")
                continue
            url, size = pdf
            print(f"[get ] {tid}: {title!r} -> {ident} ({size} bytes)")
            MANUALS_DIR.mkdir(parents=True, exist_ok=True)
            _download(url, dest)
            ok, detail = verify_pdf(dest)
            if not ok:
                print(f"[warn] {tid}: downloaded PDF failed verification ({detail})")
                dest.unlink(missing_ok=True)
                continue
            print(f"[ok  ] {tid}: verified real manual ({detail}) from {ident}")
            return {"id": tid, "status": "sourced", "path": dest,
                    "detail": detail, "source": f"archive.org/details/{ident}"}
        except Exception as exc:
            print(f"[warn] {tid}: candidate {ident} failed: {exc}")
            time.sleep(REQUEST_DELAY_S)
            continue

    return {"id": tid, "status": "unsourced", "detail": "matched items had no usable PDF"}


# ── upload step ──────────────────────────────────────────────────────────────────
def _volume_listing(base: str, profile: str) -> set[str]:
    """Names already present under manuals/ (empty set if the folder is new)."""
    res = subprocess.run(
        ["databricks", "fs", "ls", base, "--profile", profile],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        return set()
    return {ln.strip().split("/")[-1] for ln in res.stdout.splitlines() if ln.strip()}


def upload(results: list[dict], catalog: str, schema: str, volume: str,
           profile: str, force: bool) -> None:
    base = f"dbfs:/Volumes/{catalog}/{schema}/{volume}/{VOLUME_SUBFOLDER}"
    to_upload = [r for r in results if r.get("path")]
    if not to_upload:
        print("[up  ] nothing to upload (no sourced manuals).")
        return

    present = _volume_listing(base, profile)
    # Upload each PDF individually (not `cp -r` on the dir) so the KA source folder
    # stays PDF-only. Additive at the folder level: --overwrite replaces a
    # same-named PDF in manuals/ (idempotent) but nothing is ever deleted, and the
    # sibling datasheets/ folder + Volume root are never touched.
    print(f"[up  ] uploading to {base}/ (profile {profile})")
    for r in to_upload:
        name = r["path"].name
        if not force and name in present:
            print(f"[up  ] {name}: already in Volume — skipping (additive/idempotent)")
            continue
        subprocess.run(
            ["databricks", "fs", "cp", "--overwrite",
             str(r["path"]), f"{base}/{name}", "--profile", profile],
            check=True,
        )
        print(f"[up  ] uploaded {name}")


# ── run summary ────────────────────────────────────────────────────────────────
def print_summary(results: list[dict]) -> None:
    sourced = [r for r in results if r["status"] in ("sourced", "present")]
    unsourced = [r for r in results if r["status"] == "unsourced"]
    print("\n" + "=" * 68)
    print(f"RUN SUMMARY — {len(sourced)}/{len(results)} real manuals sourced")
    print("=" * 68)
    for r in results:
        mark = {"sourced": "OK ", "present": "OK ", "unsourced": "-- "}[r["status"]]
        extra = r.get("source", "") or r.get("detail", "")
        print(f"  {mark} {r['id']:<16} {r['status']:<10} {extra}")
    if unsourced:
        print(f"\n  UNSOURCED ({len(unsourced)}): "
              + ", ".join(r["id"] for r in unsourced))
        print("  No real manual was found for these on the source; left out (not faked).")


def main() -> None:
    ap = argparse.ArgumentParser(description="Download + upload real Bosch demo manuals.")
    ap.add_argument("--catalog", default=DEFAULT_CATALOG)
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    ap.add_argument("--volume", default=DEFAULT_VOLUME)
    ap.add_argument("--profile", default=DEFAULT_PROFILE)
    ap.add_argument("--force", action="store_true", help="re-download even if present")
    ap.add_argument("--no-upload", action="store_true", help="download + verify only")
    ap.add_argument("--only", action="append", default=None,
                    help="restrict to this tool id (repeatable)")
    args = ap.parse_args()

    tools = TOOLS
    if args.only:
        wanted = set(args.only)
        tools = [t for t in TOOLS if t["id"] in wanted]
        if not tools:
            sys.exit(f"--only {args.only} matched no tool ids in TOOLS")

    results = [source_manual(t, args.force) for t in tools]

    if not args.no_upload:
        upload(results, args.catalog, args.schema, args.volume, args.profile, args.force)
    else:
        print("[done] --no-upload set; skipped Volume upload.")

    print_summary(results)


if __name__ == "__main__":
    main()
