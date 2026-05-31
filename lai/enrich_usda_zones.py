"""
enrich_usda_zones.py
────────────────────
Derives usda_zone from native_koppen for all species in gpr_plant_species.
No API calls needed — uses a deterministic Köppen → USDA zone mapping.

Usage:
  python enrich_usda_zones.py           # process all rows
  python enrich_usda_zones.py --resume  # skip rows that already have usda_zone
"""

import os, sys, time
import requests

from _credentials import SUPABASE_URL, SUPABASE_KEY, HEADERS

KOPPEN_ZONES = {
    'Af':  [11,12,13], 'Am':  [10,11,12], 'Aw':  [9,10,11], 'As': [9,10,11],
    'BWh': [9,10,11],  'BWk': [6,7,8],    'BSh': [8,9,10],  'BSk': [5,6,7],
    'Csa': [8,9,10],   'Csb': [8,9],      'Csc': [7,8],
    'Cwa': [9,10],     'Cwb': [8,9],      'Cwc': [7,8],
    'Cfa': [7,8,9,10], 'Cfb': [6,7,8,9],  'Cfc': [6,7],
    'Dsa': [5,6,7],    'Dsb': [4,5,6],    'Dsc': [3,4,5],   'Dsd': [2,3,4],
    'Dwa': [5,6,7],    'Dwb': [4,5,6],    'Dwc': [3,4,5],   'Dwd': [1,2,3],
    'Dfa': [4,5,6],    'Dfb': [3,4,5],    'Dfc': [2,3,4],   'Dfd': [1,2],
    'ET':  [1,2,3],    'EF':  [1,2],
}

def koppen_to_usda_zone(koppen_str):
    if not koppen_str:
        return None
    codes = [c.strip() for c in koppen_str.split(',') if c.strip()]
    zones = []
    for code in codes:
        mapped = KOPPEN_ZONES.get(code) or KOPPEN_ZONES.get(code[:3]) or KOPPEN_ZONES.get(code[:2])
        if mapped:
            zones.extend(mapped)
    if not zones:
        return None
    lo, hi = min(zones), max(zones)
    return f'{lo}-{hi}' if lo != hi else str(lo)

def fetch_all():
    """Fetch all rows in pages of 1000. Returns list of {id, native_koppen, usda_zone}."""
    all_rows, offset = [], 0
    while True:
        r = requests.get(
            f'{SUPABASE_URL}/rest/v1/gpr_plant_species',
            headers=HEADERS,
            params={'select': 'id,native_koppen,usda_zone',
                    'order': 'id.asc', 'offset': offset, 'limit': 1000},
            timeout=30
        )
        r.raise_for_status()
        batch = r.json()
        if not batch: break
        all_rows.extend(batch)
        print(f'  Fetched {len(all_rows)} rows...', end='\r')
        if len(batch) < 1000: break
        offset += 1000
    print(f'  Fetched {len(all_rows)} rows total.          ')
    return all_rows

def patch_batch(rows_to_update):
    """
    Update usda_zone for multiple rows using a single upsert call per 500 rows.
    Supabase doesn't support bulk PATCH, so we use individual PATCHes but
    pipeline them with a short sleep only every 100 rows.
    """
    total_u = len(rows_to_update)
    for i, (row_id, zone) in enumerate(rows_to_update, 1):
        pct = int(i / total_u * 100)
        line = f"  [{i:>5}/{total_u}] {pct:>3}% done  zone: {str(zone):<12}"
        print("\r" + line[:76].ljust(76), end="", flush=True)
        retries = 3
        while retries > 0:
            try:
                r = requests.patch(
                    f'{SUPABASE_URL}/rest/v1/gpr_plant_species?id=eq.{row_id}',
                    headers=HEADERS,
                    json={'usda_zone': zone},
                    timeout=15
                )
                r.raise_for_status()
                break
            except Exception as e:
                retries -= 1
                if retries == 0:
                    print(f'\n  ERROR on id={row_id}: {e}')
                else:
                    time.sleep(2)
        if i % 100 == 0:
            time.sleep(0.5)  # brief pause every 100 rows

def main():
    RESUME = '--resume' in __import__('sys').argv
    print('GPR Global Plant Database — USDA Zone Enrichment')
    print(f'Mode: {"RESUME (skipping already populated rows)" if RESUME else "FULL (all rows)"}\n')

    print('Fetching species from Supabase...')
    all_rows = fetch_all()

    # Compute zones and filter
    to_update = []
    skipped_no_koppen = 0
    skipped_already_done = 0

    for row in all_rows:
        # Resume mode: skip rows that already have a usda_zone
        if RESUME and row.get('usda_zone'):
            skipped_already_done += 1
            continue
        zone = koppen_to_usda_zone(row.get('native_koppen'))
        if zone:
            to_update.append((row['id'], zone))
        else:
            skipped_no_koppen += 1

    print(f'  To update:      {len(to_update)}')
    print(f'  Already done:   {skipped_already_done} (skipped)')
    print(f'  No Köppen data: {skipped_no_koppen} (skipped)')
    print(f'\nUpdating {len(to_update)} rows...')

    start = time.time()
    patch_batch(to_update)
    elapsed = int(time.time() - start)

    print(f'\n{"="*50}')
    print(f'Done in {elapsed//60}m {elapsed%60}s.')
    print(f'{len(to_update)} zones assigned.')

if __name__ == '__main__':
    main()