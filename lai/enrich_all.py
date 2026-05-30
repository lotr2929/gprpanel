"""
enrich_all.py
=============
GPR Global Plant Database — nightly enrichment runner.
Displays a live terminal panel. All detail goes to the log file.

Usage:
  python enrich_all.py
  python enrich_all.py --dry-run
"""

import os, sys, subprocess, datetime, time, re, threading
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE     = Path(__file__).parent
LOGS     = BASE / "logs"
SRCDATA  = BASE / "source_data"
PY       = sys.executable
DRY_RUN  = "--dry-run" in sys.argv

LOGS.mkdir(exist_ok=True)
stamp    = datetime.datetime.now().strftime("%Y%m%d_%H%M")
LOG_FILE = LOGS / f"enrich_{stamp}.log"

W = 50  # panel content width

# ── Pass definitions ──────────────────────────────────────────────────────────
PASSES = [
    {"key": "usda_zones",  "label": "USDA Zones",
     "script": "enrich_usda_zones.py",    "args": []},
    {"key": "usda_traits", "label": "USDA Traits",
     "script": "enrich_usda_traits.py",   "args": [],
     "require": str(SRCDATA / "usda_plants.db"),
     "skip_msg": "usda_plants.db not in source_data/"},
    {"key": "austraits",   "label": "AusTraits",
     "script": "enrich_austraits.py",     "args": []},
    {"key": "gbif",        "label": "GBIF Taxonomy",
     "script": "enrich_gbif.py",          "args": ["--resume"]},
    {"key": "images",      "label": "Images",
     "script": "enrich_images.py",        "args": ["--resume"]},
    {"key": "carbon",      "label": "Carbon Seq.",
     "script": "enrich_carbon.py",        "args": ["--resume"]},
    {"key": "try_sla",     "label": "TRY SLA",
     "script": "enrich_try_sla.py",
     "args": ["--try-file", str(SRCDATA / "TRY_SLA.txt")],
     "require": str(SRCDATA / "TRY_SLA.txt"),
     "skip_msg": "file missing (request #50077)"},
    {"key": "sync_sqlite", "label": "Sync SQLite",
     "script": "sync_supabase_sqlite.py", "args": []},
    {"key": "panel_db",    "label": "Rebuild Panel JSON",
     "script": "enrich_panel_db.py",      "args": []},
]

for p in PASSES:
    p.update({"status": "pending", "elapsed": 0,
               "detail": "", "progress": "", "info": ""})

# ── Helpers ───────────────────────────────────────────────────────────────────
START  = datetime.datetime.now()
_lock  = threading.Lock()

def _t(secs):
    m, s = divmod(int(secs), 60)
    h, m = divmod(m, 60)
    if h: return f"{h}h {m:02d}m"
    if m: return f"{m}m {s:02d}s"
    return f"{s}s"

def _bar(pct, w=18):
    n = int(pct / 100 * w)
    return f"[{'#'*n}{'-'*(w-n)}]"

# ── Draw panel ────────────────────────────────────────────────────────────────
def _draw():
    now     = datetime.datetime.now()
    elapsed = (now - START).total_seconds()
    div     = "=" * W

    lines = [
        div,
        "GPR Plant Database -- Nightly Enrichment",
        f"{now.strftime('%a %d %b %y')}  {now.strftime('%H:%M:%S')}  |  elapsed {_t(elapsed)}",
        div,
    ]

    for p in PASSES:
        st, label = p["status"], p["label"]
        if st == "done":
            detail = f"  {p['detail']}" if p["detail"] else ""
            lines.append(f"  v  {label:<24} {_t(p['elapsed'])}{detail}")
        elif st == "fail":
            lines.append(f"  x  {label:<24} FAILED")
        elif st == "skip":
            lines.append(f"  -  {label:<24} [{p.get('skip_msg','skipped')}]")
        elif st == "running":
            lines.append(f"  >  {label}")
            if p["progress"]:
                lines.append(f"       {p['progress']}")
            if p["info"]:
                lines.append(f"       {p['info']}")
        else:
            lines.append(f"  -  {label}")

    lines.append(div)

    panel  = "\n".join(lines)
    height = len(lines)

    with _lock:
        if hasattr(_draw, "_h"):
            sys.stdout.write(f"\033[{_draw._h}A\033[J")
        sys.stdout.write(panel + "\n")
        sys.stdout.flush()
        _draw._h = height

_stop = threading.Event()

def _redraw_loop():
    while not _stop.is_set():
        _draw()
        time.sleep(2)

# ── Logging ───────────────────────────────────────────────────────────────────
def _log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

# ── Parse script output ───────────────────────────────────────────────────────
def _parse(line, p):
    m = re.search(r'\[([#\-]+)\]\s+(\d+)%\s+([\d,]+)/([\d,]+)', line)
    if m:
        pct = int(m.group(2))
        p["progress"] = f"{_bar(pct)} {m.group(2)}%  {m.group(3)}/{m.group(4)}"

    parts = []
    mm = re.search(r'matched\s+([\d,]+)', line)
    em = re.search(r'[Ee]nriched[:\s]+([\d,]+)', line)
    tm = re.search(r'eta\s+([\dhms ]+)', line)
    if mm: parts.append(f"matched {mm.group(1)}")
    if em: parts.append(f"enriched {em.group(1)}")
    if tm: parts.append(f"eta {tm.group(1).strip()}")
    if parts:
        p["info"] = "  |  ".join(parts)

    # capture summary for done line
    fm = re.search(r'[Ee]nriched[:\s]+([\d,]+)/([\d,]+)', line)
    if fm: p["_sum"] = f"{fm.group(1)} enriched"
    xm = re.search(r'[Mm]atched\s*:\s*([\d,]+)', line)
    if xm: p["_sum"] = f"{xm.group(1)} matched"

# ── Run one pass ──────────────────────────────────────────────────────────────
def _run(p):
    script = BASE / p["script"]
    if not script.exists():
        p["status"] = "skip"; p["skip_msg"] = "script not found"
        _log(f"SKIP {p['script']}"); return

    req = p.get("require")
    if req and not Path(req).exists():
        p["status"] = "skip"
        _log(f"SKIP {p['script']} -- {p.get('skip_msg','')}"); return

    if DRY_RUN:
        p["status"] = "skip"; p["skip_msg"] = "dry-run"; return

    p["status"] = "running"; p["_sum"] = ""
    t0 = time.time()
    _log(f"START {p['script']}")

    proc = subprocess.Popen(
        [PY, str(script)] + p["args"],
        cwd=str(BASE),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace",
    )
    for line in proc.stdout:
        line = line.rstrip()
        _log(f"  {line}")
        _parse(line, p)
    proc.wait()

    p["elapsed"] = time.time() - t0
    p["status"]  = "done" if proc.returncode == 0 else "fail"
    p["detail"]  = p.get("_sum", "")
    _log(f"{'DONE' if proc.returncode==0 else 'FAIL'} {p['script']} in {_t(p['elapsed'])}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.system("cls" if os.name == "nt" else "clear")
    _draw()

    t = threading.Thread(target=_redraw_loop, daemon=True)
    t.start()

    _log("=" * 50)
    _log(f"GPR Nightly Enrichment  {START.strftime('%a %d %b %Y %H:%M')}")
    _log(f"dry-run={DRY_RUN}  log={LOG_FILE}")
    _log("=" * 50)

    for p in PASSES:
        _run(p)
        _draw()

    _stop.set()
    _draw()
    print()

    _log("\nSUMMARY")
    for p in PASSES:
        _log(f"  {p['label']:<24} {p['status'].upper():<6} {_t(p['elapsed']) if p['elapsed'] else ''}")
    _log(f"Total: {_t((datetime.datetime.now()-START).total_seconds())}")
    _log(f"Log: {LOG_FILE}")

if __name__ == "__main__":
    main()
