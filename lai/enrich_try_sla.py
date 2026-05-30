"""
enrich_try_sla.py
─────────────────
Enriches gpr_plant_species with Specific Leaf Area (SLA, cm²/g)
from the TRY Plant Trait Database bulk download.

TRY Trait ID 11 = Leaf area per leaf dry mass (SLA or 1/LMA) [cm²/g]

HOW TO GET THE TRY DATA:
  1. Register at https://www.try-db.org/TryWeb/Prop0.php
  2. Request Trait ID 11 (SLA) for all species — select "Open Access" data
  3. Download the resulting .txt file (tab-delimited)
  4. Save as: C:\_myProjects\+GPR\GPRTool\lai\source_data\TRY_SLA.txt

The open-access subset (~700,000 records) covers the majority of
species in the GPR database at Tier 2 and many at Tier 4.

Sources:
  Kattge, J. et al. (2020). TRY plant trait database — enhanced coverage
  and open access. Global Change Biology, 26(1), 119–188.
  https://doi.org/10.1111/gcb.14904

Usage:
  python enrich_try_sla.py --try-file source_data/TRY_SLA.txt
"""

import os, sys, csv, time, argparse
import requests

from _credentials import SUPABASE_URL, SUPABASE_KEY, HEADERS

def parse_try_file(filepath):
    """Parse TRY bulk download — returns {species_name: mean_sla}"""
    sla_values = {}  # species → list of float values
    print(f'Reading TRY file: {filepath}')
    with open(filepath, encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            species = (row.get('AccSpeciesName') or row.get('SpeciesName') or '').strip()
            val_str = (row.get('StdValue') or row.get('OrigValueStr') or '').strip()
            if not species or not val_str:
                continue
            try:
                val = float(val_str)
                if 0.1 < val < 1000:  # plausibility filter (cm²/g)
                    sla_values.setdefault(species, []).append(val)
            except ValueError:
                continue
    # Compute means
    means = {sp: round(sum(vals) / len(vals), 1) for sp, vals in sla_values.items()}
    print(f'  Loaded SLA for {len(means)} species from TRY.')
    return means

def get_all_species():
    """Fetch all species names + ids from Supabase."""
    all_rows, offset = [], 0
    while True:
        url = f"{SUPABASE_URL}/rest/v1/gpr_plant_species"
        params = {'select': 'id,species,accepted_name', 'order': 'id.asc',
                  'offset': offset, 'limit': 1000}
        r = requests.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        all_rows.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
        time.sleep(0.1)
    print(f'  Fetched {len(all_rows)} species from Supabase.')
    return all_rows

def update_sla(row_id, sla_value):
    url = f"{SUPABASE_URL}/rest/v1/gpr_plant_species?id=eq.{row_id}"
    requests.patch(url, headers=HEADERS,
                   json={'sla': sla_value, 'enrichment_sources': 'TRY'})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--try-file', required=True, help='Path to TRY bulk download .txt')
    args = parser.parse_args()

    sla_map = load_try_sla(args.try_file)
    species_rows = get_all_species()

    matched, updated = 0, 0
    for row in species_rows:
        # Try exact match first, then accepted name
        sla = sla_map.get(row['species']) or sla_map.get(row.get('accepted_name') or '')
        if sla:
            matched += 1
            update_sla(row['id'], sla)
            updated += 1
            if updated % 100 == 0:
                print(f'  Updated {updated} species...')
            time.sleep(0.05)

    print(f'\nDone. {matched} species matched, {updated} SLA values written to Supabase.')
    print(f'Match rate: {matched/len(species_rows)*100:.1f}% of {len(species_rows)} species.')

if __name__ == '__main__':
    main()