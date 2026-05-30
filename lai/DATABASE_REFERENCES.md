# GPR Plant Database — Data Sources & References

Last updated: Sat 23 May 2026

---

## LAI Values

### Primary sources in current database

All 760 species entries derive LAI values from one or both of:

**[1] ORNL DAAC — Global LAI Database (Woody Plants 1932–2011)**
- Scurlock, J.M.O., Asner, G.P., & Gower, S.T. (2001). *Worldwide Historical Estimates and Bibliography of Leaf Area Index, 1932-2000.* ORNL Technical Memorandum TM-2001/268. Oak Ridge National Laboratory, Oak Ridge, Tennessee. https://doi.org/10.3334/ORNLDAAC/622
- 648 species entries in current database (ORNL, or ORNL + TRY combined)
- Context: natural forests, plantations — NOT urban
- Access: https://daac.ornl.gov

**[2] TRY Plant Trait Database**
- Kattge, J. et al. (2020). TRY plant trait database — enhanced coverage and open access. *Global Change Biology*, 26(1), 119–188. https://doi.org/10.1111/gcb.14904
- 112 species entries in current database (TRY only)
- Context: natural/open-ground conditions — NOT urban
- Access: https://www.try-db.org (free, data request required)

### Singapore urban field measurements

**[3] Tan, P.Y. & Sia, A. (2009)**
- Tan, P.Y. & Sia, A. (2009). *LAI of Tropical Plants: A Guidebook on its Use in the Calculation of Green Plot Ratio.* Centre for Urban Greenery and Ecology, National Parks Board, Singapore.
- 35 tropical species measured directly in urban Singapore context
- Method: LAI-2000 Plant Canopy Analyser
- Context: urban tropical — THE primary urban-calibrated source for GPR
- File: `GPRTool/lai/Tan, Sia - 2009 - LAI of tropical plants - a Guidebook on its use in the calculation of GPR.pdf`
- Status: Values to be extracted and added to database as Tier 1 (urban field measured)

---

## Plant Dimensions (height, canopy radius)

**Current status:** All 760 entries use `size_source = "category default"` — dimensions are category-level estimates, NOT species-level measurements.

Sources intended for future enrichment:

**[4] i-Tree Species Database**
- Nowak, D.J., Crane, D.E., Stevens, J.C., Hoehn, R.E., Walton, J.T., & Bond, J. (2008). A ground-based method of assessing urban forest structure and ecosystem services. *Arboriculture & Urban Forestry*, 34(6), 347–358.
- Urban tree database with species-level height and canopy dimensions
- Access: https://www.itreetools.org

**[5] McPherson Urban Tree Database**
- McPherson, E.G., van Doorn, N.S., & Peper, P.J. (2016). *Urban Tree Database and Allometric Equations.* USDA Forest Service General Technical Report PSW-GTR-253. https://doi.org/10.2737/PSW-GTR-253

---

## Canopy Form Classification

**Current status:** All `canopy_form` values (round, conical, columnar, spreading, shrub, groundcover, grass) were assigned programmatically by genus-level lookup rules written in `lai_categorise.py`. No external source cited.

**Known limitation:** Programmatic classification is unreliable for non-standard genera. 
Example: *Eucalyptus grandis* classified as "round" but is visually columnar/conical.
Correction via visual verification (Wikipedia photos, iNaturalist) is a Phase 1 database task.

Sources intended for future enrichment:

**[6] Plants of the World Online (POWO)**
- Royal Botanic Gardens, Kew (2023). *Plants of the World Online.* https://powo.science.kew.org
- Growth form, native range, and taxonomic data

**[7] iNaturalist**
- iNaturalist contributors & California Academy of Sciences (2023). *iNaturalist.* https://www.inaturalist.org
- Species photos used for visual canopy form verification

---

## Wikipedia Plant Images (Panel display)

**[8] Wikimedia Commons contributors**
- Images fetched live via the Wikipedia REST API: `https://en.wikipedia.org/api/rest_v1/page/summary/{species_name}`
- License: Creative Commons Attribution-ShareAlike (CC BY-SA) per Wikimedia Commons terms
- Attribution displayed in panel as: "Image: Wikimedia Commons contributors, CC BY-SA"
- Access: https://commons.wikimedia.org

---

## Future enrichment sources (not yet incorporated)

**[9] AusTraits — Australian Plant Trait Database**
- Falster, D. et al. (2021). AusTraits, a curated plant trait database for the Australian flora. *Scientific Data*, 8, 254. https://doi.org/10.1038/s41597-021-01006-6
- HIGH PRIORITY for Perth/Australian urban context
- Access: https://austraits.org

**[10] GBIF — Global Biodiversity Information Facility**
- GBIF Secretariat (2023). *GBIF Backbone Taxonomy.* https://doi.org/10.15468/39omei
- Native species distribution — used for climate zone assignment
- Access: https://www.gbif.org

**[11] Beck et al. — Köppen-Geiger Climate Classification**
- Beck, H.E. et al. (2018). Present and future Köppen-Geiger climate classification maps at 1-km resolution. *Scientific Data*, 5, 180214. https://doi.org/10.1038/sdata.2018.214
- Used for assigning climate zones per species native range
- Data: https://www.gloh2o.org/koppen/

**[12] USDA PLANTS Database**
- USDA, NRCS (2023). *The PLANTS Database.* National Plant Data Team, Greensboro, NC. https://plants.usda.gov
- Soil type, water requirement, drought tolerance, growth rate

**[13] World Agroforestry (ICRAF) Tree Database**
- World Agroforestry (2023). *ICRAF Agroforestry Tree Database.* https://www.worldagroforestry.org/treedb
- Soil, water, and land-use suitability for tropical species

**[14] FAO Irrigation and Drainage Paper No. 56**
- Allen, R.G., Pereira, L.S., Raes, D., & Smith, M. (1998). *Crop Evapotranspiration — Guidelines for Computing Crop Water Requirements.* FAO Irrigation and Drainage Paper 56. Rome: Food and Agriculture Organization. http://www.fao.org/3/x0490e/x0490e00.htm
- Evapotranspiration reference values for hydrological calculations

**[15] NParks Flora & Fauna Web (Singapore)**
- National Parks Board Singapore (2023). *Flora & Fauna Web.* https://www.nparks.gov.sg/florafaunaweb
- Tropical species native to Singapore; growth habit, images
- Use: species crosswalk for tropical context

**[16] FloraBase — Western Australia**
- Western Australian Herbarium (2023). *FloraBase — The Western Australian Flora.* https://florabase.dpaw.wa.gov.au
- Perth-relevant native species; growth form
- Use: species crosswalk for Perth context

---

## Database confidence tiers

| Tier | Definition | Current count |
|---|---|---|
| 1 — Urban field measured | Directly measured in urban conditions | 35 species (Tan & Sia 2009 — pending extraction) |
| 2 — Open-ground measured | Measured in natural/plantation conditions | ~725 species (ORNL/TRY) |
| 3 — Literature estimate | Expert estimate from literature or manufacturer data | 0 (not yet added) |

**Disclosure note:** All LAI values currently in the database (except the 35 Tan & Sia 2009 species) were measured in natural or plantation conditions. Urban LAI may be 30–60% lower due to root restriction, substrate depth, pruning, and other urban stressors. This uncertainty should be communicated to users. Urban calibration is a future research programme.

---

## Citation for the GPR metric itself

**[17] Ong, B.L. (2003)**
- Ong, B.L. (2003). Green plot ratio: an ecological measure for architecture and urban planning. *Landscape and Urban Planning*, 63(4), 197–211. https://doi.org/10.1016/S0169-2046(02)00191-3
