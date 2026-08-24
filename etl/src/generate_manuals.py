#!/usr/bin/env python3
"""Download + upload REAL Bosch product manuals for the Knowledge Assistant demo.

Sources genuine, downloadable manual PDFs for the 12 demo tools and lands them in
the ``manuals/`` subfolder of the ``raw_docs`` UC Volume. **Real manuals only** —
nothing is synthesized. If a tool's real manual cannot be sourced, it is left out
and reported as unsourced (see the run summary at the end).

Sources, in priority order, per tool:

  1. EXPLICIT URL (``MANUAL_URLS``, preferred) — the tool's genuine Bosch
     operating-instructions PDF on Bosch's own hosts (``bosch-professional.com``
     and regional ``media.*.bosch-pt.*`` CDNs, under ``/binary/manualsmedia/
     o<NNNNNN>v21_<docnum>_<YYYYMM>.pdf``, plus a ``bosch-diy.com/storage/…`` DIY
     manual). These are the real multilingual operating booklets, each located
     from the tool's official Bosch product page, fetched with browser-style
     headers. Eight of the twelve tools source this way (seven URLs + gbh-2-26
     via step 3).
  2. LOCAL FILE (``LOCAL_MANUALS``) — four manuals whose sources block scripted
     download (gsr-18v-55 behind Cloudflare; three discontinued DIY models absent
     from Bosch's catalogs) were downloaded manually via a browser. The script
     copies ``<--local-dir>/<filename>`` (default ~/Downloads) into
     etl/data/manuals/<tool-id>.pdf. If a local file is missing the tool is
     reported (the run does not fail); a file already staged at the destination is
     reused.
  3. INTERNET ARCHIVE fallback (archive.org) — only for tools with no explicit URL
     or local entry (gbh-2-26). Query the IA advanced-search JSON API, STRICT-match
     the candidate item's title against the tool's exact model designation.

Every candidate PDF — URL, local, or archive.org — is then verified (``%PDF``
header, non-trivial size, > 1 page) before it is allowed to be uploaded, and each
verified PDF is uploaded individually to the manuals/ Volume subfolder.

Two entries are honest NEAREST-VARIANT substitutions for discontinued tools with
no exact PDF (pbh-2100-re → Bosch PBH 2500 SRE; psr-1080-li → Bosch PSB 1080 LI-2)
and one is a family booklet (gws-22-230-jh → GWS 22-230 J/P line). These are real
Bosch manuals and are flagged as variants in the run summary (see VARIANT_NOTES).

Idempotent / additive: a tool whose verified PDF is already present locally AND
in the Volume is skipped; ``--overwrite`` on upload only replaces same-named PDFs
in manuals/ (never deletes anything, never touches the sibling datasheets/ folder
or the Volume root). Downloaded PDFs are git-ignored (etl/data/manuals/*.pdf).

Usage:
  python etl/src/generate_manuals.py                 # download + upload (defaults)
  python etl/src/generate_manuals.py --no-upload     # download + verify only
  python etl/src/generate_manuals.py --force         # re-fetch even if present
  python etl/src/generate_manuals.py --only gbh-2-26 # one tool (repeatable)
  python etl/src/generate_manuals.py --local-dir ~/Downloads   # browser-only manuals
  python etl/src/generate_manuals.py \
      --catalog nikks_fevm_workspace_7405607030687545 \
      --schema techsummit --volume raw_docs --profile FEVM
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
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
# Where the browser-only manuals (LOCAL_MANUALS) are expected to sit; override
# with --local-dir. Defaults to the user's Downloads folder.
DEFAULT_LOCAL_DIR = Path.home() / "Downloads"

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

# ── explicit URL map (scriptable download; checked BEFORE the archive.org fallback)
# Each URL is a tool's genuine Bosch operating-instructions PDF, located from the
# tool's official Bosch product page. Most are the real multilingual operating
# booklets on Bosch's own hosts (bosch-professional.com + regional media.*.bosch-pt.*
# CDNs, /binary/manualsmedia/o<NNNNNN>v21_<docnum>_<YYYYMM>.pdf — docnum series
# 160992A… = operating instructions). Verified downloadable + > 1 page:
#   gbh-18v-26-f   o431771…934  307p        gsb-18v-90-c   o482410…9RL  283p
#   gsr-12v-35     o518746…9UY   69p        gst-18v-li-s   o394849…861  279p
#   gws-18v-10     o398946…7ZT  142p        gws-22-230-jh  o612481…D4D  355p
# pbh-2100-re: the discontinued Corded Rotary Hammer has no multi-page PDF of its
#   own (Bosch DIY serves only a 1-page Declaration of Conformity for it), so this
#   points at the Bosch PBH 2500 SRE manual — the NEAREST-VARIANT in the same
#   rotary-hammer family (flagged as a variant substitution; see VARIANT_NOTES).
# Tools with NO entry here fall back to archive.org (gbh-2-26 → real 139-page
# booklet). Four more are browser-only local files (see LOCAL_MANUALS).
MANUAL_URLS: dict[str, str] = {
    "gbh-18v-26-f": "https://www.bosch-professional.com/binary/manualsmedia/o431771v21_160992A934_202309.pdf",
    "gsb-18v-90-c": "https://www.bosch-professional.com/binary/manualsmedia/o482410v21_160992A9RL_202409.pdf",
    "gsr-12v-35": "https://media.bosch-pt.com.my/binary/manualsmedia/o518746v21_160992A9UY_202412.pdf",
    "gst-18v-li-s": "https://www.bosch-professional.com/binary/manualsmedia/o394849v21_160992A861_202207.pdf",
    "gws-18v-10": "https://media.vn.bosch-pt.com/binary/manualsmedia/o398946v21_160992A7ZT_202209.pdf",
    "gws-22-230-jh": "https://www.bosch-professional.com/binary/manualsmedia/o612481v21_160992AD4D_202510.pdf",
    "pbh-2100-re": "https://www.bosch-diy.com/storage/en-sa/pbh-2500-sre-100033101-original-pdf-368315-en-sa.pdf",
}

# ── local file map (browser-only sources; staged from a local path, no download) ─
# These four sources block scripted download — gsr-18v-55's public copy sits behind
# Cloudflare (device.report) and the discontinued DIY models are absent from Bosch's
# online catalogs — so the manuals were downloaded manually via a browser. At run
# time the script copies <local_dir>/<filename> (default local_dir = ~/Downloads)
# into etl/data/manuals/<tool-id>.pdf and verifies it like any other candidate. If
# the file is instead already staged as etl/data/manuals/<tool-id>.pdf it is reused;
# if neither exists the tool is reported "local source missing" (the run does not
# fail). All four were verified real, multi-page PDFs.
LOCAL_MANUALS: dict[str, dict] = {
    "gsr-18v-55": {
        "filename": "512aebc6e0d13e92aa9c018dd2bcbe76e6622e7ff879918a8d6837548591c97a.pdf",
        "origin": "browser-download from device.report (Cloudflare-blocks scripts); GSR 18V-55, 227p, exact model",
    },
    "pws-700-115": {
        "filename": "18f72f.pdf",
        "origin": "browser-download; discontinued, absent from Bosch catalog; PWS 700-115, 38p, exact model",
    },
    "psr-1080-li": {
        "filename": "a28d32.pdf",
        "origin": "browser-download from manualslib.de; NEAREST-VARIANT — this is the Bosch PSB 1080 LI-2 booklet (214p, same 1080 LI platform), the discontinued PSR 1080 LI has no exact PDF",
    },
    "psb-1800-li-2": {
        "filename": "41bbc4.pdf",
        "origin": "browser-download; discontinued, absent from Bosch catalog; PSB 1800 LI-2, 193p, exact model",
    },
}

# ── variant / family substitution notes (real manuals that are NOT the exact model)
# Surfaced in the run summary so the reader knows the coverage is honest.
VARIANT_NOTES: dict[str, str] = {
    "pbh-2100-re": "variant: Bosch PBH 2500 SRE manual (nearest rotary-hammer family member)",
    "psr-1080-li": "variant: Bosch PSB 1080 LI-2 manual (nearest 1080 LI family member)",
    "gws-22-230-jh": "family booklet: GWS 22-230 J/P line (JH is a kit variant of that base tool)",
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
def _require_pypdf() -> None:
    """Abort up front unless pypdf is importable.

    pypdf is a MANDATORY dependency: without it we cannot confirm a candidate's
    page count, and a 1-page Declaration-of-Conformity stub would sail past a
    header+size check. Rather than silently accept unverified PDFs, fail closed
    with an actionable message. Called at the top of main() so --help still works
    without pypdf installed.
    """
    try:
        import pypdf  # noqa: F401
    except ModuleNotFoundError:
        sys.exit(
            "pypdf is REQUIRED for manual verification (the > 1 page check) but is "
            "not installed. Install the pinned deps and re-run:\n"
            "    pip install -r etl/requirements.txt\n"
            "Aborting: no manual is accepted without a verified page count."
        )


def verify_pdf(path: Path) -> tuple[bool, str]:
    """Return (ok, detail). A manual is accepted ONLY when the %PDF header, a
    non-trivial size, AND a pypdf-confirmed page count > 1 are all present.

    pypdf is mandatory (main() aborts via _require_pypdf if it is missing); this
    function reasserts it defensively and treats a missing pypdf as a failure
    rather than a pass, so verification can never silently degrade.
    """
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
        from pypdf import PdfReader  # mandatory; _require_pypdf enforces presence
    except ModuleNotFoundError:
        return False, "pypdf not installed (required for page-count verification)"
    try:
        pages = len(PdfReader(str(path)).pages)
    except Exception as exc:  # corrupt/encrypted PDF
        return False, f"unreadable PDF: {exc}"
    if pages <= 1:
        return False, f"only {pages} page(s)"
    return True, f"{size} bytes, {pages} pages"


# ── atomic staging (verify a temp copy, then replace dest only on success) ───────
def _stage_atomically(dest: Path, populate) -> tuple[bool, str]:
    """Write via ``populate(tmp)`` into a temp file, verify it, and atomically
    replace ``dest`` ONLY if verification passes.

    A failed fetch/copy — or a candidate that fails verification — never touches
    an already-valid ``dest``, so ``--force`` cannot destroy a previously-cached
    good manual when a re-fetch fails. The temp file lives in MANUALS_DIR (same
    filesystem) so ``os.replace`` is a true atomic rename.
    """
    MANUALS_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(MANUALS_DIR), prefix=f".{dest.stem}.", suffix=".pdf.tmp"
    )
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        populate(tmp)
        ok, detail = verify_pdf(tmp)
        if ok:
            os.replace(tmp, dest)
            return ok, detail
        tmp.unlink(missing_ok=True)
        return ok, detail
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


# ── download step ────────────────────────────────────────────────────────────────
def source_manual(tool: dict, force: bool, local_dir: Path) -> dict:
    """Try to source one tool's real manual. Returns a result dict for reporting.

    Precedence: already-staged verified PDF → explicit URL (MANUAL_URLS) → local
    browser-download (LOCAL_MANUALS) → archive.org search. A tool listed in
    LOCAL_MANUALS whose file is missing is reported (not crashed) and does NOT fall
    through to archive.org (there is no scriptable source for it).
    """
    tid, model = tool["id"], tool["model"]
    dest = MANUALS_DIR / f"{tid}.pdf"
    note = VARIANT_NOTES.get(tid)

    if not force and dest.exists():
        ok, detail = verify_pdf(dest)
        if ok:
            print(f"[skip] {tid}: already have a verified PDF ({detail})")
            return {"id": tid, "status": "present", "path": dest, "detail": detail,
                    "note": note}

    # 1) explicit URL (preferred). On success we are done; on failure we fall
    #    through to the archive.org search below.
    explicit = MANUAL_URLS.get(tid)
    if explicit:
        print(f"[url ] {tid}: fetching explicit Bosch URL {explicit}")
        try:
            ok, detail = _stage_atomically(dest, lambda tmp: _download(explicit, tmp))
            if ok:
                print(f"[ok  ] {tid}: verified real manual ({detail}) from explicit URL")
                return {"id": tid, "status": "sourced", "path": dest,
                        "detail": detail, "source": explicit, "note": note}
            print(f"[warn] {tid}: explicit URL PDF failed verification ({detail})")
        except Exception as exc:
            print(f"[warn] {tid}: explicit URL failed: {exc}")
        time.sleep(REQUEST_DELAY_S)

    # 2) local browser-download (LOCAL_MANUALS). Terminal for these tools — no
    #    scriptable fallback, so a missing file is reported, not searched.
    local = LOCAL_MANUALS.get(tid)
    if local:
        src = local_dir / local["filename"]
        print(f"[local] {tid}: staging from {src}")
        if not src.exists():
            print(f"[miss] {tid}: local source missing ({src})")
            return {"id": tid, "status": "unsourced",
                    "detail": f"local source missing: {src}", "note": note}
        try:
            ok, detail = _stage_atomically(dest, lambda tmp: shutil.copyfile(src, tmp))
            if ok:
                print(f"[ok  ] {tid}: verified real manual ({detail}) from local file")
                return {"id": tid, "status": "sourced", "path": dest, "detail": detail,
                        "source": f"local:{local['filename']} ({local['origin']})",
                        "note": note}
            print(f"[warn] {tid}: local PDF failed verification ({detail})")
        except Exception as exc:
            print(f"[warn] {tid}: local staging failed: {exc}")
        return {"id": tid, "status": "unsourced",
                "detail": f"local file present but unusable: {src}", "note": note}

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
            ok, detail = _stage_atomically(dest, lambda tmp: _download(url, tmp))
            if not ok:
                print(f"[warn] {tid}: downloaded PDF failed verification ({detail})")
                continue
            print(f"[ok  ] {tid}: verified real manual ({detail}) from {ident}")
            return {"id": tid, "status": "sourced", "path": dest,
                    "detail": detail, "source": f"archive.org/details/{ident}",
                    "note": note}
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
        if r.get("note"):
            print(f"      ↳ {r['note']}")
    variants = [r for r in results if r.get("note") and r["status"] in ("sourced", "present")]
    if variants:
        print(f"\n  VARIANT/FAMILY substitutions ({len(variants)}): "
              + ", ".join(r["id"] for r in variants))
        print("  Real Bosch manuals, but not the exact model — noted, not exact-match.")
    if unsourced:
        print(f"\n  UNSOURCED ({len(unsourced)}): "
              + ", ".join(r["id"] for r in unsourced))
        print("  No real manual was found for these on the source; left out (not faked).")


# ── startup validation (route coverage + target guardrails) ──────────────────────
def _validate_routes() -> None:
    """Every tool id must resolve to exactly ONE source route.

    A tool sources via its explicit URL (MANUAL_URLS), a local browser-download
    (LOCAL_MANUALS), or — for ids in neither map — the archive.org fallback. This
    asserts the maps are coherent at startup: no duplicate tool ids, no id in BOTH
    the URL and local maps (ambiguous route), and neither map referencing an
    unknown id. Ids in neither map take the archive fallback (a valid single
    route), so no id can be 'missing'. Fails closed on any coverage gap.
    """
    tool_ids = [t["id"] for t in TOOLS]
    dupes = sorted({tid for tid in tool_ids if tool_ids.count(tid) > 1})
    if dupes:
        sys.exit(f"[config] duplicate tool id(s) in TOOLS: {dupes}")
    known = set(tool_ids)
    unknown_url = sorted(set(MANUAL_URLS) - known)
    if unknown_url:
        sys.exit(f"[config] MANUAL_URLS references unknown tool id(s): {unknown_url}")
    unknown_local = sorted(set(LOCAL_MANUALS) - known)
    if unknown_local:
        sys.exit(f"[config] LOCAL_MANUALS references unknown tool id(s): {unknown_local}")
    both = sorted(set(MANUAL_URLS) & set(LOCAL_MANUALS))
    if both:
        sys.exit(f"[config] tool id(s) in BOTH URL and local routes (ambiguous): {both}")


def _validate_target(catalog: str, schema: str, volume: str,
                     allow_catalog_override: bool) -> None:
    """Fail closed BEFORE any Volume write if the target looks wrong or unsafe.

    Guardrails: reject '/'/'..'/whitespace in any component (path-redirection);
    the schema must be 'techsummit' (this demo operates ONLY there); the 'cdp'
    catalog/schema is never touched; and the catalog must be the FEVM default
    unless --allow-catalog-override is passed.
    """
    for label, val in (("catalog", catalog), ("schema", schema), ("volume", volume)):
        if not val or "/" in val or ".." in val or any(c.isspace() for c in val):
            sys.exit(f"[guard] invalid {label} {val!r}: must be non-empty and free "
                     "of '/', '..', and whitespace")
    if "cdp" in (catalog, schema):
        sys.exit("[guard] refusing to touch the 'cdp' catalog/schema")
    if schema != DEFAULT_SCHEMA:
        sys.exit(f"[guard] schema must be '{DEFAULT_SCHEMA}' (got {schema!r}); this "
                 "demo operates ONLY in techsummit")
    if catalog != DEFAULT_CATALOG and not allow_catalog_override:
        sys.exit(f"[guard] catalog must be the FEVM default '{DEFAULT_CATALOG}' "
                 f"(got {catalog!r}); pass --allow-catalog-override to target another")


def main() -> None:
    ap = argparse.ArgumentParser(description="Download + upload real Bosch demo manuals.")
    ap.add_argument("--catalog", default=DEFAULT_CATALOG)
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    ap.add_argument("--volume", default=DEFAULT_VOLUME)
    ap.add_argument("--profile", default=DEFAULT_PROFILE)
    ap.add_argument("--force", action="store_true", help="re-download even if present")
    ap.add_argument("--no-upload", action="store_true", help="download + verify only")
    ap.add_argument("--allow-partial", action="store_true",
                    help="upload the verified subset even if some expected tools "
                         "did not source (default: fail closed, upload nothing)")
    ap.add_argument("--allow-catalog-override", action="store_true",
                    help="permit a --catalog other than the FEVM default")
    ap.add_argument("--local-dir", default=str(DEFAULT_LOCAL_DIR),
                    help="folder holding the browser-only manuals (LOCAL_MANUALS); "
                         f"default {DEFAULT_LOCAL_DIR}")
    ap.add_argument("--only", action="append", default=None,
                    help="restrict to this tool id (repeatable)")
    args = ap.parse_args()

    # pypdf is mandatory for verification; abort now (after argparse, so --help works).
    _require_pypdf()
    # Coherent source-route config is a precondition for a trustworthy run.
    _validate_routes()

    local_dir = Path(args.local_dir).expanduser()

    tools = TOOLS
    if args.only:
        known = {t["id"] for t in TOOLS}
        bad = [tid for tid in args.only if tid not in known]
        if bad:
            sys.exit(f"--only: unknown tool id(s): {', '.join(bad)}. "
                     f"Known ids: {', '.join(t['id'] for t in TOOLS)}")
        wanted = set(args.only)
        tools = [t for t in TOOLS if t["id"] in wanted]

    results = [source_manual(t, args.force, local_dir) for t in tools]

    # Fail closed on a partial result: the "expected set" is exactly the tools we
    # processed (all of TOOLS, or the --only subset). Unless --allow-partial is
    # set, do not upload anything and exit non-zero if any expected tool is unsourced.
    expected_ids = {t["id"] for t in tools}
    sourced_ids = {r["id"] for r in results if r["status"] in ("sourced", "present")}
    missing = sorted(expected_ids - sourced_ids)
    if missing and not args.allow_partial:
        print_summary(results)
        sys.exit(f"\n[fail] {len(missing)} expected tool(s) not sourced: "
                 f"{', '.join(missing)}. Refusing to upload a partial set "
                 "(fail-closed). Pass --allow-partial to upload the verified subset.")

    if not args.no_upload:
        _validate_target(args.catalog, args.schema, args.volume,
                         args.allow_catalog_override)
        upload(results, args.catalog, args.schema, args.volume, args.profile, args.force)
    else:
        print("[done] --no-upload set; skipped Volume upload.")

    print_summary(results)


if __name__ == "__main__":
    main()
