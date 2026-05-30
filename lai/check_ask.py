import requests, json, csv
from pathlib import Path

BASE = "https://dlbstuzzfmjawffzhdys.supabase.co/rest/v1"
KEY  = "sb_secret_uOcM11OdtAAcMVO2lwzDCw_fUMkC9fw"
HDR  = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Prefer": "count=exact"}

# Get all topics
r = requests.get(f"{BASE}/ask_topics", headers=HDR, params={"select":"id,name,description"})
print("Topics:")
for t in r.json():
    print(f"  id={t['id']}  {t['name']}")

# Get all sources for topic 2 (GPR) with DOI or pdf URL
print("\nFetching all GPR sources...")
all_rows = []
offset = 0
while True:
    r = requests.get(f"{BASE}/ask_sources", headers=HDR,
        params={"select":"id,title,doi,url,source_type,quality_score",
                "topic_id":"eq.2", "limit":1000, "offset":offset})
    batch = r.json()
    if not batch: break
    all_rows.extend(batch)
    offset += len(batch)
    if len(batch) < 1000: break

print(f"Total GPR sources: {len(all_rows)}")

# Show breakdown
pdf_count = sum(1 for r in all_rows if r.get('source_type')=='pdf')
doi_count = sum(1 for r in all_rows if r.get('doi'))
url_count = sum(1 for r in all_rows if r.get('url'))
print(f"  With DOI: {doi_count}")
print(f"  Type=pdf: {pdf_count}")
print(f"  With URL: {url_count}")

# Export to CSV for inspection
OUT = Path(r"C:\_myLibrary\GPR\gpr_citations_ask.csv")
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id","title","doi","url","source_type","quality_score"])
    w.writeheader()
    w.writerows(all_rows)
print(f"\nExported to: {OUT}")
