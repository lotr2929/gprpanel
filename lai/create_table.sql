-- =============================================================================
-- GPR Global Plant Database — Supabase table definition
-- Project : GPRTool (sfvwhbzxkzlscfsnyrwq)
-- Table   : gpr_plant_species
-- Author  : Boon Lay Ong / GPRI
-- Created : 2026-05-24
--
-- Run this once in the Supabase SQL Editor before running upload_to_supabase.py
-- =============================================================================

CREATE TABLE IF NOT EXISTS gpr_plant_species (

  -- ── TAXONOMY ───────────────────────────────────────────────────────────────
  id                    SERIAL PRIMARY KEY,
  species               TEXT NOT NULL,
  accepted_name         TEXT,
  gbif_taxon_key        INTEGER,
  family                TEXT,
  "order"               TEXT,
  common_name           TEXT,

  -- ── BOTANICAL CLASSIFICATION ───────────────────────────────────────────────
  -- growth_form   : tree | shrub | herb | graminoid | fern | palm | liana |
  --                 bamboo | mangrove | succulent | epiphyte | aquatic
  -- landscape_cat : Tree | Shrub | Groundcover | Grass | Climber | Bamboo |
  --                 Palm | Mangrove | REVIEW
  -- leaf_phenology: evergreen | deciduous | semi-deciduous |
  --                 drought-deciduous | semi-evergreen | annual
  growth_form           TEXT,
  landscape_category    TEXT,
  leaf_phenology        TEXT,

  -- ── BIOGEOGRAPHY ──────────────────────────────────────────────────────────
  -- native_region : Afrotropical | Australasian | Indomalayan | Nearctic |
  --                 Neotropical | Palearctic | Oceanian
  -- native_koppen : comma-separated Köppen codes e.g. 'Af,Am,Aw'
  native_region         TEXT,
  native_koppen         TEXT,

  -- ── LAI DATA ──────────────────────────────────────────────────────────────
  -- lai_method    : LAI-2000 | hemispherical | destructive | litter-trap |
  --                 MODIS | PFT-inferred
  -- lai_context   : urban | natural | plantation | inferred
  lai_mean              NUMERIC(6,3),
  lai_min               NUMERIC(6,3),
  lai_max               NUMERIC(6,3),
  lai_sd                NUMERIC(6,3),
  lai_n                 INTEGER DEFAULT 0,
  lai_method            TEXT,
  lai_context           TEXT,
  lai_measurement_koppen TEXT,
  pft                   TEXT,

  -- ── PROVENANCE ────────────────────────────────────────────────────────────
  -- tier        : 1 = urban field measured  (Tan & Sia 2009 + future campaigns)
  --               2 = open-ground measured  (ORNL / TRY databases)
  --               3 = genus mean            (aggregated from related species)
  --               4 = PFT mean              (Plant Functional Type inference)
  -- tier_source : Direct_Urban_Field | ORNL_TRY_Measured | Genus_Mean |
  --               PFT_Mean_GBIF | PFT_Mean_USDA
  -- urban_context: TRUE | FALSE | UNKNOWN
  tier                  SMALLINT CHECK (tier BETWEEN 1 AND 4),
  tier_source           TEXT,
  urban_context         TEXT DEFAULT 'UNKNOWN',
  sources               TEXT,
  notes                 TEXT,

  -- ── RECORD METADATA ───────────────────────────────────────────────────────
  entry_date            DATE DEFAULT CURRENT_DATE,
  data_version          TEXT DEFAULT '1.0.0',
  -- ai_assisted : TRUE if LAI value or classification was inferred by an AI
  --               model (Tier 3 genus mean, Tier 4 PFT mean). FALSE for
  --               directly measured values (Tier 1 urban field, Tier 2 ORNL/TRY)
  ai_assisted           BOOLEAN DEFAULT FALSE,
  ai_model              TEXT,

  -- ── CONSTRAINTS ───────────────────────────────────────────────────────────
  UNIQUE (species)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_gps_species        ON gpr_plant_species (species);
CREATE INDEX IF NOT EXISTS idx_gps_accepted_name  ON gpr_plant_species (accepted_name);
CREATE INDEX IF NOT EXISTS idx_gps_family         ON gpr_plant_species (family);
CREATE INDEX IF NOT EXISTS idx_gps_growth_form    ON gpr_plant_species (growth_form);
CREATE INDEX IF NOT EXISTS idx_gps_landscape_cat  ON gpr_plant_species (landscape_category);
CREATE INDEX IF NOT EXISTS idx_gps_tier           ON gpr_plant_species (tier);
CREATE INDEX IF NOT EXISTS idx_gps_native_region  ON gpr_plant_species (native_region);
CREATE INDEX IF NOT EXISTS idx_gps_koppen         ON gpr_plant_species (native_koppen);
CREATE INDEX IF NOT EXISTS idx_gps_gbif_key       ON gpr_plant_species (gbif_taxon_key);

-- Full-text search index on species + common name
CREATE INDEX IF NOT EXISTS idx_gps_fts ON gpr_plant_species
  USING GIN (to_tsvector('english', coalesce(species,'') || ' ' || coalesce(common_name,'')));

-- =============================================================================
-- Row Level Security (RLS) — read-only public access; write via service key
-- =============================================================================
ALTER TABLE gpr_plant_species ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read access"
  ON gpr_plant_species FOR SELECT
  USING (true);

-- No public INSERT/UPDATE/DELETE — all writes via service key only

-- =============================================================================
-- Quick verification
-- =============================================================================
SELECT 'gpr_plant_species table created successfully.' AS status;
