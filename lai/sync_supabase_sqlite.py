"""
sync_supabase_sqlite.py
=======================
Pulls all rows from Supabase gpr_plant_species table and writes
to a local SQLite mirror: gpr_plants.sqlite

Usage:
    python sync_supabase_sqlite.py

Output:
    lai/gpr_plants.sqlite   -- full mirror, ready for DB Browser or queries
    lai/sync_report.txt     -- null-field audit report

Credentials: reads from C:\_myProjects\.master-env.var
Run from:    C:\_myProjects\_GPR\GPRTool\lai\
"""

import os, sys, re, sqlite3, time, requests
from pathlib import Path
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────

BASE        = Path(__file__).parent
ENV_FILE    = Path(r"C:\_myProjects\.master-env.var")
SQLITE_PATH = BASE / "gpr_plants.sqlite"
REPORT_PATH = BASE / "sync_report.txt"
TABLE       = "gpr_plant_species"
PAGE_SIZE   = 1000

# ── Load credentials ──────────────────────────────────────────────────────────

def load_env(path):
    env = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env

env = load_env(ENV_FILE)
SUPABASE_URL = env.get("GPRTOOL_SUPABASE_URL", "")
SUPABASE_KEY = env.get("GPRTOOL_SUPABASE_SECRET_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: GPRTOOL_SUPABASE_URL or GPRTOOL_SUPABASE_SECRET_KEY not found in .master-env.var")
    sys.exit(1)

HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
}

# ── Fetch all rows from Supabase ──────────────────────────────────────────────

def fetch_all():
    rows   = []
    offset = 0
    print(f"Fetching from {SUPABASE_URL}/rest/v1/{TABLE}")
    print(f"Page size: {PAGE_SIZE} rows\n")

    while True:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{TABLE}",
            headers={**HEADERS, "Range-Unit": "items",
                     "Range": f"{offset}-{offset + PAGE_SIZE - 1}",
                     "Prefer": "count=none"},
            params={"select": "*", "order": "id.asc"},
            timeout=30,
        )
        if r.status_code not in (200, 206):
            print(f"ERROR {r.status_code}: {r.text[:200]}")
            sys.exit(1)

        batch = r.json()
        if not batch:
            break

        rows.extend(batch)
        print(f"  Fetched {len(rows):>7,} rows ...", end="\r")

        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(0.05)

    print(f"  Fetched {len(rows):>7,} rows — done.      ")
    return rows

# ── Write to SQLite ───────────────────────────────────────────────────────────

def write_sqlite(rows):
    if not rows:
        print("No rows to write.")
        return []

    # Derive columns from first row
    columns = list(rows[0].keys())
    print(f"\nColumns: {len(columns)}")
    print(f"Rows:    {len(rows):,}")

    # Remove old DB
    if SQLITE_PATH.exists():
        SQLITE_PATH.unlink()
        print(f"Removed old {SQLITE_PATH.name}")

    conn = sqlite3.connect(SQLITE_PATH)
    cur  = conn.cursor()

    # Create table — all columns as TEXT for simplicity;
    # SQLite is dynamically typed so queries still work numerically
    col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
    cur.execute(f'CREATE TABLE {TABLE} ({col_defs})')

    # Insert rows in batches
    placeholders = ", ".join("?" for _ in columns)
    insert_sql   = f'INSERT INTO {TABLE} VALUES ({placeholders})'

    BATCH = 500
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        values = [
            tuple(
                str(row.get(c)) if row.get(c) is not None else None
                for c in columns
            )
            for row in batch
        ]
        cur.executemany(insert_sql, values)

    # Index the most-used lookup columns
    for col in ("species", "accepted_name", "gbif_taxon_key",
                "growth_form", "landscape_category", "tier"):
        if col in columns:
            cur.execute(f'CREATE INDEX IF NOT EXISTS idx_{col} ON {TABLE} ("{col}")')

    conn.commit()
    conn.close()

    size_mb = round(SQLITE_PATH.stat().st_size / 1_048_576, 2)
    print(f"Written:  {SQLITE_PATH}")
    print(f"Size:     {size_mb} MB")

    return columns

# ── Null-field audit ──────────────────────────────────────────────────────────

def audit(rows, columns):
    total = len(rows)
    if total == 0:
        return

    print(f"\n{'=' * 60}")
    print(f"  NULL-FIELD AUDIT  ({total:,} species)")
    print(f"{'=' * 60}")
    print(f"  {'FIELD':<35} {'POPULATED':>10}  {'%':>6}")
    print(f"  {'-'*35} {'-'*10}  {'-'*6}")

    report_lines = [
        f"GPR Plant Species — Null-Field Audit",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total species: {total:,}",
        f"Total columns: {len(columns)}",
        "",
        f"{'FIELD':<40} {'POPULATED':>10}  {'PCT':>6}",
        "-" * 60,
    ]

    for col in columns:
        populated = sum(
            1 for r in rows
            if r.get(col) not in (None, "", "None", "null")
        )
        pct = populated / total * 100
        bar_fill = "█" * int(pct / 5)
        bar_empty = "░" * (20 - int(pct / 5))
        flag = "  ← EMPTY" if populated == 0 else (
               "  ← SPARSE" if pct < 10 else "")
        line = f"  {col:<35} {populated:>10,}  {pct:>5.1f}%{flag}"
        print(line)
        report_lines.append(f"{col:<40} {populated:>10,}  {pct:>5.1f}%{flag}")

    # Summary by section
    sections = {
        "taxonomy":     [c for c in columns if c in
                         ("species","accepted_name","gbif_taxon_key","family",
                          "order_name","common_name","common_names_json",
                          "synonyms","iucn_status","invasive_regions",
                          "native_au","native_wa")],
        "morphology":   [c for c in columns if c in
                         ("height_mature_m","height_min_m","height_max_m",
                          "canopy_radius_m","trunk_diameter_cm","root_architecture",
                          "leaf_texture","leaf_size","growth_rate","longevity","sla")],
        "lai_gpr":      [c for c in columns if c.startswith("lai_") or c == "pft"],
        "eco_services": [c for c in columns if any(c.startswith(p) for p in
                         ("cooling_","carbon_","stormwater_","airquality_",
                          "biodiversity_","soilhealth_"))],
        "urban_perf":   [c for c in columns if c in
                         ("drought_tolerance","wind_tolerance","salt_tolerance",
                          "water_needs","sunlight","substrate_types",
                          "maintenance_level","usda_zones")],
    }

    print(f"\n{'=' * 60}")
    print(f"  SECTION SUMMARY")
    print(f"{'=' * 60}")
    report_lines += ["", "SECTION SUMMARY", "-" * 40]

    for section, fields in sections.items():
        present = [f for f in fields if f in columns]
        if not present:
            continue
        avg_pct = sum(
            sum(1 for r in rows if r.get(f) not in (None, "", "None", "null"))
            / total * 100
            for f in present
        ) / len(present)
        line = f"  {section:<20} {len(present):>3} fields in DB   avg {avg_pct:>5.1f}% populated"
        print(line)
        report_lines.append(line)

    # Write report
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n  Report saved: {REPORT_PATH}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    print("=" * 60)
    print("  GPR Plant Database — Supabase → SQLite Sync")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    rows    = fetch_all()
    columns = write_sqlite(rows)
    audit(rows, columns)

    elapsed = round(time.time() - t0, 1)
    print(f"\n  Done in {elapsed}s")
    print(f"  SQLite: {SQLITE_PATH}")
    print(f"  Open with: DB Browser for SQLite")

if __name__ == "__main__":
    main()
