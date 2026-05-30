"""
migrate_schema_v1_1.py
======================
Migrates gpr_globalplantdb.csv from v1.0/v1.1 schema to v1.2 schema:

  REMOVE:  ai_assisted (boolean)
           ai_model    (text)

  ADD:     data_type         (text) — 'measured' | 'generated'
           generation_method (text) — 'genus_mean' | 'pft_bonan2008' | '' (empty = NULL)

Derivation rules (based on tier, not ai_assisted):
  Tier 1, 2  →  data_type = 'measured',   generation_method = ''
  Tier 3     →  data_type = 'generated',  generation_method = 'genus_mean'
  Tier 4     →  data_type = 'generated',  generation_method = 'pft_bonan2008'

Also updates data_version to 1.2.0 on all records.

Input:  gpr_globalplantdb.csv
Output: gpr_globalplantdb.csv (in-place, after backup)

Author: Boon Lay Ong / GPRI  |  Script assisted by Claude (Anthropic)
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import csv
import shutil
from pathlib import Path
from datetime import date

BASE     = Path(r'C:\_myProjects\+GPR\GPRTool\lai')
SRC      = BASE / 'gpr_globalplantdb.csv'
BACKUP   = BASE / 'gpr_globalplantdb_pre_v1.2_backup.csv'
TODAY    = date.today().isoformat()

# ── Backup ────────────────────────────────────────────────────────────────────
print(f'Backing up to {BACKUP.name}...')
shutil.copy2(SRC, BACKUP)
print(f'  Done.')

# ── Load ─────────────────────────────────────────────────────────────────────
print(f'Loading {SRC.name}...')
with open(SRC, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    old_fields = reader.fieldnames
    rows = list(reader)
print(f'  {len(rows):,} rows, fields: {old_fields}')

# ── Build new fieldnames ──────────────────────────────────────────────────────
# Remove ai_assisted and ai_model, add data_type and generation_method
remove = {'ai_assisted', 'ai_model'}
new_fields = [f for f in old_fields if f not in remove]

# Insert data_type and generation_method at the same position ai_assisted was
if 'data_type' not in new_fields:
    # Find where ai_assisted was and insert there
    try:
        ins_pos = old_fields.index('ai_assisted')
    except ValueError:
        ins_pos = len(new_fields)
    # new_fields already has ai_assisted removed, so insert at ins_pos
    # (accounting for removed fields before it)
    adj_pos = ins_pos - sum(1 for f in old_fields[:ins_pos] if f in remove)
    new_fields.insert(adj_pos, 'data_type')
    new_fields.insert(adj_pos + 1, 'generation_method')

print(f'\nNew fields: {new_fields}')

# ── Migrate rows ──────────────────────────────────────────────────────────────
print('\nMigrating rows...')

stats = {'measured': 0, 'generated_genus': 0, 'generated_pft': 0, 'unknown': 0}

new_rows = []
for row in rows:
    new_row = {f: row.get(f, '') for f in new_fields
               if f not in ('data_type', 'generation_method')}

    tier = str(row.get('tier', '')).strip()

    if tier in ('1', '2'):
        new_row['data_type']         = 'measured'
        new_row['generation_method'] = ''
        stats['measured'] += 1
    elif tier == '3':
        new_row['data_type']         = 'generated'
        new_row['generation_method'] = 'genus_mean'
        stats['generated_genus'] += 1
    elif tier == '4':
        new_row['data_type']         = 'generated'
        new_row['generation_method'] = 'pft_bonan2008'
        stats['generated_pft'] += 1
    else:
        new_row['data_type']         = ''
        new_row['generation_method'] = ''
        stats['unknown'] += 1
        print(f'  WARNING: unknown tier "{tier}" for species: {row.get("species", "?")}')

    # Update version
    new_row['data_version'] = '1.2.0'
    new_rows.append(new_row)

# ── Write ─────────────────────────────────────────────────────────────────────
print(f'\nWriting {SRC.name}...')
with open(SRC, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=new_fields)
    writer.writeheader()
    writer.writerows(new_rows)

# ── Summary ───────────────────────────────────────────────────────────────────
print('\n' + '='*50)
print('MIGRATION COMPLETE — v1.2.0')
print('='*50)
print(f'Total rows:          {len(new_rows):>8,}')
print(f'  measured:          {stats["measured"]:>8,}  (Tier 1 + Tier 2)')
print(f'  generated/genus:   {stats["generated_genus"]:>8,}  (Tier 3)')
print(f'  generated/pft:     {stats["generated_pft"]:>8,}  (Tier 4)')
if stats['unknown']:
    print(f'  UNKNOWN tier:      {stats["unknown"]:>8,}  ← CHECK THESE')
print(f'\nFields removed:      ai_assisted, ai_model')
print(f'Fields added:        data_type, generation_method')
print(f'data_version:        1.2.0')
print(f'Backup saved:        {BACKUP.name}')
print(f'\nNext step: run the Supabase ALTER TABLE SQL in the SQL Editor')
print('='*50)
