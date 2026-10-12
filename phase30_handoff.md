# DSHD-P30 → DSHD-P31 Handoff

## Version
- **Current**: V34.0 (P30, P34 data)
- **Next**: V35.0 (P31, P35 data)

## Prerequisites for P31
1. DSHA-P35 data delivery (PHASE35_DATA_READY.flag)
2. P34 data validation complete ✅
3. V34.0 deployment stable ✅

## Required Changes for V35.0
1. Update all data files P34→P35 (version_tag, dataset_version)
2. Update version_index.json (P34→ARCHIVED, P35→ACTIVE)
3. Update HTML: P34→P35, V34.0→V35.0
4. Update gray admission: PB (15/15→16/16), CU (9/14→14/14 expected)
5. Update performance metrics if P35 has new optimizations
6. Preserve all V34.0 features (perf panel, dual-curve, null-safety)

## Reusable Components
- **Performance panel**: Can be updated with P35 metrics without structural changes
- **Dual-curve toggle**: Fully version-agnostic, no changes needed
- **Null-safety helpers**: safeVal/safeText/safePct/safeStatus/safeNav — version-agnostic
- **CI workflow**: Phase-agnostic regex (^P\d+$, ^1\.\d+$) — no changes needed
- **Deployment scripts**: _p30_deploy.py pattern reusable

## Known Issues
1. Div balance: 701 open / 699 close (diff=2) — pre-existing from V32.0, browsers handle gracefully
2. 3 remaining P33 refs in historical version list — expected, not an issue
3. p34_site_health.json: Created after deployment, will be available after CI processes next commit

## Cross-Agent Status
- **DSHA-P34**: Data delivered, 8/8 PASS
- **DSHC-P40**: V34.0 status synced
- **DSHD-P30**: Deployment complete, all ACs pass

## Compatibility Notes
- CI regex is phase-agnostic: ^P\d+$ and ^1\.\d+$
- No CI workflow changes needed for P35
- PB dual-curve toggle code reusable without changes
- All null-safety helpers version-agnostic
