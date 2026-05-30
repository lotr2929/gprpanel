"""
run_overnight.py
================
Runs all pending enrichment scripts in sequence.
Safe to run while AusTraits is finishing -- it will re-run AusTraits
at the end with --resume so nothing is duplicated.

Order:
  1. enrich_usda_traits.py   (re-run to catch 3 failed batches)
  2. enrich_austraits.py     (--resume in case already partially done)
  3. enrich_carbon.py        (fast, ~10 min)
  4. enrich_images.py        (slow, 3-5 hours, --resume)
"""
import os, sys, subprocess, time, datetime

BASE   = r"C:\_myProjects\+GPR\GPRTool\lai"
PY     = r"C:\Users\263350F\AppData\Local\Programs\Python\Python312\python.exe"
SB_KEY = "sb_secret_Jc1oW03ZbKGkwsZNI8Ll7w_hOyHzC2N"
SB_URL = "https://sfvwhbzxkzlscfsnyrwq.supabase.co"

os.makedirs(os.path.join(BASE, "logs"), exist_ok=True)
stamp    = datetime.datetime.now().strftime("%Y%m%d_%H%M")
LOG      = os.path.join(BASE, "logs", f"overnight_{stamp}.log")

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    open(LOG, "a", encoding="utf-8").write(line + "\n")

def run(name, args=None):
    script = os.path.join(BASE, name)
    if not os.path.exists(script):
        log(f"SKIP {name} -- not found"); return
    log(f"{'='*50}")
    log(f"START {name}")
    t0  = time.time()
    env = os.environ.copy()
    env["GPRTOOL_SUPABASE_SECRET_KEY"] = SB_KEY
    env["GPRTOOL_SUPABASE_URL"]        = SB_URL
    result = subprocess.run(
        [PY, script] + (args or []),
        cwd=BASE, env=env,
        encoding="utf-8", errors="replace"
    )  # no capture -- output goes direct to terminal
    elapsed = int(time.time() - t0)
    status  = "DONE" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
    log(f"{status} {name} in {elapsed//60}m {elapsed%60:02d}s")

log("GPR Overnight Enrichment Run")
log(f"Started: {datetime.datetime.now().strftime('%a %d %b %Y %H:%M')}")
log(f"Log: {LOG}")

run("enrich_usda_traits.py")
run("enrich_austraits.py",  ["--resume"])
run("enrich_carbon.py",     ["--resume"])
run("enrich_images.py",     ["--resume"])

log("="*50)
log("All overnight scripts complete.")
