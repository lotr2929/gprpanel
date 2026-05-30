# GPR Global Plant Database — Plant Record Specification
**Author:** Boon Lay Ong  
**Created:** 2026-05-28  
**Status:** Working specification — update as design decisions are made

---

## Purpose

Defines the full data structure for each plant record in the GPR Global Plant Database, and the two-tier display format in GPRPanel: a **Brief View** (panel summary) and a **Full Account** (detailed modal/page). Also records the LAIe (effective LAI) concept and correction factor framework.

This document extends the existing schema (v1.1.0, `gpr_globalplantdb_schema.md`). New fields proposed here form the basis for schema v2.0.

---

## Part 1: Brief View (Panel Summary Table)

Shown by default in the Plant Selector panel.

| Field | Example | Notes |
|---|---|---|
| Scientific name | *Aextoxicon punctatum* | Italicised binomial |
| Common name/s | Olivillo, Tique | Comma-separated, English first |
| Plant type | Tree — Broadleaf evergreen | Type + leaf_phenology flag |
| Growth form | Upright, single-trunk | Brief morphological descriptor |
| Growth rate | 0.3–0.5 m/yr (slow) | Quantified range + qualitative label |
| Mature height | 15–25 m | |
| Canopy spread | 6–10 m | |
| Climate | Temperate oceanic, warm mediterranean *(Cfb, Csb)* | Plain English first, Köppen in italics |
| LAI range | 3.8–5.4 (mean 4.6) — *Ong & Tan 2003* | T1: source cited inline on this row |
| Data tier | T1 — Urban field | T1/T2/T3/T4 with label |
| Sources | iNaturalist; Plants of the World Online | Sources for all OTHER fields in this table |

**Buttons:** [Select this plant]  [Full Account →]

---

## Part 2: Full Account Sections

### 2.1 Overview
- Hero photograph (Wikimedia Commons, CC-licensed)
- Scientific name, family, genus/species
- Common names (English + multilingual where available)
- Native origin / geographic range
- Urban suitability rating (1–5, criteria-defined)

### 2.2 LAI & GPR Data
- LAI reference value (from literature)
- LAI range (min–max) with n observations
- Data tier: T1 Urban field / T2 Literature / T3 Genus mean / T4 PFT mean
- LAI measurement method (direct harvest / indirect optical / modelled)
- Number of observations (n) underpinning the value
- Primary source/s with full citation
- LAIe correction factor breakdown per species (see Part 4)
- SLA — Specific Leaf Area (companion metric, from TRY where available)
- Phenological notes (leaf flush, senescence calendar if deciduous)

### 2.3 Morphology
- Height range (min–max) and typical at maturity
- Canopy spread range and typical
- Trunk height and radius at maturity
- Canopy shape: sphere / cone / cylinder / irregular_sphere / spreading / columnar / weeping
- Canopy density coefficient (0–1)
- Root behaviour: non-invasive / moderate / aggressive (infrastructure risk)

### 2.4 Climate & Habitat
- Köppen zone/s with plain-English description
- Native climate range
- Drought tolerance
- Salt tolerance (coastal suitability)
- Wind tolerance (rooftop/elevated site suitability)
- Frost hardiness (°C)

### 2.5 Urban Performance
- Installation type compatibility: Ground / Street tree pit / Podium / Rooftop / Vertical / Atrium
- Minimum substrate depth (mm) per installation type
- Shade tolerance: Full sun / Part shade / Full shade
- Root zone restriction tolerance
- Fire resistance rating (critical for AU/WA bushfire-prone areas)
- Invasiveness / declared weed status (by jurisdiction)
- Allergen / toxicity flags (public space planting)
- Maintenance tier: Low / Medium / High

### 2.6 Ecological & Biodiversity
- Carbon sequestration rate (tC/ha/yr where available)
- Wildlife value: attracts birds / pollinators / both / none
- Fragrance: yes / no / seasonal
- Heritage or cultural significance (where applicable)

### 2.7 Visual / Render Parameters
*(For photorealistic rendering in GPRTool and CAD plugins)*
- Leaf shape (ovate, palmate, needle, compound, etc.)
- Leaf size: length × width (cm)
- Leaf colour top / bottom (hex)
- Leaf texture: glossy / matte / waxy / rough
- Leaf arrangement: alternate / opposite / whorled
- Bark colour (hex) and texture description
- Flower colour (hex), season, fragrance flag
- Seasonal colour variants

### 2.8 GPR Certification Notes
- Known jurisdiction acceptance (e.g. Singapore Green Mark, Green Star AU)
- LAIe factor weights applied (version-stamped)

### 2.9 References
- Full citation list with DOIs
- Data provenance notes per field group
- Data quality flag: verified / provisional / estimated

---

## Part 3: Data Tiers (existing — reproduced for reference)

| Tier | Label | Definition | Count (v1.1.0) |
|---|---|---|---|
| T1 | Urban field | Measured in urban conditions | 40 |
| T2 | Open-ground measured | Natural/plantation conditions | 723 |
| T3 | Genus mean | Inferred from measured congeners | 6,993 |
| T4 | PFT mean | Inferred from Plant Functional Type | 26,673 |

---

## Part 4: LAIe — Effective LAI

### Concept
LAI_ref is a mature plant in optimal conditions. **LAIe** is the applied value used in GPR calculation, adjusted for actual urban conditions.

    LAIe = LAI_ref x sum(wi x fi)

Where fi is a normalised correction score [0–1] and wi is its weight (sum(wi) = 1).

### Correction Factors

| Factor | Source | Type | Notes |
|---|---|---|---|
| Plant maturity | Height / expected mature height | Model-derived, continuous | From design model + species DB |
| Root zone constraint | Paved/unpaved geometry around base | Model-derived | Planter bounds if modelled |
| Shade/aspect | Building proximity + orientation | Model-derived | |
| Roof/podium vs ground | Z-elevation of planting surface | Model-derived | |
| Climate zone | Site coordinates | Auto-detected | Feeds rainfall baseline |
| Irrigation regime | User-declared | 3-tier | Ideal / Normal / None |
| Maintenance intensity | User-declared | 3-tier | Ideal / Normal / Heavy |

### Irrigation Tiers
| Tier | Meaning |
|---|---|
| Ideal | Species-appropriate regime by qualified horticulturist |
| Normal | Scheduled/averaged for climate zone |
| None | Rainfall only — penalty is species-specific (drought-tolerant species penalised less) |

### Maintenance Tiers
| Tier | Meaning |
|---|---|
| Ideal | Species-appropriate pruning by qualified horticulturist |
| Normal | Routine scheduled maintenance |
| Heavy | Heavy pruning — significant LAI penalty |

### Weight Table
Weights are a versioned lookup (not hardcoded). Each version is a citable GPRI release.
v1.0 weights: TBD — calibrated from literature + expert judgement.
Long-term: calibrated against empirical urban LAI measurements.

---

## Part 5: New Schema Fields (proposed for v2.0)

Fields to be added to gpr_globalplantdb_schema.md and the Supabase table.

### Morphology fields
| Field | Type | Notes |
|---|---|---|
| height_min_m | numeric | Minimum mature height |
| height_max_m | numeric | Maximum mature height |
| height_typical_m | numeric | Typical mature height |
| canopy_radius_min_m | numeric | |
| canopy_radius_max_m | numeric | |
| canopy_shape | text | sphere/cone/cylinder/irregular_sphere/spreading/columnar/weeping |
| canopy_density | numeric | 0–1 coefficient |
| trunk_height_m | numeric | Height of clear trunk |
| trunk_radius_m | numeric | |
| root_behaviour | text | non-invasive/moderate/aggressive |
| growth_rate_min_m_yr | numeric | Annual height increment min |
| growth_rate_max_m_yr | numeric | Annual height increment max |
| growth_rate_label | text | slow/moderate/fast |

### Climate & tolerance fields
| Field | Type | Notes |
|---|---|---|
| koppen_description | text | Plain-English climate description |
| drought_tolerance | text | low/moderate/high |
| salt_tolerance | text | low/moderate/high |
| wind_tolerance | text | low/moderate/high |
| frost_hardiness_c | numeric | Minimum temperature (°C) |
| shade_tolerance | text | full_sun/part_shade/full_shade |

### Urban performance fields
| Field | Type | Notes |
|---|---|---|
| installation_ground | boolean | |
| installation_street_pit | boolean | |
| installation_podium | boolean | |
| installation_rooftop | boolean | |
| installation_vertical | boolean | |
| installation_atrium | boolean | |
| substrate_depth_min_mm | integer | Minimum viable substrate depth |
| fire_resistance | text | low/moderate/high |
| invasive_status | text | non-invasive/monitor/declared (jurisdiction) |
| allergen_flag | boolean | |
| toxicity_flag | boolean | |
| maintenance_tier | text | low/medium/high |
| urban_suitability | integer | 1–5 rating (criteria TBD) |

### Ecological/biodiversity fields
| Field | Type | Notes |
|---|---|---|
| carbon_seq_tC_ha_yr | numeric | Carbon sequestration rate where available |
| wildlife_value | text | birds/pollinators/both/none |
| fragrant | boolean | |
| fragrant_season | text | |
| heritage_notes | text | |
| sla | numeric | Specific Leaf Area (from TRY trait 3115/3116) |

### Render fields
| Field | Type | Notes |
|---|---|---|
| leaf_shape | text | ovate/palmate/needle/compound/linear/lanceolate/cordate/lobed |
| leaf_length_cm | numeric | |
| leaf_width_cm | numeric | |
| leaf_colour_top | text | Hex colour |
| leaf_colour_bottom | text | Hex colour |
| leaf_texture | text | glossy/matte/waxy/rough |
| leaf_arrangement | text | alternate/opposite/whorled/basal |
| bark_colour | text | Hex colour |
| bark_texture | text | smooth/furrowed/scaly/papery/fibrous |
| flower_colour | text | Hex colour |
| flower_season | text | |
| flower_fragrant | boolean | |

---

## Part 6: Field Population Strategy

New fields cannot be fully populated from existing sources alone.
Feasibility by source:

| Field group | Source | Feasibility |
|---|---|---|
| Height, canopy dimensions | GBIF traits, Kew POWO, USDA PLANTS | Medium — patchy coverage |
| Growth rate | USDA PLANTS, Plants for a Future DB | Medium |
| Drought/salt/wind tolerance | USDA PLANTS, FloraBase WA | Medium for AU/US species |
| Fire resistance | WA DFES/FPC, NSW RFS plant lists | Limited — manual for key species |
| Carbon sequestration | iTree species database, published papers | Limited — T1/T2 species only |
| Render parameters | No open database — manual curation required | Manual — start with T1/T2 species |
| Invasive status | GBIF, GISD, local weed registers | Medium — automatable by region |
| SLA | TRY trait request #50077 (submitted) | High — TRY data incoming |

**Recommended approach:**
1. Auto-populate height/growth/tolerance from USDA PLANTS API (existing enrich scripts)
2. Run TRY SLA enrichment once #50077 data arrives
3. Manually curate render params for T1 species (40 species) first
4. Flag all new fields as NULL by default — surface in UI as "data pending"

---

*Last updated: 2026-05-28 — Boon Lay Ong / GPRI*
