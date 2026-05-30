# GPR Global Plant Database — Schema Reference
**File:** `gpr_globalplantdb.csv`  
**Supabase table:** `gpr_plant_species`  
**Version:** 1.1.0  
**Author:** Boon Lay Ong / GPRI  
**Created:** 2026-05-24

---

## Purpose

The GPRI Global Plant Database is the shared plant data layer for all GPR
applications (GPR+AutoCAD, GPR+Revit, GPR+Rhino, GPR+Vectorworks, and future
GPRI plugins).
It is designed to serve two purposes simultaneously:

1. **Implementation** — provides LAI values and plant classification data
   for GPR calculation in design tools.
2. **Research** — provides full provenance, uncertainty quantification, and
   source traceability for academic citation and peer review.

The database is **not definitive**. LAI values improve as new urban-context
measurements become available. Every entry carries sufficient metadata for a
user or researcher to assess its fitness for their specific application.

---

## API Access

**Base URL:** `https://sfvwhbzxkzlscfsnyrwq.supabase.co/rest/v1/gpr_plant_species`  
**Auth:** Public read access (no key required for GET). Write requires service key.

### Query examples

**Web / JavaScript**
```js
// Search by species
fetch('https://sfvwhbzxkzlscfsnyrwq.supabase.co/rest/v1/gpr_plant_species?species=eq.Ficus benjamina')

// All Tier 1 species
fetch('...?tier=eq.1&select=species,lai_mean,sources')

// All trees in tropical climate
fetch('...?landscape_category=eq.Tree&native_koppen=like.*Af*')
```

**Python**
```python
import requests
BASE = "https://sfvwhbzxkzlscfsnyrwq.supabase.co/rest/v1/gpr_plant_species"
r = requests.get(f"{BASE}?species=eq.Ficus benjamina")
plant = r.json()[0]
```

**.NET (GPR+AutoCAD / GPR+Revit)**
```csharp
var url = "https://sfvwhbzxkzlscfsnyrwq.supabase.co/rest/v1/gpr_plant_species?species=eq.Ficus benjamina";
var json = await new HttpClient().GetStringAsync(url);
var plants = JsonSerializer.Deserialize<List<Plant>>(json);
```

---

## Schema

Fields are ordered in six sections. The section order is preserved in the CSV
column order and the Supabase table definition.

---

### Section 1 — TAXONOMY

Anchored to authoritative taxonomic backbones (GBIF, POWO/Kew).

| Field | Type | Description |
|---|---|---|
| `id` | integer | Sequential row ID (auto-assigned) |
| `species` | text | Binomial as used in the source dataset |
| `accepted_name` | text | GBIF/POWO accepted name (handles synonyms) |
| `gbif_taxon_key` | integer | GBIF backbone taxon ID — enables cross-referencing |
| `family` | text | Botanical family |
| `order` | text | Botanical order |
| `common_name` | text | Common/vernacular name |

---

### Section 2 — BOTANICAL CLASSIFICATION

Two parallel classification systems: botanical (scientific) and design (GPR use).

| Field | Type | Controlled vocabulary |
|---|---|---|
| `growth_form` | text | `tree` / `shrub` / `herb` / `graminoid` / `fern` / `palm` / `liana` / `bamboo` / `mangrove` / `succulent` / `epiphyte` / `aquatic` |
| `landscape_category` | text | `Tree` / `Shrub` / `Groundcover` / `Grass` / `Climber` / `Bamboo` / `Palm` / `Mangrove` / `REVIEW` |
| `leaf_phenology` | text | `evergreen` / `deciduous` / `semi-deciduous` / `drought-deciduous` / `semi-evergreen` / `annual` |

**Note on `landscape_category`:** `REVIEW` flags entries with non-standard names
(multi-species aggregates, community-level entries) that require manual curation.

---

### Section 3 — BIOGEOGRAPHY

Native origin data, not urban usage context.

| Field | Type | Description |
|---|---|---|
| `native_region` | text | Biogeographic realm: `Afrotropical` / `Australasian` / `Indomalayan` / `Nearctic` / `Neotropical` / `Palearctic` / `Oceanian` |
| `native_koppen` | text | Köppen climate codes of native range, comma-separated e.g. `Af,Am,Aw`. Populated by `enrich_koppen.py` from GBIF occurrence data. |

**Version 1.0.0 note:** `native_koppen` for Tier 4 entries is inferred from
the PFT climate classification, not from GBIF occurrence data. Run
`enrich_koppen.py --all` for occurrence-based enrichment.

---

### Section 4 — LAI DATA

The scientific core. Values, uncertainty, and full measurement context.

| Field | Type | Description |
|---|---|---|
| `lai_mean` | numeric | Best-estimate LAI for GPR calculation |
| `lai_min` | numeric | Minimum measured/estimated value |
| `lai_max` | numeric | Maximum measured/estimated value |
| `lai_sd` | numeric | Standard deviation (blank if unavailable) |
| `lai_n` | integer | Sample size. `0` = inferred, not measured |
| `lai_method` | text | `LAI-2000` / `hemispherical` / `destructive` / `litter-trap` / `MODIS` / `PFT-inferred` / `mixed` |
| `lai_context` | text | `urban` / `natural` / `plantation` / `inferred` |
| `lai_measurement_koppen` | text | Köppen code at measurement site (distinct from native range) |
| `pft` | text | Plant Functional Type code (Bonan 2008) |

**PFT codes:** TrBE, TrBD, SuBE, TeBE, TeBD, TeNE, TrN, MedBE, BoNE, Palm,
Bamb, TrES, TeDS, TeES, MedS, CLM, TrGr, TeGr, TrGC, TeGC, Fern, Herb, Succ

---

### Section 5 — PROVENANCE

Full traceability for every LAI value.

| Field | Type | Description |
|---|---|---|
| `tier` | integer | Data quality tier (1–4); see Tier Definitions below |
| `tier_source` | text | `Direct_Urban_Field` / `ORNL_TRY_Measured` / `Genus_Mean` / `PFT_Mean_GBIF` / `PFT_Mean_USDA` |
| `urban_context` | text | `TRUE` — measured in urban conditions / `FALSE` — open/natural / `UNKNOWN` |
| `sources` | text | Full citation string(s) |
| `notes` | text | Method caveats, known variation, context limitations |

---

### Section 6 — RECORD METADATA

| Field | Type | Description |
|---|---|---|
| `entry_date` | date | ISO date record was added |
| `data_version` | text | Database version e.g. `1.0.0` |
| `ai_assisted` | boolean | `FALSE` for all current records. **Important distinction:** no LAI values in this database were generated by an AI model. Tier 3 values are genus means computed algorithmically from measured Tier 1/2 data. Tier 4 values are PFT means derived from published equations in Bonan (2008) applied via Python script. Claude (Anthropic) was used solely to write Python data-processing scripts — equivalent to using any programmer or research assistant for code. It did not generate, estimate, or fabricate any data values. This field is reserved for future records where an AI model directly infers a value without an empirical or published-equation basis. |
| `ai_model` | text | Identifier of the AI model, if `ai_assisted = TRUE`. Blank for all current records. For disclosure purposes: Python scripts used to build this database were written with assistance from Claude Sonnet (Anthropic). |

---

## Tier Definitions

| Tier | Name | Description | Current count |
|---|---|---|---|
| 1 | Urban field measured | Directly measured in urban conditions. Primary source: Tan & Sia (2009). | 40 |
| 2 | Open-ground measured | Measured in natural/plantation conditions; reliable proxy with disclosed uncertainty. Primary sources: ORNL DAAC, TRY Database. | 723 |
| 3 | Genus mean | LAI inferred from genus mean of measured congeners (Tier 1/2 data). Algorithmically computed — no AI generation. | 6,993 |
| 4 | PFT mean | Inferred from Plant Functional Type classification using Bonan (2008) equations. Lowest confidence. Sources: GBIF taxonomy + Bonan (2008). | 26,673 |

**For GPR calculation:** use `lai_mean` regardless of tier. Disclose tier to
users — a GPR result based entirely on Tier 4 values is less defensible than
one using Tier 1 or 2 values. The GPRI plugin suite (GPR+AutoCAD, GPR+Revit,
GPR+Rhino, GPR+Vectorworks) surfaces tier information to the user at the point
of species selection via GPRSELECT.

---

## Key References

- Bonan, G.B. (2008). Forests and climate change: Forcings, feedbacks, and the climate benefits of forests. *Science*, 320(5882), 1444–1449.
- Running, S.W. et al. (2000). Global terrestrial gross and net primary productivity from the Earth Observing System. *Science*, 289(5487), 1772–1775.
- Tan, P.Y. & Sia, A. (2009). *LAI of Tropical Plants — A Guidebook on its Use in the Calculation of GPR*. Singapore.
- Ong, B.L. (2003). Green plot ratio: An ecological measure for architecture and urban planning. *Landscape and Urban Planning*, 63(4), 197–211. DOI: 10.1016/S0169-2046(02)00191-3
- GBIF Secretariat (2023). GBIF Backbone Taxonomy. DOI: 10.15468/39omei
- Beck, H.E. et al. (2018). Present and future Köppen-Geiger climate classification maps at 1-km resolution. *Scientific Data*, 5, 180214.
