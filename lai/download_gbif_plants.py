"""
download_gbif_plants.py
=======================
Downloads cultivated/urban plant species from GBIF and World Flora Online
to supplement the USDA PLANTS data with global tropical/subtropical species
not well covered by the US-centric USDA database.

Sources:
  GBIF Species API: https://api.gbif.org/v1/species
  World Flora Online: http://www.worldfloraonline.org/api
  Plants of the World Online (POWO): https://powo.science.kew.org/api/2/

Targets genera with high urban relevance NOT in ORNL/TRY:
  - Tropical ornamental trees (Terminalia, Samanea, Bauhinia, Delonix, etc.)
  - SE Asian urban trees (NParks Singapore recommended list)
  - Australian urban trees (FloraBase WA, Hort Innovation)

Output: LAI_gbif_tier4.csv

Run: python download_gbif_plants.py
Requirements: pip install requests tqdm
"""

import csv, json, time, requests
from pathlib import Path
from tqdm import tqdm

BASE = Path(r"C:\_myProjects\+GPR\GPRTool\lai")
OUT  = BASE / "LAI_gbif_tier4.csv"

GBIF_SPECIES = "https://api.gbif.org/v1/species"
GBIF_BACKBONE = 1  # GBIF backbone taxonomy key

# PFT LAI reference (same as download_usda_plants.py)
PFT_LAI = {
    "TrBE":(4.5,2.5,7.5), "TrBD":(3.2,1.5,5.5), "SuBE":(4.0,2.0,6.5),
    "TeBE":(4.5,2.5,7.0), "TeBD":(3.8,1.5,6.5), "TeNE":(5.0,2.5,9.0),
    "TrN": (3.0,1.5,5.5), "MedBE":(3.0,1.5,5.5),"BoNE":(4.5,1.5,8.0),
    "Palm":(3.0,1.5,5.0), "Bamb":(3.5,2.0,6.5), "TrES":(2.5,1.0,4.5),
    "TeDS":(2.0,0.8,3.8), "TeES":(2.5,1.0,4.5), "MedS":(2.0,0.8,4.0),
    "CLM": (2.5,1.0,4.5), "TrGr":(1.8,0.5,3.5), "TeGr":(1.5,0.5,3.0),
    "TrGC":(2.0,0.5,3.5), "TeGC":(1.5,0.5,3.0),
}

# Target genera: (genus_name, category, pft, climate, canopy_form)
# Focus on tropical/subtropical urban genera NOT in ORNL/TRY
TARGET_GENERA = [
    # SE Asian urban trees
    ("Terminalia",  "Tree",  "TrBD","tropical",   "spreading"),
    ("Samanea",     "Tree",  "TrBE","tropical",   "spreading"),
    ("Albizia",     "Tree",  "TrBD","tropical",   "spreading"),
    ("Falcataria",  "Tree",  "TrBE","tropical",   "spreading"),
    ("Bauhinia",    "Tree",  "TrBD","tropical",   "round"),
    ("Delonix",     "Tree",  "TrBD","tropical",   "spreading"),
    ("Cassia",      "Tree",  "TrBD","tropical",   "round"),
    ("Senna",       "Tree",  "TrBE","tropical",   "round"),
    ("Spathodea",   "Tree",  "TrBE","tropical",   "round"),
    ("Tabebuia",    "Tree",  "TrBD","tropical",   "round"),
    ("Handroanthus","Tree",  "TrBD","tropical",   "round"),
    ("Jacaranda",   "Tree",  "TrBD","tropical",   "spreading"),
    ("Plumeria",    "Tree",  "TrBD","tropical",   "round"),
    ("Khaya",       "Tree",  "TrBE","tropical",   "round"),
    ("Swietenia",   "Tree",  "TrBE","tropical",   "round"),
    ("Azadirachta", "Tree",  "TrBE","tropical",   "round"),
    ("Mangifera",   "Tree",  "TrBE","tropical",   "round"),
    ("Syzygium",    "Tree",  "TrBE","tropical",   "round"),
    ("Callistemon", "Shrub", "SuBE","subtropical","round"),
    ("Fagraea",     "Tree",  "TrBE","tropical",   "spreading"),
    ("Polyalthia",  "Tree",  "TrBE","tropical",   "columnar"),
    ("Hopea",       "Tree",  "TrBE","tropical",   "conical"),
    # Palms
    ("Cocos",       "Palm",  "Palm","tropical",   "spreading"),
    ("Phoenix",     "Palm",  "Palm","tropical",   "spreading"),
    ("Livistona",   "Palm",  "Palm","tropical",   "spreading"),
    ("Washingtonia","Palm",  "Palm","subtropical","columnar"),
    ("Roystonea",   "Palm",  "Palm","tropical",   "columnar"),
    ("Bismarckia",  "Palm",  "Palm","tropical",   "spreading"),
    ("Dypsis",      "Palm",  "Palm","tropical",   "spreading"),
    ("Syagrus",     "Palm",  "Palm","subtropical","spreading"),
    ("Archontophoenix","Palm","Palm","subtropical","columnar"),
    ("Wodyetia",    "Palm",  "Palm","tropical",   "spreading"),
    ("Trachycarpus","Palm",  "Palm","subtropical","spreading"),
    ("Brahea",      "Palm",  "Palm","subtropical","spreading"),
    ("Licuala",     "Palm",  "Palm","tropical",   "spreading"),
    ("Rhapis",      "Palm",  "Palm","tropical",   "spreading"),
    # Bamboos
    ("Bambusa",     "Bamboo","Bamb","tropical",   "columnar"),
    ("Dendrocalamus","Bamboo","Bamb","tropical",  "columnar"),
    ("Guadua",      "Bamboo","Bamb","tropical",   "columnar"),
    ("Fargesia",    "Bamboo","Bamb","temperate",  "columnar"),
    # Tropical shrubs
    ("Hibiscus",    "Shrub", "TrES","tropical",   "round"),
    ("Ixora",       "Shrub", "TrES","tropical",   "hemisphere"),
    ("Gardenia",    "Shrub", "TrES","tropical",   "hemisphere"),
    ("Mussaenda",   "Shrub", "TrES","tropical",   "round"),
    ("Duranta",     "Shrub", "TrES","tropical",   "round"),
    ("Lantana",     "Shrub", "TrES","tropical",   "hemisphere"),
    ("Bougainvillea","Climber","CLM","tropical",  "spreading"),
    ("Acalypha",    "Shrub", "TrES","tropical",   "round"),
    ("Heliconia",   "Groundcover","TrGC","tropical","flat"),
    ("Alpinia",     "Groundcover","TrGC","tropical","flat"),
    ("Strelitzia",  "Groundcover","TrGC","tropical","flat"),
    # Tropical grasses (lawn species)
    ("Axonopus",    "Grass", "TrGr","tropical",   "flat"),
    ("Zoysia",      "Grass", "TrGr","tropical",   "flat"),
    ("Stenotaphrum","Grass", "TrGr","tropical",   "flat"),
    ("Paspalum",    "Grass", "TrGr","tropical",   "flat"),
    ("Pennisetum",  "Grass", "TrGr","tropical",   "flat"),
    # Australian urban genera
    ("Agonis",      "Tree",  "SuBE","subtropical","spreading"),
    ("Lophostemon", "Tree",  "SuBE","subtropical","round"),
    ("Tristaniopsis","Tree", "SuBE","subtropical","round"),
    ("Corymbia",    "Tree",  "SuBE","subtropical","round"),
    ("Brachychiton","Tree",  "SuBE","subtropical","conical"),
    ("Melaleuca",   "Tree",  "SuBE","subtropical","round"),
    # Temperate urban genera (beyond ORNL/TRY)
    ("Platanus",    "Tree",  "TeBD","temperate",  "spreading"),
    ("Tilia",       "Tree",  "TeBD","temperate",  "round"),
    ("Ulmus",       "Tree",  "TeBD","temperate",  "round"),
    ("Fraxinus",    "Tree",  "TeBD","temperate",  "round"),
    ("Gleditsia",   "Tree",  "TeBD","temperate",  "spreading"),
    ("Cercis",      "Tree",  "TeBD","temperate",  "round"),
    ("Koelreuteria","Tree",  "TeBD","temperate",  "round"),
    ("Sorbus",      "Tree",  "TeBD","temperate",  "round"),
    ("Amelanchier", "Tree",  "TeBD","temperate",  "round"),
    ("Zelkova",     "Tree",  "TeBD","temperate",  "round"),
    ("Pyrus",       "Tree",  "TeBD","temperate",  "conical"),
    ("Styrax",      "Tree",  "TeBD","temperate",  "round"),
    # Mediterranean
    ("Olea",        "Tree",  "MedBE","mediterranean","spreading"),
    ("Ceratonia",   "Tree",  "MedBE","mediterranean","spreading"),
    # Climbers
    ("Hedera",      "Climber","CLM","temperate",  "flat"),
    ("Parthenocissus","Climber","CLM","temperate","flat"),
    ("Wisteria",    "Climber","CLM","temperate",  "spreading"),
    ("Clematis",    "Climber","CLM","temperate",  "flat"),
    ("Campsis",     "Climber","CLM","temperate",  "spreading"),
    ("Trachelospermum","Climber","CLM","subtropical","flat"),
    ("Thunbergia",  "Climber","CLM","tropical",   "flat"),
    ("Passiflora",  "Climber","CLM","tropical",   "flat"),
]

def get_gbif_species(genus, limit=200):
    """Query GBIF species API for all accepted species in a genus."""
    url = f"{GBIF_SPECIES}?name={genus}&rank=GENUS&datasetKey={GBIF_BACKBONE}&limit=1"
    try:
        r = requests.get(url, timeout=15)
        if not r.ok:
            return []
        data = r.json()
        if not data.get("results"):
            return []
        genus_key = data["results"][0].get("key")
        if not genus_key:
            return []
        # Now get all species in this genus
        species_url = f"{GBIF_SPECIES}?higherTaxonKey={genus_key}&rank=SPECIES&status=ACCEPTED&limit={limit}&offset=0"
        sr = requests.get(species_url, timeout=30)
        if not sr.ok:
            return []
        return sr.json().get("results", [])
    except Exception as e:
        return []

def build():
    # Load existing species
    existing = set()
    for csv_file in ["LAI_global.csv", "LAI_usda_tier4.csv"]:
        p = BASE / csv_file
        if p.exists():
            with open(p, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    existing.add(row["species"].strip().lower())
    print(f"Existing species (all sources): {len(existing):,}")

    FIELDS = [
        "id","species","common_name","category","mean_lai","lai_min","lai_max",
        "measurement_count","pft","canopy_form","climate","deciduous",
        "tier","tier_source","sources","notes"
    ]

    results = []
    uid = 50000

    for genus, cat, pft, climate, form in tqdm(TARGET_GENERA, desc="Querying GBIF"):
        species_list = get_gbif_species(genus)
        time.sleep(0.3)  # be polite to GBIF

        lai, lmin, lmax = PFT_LAI.get(pft, (2.0, 0.5, 4.0))

        for sp_data in species_list:
            sp = sp_data.get("canonicalName","").strip()
            if not sp or len(sp.split()) < 2:
                continue
            if sp.lower() in existing:
                continue
            # Skip infraspecific
            if len(sp.split()) > 2:
                continue
            cn = sp_data.get("vernacularName","").strip()

            results.append({
                "id":                uid,
                "species":           sp,
                "common_name":       cn,
                "category":          cat,
                "mean_lai":          round(lai, 2),
                "lai_min":           round(lmin, 2),
                "lai_max":           round(lmax, 2),
                "measurement_count": 0,
                "pft":               pft,
                "canopy_form":       form,
                "climate":           climate,
                "deciduous":         "FALSE",
                "tier":              4,
                "tier_source":       "PFT_Mean_GBIF",
                "sources":           f"GBIF Backbone Taxonomy (gbif.org, doi:10.15468/39omei); PFT LAI: Bonan (2008) Science 320:1444",
                "notes":             f"GBIF accepted species for genus {genus}. PFT: {pft}.",
            })
            existing.add(sp.lower())
            uid += 1

        if not species_list:
            print(f"  No GBIF results for {genus}")

    print(f"\nNew GBIF Tier 4 entries: {len(results):,}")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(results)

    print(f"Output: {OUT}")

if __name__ == "__main__":
    build()
