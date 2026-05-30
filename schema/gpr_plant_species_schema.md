# GPR Global Plant Database - Schema v2.0
# Reference Document | Created: 30 May 2026 | Author: GPRI / Boon Lay Ong
#
# PURPOSE
# Defines every field in gpr_plant_species (single table).
# Card templates render dynamically from this data - no prose stored.
#
# CONFIDENCE CODES
# M  Measured    - Direct field/lab measurement, citable DOI
# D  Derived     - Calculated from measured parameters via equations
# E  Estimated   - Modelled from PFT, genus mean, or trait class
# P  Placeholder - No data yet; field flagged in card display
#
# STATUS CODES
# existing  - In Supabase, reasonably populated
# partial   - In Supabase, incompletely populated
# scripted  - Enrichment script exists; column may need adding to Supabase
# needed    - Not yet in schema or pipeline

# ============================================================
# SECTION 1 - TAXONOMY & IDENTITY  (13 fields)
# ============================================================
# FIELD                  TYPE      STATUS    SOURCE
# id                     integer   existing  auto-increment primary key
# species                text      existing  binomial, unique, conflict key
# accepted_name          text      existing  GBIF accepted name
# gbif_taxon_key         integer   partial   GBIF backbone ID — enrich_gbif.py
# family                 text      existing  taxonomic family
# order_name             text      existing  taxonomic order
# common_name            text      existing  primary English common name
# common_names_json      jsonb     needed    multilingual {en:[],zh:[],ms:[],id:[]}
# synonyms               text[]    needed    POWO/GBIF synonym list
# iucn_status            text      needed    LC/NT/VU/EN/CR/EX — IUCN Red List API
# invasive_regions       text[]    needed    regions where invasive — GBIF checklist
# native_au              boolean   needed    native to Australia
# native_wa              boolean   needed    native to Western Australia — Florabase

# ============================================================
# SECTION 2 - BOTANICAL CLASSIFICATION  (5 fields)
# ============================================================
# growth_form            text      existing  tree/shrub/herb/graminoid/liana/bamboo/palm/mangrove
# landscape_category     text      existing  Tree/Shrub/Groundcover/Grass/Climber/Bamboo/Palm/Mangrove
# leaf_phenology         text      scripted  evergreen/deciduous/drought-deciduous — AusTraits
# canopy_shape           text      needed    round/spreading/conical/columnar/weeping/irregular
# plant_type_detail      text      needed    sub-classification within growth_form

# ============================================================
# SECTION 3 - MORPHOLOGY  (21 fields)
# ============================================================
# height_mature_m        numeric   scripted  typical mature height — AusTraits
# height_min_m           numeric   needed    minimum recorded height
# height_max_m           numeric   needed    maximum recorded height
# canopy_radius_m        numeric   needed    typical canopy radius at maturity
# canopy_radius_min_m    numeric   needed    minimum canopy radius
# canopy_radius_max_m    numeric   needed    maximum canopy radius
# trunk_diameter_cm      numeric   needed    typical DBH at maturity
# root_architecture      text      needed    shallow/deep/spreading/taproot/fibrous
# substrate_depth_min_mm integer   needed    minimum substrate depth for establishment (mm)
# leaf_texture           text      needed    smooth/waxy/hairy/rough/scaly — PM capture proxy
# leaf_size              text      needed    small(<20cm2)/medium/large(>2000cm2)
# leaf_arrangement       text      needed    alternate/opposite/whorled/basal
# bark_texture           text      needed    smooth/furrowed/plated/fibrous/papery
# flower_colour          text      needed    primary flower colour
# flower_season          text[]    needed    months of flowering e.g. [Sep,Oct,Nov]
# fruit_type             text      needed    dry/fleshy/cone/capsule/none
# growth_rate            text      needed    slow/medium/fast — context-qualified
# growth_rate_note       text      needed    e.g. 'irrigated urban Perth conditions'
# longevity              text      needed    short(<25yr)/medium(25-100yr)/long(>100yr)
# sla                    numeric   scripted  specific leaf area (cm2/g) — AusTraits/TRY
# deciduous              boolean   needed    true/false (derived from leaf_phenology)

# ============================================================
# SECTION 4 - BIOGEOGRAPHY  (5 fields)
# ============================================================
# native_region          text      partial   biogeographic realm — enrich_gbif.py
# native_koppen          text      partial   Köppen zones of origin e.g. Af,Am,Csa
# native_region_detail   text      needed    plain-English: 'Eastern Australia, SE Asia'
# koppen_suitable        text[]    needed    Köppen zones where performs well in urban context
# uhi_suitable           boolean   needed    tolerates urban heat island conditions

# ============================================================
# SECTION 5 - LAI & GPR DATA  (14 fields — best-populated section)
# ============================================================
# lai_mean               numeric   existing  mean LAI value
# lai_min                numeric   existing  minimum LAI recorded
# lai_max                numeric   existing  maximum LAI recorded
# lai_sd                 numeric   existing  standard deviation
# lai_n                  integer   existing  number of measurements
# lai_method             text      existing  LAI-2000/hemispherical/harvest/PFT-inferred/mixed
# lai_context            text      existing  urban/natural/inferred
# lai_measurement_koppen text      existing  climate where LAI was measured
# lai_urban              numeric   needed    measured urban LAI (distinct from natural stand value)
# lai_urban_flag         boolean   needed    true if lai_mean is from urban context
# lai_confidence         text      needed    M/D/E/P confidence code
# clumping_index         numeric   needed    gamma — Beer-Lambert clumping correction
# extinction_coeff       numeric   needed    k — Beer-Lambert extinction coefficient
# pft                    text      existing  plant functional type (IGBP classification)

# ============================================================
# SECTION 6 - ECOSYSTEM SERVICES  (36 fields)
# Each service: rating(1-5), confidence(M/D/E/P), key parameters, source, notes
# ============================================================

# --- Urban Cooling (6 fields) ---
# cooling_rating         integer   needed    1-5 composite score
# cooling_confidence     text      needed    M/D/E/P
# cooling_stomatal_gs    numeric   needed    stomatal conductance mmol/m2/s — TRY Database
# cooling_bowen_ratio    numeric   needed    Bowen ratio (sensible/latent heat flux)
# cooling_shade_factor   numeric   scripted  0-1 shade fraction — enrich_carbon.py (McPherson)
# cooling_source         text      needed    citation keys

# --- Carbon Sequestration (6 fields) ---
# carbon_rating          integer   needed    1-5 composite score
# carbon_confidence      text      needed    M/D/E/P
# carbon_seq_kg_yr       numeric   scripted  kg CO2/yr at maturity — enrich_carbon.py (McPherson)
# carbon_wood_density    numeric   needed    g/cm3 — Global Wood Density Database (Chave 2009)
# carbon_agb_equation    text      needed    allometric equation reference (Jenkins 2003 etc)
# carbon_source          text      needed    citation keys

# --- Stormwater Interception (6 fields) ---
# stormwater_rating      integer   needed    1-5 composite score
# stormwater_confidence  text      needed    M/D/E/P (typically D — LAI-derived)
# stormwater_intercept   numeric   needed    canopy interception fraction 0-1
# stormwater_capacity_s  numeric   needed    mm water storage per unit LAI (Xiao 2000)
# stormwater_stemflow    numeric   needed    proportion reaching ground via stem
# stormwater_source      text      needed    citation keys

# --- Air Quality / PM Capture (5 fields) ---
# airquality_rating      integer   needed    1-5 composite score
# airquality_confidence  text      needed    M/D/E/P
# airquality_pm_vd       numeric   needed    PM deposition velocity Vd (cm/s) — Freer-Smith 2005
# airquality_leaf_class  text      needed    smooth/waxy/hairy/rough (derived from leaf_texture)
# airquality_source      text      needed    citation keys

# --- Biodiversity (6 fields) ---
# biodiversity_rating    integer   needed    1-5 composite score
# biodiversity_confidence text     needed    M/D/E/P
# biodiversity_insects   integer   needed    associated herbivorous insect species — HOSTS DB (NHM)
# biodiversity_pollinator text     needed    low/medium/high + pollinator guild type
# biodiversity_bird      text      needed    low/medium/high habitat value
# biodiversity_source    text      needed    citation keys
# NOTE: native_au flag automatically elevates biodiversity_rating

# --- Soil Health (7 fields) ---
# soilhealth_rating      integer   needed    1-5 composite score
# soilhealth_confidence  text      needed    M/D/E/P
# soilhealth_cn_ratio    numeric   needed    C:N ratio of leaf litter — TRY Database
# soilhealth_mycorrhizal text      needed    AM/EM/none/unknown — FungalRoot DB (Soudzilovskaia 2020)
# soilhealth_n_fixing    boolean   needed    nitrogen fixing — Fabaceae/Casuarinaceae/Alnus etc
# soilhealth_decomp_rate text      needed    slow/medium/fast
# soilhealth_source      text      needed    citation keys

# ============================================================
# SECTION 7 - URBAN PERFORMANCE  (14 fields)
# ============================================================
# drought_tolerance      text      scripted  low/medium/high — AusTraits
# drought_mechanism      text      needed    deep roots/leaf drop/CAM/stomatal closure
# fire_tolerance         text      scripted  resprouter/seeder/sensitive — AusTraits
# pollution_tolerance    text      needed    low/medium/high — literature
# wind_tolerance         text      needed    sheltered/moderate/exposed
# salt_tolerance         text      needed    low/medium/high
# water_needs            text      needed    low/medium/high (urban irrigation context)
# sunlight               text      needed    full/partial/shade/versatile
# substrate_types        text[]    needed    ground/podium/rooftop/vertical/atrium
# irrigation_required    boolean   needed    false = survives on Perth rainfall alone
# maintenance_level      text      needed    low/medium/high
# establishment_period   text      needed    months to establishment
# usda_zones             text      scripted  USDA hardiness zones — enrich_usda_zones.py
# perth_notes            text      needed    Perth-specific performance notes (curated)

# ============================================================
# SECTION 8 - IMAGES & DISPLAY  (3 fields)
# ============================================================
# image_url              text      partial   Wikipedia/Wikimedia full image URL
# image_credit           text      partial   Wikimedia Commons attribution string
# image_thumb_url        text      needed    smaller thumbnail for list view

# ============================================================
# SECTION 9 - PROVENANCE & METADATA  (14 fields)
# ============================================================
# tier                   integer   existing  1=urban field/2=ORNL-TRY/3=genus mean/4=PFT
# tier_source            text      existing  Direct_Urban_Field/ORNL_TRY_Measured/Genus_Mean/PFT_Mean_GBIF
# urban_context          text      existing  TRUE/FALSE/UNKNOWN
# sources                text      existing  pipe-delimited citation list
# data_type              text      existing  measured/generated (schema v1.2.0)
# generation_method      text      existing  genus_mean/pft_bonan2008 (schema v1.2.0)
# enrichment_sources     text      scripted  pipe-delimited: AusTraits|McPherson|TRY etc
# data_completeness      integer   needed    0-100 auto-calculated pct non-null fields
# overall_confidence     text      needed    auto-derived: lowest confidence code across all fields
# notes                  text      existing  general notes
# entry_date             date      existing  record creation date
# data_version           text      existing  schema version string
# last_updated           date      needed    date of most recent enrichment
# added_by               text      needed    data contributor identifier

# ============================================================
# FIELD COUNT SUMMARY
# ============================================================
# Section 1  Taxonomy & Identity          13  (8 existing/partial, 5 needed)
# Section 2  Botanical Classification      5  (3 existing, 2 needed)
# Section 3  Morphology                   21  (2 scripted, 19 needed)
# Section 4  Biogeography                  5  (2 partial, 3 needed)
# Section 5  LAI & GPR                    14  (9 existing, 5 needed)
# Section 6  Ecosystem Services           36  (2 scripted, 34 needed)
# Section 7  Urban Performance            14  (3 scripted, 11 needed)
# Section 8  Images & Display              3  (2 partial, 1 needed)
# Section 9  Provenance & Metadata        14  (8 existing, 6 needed)
# ──────────────────────────────────────────────────────────
# TOTAL                                  125 fields
# Already in Supabase (existing/partial):  ~35 fields
# Scripted, column may need adding:         ~8 fields
# Not yet in schema or pipeline:           ~82 fields
#
# ESTIMATED TABLE SIZE AT 300,000 SPECIES
# Sparse (realistic — most ecosystem fields null):  ~120 MB
# Fully populated:                                  ~320 MB
# Both well within Supabase Pro 8 GB limit.

# ============================================================
# DATA SOURCES
# ============================================================
# Source                        Fields covered                     Access
# GBIF API                      gbif_taxon_key, invasive_regions   Free API
# POWO (Kew)                    synonyms, native_region_detail     Free API
# IUCN Red List API             iucn_status                        Free API (registration)
# Florabase (WA)                native_wa                          Free web
# AusTraits v6 (Zenodo)         height, sla, drought/fire          Free download
# TRY Plant Trait Database      sla, cn_ratio, stomatal_gs         Free (registered)
# Global Wood Density DB        carbon_wood_density                Free download
# McPherson PSW-GTR-253         carbon_seq_kg_yr, shade_factor     Free download
# i-Tree Species Database       ecosystem service validation        Free web
# HOSTS DB (NHM London)         biodiversity_insects               Free web
# FungalRoot DB                 soilhealth_mycorrhizal             Free download
# iNaturalist / ALA             biodiversity ratings               Free API
# Wikipedia/Wikimedia           image_url, image_credit            Free API (in use)
# USDA Plants                   usda_zones, growth cues            Free (in use)
# Manual curation (GPRI)        perth_notes, canopy_shape,         Expert knowledge
#                               root_architecture, conflicts

# ============================================================
# MIGRATION SEQUENCE (current v1.2 -> v2.0)
# ============================================================
# Step 1.  Lock this schema document (no additions mid-build)
# Step 2.  Build SQLite sync script -> audit current data quality
# Step 3.  ALTER TABLE in Supabase to add ~90 new columns
# Step 4.  Update build_gpr_globalplantdb.py FIELDS list
# Step 5.  Build Detail Card + Full Description rendering engine in panel.html
# Step 6.  Run enrichment pipeline in priority order:
#          a. GBIF        - gbif_taxon_key gap-fill, invasive_regions
#          b. IUCN        - iucn_status
#          c. POWO        - synonyms, native_region_detail
#          d. AusTraits   - already scripted, re-run for new fields
#          e. TRY         - cn_ratio, stomatal_gs
#          f. Wood Density DB - carbon_wood_density
#          g. McPherson   - already scripted, verify run
#          h. FungalRoot  - soilhealth_mycorrhizal
#          i. HOSTS DB    - biodiversity_insects
#          j. Florabase   - native_wa
#          k. Compute ratings from parameters
#          l. Compute data_completeness + overall_confidence
