import sqlite3, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB = r"C:\_myProjects\+GPR\GPRTool\lai\source_data\usda_plants.db"
if not os.path.exists(DB):
    print("DB not found - still compressed?"); sys.exit(1)

conn = sqlite3.connect(DB)

# List all tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("TABLES:", [t[0] for t in tables])

for t in tables:
    cols = conn.execute(f"PRAGMA table_info({t[0]})").fetchall()
    cnt  = conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
    print(f"\n{t[0]} ({cnt:,} rows):")
    for c in cols[:15]:
        print(f"  {c[1]} ({c[2]})")

# Sample a few rows from each table
for t in tables:
    rows = conn.execute(f"SELECT * FROM {t[0]} LIMIT 2").fetchall()
    if rows:
        print(f"\nSample {t[0]}:", rows[0])

conn.close()
