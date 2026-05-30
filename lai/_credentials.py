import os, sys
from pathlib import Path

def _load_master_env():
    env_file = Path(r"C:\_myProjects\.master-env.var")
    env = {}
    if not env_file.exists():
        return env
    for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip(chr(34)).strip(chr(39))
    return env

_env = _load_master_env()
SUPABASE_URL = (_env.get("GPRTOOL_SUPABASE_URL")
    or os.environ.get("GPRTOOL_SUPABASE_URL")
    or "https://sfvwhbzxkzlscfsnyrwq.supabase.co")
SUPABASE_KEY = (_env.get("GPRTOOL_SUPABASE_SECRET_KEY")
    or os.environ.get("GPRTOOL_SUPABASE_SECRET_KEY")
    or "")

if not SUPABASE_KEY:
    print("ERROR: GPRTOOL_SUPABASE_SECRET_KEY not found in .master-env.var")
    sys.exit(1)

HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": "Bearer " + SUPABASE_KEY,
    "Content-Type":  "application/json",
    "Prefer":        "return=minimal,resolution=merge-duplicates",
}

if __name__ == "__main__":
    print("URL:", SUPABASE_URL)
    print("Key:", SUPABASE_KEY[:20] + "...")
    print("Credentials loaded OK.")
