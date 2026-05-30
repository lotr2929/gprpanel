"""
download_usda_plants.py
=======================
STATUS: USDA PLANTS bulk CSV download was removed from plants.usda.gov
in the 2024/2025 site redesign. The download page no longer exists.

USDA PLANTS data (North American species) is substantially covered by
our GBIF download (LAI_gbif_comprehensive.csv), as USDA PLANTS is
registered as a GBIF checklist dataset (DOI: 10.15468/t40oqu) and its
species are incorporated into the GBIF backbone taxonomy.

This script is retained as a placeholder. If USDA restores bulk download
access, update USDA_URLS below and remove the early exit.

Future alternative: download via GBIF dataset API using dataset key
705922f7-5ba5-49ab-a75d-722e3090e690. This would require pagination
through the GBIF occurrence API and is not yet implemented.

Run: python download_usda_plants.py
"""

import sys

print("=" * 60)
print("  USDA PLANTS download — UNAVAILABLE")
print("=" * 60)
print()
print("  The USDA PLANTS bulk CSV download was removed from")
print("  plants.usda.gov in the 2024/2025 site redesign.")
print()
print("  USDA species are substantially covered by the GBIF")
print("  download (LAI_gbif_comprehensive.csv), as USDA PLANTS")
print("  is incorporated into the GBIF backbone taxonomy.")
print("  GBIF dataset key: 705922f7-5ba5-49ab-a75d-722e3090e690")
print("  DOI: 10.15468/t40oqu")
print()
print("  No action required. Skipping.")
print("=" * 60)
sys.exit(0)
