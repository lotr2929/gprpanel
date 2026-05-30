# GPR Global Plant Database — Data Descriptor v0.3

**Author:** Boon Lay Ong
**Affiliation:** Green Plot Ratio Institute (GPRI); School of Design and the Built Environment, Curtin University, Perth, Western Australia
**Contact:** boon.ong@curtin.edu.au
**Date:** May 2026
**Version:** Draft v0.3 — working document, not yet submitted
**Target journal:** *Scientific Data* (Nature Research)

---

## Abstract

The Green Plot Ratio (GPR) is an ecological metric for quantifying three-dimensional urban greenery using Leaf Area Index (LAI), introduced by Ong (2003) and adopted in Singapore's Green Mark certification scheme. Despite its growing citation record (464+ citations as of 2026), no open, structured plant database has existed to support its consistent application across climate zones and urban typologies. This paper describes the GPR Global Plant Database (version 1.0.0), a 34,429-species open dataset providing LAI values, botanical classification, biogeographic origin, and full data provenance for use in GPR calculation.

The database integrates four confidence tiers: direct urban field measurement, open-ground scientific measurement, genus-mean extrapolation, and Plant Functional Type inference. Records are classified as either measured (values taken directly from instruments or peer-reviewed databases) or generated (values derived by applying documented formulae to existing measured data), with the derivation method explicitly recorded for every entry.

The dataset is freely accessible via REST API and is the shared data layer for a suite of GPR calculation plugins for AutoCAD, Revit, Rhino, and Vectorworks. It is designed to improve as urban-context LAI measurement campaigns expand.

---

## 1. Background and Summary

### 1.1 The Green Plot Ratio: origins and global reach

The Green Plot Ratio (GPR), introduced by Ong (2003), is a quantitative metric for three-dimensional urban greenery based on the Leaf Area Index (LAI) — the ratio of one-sided leaf area to ground area. Expressed as:

> GPR = Total Leaf Area (m²) / Site Area (m²)
> = Σ(LAIᵢ × Canopy Areaᵢ) / Site Area

GPR provides architects and planners with a single dimensionless index of greenery intensity that is directly comparable to building plot ratio, enabling greenery to be regulated as rigorously as floor area.

Since its publication, GPR has accumulated 464+ citations across research and practice in Singapore, China, Europe, the Middle East, and Australia. It underpins Singapore's Green Mark mandatory greenery provisions and has been adopted in urban planning research across 110 Chinese cities (Yangtze River Economic Belt study, 2026). The metric is increasingly used in building simulation, thermal comfort modelling, and ecological service assessment.

### 1.2 The need for a structured plant LAI database

Despite its global uptake, GPR has lacked a consistent, open, scientifically structured source of LAI values for the species used in urban design. Existing databases (ORNL DAAC, TRY Plant Trait Database) provide LAI for ecological and climate modelling, not for per-species lookup by design practitioners. Their values were measured in natural forests and plantations under open-ground conditions — not in urban settings where root restriction, substrate depth, reduced light availability, and management systematically reduce LAI below reference values.

In practice, researchers applying GPR have used estimated or locally measured LAI values with limited documentation (Dong et al. 2024, Chongqing). The result is that GPR calculations for the same species in different studies are not directly comparable, and ecological service calculations derived from them carry unquantified uncertainty.

The GPR Global Plant Database addresses this gap. It provides a single open, versioned, peer-reviewed reference dataset for LAI values usable in GPR calculation, with full provenance and explicit disclosure of how each value was obtained.

---

## 2. GPR and Ecological Services

### 2.1 GPR as an exact total-leaf-area metric

GPR is exact as a total leaf area accounting: multiplying GPR by site area recovers total leaf area exactly. This makes GPR directly applicable to any ecological service calculation that depends on total leaf area — carbon sequestration based on photosynthetic surface, rainfall interception capacity, and cumulative air pollutant deposition all scale with total leaf area and are correctly calculated using GPR.

### 2.2 The Beer-Lambert law: original formulation and its fundamental assumption

The standard form of the Beer-Lambert law as applied to plant canopies describes radiation attenuation through a vegetation medium:

> Q(F) = Q₀ · e^(−k · F)

where Q₀ is incident PAR above the canopy, k is the extinction coefficient (typically 0.4–0.7 for broadleaf species), and F is cumulative LAI from the canopy top. The fraction of radiation intercepted is:

> f_int = 1 − e^(−k · LAI)

This formulation is valid only for the "turbid medium" assumption — a homogeneous, isotropic canopy. Real canopies violate this in virtually every field situation.

### 2.3 Adaptations in practice

**Clumping index (Nilson 1971):**

Leaves are not randomly distributed. The clumping-corrected form is:

> Q(F) = Q₀ · e^(−γ · k · F)

where γ is the clumping index (0 < γ ≤ 1; γ = 1 recovers the standard equation). Clumped canopies transmit more light than the standard equation predicts.

**k is not constant:**

k varies with solar elevation angle, ratio of direct to diffuse radiation, leaf angle distribution, and canopy self-shading. A species- and structure-specific k must be used for accurate calculations.

**Fractional vegetation coverage correction (FVC):**

When vegetation covers only a fraction of the ground surface — as in savannahs, open woodlands, and urban sites — the standard equation overestimates site-level light interception. The correction applies Beer-Lambert within the vegetated area only, then weights by FVC:

> FAPAR_site = FVC × (1 − e^(−k · LAI_canopy))

### 2.4 The exact per-plant summation for urban sites

The correct site-level light interception for a heterogeneous urban site is:

> f_int,site = (1/A_site) × Σᵢ [Aᵢ × (1 − e^(−γᵢ · kᵢ · LAI_eff,i · SVF_i))]

where:
- Aᵢ = canopy area of plant i (from CAD model)
- LAI_eff,i = effective LAI (database reference × substrate modifier × growth-stage modifier)
- γᵢ = clumping index (PFT-assigned; default 0.7 pending species-level data)
- kᵢ = extinction coefficient (PFT-assigned; Version 1.4 target)
- SVF_i = sky view factor at plant location (calculated from 3D building geometry)
- A_site = total site area

Substituting a single GPR value into the standard Beer-Lambert equation — 1 − e^(−k · GPR) — approximates this by treating the site as a uniform canopy, which overestimates interception in any heterogeneous setting. The per-plant summation is exact and requires no spatial uniformity assumption. GPR+ implements this exact form.

### 2.5 Urban complexities

**Reduced light availability:**

Urban morphology is the single most important determinant of leaf photosynthesis in urban canyons. The sky view factor (SVF) quantifies this reduction. In one study, 56.4% of potential tree shade was lost due to building shade inhibition.

Effective PAR at each plant: PAR_eff,i = SVF_i × PAR_open

**Substrate and root restriction:**

Soil volume constrains crown development and sets a ceiling on achievable LAI. Effective urban LAI:

> LAI_eff,i = LAI_ref,i × f_sub,i × f_growth,i

where f_sub is the installation-type modifier and f_growth is the growth-stage modifier (both planned for Version 1.3).

**Vertical surfaces — LAI_v:**

For vertical green facades, standard LAI (per unit ground area) is geometrically inappropriate. A redefined LAI_v — leaf area per unit wall projection area — is required. LAI_v ceases to be a significant shading parameter beyond 2.5; facade orientation becomes the dominant variable.

**Multi-strata layering:**

For stacked vegetation (trees over shrubs over groundcovers), Beer-Lambert applies sequentially:

> Q_shrub = Q₀ · e^(−k_T · LAI_T)
> Q_ground = Q_shrub · e^(−k_S · LAI_S)

GPR remains correctly additive across strata; light-dependent ecological service calculations require the sequential Beer-Lambert product.

### 2.6 Proposed ecological service equations

**Light interception (foundational):**

> f_int,site = (1/A_site) × Σᵢ [Aᵢ × (1 − e^(−γᵢ · kᵢ · LAI_eff,i · SVF_i))]

**Rainfall interception (Xiao & McPherson 2000):**

Per event per plant:

> I_event,i = S_max,i × (1 − e^(−P / S_max,i)) × Aᵢ / A_site
> S_max,i = S_leaf × LAI_eff,i + S_bark × BAI_i

where S_leaf = leaf storage capacity (0.2–0.5 mm per unit LAI, species-dependent), P = rainfall depth per event (mm).

**Evapotranspiration and cooling (Penman-Monteith, urban-modified):**

> λET_i = [Δ · (R_n,i − G) + ρₐ · cₚ · VPD / rₐ] / [Δ + γ_psy · (1 + rₛ,i / rₐ)]
> R_n,i = SVF_i · R_n,open
> rₛ,i = r_leaf / (0.5 · LAI_eff,i)

**Carbon sequestration (LAI-based):**

> GPP_i = ε_max · APAR_i · f_stress,i
> APAR_i = PAR_open · SVF_i · (1 − e^(−k · LAI_eff,i)) · Aᵢ
> C_seq,i ≈ 0.47 · GPP_i

Where DBH is available, McPherson et al. (2016) species-specific allometric equations are preferred.

**Particulate matter capture:**

> PM_cap,i = V_d,i · C_PM · LAI_eff,i · Aᵢ · t

where V_d,i is the dry deposition velocity (PFT-dependent, 0.01–0.05 m s⁻¹).

### 2.7 Areas for further research

- Species-level extinction coefficients (k) for common urban species
- Clumping index (γ) for open-grown urban tree forms
- Installation-type LAI adjustment factors (f_sub) by installation and climate
- LAI_v standardisation protocol for vertical green facades
- Combined SVF × substrate adjustment factor for street canyon conditions
- Multi-climate urban LAI field campaigns (temperate Mediterranean, subtropical, continental)
- Phenological functions LAI(t) for deciduous species in seasonally variable climates

---

## 3. Methods

### 3.1 Value derivation by tier

Every record carries a `data_type` field (`measured` or `generated`) and, for generated records, a `generation_method` field specifying which formula was applied.

---

#### Measured records (Tier 1 and Tier 2)

`data_type = measured`, `generation_method = NULL`

No formula is applied. The value in `lai_mean` is the value as reported in the primary source.

**Tier 1 — Direct urban field measurement (40 species)**

Source: Tan & Sia (2009). Values taken directly from LAI-2000 Plant Canopy Analyser measurements in urban Singapore (Köppen Af/Am). No transformation applied.

**Tier 2 — Open-ground scientific measurement (723 species)**

Sources: ORNL DAAC (Scurlock et al. 2001), TRY Plant Trait Database v6.0 (Kattge et al. 2020). Values extracted as published. Where a species appeared in both sources, the mean of all available measurements was taken and both sources cited.

---

#### Generated records — Genus mean (Tier 3)

`data_type = generated`, `generation_method = genus_mean`

For species with no direct measurement but with one or more measured congeners in Tier 1 or Tier 2, LAI is generated by the genus mean formula:

> LAI_i = (1/n) × Σⱼ LAI_j

where j ∈ {all Tier 1 or 2 species in the same genus}, and n is the count of measured congeners.

Database fields:
- `lai_mean` = genus mean of all congener lai_mean values
- `lai_min` = minimum lai_min across all congeners
- `lai_max` = maximum lai_max across all congeners
- `lai_sd` = sample standard deviation of congener lai_mean values (blank if n < 2)
- `lai_n` = n (count of measured congeners used)

---

#### Generated records — PFT equation (Tier 4)

`data_type = generated`, `generation_method = pft_bonan2008`

**Step 1 — PFT assignment:**

> PFT_i = f(growth_form_i, native_koppen_i)

Each species is assigned to a Plant Functional Type (PFT) code following Bonan (2008) based on its growth form (from GBIF taxonomy) and native climate zone. The complete mapping rules are documented in Supplementary Table S1 and implemented in `build_gpr_globalplantdb.py`.

**Step 2 — LAI assignment from published PFT means:**

> LAI_i = LAI_PFT from Bonan (2008)

| PFT | Code | LAI mean | Range | Source |
|---|---|---|---|---|
| Tropical broadleaf evergreen tree | TrBE | 5.1 | 4–8 | Bonan 2008 |
| Tropical broadleaf deciduous tree | TrBD | 3.8 | 2–6 | Bonan 2008 |
| Temperate broadleaf evergreen tree | TeBE | 4.5 | 2–7 | Bonan 2008 |
| Temperate broadleaf deciduous tree | TeBD | 4.0 | 2–6 | Bonan 2008 |
| Temperate needleleaf evergreen tree | TeNE | 5.5 | 3–9 | Bonan 2008 |
| Shrub (all types) | MedS/TeDS | 2.2 | 1–4 | Bonan 2008 |
| Grass / Groundcover | TrGr/TeGr | 1.5 | 0.5–3 | Bonan 2008 |
| Palm | Palm | 3.5 | 2–6 | Running et al. 2000 |
| Bamboo | Bamb | 4.0 | 2–7 | Literature estimate |
| Mangrove | MrBE | 4.2 | 3–6 | Literature estimate |

Database fields:
- `lai_mean` = published PFT mean
- `lai_min` = published PFT minimum
- `lai_max` = published PFT maximum
- `lai_sd` = blank (not derivable from published PFT data)
- `lai_n` = 0 (no individual measurements)

---

### 3.2 Database construction

**Construction pipeline:**

Four stages: (1) source acquisition, (2) source-specific processing, (3) priority-order merging with deduplication, (4) schema validation and output.

Central principle — **tier priority**: where multiple sources provide a value for the same species, the highest-confidence (lowest tier number) value is retained.

Sources processed in order: Tier 1 → Tier 2 → Tier 3 → Tier 4. Species matching is case-insensitive on binomial name. Once a species is recorded from a higher-confidence source, all lower-confidence entries are discarded.

Output: `gpr_globalplantdb.csv` — 34,429 rows, 30 fields, 12.57 MB.

---

### 3.3 Schema design

30 fields across 6 sections:

**Section 1 — Taxonomy:** `species`, `accepted_name`, `gbif_taxon_key`, `family`, `order`, `common_name`

**Section 2 — Botanical classification:** `growth_form`, `landscape_category`, `leaf_phenology`
Two parallel vocabularies: scientific (`growth_form`) and design-practice (`landscape_category`). No comparable database makes this distinction.

**Section 3 — Biogeography:** `native_region`, `native_koppen`

**Section 4 — LAI data:** `lai_mean`, `lai_min`, `lai_max`, `lai_sd`, `lai_n`, `lai_method`, `lai_context`, `lai_measurement_koppen`, `pft`

**Section 5 — Provenance:** `tier`, `tier_source`, `urban_context`, `sources`, `notes`

**Section 6 — Record metadata:** `entry_date`, `data_version`, `data_type`, `generation_method`

| Field | Type | Description |
|---|---|---|
| `data_type` | text | `measured` — value from instrument or peer-reviewed database. `generated` — value derived by documented formula |
| `generation_method` | text | `genus_mean` (Tier 3), `pft_bonan2008` (Tier 4), NULL for measured records |

---

## 4. Data Records

| Property | Value |
|---|---|
| Format | CSV (UTF-8, comma-delimited) |
| Rows | 34,429 |
| Fields | 30 |
| File size | 12.57 MB |
| Version | 1.0.0 |
| Entry date | 2026-05-25 |
| API | https://sfvwhbzxkzlscfsnyrwq.supabase.co/rest/v1/gpr_plant_species |

**By tier and data type:**

| Tier | Name | data_type | Count | % |
|---|---|---|---|---|
| 1 | Urban field measured | measured | 40 | 0.1% |
| 2 | Open-ground measured | measured | 723 | 2.1% |
| 3 | Genus mean | generated | 22 | 0.1% |
| 4 | PFT equation | generated | 33,644 | 97.7% |
| **Total** | | | **34,429** | |

Measured records: 763 (2.2%) | Generated records: 33,666 (97.8%)

---

## 5. Technical Validation

- **Binomial name validation:** All species names validated against standard binomial regex. 361 non-conforming entries assigned `landscape_category = REVIEW`.
- **LAI range plausibility:** Values not filtered by absolute range; `lai_min`/`lai_max` communicate uncertainty.
- **Tier priority integrity:** No species appears more than once; no Tier 4 entry exists for any species present in Tier 1–3.
- **data_type coverage:** `measured`: 763 entries; `generated`: 33,666 entries; blank: 0.
- **generation_method coverage:** `genus_mean`: 22; `pft_bonan2008`: 33,644; NULL: 763; blank: 0.

---

## 6. Usage Notes

### GPRSELECT workflow

1. Designer places own 3D plant objects. No geometry generated by plugin.
2. Designer assigns species name to each plant object via GPRSELECT.
3. Plugin queries database for `lai_mean`, `tier`, and `data_type`.
4. Plugin calculates Total Leaf Area = LAI_eff,i × Canopy Area for each plant.
5. GPR = Σ(Total Leaf Area) / Site Area.
6. Result reported with data_type composition — e.g. "GPR = 1.4, based on 12 measured and 6 generated species."

### Urban LAI adjustment

All Tier 2 values were measured in natural or plantation conditions. Urban LAI is typically 30–60% lower. For regulatory and professional practice applications, unadjusted values are appropriate as a conservative upper bound. Installation-type adjustment factors are planned for Version 1.3.

---

## 7. Limitations

1. **Urban vs natural LAI mismatch (Tier 2).** 723 measured species carry natural/plantation values. Urban LAI may be 30–60% lower.
2. **PFT equation uncertainty (Tier 4).** 33,644 generated species carry PFT mean values with wide uncertainty ranges.
3. **Temperate bias.** Tier 2 dominated by temperate Northern Hemisphere species.
4. **Canopy form classification.** Tier 4 growth_form/landscape_category assigned programmatically; unreliable for non-standard genera.
5. **Synonym resolution incomplete.** Exact binomial string matching only in v1.0.0.
6. **Version 1.0.0 is a foundation.** Scientific value lies in schema design, theoretical framework (Section 2), and the 763 measured records.

---

## 8. Future Development

| Version | Focus | Timeline |
|---|---|---|
| v1.1 | Tier 1 expansion: Perth urban field LAI campaign | 12 months |
| v1.2 | Tier 2 enrichment: AusTraits and NParks integration | 18 months |
| v1.3 | Installation-type adjustment factors; growth-stage modifiers; k and γ by PFT | 24 months |
| v1.4 | Ecological service output fields: carbon, rainfall, ET | 30 months |
| v2.0 | Methods paper on urban LAI adjustment; multi-city field campaigns | 36 months |

### Contributor pathway

Researchers measuring urban LAI for regional species are invited to contribute under the GPRI Contributor Licence Agreement (CLA). Priority regions: temperate Australia (Perth), subtropical Southeast Asia, temperate continental Europe, arid Middle East.

---

## References

1. Ong, B.L. (2003). Green plot ratio: an ecological measure for architecture and urban planning. *Landscape and Urban Planning*, 63(4), 197–211. https://doi.org/10.1016/S0169-2046(02)00191-3
2. Tan, P.Y. & Sia, A. (2009). *LAI of Tropical Plants.* National Parks Board, Singapore.
3. Scurlock, J.M.O. et al. (2001). *Worldwide Historical Estimates of LAI, 1932–2000.* ORNL TM-2001/268.
4. Kattge, J. et al. (2020). TRY plant trait database. *Global Change Biology*, 26(1), 119–188.
5. GBIF Secretariat (2023). *GBIF Backbone Taxonomy.* https://doi.org/10.15468/39omei
6. Bonan, G.B. (2008). Forests and climate change. *Science*, 320(5882), 1444–1449.
7. Running, S.W. et al. (2000). Global terrestrial gross and net primary productivity. *Science*, 289(5487), 1772–1775.
8. Beck, H.E. et al. (2018). Köppen-Geiger climate classification maps at 1-km resolution. *Scientific Data*, 5, 180214.
9. Nilson, T. (1971). A theoretical analysis of the frequency of gaps in plant stands. *Agricultural Meteorology*, 8, 25–38.
10. Bailey, B.N. & Mahaffee, W.F. (2017). Evaluating Beer's law for heterogeneous canopies. *Agricultural and Forest Meteorology*, 253–254, 128–140.
11. He, L. et al. (2023). A modified Beer–Lambert–Bouguer law for nonrandom distributions. *Journal of Advances in Modeling Earth Systems*, 15, e2022MS003281.
12. Xiao, Q. & McPherson, E.G. (2000). A new approach to modeling tree rainfall interception. *Journal of Geophysical Research*, 105(D23), 29173–29188.
13. McPherson, E.G., van Doorn, N.S., & Peper, P.J. (2016). *Urban Tree Database and Allometric Equations.* USDA Forest Service PSW-GTR-253.
14. Falster, D. et al. (2021). AusTraits. *Scientific Data*, 8, 254.
15. Dong, W. et al. (2025). A global urban tree leaf area index dataset. *Scientific Data*.
16. Dong, L. et al. (2024). Optimization of LAI measurement method and correction of GPR formula — Chongqing. *Environmental Science and Pollution Research*, 31, 30914–30942.
17. Tams, F. et al. (2023). Impact of shading on evapotranspiration and water stress of urban trees. *Ecohydrology*.
18. Building and Construction Authority, Singapore (2021). *Green Mark for Buildings (GM: 2021).*
19. USDA NRCS (2024). *The PLANTS Database.* National Plant Data Team, Greensboro, NC. https://plants.usda.gov. Accessed via PlantAtlas.ai (https://data.plantatlas.ai), October 2025. Used for: growth rate, drought tolerance, shade tolerance, root depth, and related functional traits in database enrichment.

---

*End of draft v0.3 — 25 May 2026*
*Working document — not for distribution*
