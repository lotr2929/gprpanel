-- ============================================================
-- GPR Global Plant Database — Schema migration to v1.2.0
-- Run in: Supabase SQL Editor (project sfvwhbzxkzlscfsnyrwq)
-- Date: 2026-05-25
--
-- Changes:
--   REMOVE: ai_assisted (boolean), ai_model (text)
--   ADD:    data_type (text), generation_method (text)
-- ============================================================

-- Step 1: Add new columns
ALTER TABLE gpr_plant_species
  ADD COLUMN IF NOT EXISTS data_type        TEXT,
  ADD COLUMN IF NOT EXISTS generation_method TEXT;

-- Step 2: Populate from tier
UPDATE gpr_plant_species
SET
  data_type         = CASE
                        WHEN tier IN (1, 2) THEN 'measured'
                        WHEN tier IN (3, 4) THEN 'generated'
                        ELSE ''
                      END,
  generation_method = CASE
                        WHEN tier = 3 THEN 'genus_mean'
                        WHEN tier = 4 THEN 'pft_bonan2008'
                        ELSE NULL
                      END;

-- Step 3: Update data_version
UPDATE gpr_plant_species
SET data_version = '1.2.0';

-- Step 4: Add NOT NULL constraint now that data is populated
ALTER TABLE gpr_plant_species
  ALTER COLUMN data_type SET NOT NULL;

-- Step 5: Drop old columns
ALTER TABLE gpr_plant_species
  DROP COLUMN IF EXISTS ai_assisted,
  DROP COLUMN IF EXISTS ai_model;

-- Step 6: Verify
SELECT
  data_type,
  generation_method,
  COUNT(*) AS count
FROM gpr_plant_species
GROUP BY data_type, generation_method
ORDER BY data_type, generation_method;

-- Expected result:
--   generated | genus_mean    |    22
--   generated | pft_bonan2008 | 33,644
--   measured  | NULL          |   763
-- ============================================================
