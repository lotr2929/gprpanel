-- =============================================================================
-- GPR Global Plant Database — Schema enrichment
-- Run in: https://supabase.com/dashboard/project/sfvwhbzxkzlscfsnyrwq/sql/new
-- Adds functional trait fields to gpr_plant_species for enrichment via
-- open sources: TRY, USDA Plants, AusTraits, McPherson et al. 2016
-- =============================================================================

ALTER TABLE gpr_plant_species

  -- From TRY Plant Trait Database (Kattge et al. 2020)
  -- Trait ID 11 = SLA; cm²/g; higher = more acquisitive leaf strategy
  ADD COLUMN IF NOT EXISTS sla              numeric,

  -- From USDA Plants Database / AusTraits
  -- Controlled vocabulary: 'slow' / 'medium' / 'fast'
  ADD COLUMN IF NOT EXISTS growth_rate      text,

  -- From USDA Plants Database drought tolerance ratings
  -- Controlled vocabulary: 'low' / 'moderate' / 'high'
  ADD COLUMN IF NOT EXISTS drought_tolerance text,

  -- From USDA Plants Database / literature
  -- Controlled vocabulary: 'shallow' / 'medium' / 'deep'
  ADD COLUMN IF NOT EXISTS root_depth       text,

  -- Urban air pollution tolerance (particulate, NO2, SO2)
  -- Controlled vocabulary: 'low' / 'moderate' / 'high'
  -- Source: Nowak et al. 2008, literature synthesis
  ADD COLUMN IF NOT EXISTS pollution_tolerance text,

  -- Fraction of solar radiation intercepted at ground level (0–1)
  -- Source: McPherson et al. 2016 USDA Forest Service GTR PSW-253
  ADD COLUMN IF NOT EXISTS shade_factor     numeric,

  -- kg CO2 sequestered per tree per year (mature canopy)
  -- Source: McPherson et al. 2016
  ADD COLUMN IF NOT EXISTS carbon_seq_kg_yr numeric,

  -- USDA Plant Hardiness Zone range e.g. '9-12'
  -- Derived from native_koppen via standard zone-climate mapping
  ADD COLUMN IF NOT EXISTS usda_zone        text,

  -- Shade tolerance of the species itself (not shade it casts)
  -- Controlled vocabulary: 'intolerant' / 'intermediate' / 'tolerant'
  -- Source: USDA Plants Database
  ADD COLUMN IF NOT EXISTS shade_tolerance  text;

-- Add enrichment source tracking
ALTER TABLE gpr_plant_species
  ADD COLUMN IF NOT EXISTS enrichment_sources text;
  -- Pipe-delimited list of sources used for functional trait fields
  -- e.g. 'TRY|USDA|AusTraits|McPherson2016'

COMMENT ON COLUMN gpr_plant_species.sla               IS 'Specific Leaf Area (cm²/g). Source: TRY Trait ID 11.';
COMMENT ON COLUMN gpr_plant_species.growth_rate        IS 'Growth rate class: slow/medium/fast. Source: USDA Plants / AusTraits.';
COMMENT ON COLUMN gpr_plant_species.drought_tolerance  IS 'Drought tolerance: low/moderate/high. Source: USDA Plants Database.';
COMMENT ON COLUMN gpr_plant_species.root_depth         IS 'Root system depth: shallow/medium/deep.';
COMMENT ON COLUMN gpr_plant_species.pollution_tolerance IS 'Urban air pollution tolerance: low/moderate/high. Source: Nowak et al. 2008.';
COMMENT ON COLUMN gpr_plant_species.shade_factor       IS 'Fraction of ground shaded at solar noon (0–1). Source: McPherson et al. 2016.';
COMMENT ON COLUMN gpr_plant_species.carbon_seq_kg_yr   IS 'kg CO2 sequestered per mature tree per year. Source: McPherson et al. 2016.';
COMMENT ON COLUMN gpr_plant_species.usda_zone          IS 'USDA Hardiness Zone range e.g. 9-12. Derived from native_koppen.';
COMMENT ON COLUMN gpr_plant_species.shade_tolerance    IS 'Species shade tolerance: intolerant/intermediate/tolerant. Source: USDA Plants.';

-- =============================================================================
-- Image enrichment fields
-- Populated by enrich_images.py
-- Sources tried in order: Wikipedia → iNaturalist → GBIF
-- =============================================================================
ALTER TABLE gpr_plant_species
  ADD COLUMN IF NOT EXISTS image_url    text,
  ADD COLUMN IF NOT EXISTS image_credit text,
  ADD COLUMN IF NOT EXISTS image_source text;
  -- image_source values: 'wikipedia' | 'inaturalist' | 'gbif'

COMMENT ON COLUMN gpr_plant_species.image_url    IS 'Direct URL to a free-licence species image.';
COMMENT ON COLUMN gpr_plant_species.image_credit IS 'Attribution string for display (e.g. "© John Smith, CC BY 4.0")';
COMMENT ON COLUMN gpr_plant_species.image_source IS 'Source of image: wikipedia | inaturalist | gbif';
