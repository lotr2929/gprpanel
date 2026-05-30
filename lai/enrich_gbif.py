"""
enrich_gbif.py
==============
Enriches gpr_plant_species with data from the GBIF Species API.

Fields written to Supabase:
  gbif_taxon_key   : GBIF backbone taxon ID
  accepted_name    : GBIF accepted scientific name
  family           : taxonomic family
  order            : taxonomic order
  common_name      : primary English vernacular name (if not already set)
  native_region    : biogeographic realm (inferred from GBIF distributions)

Resume-safe: skips species where gbif_taxon_key is already populated.
Rate-limited to 3 req/sec to respect GBIF API.
Progress: single-line in-place update, no scroll.

Usage:
  python enrich_gbif.py              # full run (skips populated)
  python enrich_gbif.py --limit 100  # test first 100
  python enrich_gbif.py --resume     # same as default (alias)
"""

import sys, os, time, argparse, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from _credentials import SUPABASE_URL, SUPABASE_KEY, HEADERS

# ── Config ────────────────────────────────────────────────────────────────────
GBIF_MATCH  = "https://api.gbif.org/v1/species/match"
GBIF_DIST   = "https://api.gbif.org/v1/species/{key}/distributions"
GBIF_VERN   = "https://api.gbif.org/v1/species/{key}/vernacularNames"
DELAY       = 0.34   # ~3 req/sec
BATCH_SIZE  = 200
LOG_FILE    = Path(__file__).parent / "enrich_gbif_progress.txt"
_warnings   = []

# Biogeographic realms from GBIF distribution country codes
COUNTRY_REALM = {
    "AU": "Australasian", "NZ": "Australasian", "PG": "Australasian",
    "ID": "Indomalayan",  "MY": "Indomalayan",  "PH": "Indomalayan",
    "SG": "Indomalayan",  "TH": "Indomalayan",  "VN": "Indomalayan",
    "IN": "Indomalayan",  "LK": "Indomalayan",  "MM": "Indomalayan",
    "CN": "Palearctic",   "JP": "Palearctic",   "KR": "Palearctic",
    "RU": "Palearctic",   "GB": "Palearctic",   "DE": "Palearctic",
    "FR": "Palearctic",   "ES": "Palearctic",   "IT": "Palearctic",
    "US": "Nearctic",     "CA": "Nearctic",
    "MX": "Neotropical",  "BR": "Neotropical",  "CO": "Neotropical",
    "PE": "Neotropical",  "AR": "Neotropical",
    "ZA": "Afrotropical", "KE": "Afrotropical", "NG": "Afrotropical",
    "ET": "Afrotropical", "GH": "Afrotropical", "TZ": "Afrotropical",
}

def guess_realm_from_text(text):
    if not text: return ""
    t = text.lower()
    if any(k in t for k in ["australia","queensland","new south wales","victoria","western australia"]): return "Australasian"
    if any(k in t for k in ["indonesia","malaysia","singapore","philippines","thailand","india"]): return "Indomalayan"
    if any(k in t for k in ["china","japan","europe","russia","korea"]): return "Palearctic"
    if any(k in t for k in ["north america","united states","canada"]): return "Nearctic"
    if any(k in t for k in ["brazil","colombia","peru","amazon","neotrop"]): return "Neotropical"
    if any(k in t for k in ["africa","kenya","nigeria","south africa","ethiopia"]): return "Afrotropical"
    return ""

def get_gbif_data(species_name):
    """Returns dict of enrichment data for one species, or None on failure."""
    try:
        # Step 1: species match
        r = requests.get(GBIF_MATCH, params={"name": species_name, "verbose": "false"}, timeout=10)
        if r.status_code != 200: return None
        d = r.json()

        # Only accept confident matches
        match_type = d.get("matchType", "NONE")
        if match_type not in ("EXACT", "FUZZY"): return None

        key = d.get("usageKey") or d.get("speciesKey")
        if not key: return None

        payload = {
            "gbif_taxon_key": key,
            "accepted_name":  d.get("species") or d.get("canonicalName") or species_name,
            "family":         d.get("family", ""),
            "order":          d.get("order", ""),
        }
        # Remove empty strings
        payload = {k: v for k, v in payload.items() if v}

        # Step 2: vernacular name (English)
        time.sleep(0.12)
        r2 = requests.get(GBIF_VERN.format(key=key), params={"limit": 20}, timeout=8)
        if r2.status_code == 200:
            names = r2.json().get("results", [])
            en_names = [n["vernacularName"] for n in names
                        if n.get("language", "").lower() in ("eng", "en", "english", "")]
            if en_names:
                payload["common_name"] = en_names[0]

        # Step 3: native region from distributions
        time.sleep(0.12)
        r3 = requests.get(GBIF_DIST.format(key=key), params={"limit": 20}, timeout=8)
        if r3.status_code == 200:
            dists = r3.json().get("results", [])
            realm = ""
            for dist in dists:
                # Try locality text first
                locality = dist.get("locality", "") or dist.get("locationId", "")
                realm = guess_realm_from_text(locality)
                if realm: break
                # Try country code
                country = dist.get("country", "")
                if country in COUNTRY_REALM:
                    realm = COUNTRY_REALM[country]
                    break
            if realm:
                payload["native_region"] = realm

        return payload if len(payload) > 1 else None

    except Exception as e:
        return None

def patch_row(row_id, payload):
    for attempt in range(3):
        try:
            r = requests.patch(
                f"{SUPABASE_URL}/rest/v1/gpr_plant_species?id=eq.{row_id}",
                headers=HEADERS, json=payload, timeout=30)
            if r.status_code not in (200, 204):
                _warnings.append(f"WARN id={row_id}: HTTP {r.status_code}")
            return
        except Exception as e:
            if attempt == 2: _warnings.append(f"WARN id={row_id}: {e}")
            else: time.sleep(2)

def fetch_species(resume=True, limit=None):
    """Fetch species needing GBIF enrichment."""
    rows, offset = [], 0
    while True:
        params = {
            "select": "id,species,common_name",
            "order":  "id.asc",
            "offset": offset,
            "limit":  1000,
        }
        if resume:
            params["gbif_taxon_key"] = "is.null"
        r = requests.get(f"{SUPABASE_URL}/rest/v1/gpr_plant_species",
                         headers=HEADERS, params=params, timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch: break
        rows.extend(batch)
        if len(batch) < 1000: break
        offset += 1000
    if limit:
        rows = rows[:limit]
    return rows

def progress(done, total, matched, t0, label=""):
    elapsed = time.time() - t0
    rate    = done / elapsed if elapsed > 0 else 1
    eta     = (total - done) / rate if rate > 0 else 0
    pct     = int(done / total * 100) if total else 0
    bar     = "#" * (pct // 5) + "-" * (20 - pct // 5)
    line    = (f"  [{bar}] {pct:>3}%  {done:>6,}/{total:,}  "
               f"matched {matched:,}  "
               f"{int(elapsed//60)}m{int(elapsed%60):02d}s  "
               f"eta {int(eta//60)}m{int(eta%60):02d}s  "
               f"{label[:12]}")
    print("\r" + line[:78].ljust(78), end="", flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()
    resume = not args.no_resume

    t0 = time.time()
    print("=" * 60)
    print("  GPR Global Plant Database — GBIF Enrichment")
    print(f"  {datetime.now().strftime('%a %d %b %Y %H:%M')}")
    print(f"  Resume mode: {resume}")
    print("=" * 60)

    print("Fetching species list from Supabase...", end=" ", flush=True)
    rows = fetch_species(resume=resume, limit=args.limit)
    total = len(rows)
    print(f"{total:,} to process\n")

    if total == 0:
        print("Nothing to do — all species already have GBIF data.")
        return

    matched = 0
    done    = 0
    save_count = 0

    with open(LOG_FILE, "w", encoding="utf-8") as log:
        log.write(f"GBIF Enrichment started: {datetime.now()}\n")
        log.write(f"Total to process: {total:,} | Resume: {resume}\n\n")

    for row in rows:
        species = (row.get("species") or "").strip()
        if not species:
            done += 1
            continue

        data = get_gbif_data(species)
        if data:
            # Don't overwrite existing common_name
            if row.get("common_name") and "common_name" in data:
                del data["common_name"]
            patch_row(row["id"], data)
            matched += 1
            save_count += 1

        done += 1
        progress(done, total, matched, t0, species[:12])
        time.sleep(DELAY)

        # Log progress every 500
        if done % 500 == 0:
            with open(LOG_FILE, "a", encoding="utf-8") as log:
                elapsed = time.time() - t0
                log.write(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"{done:,}/{total:,} ({done/total*100:.1f}%) "
                          f"matched {matched:,}\n")

    progress(done, total, matched, t0, "done")
    print()

    elapsed = time.time() - t0
    match_rate = matched / total * 100 if total else 0

    print(f"\n{'=' * 60}")
    print(f"  GBIF Enrichment complete")
    print(f"  Processed : {done:,}")
    print(f"  Matched   : {matched:,} ({match_rate:.1f}%)")
    print(f"  Time      : {int(elapsed//60)}m {int(elapsed%60):02d}s")
    if _warnings:
        print(f"  Warnings  : {len(_warnings)} (see log)")
    print(f"  Log       : {LOG_FILE}")
    print(f"{'=' * 60}")

    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\nCOMPLETE: {matched:,}/{total:,} matched ({match_rate:.1f}%)\n")
        for w in _warnings: log.write(f"  {w}\n")

if __name__ == "__main__":
    main()
