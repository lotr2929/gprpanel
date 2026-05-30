"""
download_gbif_comprehensive.py
================================
Downloads accepted plant species from GBIF for all major
ornamental/urban plant genera. Builds a comprehensive Tier 4
LAI database for GPR.

Strategy:
  - Query GBIF species/search for each target genus
  - Filter: rank=SPECIES, status=ACCEPTED, kingdom=Plantae
  - Assign PFT-based LAI from genus lookup table
  - Paginate up to 300 species per genus (GBIF limit per page)
  - Outputs: LAI_gbif_comprehensive.csv

Expected output: 15,000 - 30,000 species

References:
  GBIF Secretariat (2023). GBIF Backbone Taxonomy.
  https://doi.org/10.15468/39omei
  PFT LAI: Bonan (2008) Science 320:1444;
  Running et al. (2000) Science 289:1772

Run: python download_gbif_comprehensive.py
Estimated time: 30-60 minutes (rate-limited API calls)
"""

import sys, csv, time, requests
from pathlib import Path
from collections import Counter
from tqdm import tqdm

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = Path(r"C:\_myProjects\+GPR\GPRTool\lai")
OUT  = BASE / "LAI_gbif_comprehensive.csv"

GBIF_SEARCH = "https://api.gbif.org/v1/species/search"
DELAY = 0.25  # seconds between requests (polite)

# PFT LAI (mean, min, max)
PFT_LAI = {
    "TrBE":(4.5,2.5,7.5),"TrBD":(3.2,1.5,5.5),"SuBE":(4.0,2.0,6.5),
    "TeBE":(4.5,2.5,7.0),"TeBD":(3.8,1.5,6.5),"TeNE":(5.0,2.5,9.0),
    "TrN": (3.0,1.5,5.5),"MedBE":(3.0,1.5,5.5),"BoNE":(4.5,1.5,8.0),
    "Palm":(3.0,1.5,5.0),"Bamb":(3.5,2.0,6.5),"TrES":(2.5,1.0,4.5),
    "TeDS":(2.0,0.8,3.8),"TeES":(2.5,1.0,4.5),"MedS":(2.0,0.8,4.0),
    "CLM": (2.5,1.0,4.5),"TrGr":(1.8,0.5,3.5),"TeGr":(1.5,0.5,3.0),
    "TrGC":(2.0,0.5,3.5),"TeGC":(1.5,0.5,3.0),"Fern":(2.0,0.8,4.0),
    "Herb":(1.5,0.5,3.5),"Succ":(0.8,0.2,2.0),
}

# (genus, category, pft, climate, canopy_form)
# Comprehensive list of ornamental/urban plant genera globally
TARGET_GENERA = [
    # ── Tropical trees — SE Asia ─────────────────────────────────────────
    ("Terminalia",   "Tree",  "TrBD","tropical",    "spreading"),
    ("Samanea",      "Tree",  "TrBE","tropical",    "spreading"),
    ("Albizia",      "Tree",  "TrBD","tropical",    "spreading"),
    ("Falcataria",   "Tree",  "TrBE","tropical",    "spreading"),
    ("Bauhinia",     "Tree",  "TrBD","tropical",    "round"),
    ("Delonix",      "Tree",  "TrBD","tropical",    "spreading"),
    ("Cassia",       "Tree",  "TrBD","tropical",    "round"),
    ("Senna",        "Tree",  "TrBE","tropical",    "round"),
    ("Leucaena",     "Tree",  "TrBE","tropical",    "spreading"),
    ("Acacia",       "Tree",  "TrBE","tropical",    "round"),
    ("Calliandra",   "Shrub", "TrES","tropical",    "hemisphere"),
    ("Enterolobium", "Tree",  "TrBD","tropical",    "spreading"),
    ("Parkia",       "Tree",  "TrBD","tropical",    "spreading"),
    ("Spathodea",    "Tree",  "TrBE","tropical",    "round"),
    ("Tabebuia",     "Tree",  "TrBD","tropical",    "round"),
    ("Handroanthus", "Tree",  "TrBD","tropical",    "round"),
    ("Jacaranda",    "Tree",  "TrBD","tropical",    "spreading"),
    ("Tecoma",       "Shrub", "TrES","tropical",    "round"),
    ("Crescentia",   "Tree",  "TrBE","tropical",    "spreading"),
    ("Plumeria",     "Tree",  "TrBD","tropical",    "round"),
    ("Thevetia",     "Tree",  "TrBE","tropical",    "round"),
    ("Alstonia",     "Tree",  "TrBE","tropical",    "round"),
    ("Rauvolfia",    "Shrub", "TrES","tropical",    "round"),
    ("Khaya",        "Tree",  "TrBE","tropical",    "round"),
    ("Swietenia",    "Tree",  "TrBE","tropical",    "round"),
    ("Toona",        "Tree",  "TrBD","tropical",    "round"),
    ("Azadirachta",  "Tree",  "TrBE","tropical",    "round"),
    ("Cedrela",      "Tree",  "TrBD","tropical",    "round"),
    ("Dysoxylum",    "Tree",  "TrBE","tropical",    "round"),
    ("Mangifera",    "Tree",  "TrBE","tropical",    "round"),
    ("Anacardium",   "Tree",  "TrBE","tropical",    "round"),
    ("Spondias",     "Tree",  "TrBD","tropical",    "round"),
    ("Dracontomelon","Tree",  "TrBE","tropical",    "spreading"),
    ("Canarium",     "Tree",  "TrBE","tropical",    "round"),
    ("Ficus",        "Tree",  "TrBE","tropical",    "round"),
    ("Artocarpus",   "Tree",  "TrBE","tropical",    "round"),
    ("Morus",        "Tree",  "TeBD","temperate",   "round"),
    ("Syzygium",     "Tree",  "TrBE","tropical",    "round"),
    ("Psidium",      "Tree",  "TrBE","tropical",    "round"),
    ("Eugenia",      "Tree",  "TrBE","tropical",    "round"),
    ("Melaleuca",    "Tree",  "SuBE","subtropical", "round"),
    ("Callistemon",  "Shrub", "SuBE","subtropical", "round"),
    ("Lophostemon",  "Tree",  "SuBE","subtropical", "round"),
    ("Tristaniopsis","Tree",  "SuBE","subtropical", "round"),
    ("Metrosideros", "Tree",  "SuBE","subtropical", "round"),
    ("Persea",       "Tree",  "SuBE","subtropical", "round"),
    ("Cinnamomum",   "Tree",  "SuBE","subtropical", "round"),
    ("Phoebe",       "Tree",  "SuBE","subtropical", "round"),
    ("Fagraea",      "Tree",  "TrBE","tropical",    "spreading"),
    ("Polyalthia",   "Tree",  "TrBE","tropical",    "columnar"),
    ("Annona",       "Tree",  "TrBD","tropical",    "round"),
    ("Rollinia",     "Tree",  "TrBD","tropical",    "round"),
    ("Casuarina",    "Tree",  "TrN", "tropical",    "conical"),
    ("Allocasuarina","Tree",  "SuBE","subtropical", "round"),
    ("Araucaria",    "Tree",  "TrN", "tropical",    "conical"),
    ("Agathis",      "Tree",  "SuBE","subtropical", "conical"),
    ("Podocarpus",   "Tree",  "SuBE","subtropical", "columnar"),
    ("Dacrydium",    "Tree",  "SuBE","subtropical", "conical"),
    ("Hopea",        "Tree",  "TrBE","tropical",    "conical"),
    ("Shorea",       "Tree",  "TrBE","tropical",    "round"),
    ("Dipterocarpus","Tree",  "TrBE","tropical",    "conical"),
    ("Dryobalanops", "Tree",  "TrBE","tropical",    "conical"),
    ("Palaquium",    "Tree",  "TrBE","tropical",    "round"),
    ("Madhuca",      "Tree",  "TrBE","tropical",    "round"),
    # ── Subtropical trees ────────────────────────────────────────────────
    ("Brachychiton", "Tree",  "SuBE","subtropical", "conical"),
    ("Agonis",       "Tree",  "SuBE","subtropical", "spreading"),
    ("Corymbia",     "Tree",  "SuBE","subtropical", "round"),
    ("Angophora",    "Tree",  "SuBE","subtropical", "spreading"),
    ("Grevillea",    "Tree",  "SuBE","subtropical", "round"),
    ("Banksia",      "Shrub", "SuBE","subtropical", "round"),
    ("Hakea",        "Shrub", "SuBE","subtropical", "round"),
    ("Acmena",       "Tree",  "SuBE","subtropical", "round"),
    ("Stenocarpus",  "Tree",  "SuBE","subtropical", "round"),
    ("Buckinghamia", "Tree",  "SuBE","subtropical", "round"),
    # Mediterranean trees
    ("Olea",         "Tree",  "MedBE","mediterranean","spreading"),
    ("Ceratonia",    "Tree",  "MedBE","mediterranean","spreading"),
    ("Pistacia",     "Tree",  "MedBE","mediterranean","round"),
    ("Laurus",       "Tree",  "MedBE","mediterranean","round"),
    ("Arbutus",      "Tree",  "MedBE","mediterranean","round"),
    # ── Temperate trees (beyond ORNL/TRY) ───────────────────────────────
    ("Platanus",     "Tree",  "TeBD","temperate",   "spreading"),
    ("Tilia",        "Tree",  "TeBD","temperate",   "round"),
    ("Ulmus",        "Tree",  "TeBD","temperate",   "round"),
    ("Fraxinus",     "Tree",  "TeBD","temperate",   "round"),
    ("Gleditsia",    "Tree",  "TeBD","temperate",   "spreading"),
    ("Cercis",       "Tree",  "TeBD","temperate",   "round"),
    ("Koelreuteria", "Tree",  "TeBD","temperate",   "round"),
    ("Aesculus",     "Tree",  "TeBD","temperate",   "round"),
    ("Sorbus",       "Tree",  "TeBD","temperate",   "round"),
    ("Amelanchier",  "Tree",  "TeBD","temperate",   "round"),
    ("Zelkova",      "Tree",  "TeBD","temperate",   "round"),
    ("Pyrus",        "Tree",  "TeBD","temperate",   "conical"),
    ("Styrax",       "Tree",  "TeBD","temperate",   "round"),
    ("Ginkgo",       "Tree",  "TeBD","temperate",   "conical"),
    ("Catalpa",      "Tree",  "TeBD","temperate",   "round"),
    ("Magnolia",     "Tree",  "TeBE","temperate",   "round"),
    ("Nyssa",        "Tree",  "TeBD","temperate",   "round"),
    ("Cercidiphyllum","Tree", "TeBD","temperate",   "round"),
    ("Parrotia",     "Tree",  "TeBD","temperate",   "spreading"),
    ("Liquidambar",  "Tree",  "TeBD","temperate",   "conical"),
    ("Liriodendron", "Tree",  "TeBD","temperate",   "conical"),
    ("Cladrastis",   "Tree",  "TeBD","temperate",   "round"),
    ("Gymnocladus",  "Tree",  "TeBD","temperate",   "round"),
    ("Maclura",      "Tree",  "TeBD","temperate",   "round"),
    ("Celtis",       "Tree",  "TeBD","temperate",   "round"),
    ("Styphnolobium","Tree",  "TeBD","temperate",   "round"),
    # Fruit trees
    ("Malus",        "Tree",  "TeBD","temperate",   "round"),
    ("Prunus",       "Tree",  "TeBD","temperate",   "round"),
    ("Pyrus",        "Tree",  "TeBD","temperate",   "round"),
    ("Cydonia",      "Tree",  "TeBD","temperate",   "round"),
    ("Mespilus",     "Tree",  "TeBD","temperate",   "round"),
    ("Eriobotrya",   "Tree",  "SuBE","subtropical", "round"),
    ("Diospyros",    "Tree",  "TeBD","temperate",   "round"),
    ("Juglans",      "Tree",  "TeBD","temperate",   "spreading"),
    ("Carya",        "Tree",  "TeBD","temperate",   "round"),
    ("Castanea",     "Tree",  "TeBD","temperate",   "round"),
    # Additional conifers
    ("Cedrus",       "Tree",  "TeNE","temperate",   "conical"),
    ("Thuja",        "Tree",  "TeNE","temperate",   "conical"),
    ("Chamaecyparis","Tree",  "TeNE","temperate",   "conical"),
    ("Juniperus",    "Tree",  "TeNE","temperate",   "columnar"),
    ("Taxus",        "Tree",  "TeNE","temperate",   "round"),
    ("Sequoia",      "Tree",  "TeNE","temperate",   "conical"),
    ("Sequoiadendron","Tree", "TeNE","temperate",   "conical"),
    ("Cephalotaxus", "Tree",  "TeNE","temperate",   "round"),
    ("Callitris",    "Tree",  "TeNE","subtropical", "conical"),
    ("Wollemia",     "Tree",  "SuBE","subtropical", "conical"),
    # ── Palms ────────────────────────────────────────────────────────────
    ("Cocos",        "Palm",  "Palm","tropical",    "spreading"),
    ("Phoenix",      "Palm",  "Palm","tropical",    "spreading"),
    ("Livistona",    "Palm",  "Palm","tropical",    "spreading"),
    ("Washingtonia", "Palm",  "Palm","subtropical", "columnar"),
    ("Roystonea",    "Palm",  "Palm","tropical",    "columnar"),
    ("Bismarckia",   "Palm",  "Palm","tropical",    "spreading"),
    ("Dypsis",       "Palm",  "Palm","tropical",    "spreading"),
    ("Elaeis",       "Palm",  "Palm","tropical",    "spreading"),
    ("Syagrus",      "Palm",  "Palm","subtropical", "spreading"),
    ("Archontophoenix","Palm","Palm","subtropical", "columnar"),
    ("Wodyetia",     "Palm",  "Palm","tropical",    "spreading"),
    ("Trachycarpus", "Palm",  "Palm","subtropical", "spreading"),
    ("Brahea",       "Palm",  "Palm","subtropical", "spreading"),
    ("Licuala",      "Palm",  "Palm","tropical",    "spreading"),
    ("Rhapis",       "Palm",  "Palm","tropical",    "spreading"),
    ("Caryota",      "Palm",  "Palm","tropical",    "spreading"),
    ("Arenga",       "Palm",  "Palm","tropical",    "spreading"),
    ("Pinanga",      "Palm",  "Palm","tropical",    "spreading"),
    ("Chamaerops",   "Palm",  "Palm","mediterranean","spreading"),
    ("Sabal",        "Palm",  "Palm","subtropical", "spreading"),
    ("Pritchardia",  "Palm",  "Palm","tropical",    "spreading"),
    ("Hyophorbe",    "Palm",  "Palm","tropical",    "spreading"),
    ("Butia",        "Palm",  "Palm","subtropical", "spreading"),
    ("Jubaea",       "Palm",  "Palm","mediterranean","spreading"),
    # ── Bamboos ──────────────────────────────────────────────────────────
    ("Bambusa",      "Bamboo","Bamb","tropical",    "columnar"),
    ("Dendrocalamus","Bamboo","Bamb","tropical",    "columnar"),
    ("Guadua",       "Bamboo","Bamb","tropical",    "columnar"),
    ("Fargesia",     "Bamboo","Bamb","temperate",   "columnar"),
    ("Chusquea",     "Bamboo","Bamb","tropical",    "columnar"),
    ("Pleioblastus", "Bamboo","Bamb","temperate",   "columnar"),
    ("Yushania",     "Bamboo","Bamb","temperate",   "columnar"),
    ("Borinda",      "Bamboo","Bamb","temperate",   "columnar"),
    # ── Shrubs — tropical ────────────────────────────────────────────────
    ("Hibiscus",     "Shrub", "TrES","tropical",    "round"),
    ("Ixora",        "Shrub", "TrES","tropical",    "hemisphere"),
    ("Gardenia",     "Shrub", "TrES","tropical",    "hemisphere"),
    ("Mussaenda",    "Shrub", "TrES","tropical",    "round"),
    ("Duranta",      "Shrub", "TrES","tropical",    "round"),
    ("Lantana",      "Shrub", "TrES","tropical",    "hemisphere"),
    ("Bougainvillea","Climber","CLM","tropical",    "spreading"),
    ("Acalypha",     "Shrub", "TrES","tropical",    "round"),
    ("Codiaeum",     "Shrub", "TrES","tropical",    "round"),
    ("Graptophyllum","Shrub", "TrES","tropical",    "round"),
    ("Pentas",       "Shrub", "TrES","tropical",    "hemisphere"),
    ("Hamelia",      "Shrub", "TrES","tropical",    "round"),
    ("Quisqualis",   "Climber","CLM","tropical",    "flat"),
    ("Clerodendrum", "Shrub", "TrES","tropical",    "round"),
    ("Thunbergia",   "Climber","CLM","tropical",    "flat"),
    ("Plumbago",     "Shrub", "TrES","subtropical", "round"),
    ("Pseuderanthemum","Shrub","TrES","tropical",   "round"),
    ("Strobilanthes","Shrub", "TrES","tropical",    "round"),
    ("Ruellia",      "Shrub", "TrES","tropical",    "hemisphere"),
    ("Justicia",     "Shrub", "TrES","tropical",    "hemisphere"),
    ("Crossandra",   "Shrub", "TrES","tropical",    "hemisphere"),
    ("Pachystachys", "Shrub", "TrES","tropical",    "hemisphere"),
    # ── Shrubs — temperate ───────────────────────────────────────────────
    ("Rosa",         "Shrub", "TeDS","temperate",   "round"),
    ("Rhododendron", "Shrub", "TeES","temperate",   "hemisphere"),
    ("Forsythia",    "Shrub", "TeDS","temperate",   "round"),
    ("Viburnum",     "Shrub", "TeES","temperate",   "round"),
    ("Spiraea",      "Shrub", "TeDS","temperate",   "hemisphere"),
    ("Photinia",     "Shrub", "TeES","temperate",   "round"),
    ("Pittosporum",  "Shrub", "SuBE","subtropical", "round"),
    ("Lonicera",     "Shrub", "TeES","temperate",   "round"),
    ("Ligustrum",    "Shrub", "TeES","temperate",   "round"),
    ("Buxus",        "Shrub", "TeES","temperate",   "hemisphere"),
    ("Euonymus",     "Shrub", "TeES","temperate",   "round"),
    ("Osmanthus",    "Shrub", "SuBE","subtropical", "round"),
    ("Camellia",     "Shrub", "SuBE","subtropical", "round"),
    ("Lavandula",    "Shrub", "MedS","mediterranean","hemisphere"),
    ("Rosmarinus",   "Shrub", "MedS","mediterranean","round"),
    ("Salvia",       "Shrub", "TeES","temperate",   "hemisphere"),
    ("Cistus",       "Shrub", "MedS","mediterranean","hemisphere"),
    ("Phlomis",      "Shrub", "MedS","mediterranean","hemisphere"),
    ("Eleagnus",     "Shrub", "TeES","temperate",   "round"),
    ("Ilex",         "Shrub", "TeES","temperate",   "round"),
    ("Ceanothus",    "Shrub", "MedS","mediterranean","hemisphere"),
    ("Escallonia",   "Shrub", "SuBE","subtropical", "round"),
    ("Abelia",       "Shrub", "TeES","temperate",   "round"),
    ("Weigela",      "Shrub", "TeDS","temperate",   "round"),
    ("Deutzia",      "Shrub", "TeDS","temperate",   "hemisphere"),
    ("Kolkwitzia",   "Shrub", "TeDS","temperate",   "round"),
    ("Cornus",       "Shrub", "TeDS","temperate",   "round"),
    ("Cotoneaster",  "Shrub", "TeES","temperate",   "spreading"),
    ("Pyracantha",   "Shrub", "TeES","temperate",   "round"),
    ("Berberis",     "Shrub", "TeDS","temperate",   "hemisphere"),
    ("Mahonia",      "Shrub", "TeES","temperate",   "round"),
    ("Hypericum",    "Shrub", "TeES","temperate",   "hemisphere"),
    ("Potentilla",   "Shrub", "TeDS","temperate",   "hemisphere"),
    ("Sambucus",     "Shrub", "TeDS","temperate",   "round"),
    ("Buddleja",     "Shrub", "TeDS","temperate",   "round"),
    ("Hebe",         "Shrub", "TeES","temperate",   "hemisphere"),
    ("Veronica",     "Shrub", "TeES","temperate",   "hemisphere"),
    ("Leptospermum", "Shrub", "SuBE","subtropical", "round"),
    ("Westringia",   "Shrub", "SuBE","subtropical", "hemisphere"),
    # ── Climbers ────────────────────────────────────────────────────────
    ("Hedera",       "Climber","CLM","temperate",   "flat"),
    ("Parthenocissus","Climber","CLM","temperate",  "flat"),
    ("Wisteria",     "Climber","CLM","temperate",   "spreading"),
    ("Campsis",      "Climber","CLM","temperate",   "spreading"),
    ("Trachelospermum","Climber","CLM","subtropical","flat"),
    ("Passiflora",   "Climber","CLM","tropical",    "flat"),
    ("Clematis",     "Climber","CLM","temperate",   "flat"),
    ("Ipomoea",      "Climber","CLM","tropical",    "flat"),
    ("Monstera",     "Climber","CLM","tropical",    "spreading"),
    ("Epipremnum",   "Climber","CLM","tropical",    "flat"),
    ("Philodendron", "Climber","CLM","tropical",    "flat"),
    ("Cissus",       "Climber","CLM","tropical",    "flat"),
    ("Vitis",        "Climber","CLM","temperate",   "flat"),
    ("Ampelopsis",   "Climber","CLM","temperate",   "flat"),
    ("Jasminum",     "Climber","CLM","subtropical", "flat"),
    ("Mandevilla",   "Climber","CLM","tropical",    "flat"),
    ("Allamanda",    "Climber","CLM","tropical",    "flat"),
    ("Petrea",       "Climber","CLM","tropical",    "flat"),
    ("Pyrostegia",   "Climber","CLM","tropical",    "flat"),
    # ── Tropical groundcovers ────────────────────────────────────────────
    ("Heliconia",    "Groundcover","TrGC","tropical","flat"),
    ("Alpinia",      "Groundcover","TrGC","tropical","flat"),
    ("Etlingera",    "Groundcover","TrGC","tropical","flat"),
    ("Zingiber",     "Groundcover","TrGC","tropical","flat"),
    ("Strelitzia",   "Groundcover","TrGC","tropical","flat"),
    ("Ravenala",     "Tree",  "TrBE","tropical",    "spreading"),
    ("Musa",         "Groundcover","TrGC","tropical","flat"),
    ("Canna",        "Groundcover","TrGC","tropical","flat"),
    ("Tradescantia", "Groundcover","TrGC","tropical","flat"),
    ("Callisia",     "Groundcover","TrGC","tropical","flat"),
    ("Ophiopogon",   "Groundcover","TrGC","tropical","flat"),
    ("Liriope",      "Groundcover","TrGC","subtropical","flat"),
    ("Wedelia",      "Groundcover","TrGC","tropical","flat"),
    # ── Grasses — tropical ───────────────────────────────────────────────
    ("Axonopus",     "Grass", "TrGr","tropical",    "flat"),
    ("Zoysia",       "Grass", "TrGr","tropical",    "flat"),
    ("Cynodon",      "Grass", "TrGr","tropical",    "flat"),
    ("Stenotaphrum", "Grass", "TrGr","tropical",    "flat"),
    ("Paspalum",     "Grass", "TrGr","tropical",    "flat"),
    ("Pennisetum",   "Grass", "TrGr","tropical",    "flat"),
    ("Saccharum",    "Grass", "TrGr","tropical",    "flat"),
    ("Miscanthus",   "Grass", "TeGr","temperate",   "flat"),
    ("Panicum",      "Grass", "TrGr","tropical",    "flat"),
    ("Eremochloa",   "Grass", "TrGr","tropical",    "flat"),
    # ── Grasses — temperate ──────────────────────────────────────────────
    ("Lolium",       "Grass", "TeGr","temperate",   "flat"),
    ("Cynosurus",    "Grass", "TeGr","temperate",   "flat"),
    ("Dactylis",     "Grass", "TeGr","temperate",   "flat"),
    ("Stipa",        "Grass", "TeGr","temperate",   "flat"),
    ("Molinia",      "Grass", "TeGr","temperate",   "flat"),
    ("Deschampsia",  "Grass", "TeGr","temperate",   "flat"),
    ("Hakonechloa",  "Grass", "TeGr","temperate",   "flat"),
    ("Nassella",     "Grass", "TeGr","temperate",   "flat"),
    ("Sporobolus",   "Grass", "TeGr","temperate",   "flat"),
    ("Muhlenbergia", "Grass", "TeGr","temperate",   "flat"),
    # ── Temperate groundcovers ───────────────────────────────────────────
    ("Vinca",        "Groundcover","TeGC","temperate","flat"),
    ("Pachysandra",  "Groundcover","TeGC","temperate","flat"),
    ("Ajuga",        "Groundcover","TeGC","temperate","flat"),
    ("Lamium",       "Groundcover","TeGC","temperate","flat"),
    ("Bergenia",     "Groundcover","TeGC","temperate","flat"),
    ("Stachys",      "Groundcover","TeGC","temperate","flat"),
    ("Sedum",        "Groundcover","TeGC","temperate","flat"),
    ("Sempervivum",  "Groundcover","Succ","temperate","flat"),
    ("Echeveria",    "Groundcover","Succ","subtropical","flat"),
    ("Aloe",         "Groundcover","Succ","subtropical","flat"),
    ("Agave",        "Groundcover","Succ","subtropical","flat"),
    ("Yucca",        "Shrub", "SuBE","subtropical", "round"),
    ("Phormium",     "Groundcover","TeGC","subtropical","flat"),
    ("Libertia",     "Groundcover","TeGC","subtropical","flat"),
    ("Acanthus",     "Groundcover","TeGC","temperate","flat"),
    ("Hosta",        "Groundcover","TeGC","temperate","flat"),
    ("Astilbe",      "Groundcover","TeGC","temperate","flat"),
    ("Hemerocallis", "Groundcover","TeGC","temperate","flat"),
    ("Iris",         "Groundcover","TeGC","temperate","flat"),
    # ── Ferns ────────────────────────────────────────────────────────────
    ("Nephrolepis",  "Groundcover","Fern","tropical", "flat"),
    ("Asplenium",    "Groundcover","Fern","temperate","flat"),
    ("Dicksonia",    "Tree",  "Fern","subtropical",  "spreading"),
    ("Cyathea",      "Tree",  "Fern","subtropical",  "spreading"),
    ("Polystichum",  "Groundcover","Fern","temperate","flat"),
    ("Dryopteris",   "Groundcover","Fern","temperate","flat"),
    ("Blechnum",     "Groundcover","Fern","subtropical","flat"),
    ("Woodwardia",   "Groundcover","Fern","subtropical","flat"),
    # ── Mangroves ────────────────────────────────────────────────────────
    ("Rhizophora",   "Mangrove","TrBE","tropical",   "spreading"),
    ("Avicennia",    "Mangrove","TrBE","tropical",   "spreading"),
    ("Bruguiera",    "Mangrove","TrBE","tropical",   "round"),
    ("Sonneratia",   "Mangrove","TrBE","tropical",   "round"),
    ("Laguncularia", "Mangrove","TrBE","tropical",   "round"),
    ("Ceriops",      "Mangrove","TrBE","tropical",   "round"),
    ("Aegiceras",    "Mangrove","TrBE","tropical",   "round"),
    ("Xylocarpus",   "Mangrove","TrBE","tropical",   "round"),
]

FIELDS = [
    "id","species","common_name","category","mean_lai","lai_min","lai_max",
    "measurement_count","pft","canopy_form","climate","deciduous",
    "tier","tier_source","sources","notes"
]

def get_species_for_genus(genus, max_species=500):
    """Query GBIF species search for accepted species in a genus."""
    results = []
    offset = 0
    limit  = 300

    while offset < max_species:
        params = {
            "q":      genus,
            "rank":   "SPECIES",
            "status": "ACCEPTED",
            "kingdom":"Plantae",
            "limit":  min(limit, max_species - offset),
            "offset": offset,
        }
        try:
            r = requests.get(GBIF_SEARCH, params=params, timeout=30)
            if not r.ok:
                break
            data = r.json()
            batch = data.get("results", [])
            if not batch:
                break
            # Filter to actual species in this genus
            for sp_data in batch:
                cn = sp_data.get("canonicalName","")
                fam = sp_data.get("family","")
                # Must start with genus name and be exactly binomial
                parts = cn.split()
                if len(parts) == 2 and parts[0].lower() == genus.lower():
                    results.append((cn, sp_data.get("vernacularName",""), fam))
            offset += len(batch)
            if len(batch) < limit:
                break
        except Exception:
            break
        time.sleep(DELAY)

    return results

def build():
    # Load existing species
    existing = set()
    for csv_file in ["LAI_global.csv", "LAI_usda_tier4.csv"]:
        p = BASE / csv_file
        if p.exists():
            with open(p, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    existing.add(row["species"].strip().lower())
    print(f"Existing species: {len(existing):,}")

    results = []
    uid = 100000
    genus_counts = {}

    for genus, cat, pft, climate, form in tqdm(TARGET_GENERA, desc="Querying GBIF genera"):
        species_list = get_species_for_genus(genus)
        genus_counts[genus] = len(species_list)
        lai, lmin, lmax = PFT_LAI.get(pft, (2.0, 0.5, 4.0))

        for sp, cn, family in species_list:
            if sp.lower() in existing:
                continue
            results.append({
                "id":                uid,
                "species":           sp,
                "common_name":       cn or "",
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
                "sources":           f"GBIF Backbone Taxonomy (gbif.org, doi:10.15468/39omei). Family: {family}. PFT LAI: Bonan (2008) Science 320:1444",
                "notes":             f"Genus {genus} GBIF accepted species. PFT: {pft}. Urban LAI may differ from natural conditions.",
            })
            existing.add(sp.lower())
            uid += 1

    # Write
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(results)

    cats = Counter(r["category"] for r in results)
    print(f"\n{'='*55}")
    print(f"  LAI_gbif_comprehensive.csv: {len(results):,} species")
    print(f"  By category:")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"    {c:<20} {n:,}")
    print(f"\n  Top 10 genera by species count:")
    for g, n in sorted(genus_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    {g:<20} {n:,}")
    print(f"  Output: {OUT}")
    print(f"{'='*55}")

    return results

if __name__ == "__main__":
    build()
