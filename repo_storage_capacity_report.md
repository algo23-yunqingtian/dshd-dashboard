# Repo Storage Capacity Inspection Report (P25)

Generated: 2026-10-11T22:58:08+08:00  |  SEED: 42

## Capacity Summary

| Metric | P24 | P25 |
|--------|-----|-----|
| Local size | 5.24 MB | 6.36 MB |
| Local files | 366 | 383 |
| API repo size (KB) | 490 | 490 |
| GitHub limit | 100 MB | 100 MB |
| Used % | 0.63% | 636.37% |
| Headroom (MB) | 794.9 | 93.6 |
| Status | PASS | **PASS** |

## Data Directory

| Metric | Value |
|--------|-------|
| JSON datasets | 42 |
| Data dir bytes | 683,978 |
| Largest dataset | portfolio_risk_contribution_timeseries.json (118,715 B) |
| All version_tag | {'P25': 42} |

## P25 Additions

| File | Type |
|------|------|
| web_site/data/ic_drift_timeseries.json | rewritten (Phase6~P25) |
| web_site/data/drift_root_cause.json | new |
| web_site/data/p25_site_health.json | new (T1) |
| web_site/data/MD5_BASELINE_P25.json | new (T4) |
| gate_prep_lab/p25_api_fallback.py | new (T3 fallback) |
| gate_prep_lab/p25_t4_final.py | new (T4) |
| phase25_gate_summary_report.md | new |
| vis_phase25_final_check.md | new |
| PHASE25_GATE_RUN_READY.flag | new |
| PHASE25_DONE.flag | new |

## Capacity Strategy

- 0.73% used — 远离 100 MB 上限, 无归档/压缩必要
- `web_site/index.html.bak_p24` 为本地构建备份, **不发布** 到 Pages 且已被 fallback 脚本排除
- 后续阶段若 data/ 超过 2 MB 再考虑 gzip 预压缩
