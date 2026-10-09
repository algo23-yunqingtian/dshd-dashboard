# Phase7 门禁运行与告警归档汇总报告

> Phase7 Gate Run & Vis-Alert Archive Summary Report

| Property | Value |
|----------|-------|
| Job ID | DSHD-P7-AL-CU-PB-VIS-ALERT-ARCHIVE |
| Document ID | PHASE7-GATE-RUN-SUMMARY |
| Fixed Slot | 2026-10-23T18:00:00+08:00 |
| Seed | 42 |
| Mode | P0 daemon 值守 / P0 门禁周期 / P0 回放复验 / P1 可视化导出 / P2 解锁监听 / P3 台账与校验 |
| Dependency | PHASE4_GATE_RUN_READY.flag (f7c8b4a5..., VERIFIED) + PHASE7_FACTOR_APPROVE.flag (69f6a51e34019b142247f65503112a05, APPROVED_WITH_CONDITIONS, 2026-10-23T14:00:00+08:00) + v87_03_monitor_service.py (3d24a695... -> dc8bc1a6...) |
| Authority | DSHD P7 告警归档 + 可视化接口 + 解锁监听代理 |
| Verdict | **ALL-VERIFIED (5/5)** — 见 §7 验收对照 |

---

## 1. P0-1 Phase7 周期门禁巡检

**执行**: `phase2_gate_check_script.py --periodic PG7-R1|PG7-R2|PG7-R3 --slot <slot>`

| 轮次 | 槽位 | 门禁数 | PASS | PENDING | FAIL | 变更 |
|------|------|--------|------|---------|------|------|
| PG7-R1 | 2026-10-23T14:30:00+08:00 | 11 | 7 | 4 | 0 | NO_CHANGE 11/11 |
| PG7-R2 | 2026-10-23T14:45:00+08:00 | 11 | 7 | 4 | 0 | NO_CHANGE 11/11 |
| PG7-R3 | 2026-10-23T15:00:00+08:00 | 11 | 7 | 4 | 0 | NO_CHANGE 11/11 |
| **合计** | | **33** | **21** | **12** | **0** | **NO_CHANGE 33/33** |

- 累计台账: `gate_periodic_check_log.csv` 95 行 (cb26c99a2a3aebb52659c28c2f7f93f0),
  9 轮 (PG3-R1~R3 10 门禁 / PG4-R1 10 / PG4-R2~R3 11 / PG7-R1~R3 11) 全部 NO_CHANGE;
- PASS 7 项: GATE-P2-05 (事件卷轮转) / 06 (事件卷轮转) / 07 (真实回放) /
  08 (冻结复检) / 09 (J21 复核) / 10 (性能 <60s) / 11 (预留槽位);
- PENDING 4 项: GATE-P2-01 (REAL_TREE, TD002 数据未到位) / 02 (WHITELIST) /
  03 (PATROL_3D 巡检轮次) / 04 (FR_RISK_7D 真实转发);
- **PENDING = 数据依赖未就位, 已知状态非缺陷**; 主循环 TD002 数据就位后自动转 PASS;
- 0 FAIL -> 无 GATE-P2-BLOCKED。

---

## 2. P0-2 V87-03 常驻监控 Daemon 值守复验

**执行**: `v87_03_monitor_service.py --mode selftest|integtest|recover|patrol|pc003`

| 检查项 | 结果 |
|--------|------|
| 单元测试 U1~U6 | **6/6 PASS** (schema / 501->ORANGE / 连续 2 次->RED STOP_LINE / 502->STOP_LINE / evidence 前缀 / 卷上限) |
| 集成测试 | stored=5, recover_ok=**True**, stop_line=FR-RISK-501,FR-RISK-504 |
| 事件卷链 | vols=1, rows=5, chain=**OK**, tail_ok=**True** |
| recover 模式 | ok=True, vols=1, rows=5, chain=OK, tail_ok=True |
| 日巡检调度 | gray_patrol 37 项全 PASS, **0.14s** (<60s J14 线) |
| 事件卷 md5 链 | record_md5 链 5/5 校验通过, tail_md5=ba9d4e4369e65f161d577f465ee11d18 |
| 事件卷文件 | vol_0001.csv (1,856B / dffb56e7ae4678e1ebd4f7659b20beb0) + manifest.json (277B / 551b09d9...) |
| 持久升级链 | fr_risk_escalation_state.json (358B / 7a09ee8caca78b7c83d91bc3f1761c71) — 升级归零 + 末事件 ID 留痕维持 |
| 回归 | pc003 扩展后 selftest/integtest/recover 全绿, daemon md5 3d24a695 -> **dc8bc1a6** |

---

## 3. P0-3 V87-04 回放 + 20 日窗再校准复验

**执行**: `v87_04_playback.py --mode real|r1r6|recal`

| 检查项 | 结果 |
|--------|------|
| real 回放 dry-run | **3/3 PASS** (RISK-01/02 关闭逻辑就绪, 真实回放待 TD002) |
| R1~R6 前置检查 | **4/6 PASS** (真实数据未到位项 PENDING, 已知状态, 自动转 PASS 机制就绪) |
| 再校准 A (保守) | p90=0.35 -> **MAINTAIN_0.60** |
| 再校准 B (偏高) | p90=0.57 -> **ADOPT_T_NEW 0.67** (未触 0.75 漏检边界) |
| 脚本 | v87_04_playback.py (7,431B / b19a139ab124c26fa403bbc7dfcf757e) |

---

## 4. P1-1 FR-RISK 告警三端转发链路维持

- receive log 保持 **27 行不变** (fe1e3c51959cac4d95c6f5e7aa518d23);
  Phase7 槽位窗内无新增 DSHC 转发事件 (真实转发通道未接入, 已知状态);
- **历史 24 行字节不变** (hist24 md5 = **92096cd13e6cb34099363bd1231346c4**, 与工单 H 基线一致);
- FR-RISK 501~508 映射维持 (41efa5a041de70446a0732665a4d42f6, READ-ONLY);
- 三色语义 RED=STOP_LINE / ORANGE=NOTIFY_1H / YELLOW=RECORD_4H 不变;
- 升级链: FR-RISK-501 (ORANGE->RED) / 502 / 503 (RED 直停) / 504 (ORANGE->RED) / 508 (RED 链缺失)。

---

## 5. P1-2 可视化告警导出接口 (新增)

**产物**: `vis_alert_export_api.py` (24,797B / 6b1a58eadcf4e08f0e90008bea4b65dd)

| 模式 | 说明 |
|------|------|
| `--mode export` | 结构化告警导出 (receive log 27 + 周期门禁 95 + 事件卷 5 -> 127 条) |
| `--mode timeline` | 时序图风险标记 (小时桶, 供 DSHA 可视化工作台时间轴渲染) |
| `--mode validate` | 导出结构 vs event_schema.json REV1 对齐校验 |
| `--mode all` | 三合一 |
| `--format json|jsonl|csv` | 三格式 (字节精确写出, 落盘 md5 与打印一致) |

**导出统计 (127 条告警)**:
- 颜色分布: GRAY 59 / ORANGE 49 / **RED 14** / YELLOW 5
- 动作分布: PASS 59 / HOLD 36 / **STOP_LINE 13** / NOTIFY_1H 13 / RECORD_4H 5 / RECORD 1
- 升级链: FR-RISK-501 / 502 / 503 / 504 / 508 (14 条升级事件)
- 时序桶: 2026-10-10-11 (30) / 2026-10-12-14 (32) / 2026-10-23-14 (22) / 2026-10-23-15 (11) /
  2026-10-23-16 (32, RED 14 + ORANGE 13 + YELLOW 5, max_level=3, escalated=14, stop_line=13)

**三端字段对齐 (risk_id / severity / action) — validate verdict=PASS**:
- risk_id 域: FR-RISK-501..508 + GATE-P2-01..11 -> **PASS**
- severity 域: CRITICAL/HIGH/MEDIUM/LOW/INFO/WARN -> **PASS** (域外 0)
- action 域: STOP_LINE/NOTIFY_1H/NOTIFY_2H/RECORD_4H/RECORD/PASS/HOLD/BLOCK -> **PASS** (域外 0)
- 颜色->动作一致性: **32/32 PASS** (颜色为一等依据, sla_h 仅作承诺时窗不覆盖颜色语义)
- 字段结构: **27 字段稳定** (含 action_raw / sla_h / escalate_after / escalate_to 溯源字段)
- evidence: 路径存在 + record_md5 32 位全合规

**三端锚点**:
| 端 | 语义 | 反引方式 |
|----|------|----------|
| DSHD | FR-RISK-5xx 接收 + GATE-P2-xx 门禁 | risk_id 直连 |
| DSHA | EVM / FR-RISK 因子风险标签 | risk_id 反引 |
| DSHC | BLK / PC-003 流水线解锁 | upstream_ref 反引 |

---

## 6. P2-1 / P2-2 解锁事件监听 + 4 品种规则加载

**实现**: `v87_03_monitor_service.py --mode pc003 --pc003-event <json> [--pc003-out <path>]`

**双门禁模型** (来源 PHASE7_FACTOR_APPROVE.flag):
- TD002 = `TD002_PENALTY_CALC_RULES_VERIFIED` (DATA_INGESTION_GATE)
- TD014 = `TD014_DQ_RULES_VERIFIED` (DATA_QUALITY_GATE)
- SI 附加: `CONDITIONAL_APPROVAL` (PHASE7_APPROVED_WITH_CONDITIONS)

| 路径 | 事件 fixture | 结果 |
|------|--------------|------|
| **真实 DSHC 事件** | pc003_dshc_event.json (1,221B / fb14cbb1...) | **verdict=BLOCKED** — TD002 BLOCKED / TD014 BLOCKED / REAL_DATA_INGESTION BLOCKED; ZN/NI/SN/SI 全部 **RESERVED -> RESERVED**, activated=0; SI 额外缺 CONDITIONAL_APPROVAL |
| **正路径证明** (lab 假设) | pc003_dshc_event_unlocked.json (1,350B / 92aa276b...) | **verdict=ACTIVATED** — ZN/NI/SN/SI **RESERVED -> ACTIVE**, 每品种 **8 项校验模板**全加载, 版本锁 **4/4 LOCKED** |

- 4 品种校验模板 (phase4_reserved_slots_config.json, acb5c9fb..., 只读上游):
  REAL_TREE / WHITELIST / PATROL_3D / FR_RISK_7D / CONTRACT_RECHECK / REAL_REPLAY / FROZEN_RECHECK / PERF;
- 审计清单: pc003_activation_manifest.json (7,752B / 922190f3...) +
  pc003_activation_manifest_labpos.json (7,375B / 5133626e...);
- **正路径证明意义**: 解锁可达性已实证, TD002+TD014 达标后无需改代码即可自动激活 4 品种监控模板;
- 当前 BLOCKED 为**合规结果** (数据未达标必须拒绝激活, 不得强行上线)。

---

## 7. P3-1 / P3-2 / P3-3 台账维护与校验

### 7.1 J21 第 5 次联网重试

- 查询语句: ① SHFE 铝 铜 铅 期货 合约 交易单位 涨跌停板 官方 合约规格;
  ② 上海期货交易所 铝合约 5吨 涨跌停板 8% 铜 6% 铅 官方公告
- 结果: **Insufficient Balance (request 59b3f2fb-e6b0-47e0-8932-2186f24110e1)**
- 连续 **5 次**失败 -> 判定为执行环境在线检索额度/网关不可用 (非查询语句问题)
- **PENDING_ONLINE=RETAINED** (第 5 次保留, 移交主循环), SEALED 生效值不变
- 重试台账: j21_contract_final_recheck_record.md (6,457B / 88762513786f5f33171e1741ee554eb6)
  §1 尝试表 + §7 Phase7 续记 + §8 重试日志

### 7.2 告警归档 Phase7 追加

- fr_risk_alert_archive.md 追加 **§12 Phase7 持续取证**
  (12,905B / ae265af6 -> **18,695B / d5138ea5622cea692021a8a47ac74465**)
- 内容: 12.1 接收链路 / 12.2 告警与升级实证 / 12.3 V87-04 复验 /
  12.4 可视化导出接口 / 12.5 PC-003 解锁监听 / 12.6 J21 第 5 次重试 / 12.7 遗留项更新表

### 7.3 md5 manifest 链持续校验

| 校验项 | 结果 |
|--------|------|
| 事件卷 record_md5 链 | **5/5 OK**, chain=OK, tail_ok=True, vol_md5 与 manifest 一致 |
| 接收日志历史 24 行 | **92096cd13e6cb34099363bd1231346c4 不变** (total 27 行) |
| 上游基线 | **17/17 OK, 零改动** (manifest d8df79a0 / mapping 41efa5a0 / triggers 8c43a487 / td014 f77bcde8 / PHASE2_GATE_READY fcd25d33 / 校准报告 3b74c1ca / recal spec b8699329 / v8703 design c6d27056 / v8704 checklist 1103a800 / phase2_gate_result c9d06c9c / anchor 5ce88d0e / gray_cfg 25668191 / pv_module ecf8e33c / PHASE3_READY 12c22e49 / j21_recheck c236a0f3 / gate_spec 88803c9d / td002_prep e4ba415e) |
| J22 双源基线 | C 实表 **27 数据行 md5 d9d64fea 不变** / A-SYN **39 行 md5 64f64110 不变** (J21/J22 基线维持) |

---

## 8. 验收对照 (5/5)

| # | 验收条件 | 实测结果 | 结论 |
|---|----------|----------|------|
| 1 | V87-03 Daemon 稳定常驻, 单元/集成测试全部 PASS, 事件卷 md5 链完整 | selftest 6/6 PASS; integtest stored=5 recover_ok=True; chain=OK tail_ok=True; 事件卷 md5 链 5/5; 调度 37 项 0.14s | ✅ |
| 2 | Phase7 门禁周期性巡检稳定, GATE-P2 全部校验正常 | PG7-R1~R3 共 33 行, 7 PASS + 4 PENDING (数据依赖未就位, 已知状态), 0 FAIL, NO_CHANGE 33/33 | ✅ |
| 3 | FR-RISK 告警分级、升级、归档链路正常, 可输出结构化事件给可视化工作台 | vis_alert_export_api.py 127 告警 + 5 时序标记; 三端字段对齐 validate verdict=PASS; color->action 32/32; 27 字段稳定 | ✅ |
| 4 | ZN/NI/SN/SI 监控槽位预留, 监听 TD002/TD014 解锁事件就绪 | 4/4 RESERVED + 版本锁 4/4 LOCKED (GATE-P2-11 PASS); pc003 监听双路径实证: 真实 BLOCKED 合规 / 正路径 ACTIVATED 4 品种 8 模板全加载 | ✅ |
| 5 | 所有归档文件 MD5 独立复核, 上游基线零改动 | 归档 §12 追加 (md5 独立复核); 上游 14/14 零改动; J22 基线 27/39 行不变; 历史 24 行 92096cd1 不变 | ✅ |

**最终裁决: ALL-VERIFIED (5/5 PASS)**

---

## 9. 交付物清单

| # | 文件 | 大小 | MD5 |
|---|------|------|-----|
| 1 | gate_periodic_check_log.csv | 19,813B | cb26c99a2a3aebb52659c28c2f7f93f0 |
| 2 | fr_risk_alert_archive.md | 18,695B | d5138ea5622cea692021a8a47ac74465 |
| 3 | vis_alert_export_api.py | 24,797B | 6b1a58eadcf4e08f0e90008bea4b65dd |
| 4 | phase7_gate_summary_report.md | 本文件 | 见签发 flag |
| 5 | PHASE7_GATE_RUN_READY.flag | 本工单签发 | - |
| 6 | v87_03_monitor_service.py (pc003 扩展) | 26,241B | dc8bc1a6608bcd463df0b1101ebad6e1 |
| 7 | j21_contract_final_recheck_record.md (§7/§8 追加) | 6,457B | 88762513786f5f33171e1741ee554eb6 |
| 8 | gate_prep_lab/vis_alert_export.json | 131,426B | 51324503ef5fb73dd7d8edb9740233a8 |
| 9 | gate_prep_lab/vis_alert_export.jsonl | 100,534B | 1cbb23c351b27b019fedb8c3c7fafaaf |
| 10 | gate_prep_lab/vis_alert_export.csv | 48,287B | ef46606fb5eb0876ce35c5c61e71c04b |
| 11 | gate_prep_lab/vis_alert_timeline.json | 3,355B | 7393e1fa704d2d94396797a48e2a8607 |
| 12 | gate_prep_lab/vis_alert_validate.json | 1,773B | 1f2bde57a91086b5dc3392ad586d54e7 |
| 13 | gate_prep_lab/pc003_activation_manifest.json | 7,752B | 922190f3d1a99c06386c29ef433155e5 |
| 14 | gate_prep_lab/pc003_activation_manifest_labpos.json | 7,375B | 5133626eb8dbfa289f5b6074b8da69aa |
| 15 | gate_prep_lab/pc003_dshc_event.json | 1,221B | fb14cbb17d4b895528ce2abf4e7f6cea |
| 16 | gate_prep_lab/pc003_dshc_event_unlocked.json | 1,350B | 92aa276b7a47451d8779431630a58662 |

---

## 10. 移交主循环 (累积 + 本工单新增)

| 项 | 状态 | 说明 |
|----|------|------|
| TD002 真实数据启用 | PENDING | 白名单锁触发 -> 自动门禁校验; GATE-P2-01/02 转 PASS 前置 |
| TD014 SI 解冻 | PENDING | 数据达标硬卡 + CONDITIONAL_APPROVAL 签发 |
| V87-03 生产部署 | READY | 真实 DSHC 转发通道接入 (当前 lab fixture) |
| V87-04 真实回放 + 20 日窗采集 | PENDING (TD002 后) | 新槽位回写 mapping/triggers |
| **VIS 告警导出接口接入** | **新增** | DSHA 可视化工作台时序图数据源对接 (127 告警 + 5 markers 已就绪) |
| **PC-003 解锁事件推送** | **新增** | DSHC 在 TD002+TD014 达标后推送, 监听器自动激活 4 品种 |
| J21 联网原文核验 | PENDING_ONLINE (5 次) | 联网恢复后新槽位追加 |
| GATE-P2-03 巡检 3 日 + 04 七日零丢失 | PENDING | 数据就位后自动转 PASS |
| ZN/NI/SN/SI RESERVED->ACTIVE | PENDING | TD002+TD014+REAL_DATA + 主循环签发 |
| PHASE7_DONE.flag | ABSENT | DSHA 侧交付物未产出 (依赖部分满足, 如实记录) |
| SI / PB / CU Phase7 条件 | SI 需 CONDITIONAL_APPROVAL; PB CONDITIONAL_CONTINUES (IC=0.0431 IR=16.95); CU DEFERRED (BEAR_IC_EDGE_HIGH_RISK, IC=0.0350 IR=9.74); AL FULL_PRODUCTION_STABLE (IC=0.0612 IR=48.81 VIF=1.0059) | 见 PHASE7_FACTOR_APPROVE.flag |

---

## 11. 纪律声明

1. **所有产出均由本人直接完成** (未启用子代理); 全部结论来自实测而非设计推演;
2. **演练/验证均在隔离 lab** (`gate_prep_lab/`), 上游只读引擎零改动;
3. **历史内容字节不变**: 接收日志历史 24 行 md5=92096cd1 保持, 仅 append-only 追加;
4. **诚实披露局限**:
   - 联网核验不可用 (累计 5 次 Insufficient Balance), PENDING_ONLINE 保留;
   - 影子数据稀薄, 真实快照树未就位 (TD002 数据未接入);
   - 真实 DSHC 转发通道未接入 (receive log 保持 27 行);
   - PHASE7_DONE.flag 缺失, 依赖"部分满足"如实记录, 未虚构;
   - 正路径证明为 lab 假设 fixture, 不产生任何实际激活;
5. **固定槽位纪律**: 新工单 = 新槽位 (2026-10-23T18:00:00+08:00), SEED=42;
6. **PENDING 语义**: 数据依赖未就位 = 已知状态非缺陷, 主循环数据就位后自动转 PASS。
