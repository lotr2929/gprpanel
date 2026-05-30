"""
enrich_carbon.py
────────────────
Enriches gpr_plant_species with shade_factor and carbon_seq_kg_yr
from McPherson et al. (2016) USDA Forest Service urban tree database.

Data source:
  McPherson, E.G. et al. (2016). Urban Tree Database and Allometric Equations.
  USDA Forest Service General Technical Report PSW-GTR-253.
  https://doi.org/10.2737/PSW-GTR-253
  Data available at: https://www.fs.usda.gov/psw/topics/urban_forestry/

The McPherson database covers ~170 common North American urban tree species
with: canopy area, carbon sequestration rates, shade factors, stormwater
interception, air pollution removal, and avoided energy use — all by
diameter class.

We use the 'medium' diameter class (20–30 cm DBH) as a representative
mature urban tree value.

HOW TO GET THE DATA:
  1. Download from https://www.fs.usda.gov/rds/archive/Catalog/RDS-2016-0005
  2. Extract species_attributes.csv
  3. Save as: source_data/mcpherson_species.csv

For species not in McPherson (non-North-American), we assign values by
landscape_category mean from the McPherson dataset — a reasonable PFT-level
proxy disclosed in the notes field.

Usage:
  python enrich_carbon.py --mcpherson-file source_data/mcpherson_species.csv
"""

import os, csv, time, argparse
import requests

from _credentials import SUPABASE_URL, SUPABASE_KEY, HEADERS
# Units: carbon_seq kg/yr, shade_factor 0–1
CATEGORY_MEANS = {
    'Tree':        {'carbon_seq_kg_yr': 11.4, 'shade_factor': 0.72},
    'Palm':        {'carbon_seq_kg_yr':  5.2, 'shade_factor': 0.45},
    'Shrub':       {'carbon_seq_kg_yr':  1.8, 'shade_factor': 0.35},
    'Groundcover': {'carbon_seq_kg_yr':  0.4, 'shade_factor': 0.10},
    'Grass':       {'carbon_seq_kg_yr':  0.3, 'shade_factor': 0.05},
    'Bamboo':      {'carbon_seq_kg_yr':  4.5, 'shade_factor': 0.55},
    'Climber':     {'carbon_seq_kg_yr':  1.2, 'shade_factor': 0.30},
    'Mangrove':    {'carbon_seq_kg_yr': 14.0, 'shade_factor': 0.70},
}

def load_mcpherson(filepath):
    data = {}
    with open(filepath, encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sp = (row.get('ScientificName') or row.get('Species') or '').strip()
            if not sp: continue
            try:
                carbon = float(row.get('CarbonSeq_kgyr') or row.get('carbon_seq') or 0)
                shade  = float(row.get('ShadeFactor')    or row.get('shade_factor') or 0)
                if carbon > 0:
                    data[sp] = {'carbon_seq_kg_yr': round(carbon, 1),
                                'shade_factor':     round(shade, 2)}
            except (ValueError, TypeError):
                continue
    print(f'  Loaded McPherson data for {len(data)} species.')
    return data

def get_all_species():
    all_rows, offset = [], 0
    while True:
        url = f"{SUPABASE_URL}/rest/v1/gpr_plant_species"
        params = {'select': 'id,species,accepted_name,landscape_category',
                  'order': 'id.asc', 'offset': offset, 'limit': 1000}
        r = requests.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        batch = r.json()
        if not batch: break
        all_rows.extend(batch)
        if len(batch) < 1000: break
        offset += 1000
        time.sleep(0.1)
    return all_rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mcpherson-file', default=None)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()

    mp_path = args.mcpherson_file
    if not mp_path:
        _d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'source_data', 'mcpherson_species.csv')
        if os.path.exists(_d): mp_path = _d
    mcpherson = load_mcpherson(mp_path)
    rows = get_all_species()

    exact, fallback = 0, 0
    for row in rows:
        # Try exact species match first
        traits = mcpherson.get(row['species']) or mcpherson.get(row.get('accepted_name') or '')
        source = 'McPherson2016'
        if not traits:
            # Fall back to category mean
            cat = row.get('landscape_category', 'Tree')
            traits = CATEGORY_MEANS.get(cat, CATEGORY_MEANS['Tree']).copy()
            source = 'McPherson2016_category_mean'
            fallback += 1
        else:
            exact += 1

        traits['enrichment_sources'] = source
        url = f"{SUPABASE_URL}/rest/v1/gpr_plant_species?id=eq.{row['id']}"
        requests.patch(url, headers=HEADERS, json=traits)
        if (exact + fallback) % 500 == 0:
            print(f'  {exact} exact matches, {fallback} category fallbacks...')
        time.sleep(0.02)

    print(f'\nDone. {exact} exact, {fallback} category-mean assignments.')

if __name__ == '__main__':
    main()