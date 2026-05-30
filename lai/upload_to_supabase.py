import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
"""
upload_to_supabase.py
=====================
Upserts gpr_globalplantdb.csv -> Supabase table gpr_plant_species.

Uses GPRTool Supabase project (sfvwhbzxkzlscfsnyrwq).
Reads credentials from environment or .env file.
Upserts in batches of 500; conflict key = species (UNIQUE).

Run: python upload_to_supabase.py
"""

import csv, json, os, sys, time, requests
from pathlib import Path
from tqdm import tqdm

BASE = Path(r"C:\_myProjects\+GPR\GPRTool\lai")
DB   = BASE / "gpr_globalplantdb.csv"

# ── Credentials ───────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get(
    "GPRTOOL_SUPABASE_URL",
    "https://sfvwhbzxkzlscfsnyrwq.supabase.co"
)
SUPABASE_KEY = os.environ.get(
    "GPRTOOL_SUPABASE_SECRET_KEY",
    "sb_secret_Jc1oW03ZbKGkwsZNI8Ll7w_hOyHzC2N"
)

ENDPOINT = f"{SUPABASE_URL}/rest/v1/gpr_plant_species"
HEADERS  = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "resolution=merge-duplicates",
}

BATCH_SIZE = 500

# Fields to exclude from upload (id is SERIAL — let Supabase assign it)
EXCLUDE = {"id"}

# Numeric fields — must be cast or None, not empty string
NUMERIC = {
    "gbif_taxon_key", "lai_mean","lai_min","lai_max","lai_sd","lai_n","tier"
}


def cast_row(row):
    """Clean one CSV row for JSON upload."""
    out = {}
    for k, v in row.items():
        if k in EXCLUDE:
            continue
        v = v.strip() if isinstance(v, str) else v
        if k in NUMERIC:
            try:
                # gbif_taxon_key and tier are integers
                if k in ("gbif_taxon_key","lai_n","tier"):
                    out[k] = int(v) if v not in ("","None") else None
                else:
                    out[k] = float(v) if v not in ("","None") else None
            except (ValueError, TypeError):
                out[k] = None
        else:
            out[k] = v if v != "" else None
    return out


def upload():
    if not DB.exists():
        print(f"ERROR: {DB} not found — run build_gpr_globalplantdb.py first")
        sys.exit(1)

    with open(DB, encoding="utf-8") as f:
        rows = [cast_row(r) for r in csv.DictReader(f)]

    total   = len(rows)
    batches = [rows[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]

    print(f"Uploading {total:,} species in {len(batches)} batches of {BATCH_SIZE}...")
    print(f"Target: {ENDPOINT}\n")

    uploaded = 0
    errors   = 0

    for batch in tqdm(batches, desc="Uploading"):
        r = requests.post(
            f"{ENDPOINT}?on_conflict=species",
            headers=HEADERS,
            data=json.dumps(batch),
            timeout=60,
        )
        if r.status_code in (200, 201):
            uploaded += len(batch)
        else:
            errors += len(batch)
            print(f"\n  [FAIL] Batch error {r.status_code}: {r.text[:200]}")
        time.sleep(0.1)   # brief pause between batches

    print(f"\n{'=' * 50}")
    print(f"  Uploaded : {uploaded:,}")
    print(f"  Errors   : {errors:,}")
    print(f"  Table    : gpr_plant_species")
    print(f"  Project  : sfvwhbzxkzlscfsnyrwq (GPRTool)")
    print(f"{'=' * 50}")

    if errors == 0:
        print("\n  [OK] All species uploaded successfully.")
        print(f"\n  API endpoint (public read):")
        print(f"  {SUPABASE_URL}/rest/v1/gpr_plant_species")
        print(f"\n  Example query — search by species:")
        print(f'  GET {SUPABASE_URL}/rest/v1/gpr_plant_species?species=eq.Ficus benjamina')
        print(f"\n  Example query — all Tier 1 species:")
        print(f'  GET {SUPABASE_URL}/rest/v1/gpr_plant_species?tier=eq.1')


if __name__ == "__main__":
    upload()
