import sqlite3, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DB = r"C:\_myProjects\+GPR\GPRTool\lai\source_data\usda_plants.db"
conn = sqlite3.connect(DB)

# Full column list for plant_characteristics
cols = conn.execute("PRAGMA table_info(plant_characteristics)").fetchall()
print("plant_characteristics columns:")
for c in cols:
    print(f"  {c[0]:>3}: {c[1]} ({c[2]})")

# Check scientific_name format
print("\nSample scientific_names (raw):")
rows = conn.execute("SELECT scientific_name FROM plants LIMIT 5").fetchall()
for r in rows: print(" ", repr(r[0]))

# Strip HTML and author - show cleaned names
print("\nSample scientific_names (cleaned - first 2 words):")
for r in rows:
    clean = re.sub(r"<[^>]+>", "", r[0]).strip()
    binomial = " ".join(clean.split()[:2])
    print(f"  {repr(r[0][:50])} => {repr(binomial)}")

# Sample a characteristics row with column names
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT c.*, p.scientific_name FROM plant_characteristics c JOIN plants p ON p.id=c.plant_id LIMIT 1").fetchone()
if row:
    print("\nFirst characteristics row (key fields):")
    for key in row.keys():
        v = row[key]
        if v not in (None, "", "None"):
            print(f"  {key}: {v}")
conn.close()
