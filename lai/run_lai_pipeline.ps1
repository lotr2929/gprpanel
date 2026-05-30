$ErrorActionPreference = "Stop"
$BASE = "C:\_myProjects\+GPR\GPRTool\lai"
$SEP  = "-" * 60

Write-Host $SEP
Write-Host "  Step 1: Download USDA PLANTS"
Write-Host $SEP
python "$BASE\download_usda_plants.py"

Write-Host $SEP
Write-Host "  Step 2: Build GPR Global Plant Database"
Write-Host $SEP
python "$BASE\build_gpr_globalplantdb.py"

Write-Host $SEP
Write-Host "  Step 3: Enrich Tier 1 and 2 from GBIF"
Write-Host $SEP
python "$BASE\enrich_koppen.py"

Write-Host $SEP
Write-Host "  Step 4: Upload to Supabase"
Write-Host $SEP
python "$BASE\upload_to_supabase.py"

Write-Host $SEP
Write-Host "  Pipeline complete."
Write-Host $SEP
