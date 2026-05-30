"""
enrich_nightly.py
─────────────────
Master enrichment script for the GPR Global Plant Database.
Runs all available enrichment passes in sequence.
Safe to run every night — all scripts use --resume logic to skip
already-populated records, so repeat runs only fill gaps.

Scheduled via Windows Task Scheduler to run at 11pm nightly.
Log written to: C:\_myProjects\+GPR\GPRTool\lai\logs\enrich_YYYY-MM-DD.log

Usage:
  python enrich_nightly.py           # run all passes
  python enrich_nightly.py --dry-run # show what would run, no changes
"""

import os, sys, subprocess, datetime, time

# ── Config ────────────────────────────────────────────────────────────────────
LAI_DIR  = r'C:\_myProjects\+GPR\GPRTool\lai'
LOG_DIR  = os.path.join(LAI_DIR, 'logs')
SB_KEY   = 'sb_secret_Jc1oW03ZbKGkwsZNI8Ll7w_hOyHzC2N'
SB_URL   = 'https://sfvwhbzxkzlscfsnyrwq.supabase.co'
DRY_RUN  = '--dry-run' in sys.argv

os.makedirs(LOG_DIR, exist_ok=True)
today    = datetime.date.today().isoformat()
log_path = os.path.join(LOG_DIR, f'enrich_{today}.log')

# ── Logging ───────────────────────────────────────────────────────────────────
class Tee:
    """Write to both stdout and log file."""
    def __init__(self, path):
        self.f = open(path, 'a', encoding='utf-8')
    def write(self, msg):
        sys.__stdout__.write(msg)
        self.f.write(msg)
    def flush(self):
        sys.__stdout__.flush()
        self.f.flush()

sys.stdout = Tee(log_path)
sys.stderr = sys.stdout

def log(msg=''):
    ts = datetime.datetime.now().strftime('%H:%M:%S')
    print(f'[{ts}] {msg}')

# ── Enrichment passes ─────────────────────────────────────────────────────────
# Each entry: (script_name, extra_args, description, requires_download)
PASSES = [
    ('enrich_usda_zones.py',   [],             'USDA hardiness zones from Köppen mapping',        False),
    ('enrich_images.py',       ['--resume'],   'Species images (Wikipedia → iNaturalist → GBIF)', False),
    ('enrich_carbon.py',       [],             'Carbon sequestration + shade factor (McPherson)',  False),
    # Below need manual data downloads — skipped if source files not present
    ('enrich_try_sla.py',      ['--try-file',  os.path.join(LAI_DIR, 'source_data', 'TRY_SLA.txt')],
                                               'SLA from TRY bulk download',                      True),
    ('enrich_usda_traits.py',  ['--usda-file', os.path.join(LAI_DIR, 'source_data', 'usda_plant_char.csv')],
                                               'Drought/shade tolerance from USDA Plants',        True),
]

# ── Run ───────────────────────────────────────────────────────────────────────
log('='*60)
log(f'GPR Global Plant Database — Nightly Enrichment')
log(f'Date: {today}')
log(f'Dry run: {DRY_RUN}')
log('='*60)

env = os.environ.copy()
env['GPRTOOL_SUPABASE_URL']        = SB_URL
env['GPRTOOL_SUPABASE_SECRET_KEY'] = SB_KEY

results = []
for script, args, desc, needs_download in PASSES:
    script_path = os.path.join(LAI_DIR, script)

    # Check if script exists
    if not os.path.exists(script_path):
        log(f'\nSKIP (script not found): {script}')
        results.append((script, 'SKIP - not found'))
        continue

    # Check if required data files exist for download-dependent scripts
    if needs_download and args:
        data_file = args[-1]  # last arg is the file path
        if not os.path.exists(data_file):
            log(f'\nSKIP (data file not downloaded): {script}')
            log(f'  Need: {data_file}')
            results.append((script, 'SKIP - data file missing'))
            continue

    log(f'\n{"─"*60}')
    log(f'RUNNING: {script}')
    log(f'  {desc}')

    if DRY_RUN:
        log('  [DRY RUN — not executing]')
        results.append((script, 'DRY RUN'))
        continue

    start = time.time()
    try:
        r = subprocess.run(
            [sys.executable, script_path] + args,
            env=env, cwd=LAI_DIR,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            encoding='utf-8', errors='replace'
        )
        elapsed = int(time.time() - start)
        # Print last 20 lines of output (summary)
        lines = r.stdout.strip().split('\n') if r.stdout else []
        for line in lines[-20:]:
            log(f'  {line}')
        status = 'OK' if r.returncode == 0 else f'ERROR (exit {r.returncode})'
        log(f'  → {status} in {elapsed//60}m {elapsed%60}s')
        results.append((script, f'{status} ({elapsed//60}m {elapsed%60}s)'))
    except Exception as e:
        log(f'  EXCEPTION: {e}')
        results.append((script, f'EXCEPTION: {e}'))

# ── Summary ───────────────────────────────────────────────────────────────────
log(f'\n{"="*60}')
log('SUMMARY')
log('='*60)
for script, status in results:
    log(f'  {script:<30} {status}')
log(f'\nLog saved to: {log_path}')
log('Done.')
