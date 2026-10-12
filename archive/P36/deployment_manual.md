# DSHD-P36 Deployment Manual

## Deployment Steps

1. **Data Preparation**: Generate P40 data (dataset_version=1.15), verify PHASE40_DATA_READY.flag
2. **Frontend Update**: index.html V39.0 -> V40.0 (metrics, FR-RISK, rolling F32, cost model, factors, version Comparison)
3. **Validation**: 86/86 local checks (JSON version, HTML structure 18 tabs/17 panels, cross-agent sync)
4. **Deployment**: Contents API PUT to main + gh-pages (index.html, data/*.json, flags, archive/P36/*)
5. **Verification**: live site V40.0 check, data files accessible, PHASE36_DONE.flag issued

## Rollback
- Previous: V39.0 (archive/P35/index.html)
