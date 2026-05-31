"""
enrich_images.py
────────────────
Fetches a free-licence image URL for every species in gpr_plant_species.

Sources tried in order per species:
  1. Wikipedia REST API  — thumbnail from species article
  2. iNaturalist API     — first CC-licensed observation photo
  3. GBIF Media API      — first CC-licensed occurrence image

Stores: image_url, image_credit, image_source back to Supabase.
Skips species that already have image_url populated (safe to re-run).

Concurrency: 8 parallel workers — ~34,000 species takes 2–4 hours
depending on network. Progress printed per species.

Usage:
  python enrich_images.py
  python enrich_images.py --resume      # skip already-populated
  python enrich_images.py --limit 100   # test with first 100 species
"""

import os, sys, time, json, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from _credentials import SUPABASE_URL, SUPABASE_KEY
SB_HEADERS = {
    'apikey':        SUPABASE_KEY,
    'Authorization': 'Bearer ' + SUPABASE_KEY,
    'Content-Type':  'application/json',
    'Prefer':        'return=minimal,resolution=merge-duplicates',
}

WIKI_HEADERS  = {'User-Agent': 'GPRPlantDatabase/1.0 (boon.ong@curtin.edu.au)'}
INAT_HEADERS  = {'User-Agent': 'GPRPlantDatabase/1.0 (boon.ong@curtin.edu.au)'}
GBIF_HEADERS  = {'User-Agent': 'GPRPlantDatabase/1.0 (boon.ong@curtin.edu.au)'}

WORKERS = 8
TIMEOUT = 10

# ── Source 1: Wikipedia ──────────────────────────────────────────────────────
def try_wikipedia(species):
    slug = species.replace(' ', '_')
    try:
        r = requests.get(
            f'https://en.wikipedia.org/api/rest_v1/page/summary/{slug}',
            headers=WIKI_HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        data = r.json()
        img = data.get('thumbnail', {}).get('source')
        if not img:
            return None
        # Get full resolution URL by removing width param
        full = img.replace(f'/thumb/', '/').rsplit('/', 1)[0]
        credit = 'Wikimedia Commons contributors, CC BY-SA'
        return {'image_url': img, 'image_credit': credit, 'image_source': 'wikipedia'}
    except Exception:
        return None

# ── Source 2: iNaturalist ────────────────────────────────────────────────────
def try_inaturalist(species):
    try:
        r = requests.get(
            'https://api.inaturalist.org/v1/observations',
            params={'taxon_name': species, 'photos': 'true',
                    'quality_grade': 'research', 'per_page': 1,
                    'license': 'cc-by,cc-by-sa,cc0'},
            headers=INAT_HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        results = r.json().get('results', [])
        if not results:
            return None
        photos = results[0].get('photos', [])
        if not photos:
            return None
        photo = photos[0]
        url = photo.get('url', '').replace('square', 'medium')
        if not url:
            return None
        attribution = photo.get('attribution', 'iNaturalist contributors')
        return {'image_url': url, 'image_credit': attribution, 'image_source': 'inaturalist'}
    except Exception:
        return None

# ── Source 3: GBIF ───────────────────────────────────────────────────────────
def try_gbif(species):
    try:
        # First get the taxon key
        r = requests.get(
            'https://api.gbif.org/v1/species/match',
            params={'name': species, 'strict': 'false'},
            headers=GBIF_HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        key = r.json().get('usageKey')
        if not key:
            return None
        # Then get media
        r2 = requests.get(
            f'https://api.gbif.org/v1/occurrence/search',
            params={'taxonKey': key, 'mediaType': 'StillImage',
                    'license': 'CC_BY,CC_BY_SA,CC0', 'limit': 1},
            headers=GBIF_HEADERS, timeout=TIMEOUT)
        if r2.status_code != 200:
            return None
        results = r2.json().get('results', [])
        if not results:
            return None
        media = results[0].get('media', [])
        if not media:
            return None
        url = media[0].get('identifier')
        if not url:
            return None
        rights = media[0].get('rightsHolder', '') or media[0].get('creator', '')
        license_str = media[0].get('license', 'CC BY')
        credit = f'{rights}, {license_str}'.strip(', ')
        return {'image_url': url, 'image_credit': credit or 'GBIF contributors',
                'image_source': 'gbif'}
    except Exception:
        return None

# ── Fetch image for one species ──────────────────────────────────────────────
def fetch_image(row):
    species = row['species']
    result = try_wikipedia(species) or try_inaturalist(species) or try_gbif(species)
    return row['id'], species, result

# ── Save to Supabase ─────────────────────────────────────────────────────────
def save_image(row_id, data):
    url = f"{SUPABASE_URL}/rest/v1/gpr_plant_species?id=eq.{row_id}"
    requests.patch(url, headers=SB_HEADERS, json=data)

# ── Load all species from Supabase ───────────────────────────────────────────
def get_species(resume=False, limit=None):
    all_rows, offset = [], 0
    while True:
        params = {'select': 'id,species', 'order': 'id.asc',
                  'offset': offset, 'limit': 1000}
        if resume:
            params['image_url'] = 'is.null'
        r = requests.get(f"{SUPABASE_URL}/rest/v1/gpr_plant_species",
                         headers=SB_HEADERS, params=params)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        all_rows.extend(batch)
        if limit and len(all_rows) >= limit:
            all_rows = all_rows[:limit]
            break
        if len(batch) < 1000:
            break
        offset += 1000
    return all_rows

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume', action='store_true', help='Skip species with existing images')
    parser.add_argument('--limit', type=int, default=None, help='Process only N species (for testing)')
    args = parser.parse_args()

    print('GPR Global Plant Database — Image Enrichment')
    print(f'Sources: Wikipedia → iNaturalist → GBIF')
    print(f'Workers: {WORKERS} concurrent\n')

    rows = get_species(resume=args.resume, limit=args.limit)
    total = len(rows)
    print(f'Species to process: {total}')
    if args.resume:
        print('(--resume: skipping already-populated species)\n')
    print()

    found, not_found, done = 0, 0, 0
    start = time.time()

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(fetch_image, row): row for row in rows}
        for future in as_completed(futures):
            done += 1
            if done % 10 == 0 or done == total:
                elapsed = time.time() - start
                rate = done / elapsed if elapsed > 0 else 1
                eta = (total - done) / rate if rate > 0 else 0
                pct = int(done / total * 100)
                bar = '#' * (pct // 5) + '-' * (20 - pct // 5)
                lbl = (species[:10]) if 'species' in dir() else ''
                line = f'  [{bar}] {pct:>3}%  {done:>6}/{total}  {int(elapsed//60)}m{int(elapsed%60):02d}s  eta {int(eta//60)}m{int(eta%60):02d}s  hits:{found}'
                print('\r' + line[:76].ljust(76), end='', flush=True)
            row_id, species, result = future.result()
            elapsed = time.time() - start
            rate = done / elapsed if elapsed > 0 else 0
            eta  = int((total - done) / rate) if rate > 0 else 0
            eta_str = f'{eta//60}m {eta%60}s' if eta > 60 else f'{eta}s'

            if result:
                found += 1
                save_image(row_id, result)
                src = result['image_source'].upper()[:4]
                pass  # progress below
            else:
                not_found += 1
                pass  # progress below

            # Print summary every 500 species
            if done % 500 == 0:
                pct = found / done * 100
                print(f'\n  ── {done}/{total} done · {found} images ({pct:.0f}%) · ETA {eta_str} ──\n')

    elapsed_total = int(time.time() - start)
    print(f'\n{"="*60}')
    print(f'Complete. {found} images found ({found/total*100:.1f}%), {not_found} no image.')
    print(f'Time: {elapsed_total//60}m {elapsed_total%60}s')

if __name__ == '__main__':
    main()
