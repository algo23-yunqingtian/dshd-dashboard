# DSHD-P25 全链路自洽最终检查 (vis_phase25_final_check)

| 字段 | 值 |
|------|-----|
| 生成时间 | 2026-10-11T22:58:08+08:00 |
| SEED / ENGINE | 42 / V86.9-C-FINAL-DEBUG-P25 |
| 检查项 | 6 |
| PASS / FAIL / WARN | 6 / 0 / 0 |
| 判定 | **PASS** |

## 1. 数据层

| 检查 | 结果 |
|------|------|
| JSON 数据集 42 个, 全部 version_tag=P25 | PASS |
| 全部 dataset_version=1.7 | PASS |
| core_18 数据集齐备 | PASS (18/18) |
| P25 新增 ic_drift_timeseries / drift_root_cause / rolling_correlation_matrix | PASS |
| p25_site_health.json (T1 巡检) | PASS |
| MD5_BASELINE_P25.json (140 文件) | PASS |

## 2. 前端层

| 检查 | 结果 |
|------|------|
| index.html 207,450 (+34022 B) | PASS |
| 内联 JS 3 块 node --check | PASS (0 语法错误) |
| P24 遗留缺陷 9 项全部修复 | PASS |
| IC 漂移预警面板 / FR-RISK 阻断面板 / 多窗口相关性 | PASS |

## 3. CI/CD 层

| 检查 | 结果 |
|------|------|
| 前置静态数据校验门禁 | PASS |
| 内联 JS 语法门禁 (阻断整页失效类缺陷上线) | PASS |
| 安全扫描 (140 文件 / 0 命中) | PASS |
| 部署失败自动重试 job | PASS |
| 网络异常 API-Contents 降级 job | PASS |
| 工作流 YAML 解析 | PASS |

## 4. 审计归档层

| 检查 | 结果 |
|------|------|
| PHASE25_GATE_RUN_READY.flag | PASS |
| phase25_gate_summary_report.md | PASS |
| web_deploy_manual.md §24 | PASS |
| fr_risk_alert_archive.md §22 | PASS |
| gate_periodic_check_log.csv PG25-R1 | PASS |
| repo_storage_capacity_report.md | PASS |
| PHASE25_DONE.flag | PASS |

## 5. 逐项明细

- [x] p25_site_health.json 生成 (JS 解析恢复 + 42 数据集 P25 + core18 完整)
- [x] MD5 基线覆盖 140 个静态资源 (77 JSON + 3 HTML/CSS/JS/SVG) — 140 files / 2346605 B
- [x] T0/T1 8 项 FAIL 已归因 (JS缺陷=4 网络=2 时延=2) — js=4 net=2 lat=2
- [x] gate_periodic_check_log.csv 追加 PG25-R1 轮次 — 414 -> 427 rows (+13)
- [x] web_deploy_manual.md §24 追加
- [x] fr_risk_alert_archive.md §22 追加
