# DSHD-P37 Deployment Manual (V41.0)

## Deployment Steps
1. **Data**: DSHA-P41 native flag 7C4478B8 verified (37 SHA256), DSHC-P54 verified (12 MD5)
2. **T1**: _p40_output -> _p41_output (P41/1.16), native twins imported, rolling rebuilt
3. **T2**: V41.0 HTML (20 tabs/20 panels, P40/P41 compare + ZN/SN/NI/SI views)
4. **T3**: 89/89 validation PASS
5. **T4**: Contents API PUT to main + gh-pages (index.html, data/*.json, flags, archive/P37)
6. **T5**: web_site/ mirror + CI (phase-agnostic workflow) 
7. **T6**: sync docs DSHD-P37_TO_DSHC/DSHA_SYNC.md

## Rollback
- Previous: V40.0 (archive/P36/*)
