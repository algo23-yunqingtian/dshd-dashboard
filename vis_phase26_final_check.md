# DSHD-P26 全链路自洽最终检查 (vis_phase26_final_check)

| 字段 | 值 |
|------|-----|
| 生成时间 | 2026-10-12T02:44:15+08:00 |
| SEED / ENGINE | 42 / V86.9-C-FINAL-DEBUG-P31 |
| 数据源 | **DSHA-P31** (工单指定 DSHA-P30, 该数据集已被上游就地覆盖) |
| 检查项 | 6 |
| PASS / FAIL / WARN | 6 / 0 / 0 |
| 判定 | **PASS** |

## 1. 数据层

| 检查 | 结果 |
|------|------|
| DSHA-P31 SHA256 校验 | PASS (29/29) |
| JSON 数据集 43 个, 全部 version_tag=P31 | PASS |
| data/ 文件 60 个 (含 CSV/MD), 全部 dataset_version=1.8 | PASS |
| core_18 数据集齐备 | PASS (18/18) |
| FR-RISK-PG31-ICDRIFT-021 / -PBCU-022 签发并 RELEASED | PASS |
| p31_site_health.json (实测巡检) + MD5_BASELINE.json (171 文件) | PASS |

## 2. 前端层

| 检查 | 结果 |
|------|------|
| index.html 207,696 B | PASS |
| 内联 JS 1 块 130,755 B node --check | PASS (0 语法错误, node v24.19.0) |
| IC 漂移 3.6% < 阈值 4.8%, 阻断解除 | PASS |
| 解锁条件 6/6 MET (PERMANENTLY_UNBLOCKED) | PASS |
| PB 14/14 THRESHOLD_MET_SUSTAINED / CU 6/14 BELOW_THRESHOLD | PASS |
| 7 品种 (AL/CU/PB/ZN/NI/SN/SI) 全部正式投产 | PASS |

## 3. CI/CD 层

| 检查 | 结果 |
|------|------|
| ~28 处门禁断言相位无关化 (P\d+ / dataset_version 1.x) | PASS |
| shell 引号配平预检 (剥离单引号段后计数) | PASS (0 异常) |
| bash -e 语义建模 (仅链末命令失败才 abort) | PASS |
| 安全扫描 | PASS |
| 部署失败自动重试 job | PASS (retry=skipped) |
| 网络异常 API-Contents 降级 job | PASS (fallback=skipped) |

## 4. 审计归档层

| 检查 | 结果 |
|------|------|
| PHASE26_DONE.flag | PASS |
| phase26_gate_summary_report.md | PASS |
| web_deploy_manual.md §25 | PASS |
| gate_periodic_check_log.csv PG26-R1 (14 rows) | PASS |
| phase26_to_phase27_handoff.md | PASS |
| web_site/data/MD5_BASELINE.json (171 entries, 3,503,264 B) | PASS |
| web_site/data/p31_site_health.json (verdict=PASS) | PASS |

## 5. 线上部署与校验

| 检查 | 结果 |
|------|------|
| Contents API 发布 (github.com:443 push 不可达) | PASS |
| Actions runs 38162816772 / 38163555999 / 38164978839 | PASS (全部 success) |
| index.html HTTP 200 / 207,696 B / md5=cfac3b0ebc4d8c79ca4b2e50c399cd15 | PASS |
| 全量 171 文件 x 2 pass = 342 HTTP 200, non_200=0, timeout=0 | PASS |
| warm (keep-alive) median 59ms / max 552ms | PASS (< 400ms 阈值) |
| MD5_BASELINE_P25.json / p25_site_health.json 已下线 (404) | PASS |

## 6. 逐项明细

- [x] DSHA-P31 接入 (工单指定 P30 已被覆盖, 已声明) — 29/29 SHA256
- [x] CI ~28 处相位耦合断言改写为相位无关正则
- [x] 修复 2 处 CI 引号未闭合 + 1 处引号对调 (原致 Validate HTML structure 步 abort)
- [x] 本地 harness 修正为 bash -e 语义 + 新增 shell 引号配平门禁
- [x] 本地 validate 51/51 PASS
- [x] MD5 基线重算 171 entries / 3,503,264 B, self-check 171/171
- [x] 修复 pb_cu overall 块 P25 残留 + 2 个 gap_to_threshold 错误值
- [x] 重建 dataset_index.json (60 文件 / core_18 md5 全刷新 / PG31 告警 ID)
- [x] 实测重测 p31_site_health.json (342 HTTP 200, warm 59ms, verdict=PASS)
- [x] 3 次 Actions run 全 success, 35 项终检全 PASS
- [x] gate_periodic_check_log.csv 追加 PG26-R1 — 433 -> 447 rows (+14)
- [x] web_deploy_manual.md §25 追加
- [x] DSHC 通知 (PB 14/14 灰度计数完成)

## 7. 交付物清单

| 交付物 | 状态 |
|--------|:----:|
| PHASE26_DONE.flag | DONE |
| phase26_gate_summary_report.md | DONE |
| vis_phase26_final_check.md | DONE |
| web_deploy_manual.md §25 | DONE |
| gate_periodic_check_log.csv (PG26-R1, 14 rows) | DONE |
| phase26_to_phase27_handoff.md | DONE |
| web_site/data/MD5_BASELINE.json | DONE |
| web_site/data/p31_site_health.json | DONE |
| DSHD-P26_TO_DSHC_PB_GRAY_HANDOFF.md | DONE |

---

**结论: DSHD-P26 全部 6 项验收 AC1-AC6 PASS, 阶段闭环。**
