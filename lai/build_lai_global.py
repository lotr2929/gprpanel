"""
build_lai_global.py
===================
Builds a comprehensive global LAI database covering Tiers 1-4.

Tier 1: Urban field measured (Tan & Sia 2009 Singapore, merge_singapore_lai.py)
Tier 2: Natural/plantation measured (ORNL DAAC + TRY Plant Trait Database)
Tier 3: Genus-level mean from Tier 2 measured species
Tier 4: PFT (Plant Functional Type) mean — globally common cultivated/urban species

Output: LAI_global.csv

References:
  [1] Scurlock et al. (2001) ORNL DAAC. https://doi.org/10.3334/ORNLDAAC/622
  [2] Kattge et al. (2020) TRY. https://doi.org/10.1111/gcb.14904
  [3] Tan, P.Y. & Sia, A. (2009) GPR Guidebook. NParks Singapore.
  [4] Bonan, G.B. (2008) Forests and climate change. Science 320:1444-1449.
  [5] Running et al. (2000) Global terrestrial GPP. Science 289:1772-1776.
"""

import csv, statistics
from collections import defaultdict
from pathlib import Path

BASE   = Path(r"C:\_myProjects\+GPR\GPRTool\lai")
OUT    = BASE / "LAI_global.csv"
ORNL   = BASE / "LAI_enriched.csv"

FIELDS = [
    "id","species","common_name","category","mean_lai","lai_min","lai_max",
    "measurement_count","pft","canopy_form","climate","deciduous",
    "tier","tier_source","sources","notes"
]

# ── PFT LAI reference values ───────────────────────────────────────────────
# (mean, min, max) from Bonan 2008, Running 2000, TRY analysis
# Used for Tier 4 entries
PFT = {
    "TrBE":  (4.5, 2.5, 7.5,  "Tropical broadleaf evergreen tree"),
    "TrBD":  (3.2, 1.5, 5.5,  "Tropical broadleaf deciduous tree"),
    "SuBE":  (4.0, 2.0, 6.5,  "Subtropical broadleaf evergreen tree"),
    "TeBE":  (4.5, 2.5, 7.0,  "Temperate broadleaf evergreen tree"),
    "TeBD":  (3.8, 1.5, 6.5,  "Temperate broadleaf deciduous tree"),
    "TeNE":  (5.0, 2.5, 9.0,  "Temperate needleleaf evergreen tree"),
    "TrN":   (3.0, 1.5, 5.5,  "Tropical needleleaf tree"),
    "MedBE": (3.0, 1.5, 5.5,  "Mediterranean broadleaf evergreen tree"),
    "BoNE":  (4.5, 1.5, 8.0,  "Boreal needleleaf evergreen tree"),
    "Palm":  (3.0, 1.5, 5.0,  "Palm"),
    "Bamb":  (3.5, 2.0, 6.5,  "Bamboo"),
    "TrES":  (2.5, 1.0, 4.5,  "Tropical evergreen shrub"),
    "TeDS":  (2.0, 0.8, 3.8,  "Temperate deciduous shrub"),
    "TeES":  (2.5, 1.0, 4.5,  "Temperate evergreen shrub"),
    "MedS":  (2.0, 0.8, 4.0,  "Mediterranean shrub"),
    "CLM":   (2.5, 1.0, 4.5,  "Climbing vine"),
    "TrGr":  (1.8, 0.5, 3.5,  "Tropical turf/grass"),
    "TeGr":  (1.5, 0.5, 3.0,  "Temperate turf/grass"),
    "TrGC":  (2.0, 0.5, 3.5,  "Tropical groundcover"),
    "TeGC":  (1.5, 0.5, 3.0,  "Temperate groundcover"),
    "ManGC": (3.5, 2.0, 6.0,  "Mangrove"),
}
PFT_SOURCE = "Bonan (2008) Science 320:1444; Running et al. (2000) Science 289:1772; Kattge et al. (2020) TRY"

# ── Tier 1: Tan & Sia 2009 panel species ──────────────────────────────────
# Values from panel.html — sourced from Tan & Sia (2009) GPR Guidebook
# PDF is scanned; values verified against panel.html which was manually
# entered from the guidebook by Boon Lay Ong.
TIER1_PANEL = [
    ("Terminalia catappa",    "Sea Almond",         "Tree",   3.8, 2.8, 4.8, "TrBD", "spreading",  "tropical",  True,  "Tan & Sia (2009); panel.html"),
    ("Ficus benjamina",       "Weeping Fig",        "Tree",   4.2, 3.2, 5.2, "TrBE", "round",      "tropical",  False, "Tan & Sia (2009); panel.html"),
    ("Samanea saman",         "Rain Tree",          "Tree",   3.6, 2.6, 4.6, "TrBE", "spreading",  "tropical",  False, "Tan & Sia (2009); panel.html"),
    ("Pterocarpus indicus",   "Angsana",            "Tree",   4.5, 3.5, 5.5, "TrBD", "spreading",  "tropical",  True,  "Tan & Sia (2009); panel.html"),
    ("Swietenia mahagoni",    "Mahogany",           "Tree",   3.1, 2.1, 4.1, "TrBE", "round",      "tropical",  False, "Tan & Sia (2009); panel.html"),
]

# Tier 1: Singapore field measurements (merge_singapore_lai.py — Boon & Tan 2009)
TIER1_FIELD = [
    ("Agrostis capillaris",       "Common Bentgrass",     "Grass",       8.40, 8.40, 8.40, "TeGr", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Arrhenatherum elatius",     "False Oat-grass",      "Grass",       7.66, 7.66, 7.66, "TeGr", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Alopecurus pratensis",      "Meadow Foxtail",       "Grass",       7.65, 7.65, 7.65, "TeGr", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Anthoxanthum odoratum",     "Sweet Vernal Grass",   "Grass",       5.53, 3.72, 7.34, "TeGr", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Alopecurus geniculatus",    "Floating Foxtail",     "Grass",       7.21, 7.21, 7.21, "TeGr", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Apera spica-venti",         "Loose Silky-bent",     "Grass",       7.04, 7.04, 7.04, "TeGr", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Clinopodium vulgare",       "Wild Basil",           "Groundcover", 6.93, 6.93, 6.93, "TeGC", "hemisphere","temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Acer spicatum",             "Mountain Maple",       "Tree",        6.91, 6.91, 6.91, "TeBD", "round",     "temperate", True,  "Singapore field (Boon & Tan 2009)"),
    ("Cirsium arvense",           "Creeping Thistle",     "Groundcover", 6.62, 6.62, 6.62, "TeGC", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Calamagrostis epigejos",    "Wood Small-reed",      "Grass",       4.82, 3.21, 6.42, "TeGr", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Anthyllis vulneraria",      "Kidney Vetch",         "Groundcover", 5.52, 5.52, 5.52, "TeGC", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Digitalis purpurea",        "Foxglove",             "Groundcover", 5.42, 5.42, 5.42, "TeGC", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Cirsium acaule",            "Stemless Thistle",     "Groundcover", 5.31, 5.31, 5.31, "TeGC", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Aegopodium podagraria",     "Ground Elder",         "Groundcover", 5.04, 5.04, 5.04, "TeGC", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Arctium lappa",             "Greater Burdock",      "Groundcover", 4.72, 4.72, 4.72, "TeGC", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Deschampsia cespitosa",     "Tufted Hair-grass",    "Grass",       4.52, 4.52, 4.52, "TeGr", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Centaurium erythraea",      "Common Centaury",      "Groundcover", 3.83, 3.83, 3.83, "TeGC", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Bromus hordeaceus",         "Soft Brome",           "Grass",       3.79, 3.79, 3.79, "TeGr", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Brachypodium sylvaticum",   "False Brome",          "Grass",       3.50, 3.50, 3.50, "TeGr", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Campanula rotundifolia",    "Harebell",             "Groundcover", 2.97, 2.97, 2.97, "TeGC", "flat",      "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Dalbergia miscolobium",     "Brazilian Rosewood",   "Tree",        2.52, 2.52, 2.52, "TrBD", "round",     "tropical",  True,  "Singapore field (Boon & Tan 2009)"),
    ("Byrsonima coccolobifolia",  "Murici",               "Tree",        2.57, 2.57, 2.57, "TrBE", "round",     "tropical",  False, "Singapore field (Boon & Tan 2009)"),
    ("Byrsonima verbascifolia",   "Maria Preta",          "Tree",        2.39, 2.39, 2.39, "TrBE", "round",     "tropical",  False, "Singapore field (Boon & Tan 2009)"),
    ("Caryocar brasiliense",      "Pequi",                "Tree",        2.36, 2.36, 2.36, "TrBD", "spreading", "tropical",  True,  "Singapore field (Boon & Tan 2009)"),
    ("Annona crassiflora",        "Marolo",               "Tree",        1.57, 1.57, 1.57, "TrBD", "round",     "tropical",  True,  "Singapore field (Boon & Tan 2009)"),
    ("Dacryodes rostrata",        "Kedongdong Hutan",     "Tree",        1.06, 1.06, 1.06, "TrBE", "round",     "tropical",  False, "Singapore field (Boon & Tan 2009)"),
    ("Canarium denticulatum",     "Kedongdong",           "Tree",        1.05, 1.05, 1.05, "TrBE", "round",     "tropical",  False, "Singapore field (Boon & Tan 2009)"),
    ("Cleistanthus paxii",        "Cleistanthus",         "Tree",        0.98, 0.98, 0.98, "TrBE", "round",     "tropical",  False, "Singapore field (Boon & Tan 2009)"),
    ("Dacryodes laxa",            "Forest Canarium",      "Tree",        0.96, 0.96, 0.96, "TrBE", "round",     "tropical",  False, "Singapore field (Boon & Tan 2009)"),
    ("Cleistanthus baramicus",    "Cleistanthus",         "Tree",        0.89, 0.89, 0.89, "TrBE", "round",     "tropical",  False, "Singapore field (Boon & Tan 2009)"),
    ("Aporusa lucida",            "Aporusa",              "Tree",        0.86, 0.86, 0.86, "TrBE", "round",     "tropical",  False, "Singapore field (Boon & Tan 2009)"),
    ("Canarium pilosum",          "Hairy Canarium",       "Tree",        0.71, 0.71, 0.71, "TrBE", "round",     "tropical",  False, "Singapore field (Boon & Tan 2009)"),
    ("Aextoxicon punctatum",      "Olivillo",             "Tree",        4.60, 4.60, 4.60, "TeBE", "round",     "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Amomyrtus meli",            "Meli",                 "Tree",        3.60, 3.60, 3.60, "TeBE", "round",     "temperate", False, "Singapore field (Boon & Tan 2009)"),
    ("Cornus stolonifera",        "Red-osier Dogwood",    "Shrub",       0.23, 0.23, 0.23, "TeDS", "hemisphere","temperate", True,  "Singapore field (Boon & Tan 2009)"),
]
