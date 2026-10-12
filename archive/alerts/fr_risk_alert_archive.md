# FR-RISK 告警取证归档 (DSHC 转发接入)

| Property | Value |
|----------|-------|
| Job ID | DSHD-P0-AL-CU-PB-GRAY-PHASE1-LIVE-MONITOR |
| Document ID | PHASE1-LIVE-MONITOR-D2 |
| Fixed Slot | 2026-10-10T06:15:00+08:00 (接收/分级) |
| Seed | 42 |
| Mode | GRAY-PHASE1 LIVE MONITOR - FR-RISK 告警链路接入取证 |
| Dependency | PHASE1_MONITOR_DONE.flag (c425024fb0a90d6c88a992576f4a8207, READ-ONLY) |
| Authority | DSHD P0 灰度上线后实时监控值守代理 |

## 1. 接入链路 (P0-3)

```
DSHC 风险引擎 --转发--> D 侧接收器 v869_d_fr_risk_receiver.py
    -> 等级映射 (fr_risk_501_508_mapping.json, 501 -> ORANGE 工单强制)
    -> 同码连续升级链 (escalate_after/escalate_to 显式字段)
    -> 只追加写入 fr_risk_receive_log.csv (record_md5, R6)
    -> 取证归档 (本文档) + phase1_live_monitor_log.csv 汇总行
```

- FR-RISK-5xx 为 DSHC 转发灰度运行期风险告警新族; 工作区实证无既有占用 (grep FR-RISK-50x = 0)。
- 上游 A 侧 FR-RISK-301~312 (v869d_ad_acl_monitor_rule.md) 为品种风险编码族, 本族 501~508 为运行期告警转发族, 两族并存不冲突。

## 2. FR-RISK-501~508 等级映射表

| 码 | 语义 | D 侧级 | 颜色 | SLA | 升级链 | 对应告警族 | 依据 |
|----|------|--------|------|-----|--------|-----------|------|
| FR-RISK-501 | CU BEAR 区持仓风险 | HIGH | ORANGE | 1h | 同码连续 2 次 -> RED 停线 | ALARM-POS-* | **工单强制** (验收: 501 -> ORANGE) |
| FR-RISK-502 | AL/CU/PB 头寸>0 缺失 (real 硬门) | CRITICAL | RED | 停线 | 立即 STOP_LINE | ALARM-POS-* | 设计扩展 (V87-04) |
| FR-RISK-503 | K11 合约规模偏离 | CRITICAL | RED | 停线 | 立即 STOP_LINE | ALARM-R04-K11-* | 设计扩展 (R04 0 误差) |
| FR-RISK-504 | K12 涨跌幅阈值偏离 | HIGH | ORANGE | 1h | 同码连续 2 次 -> RED | ALARM-R02-K12-* | 设计扩展 (R02 冻结) |
| FR-RISK-505 | 跨端差异 (25/27 / A-SYN 39) | MEDIUM | YELLOW | 4h | 同码连续 3 次 -> ORANGE | ALARM-J22-RISK-* | 设计扩展 (J22 对账) |
| FR-RISK-506 | 卷式轮转/归档失败 | MEDIUM | YELLOW | 4h | 同码连续 3 次 -> ORANGE | ME-04 | 设计扩展 |
| FR-RISK-507 | 冻结品种只读完整性异常 | HIGH | ORANGE | 1h | 同码连续 2 次 -> RED | ALARM-LOCK-*/RO-*/DIR-* | 设计扩展 |
| FR-RISK-508 | 审计链 CHAIN-001 部分缺失 | CRITICAL | RED | 2h | 缺失+探针泄漏同发 | ALARM-CHAIN-001-* | 设计扩展 |

> 诚实披露: FR-RISK-501 颜色映射由本工单验收标准强制 (ORANGE); 502~508 为沿 R01~R08 冻结阈值与 J15 三色纪律的设计扩展, 主循环确认走新槽位更新 (PENDING_MAINLOOP)。

## 3. CU BEAR 区 FR-RISK-501 全链路取证 (P1-2)

### 3.1 触发事件 (DSHC 转发报文, gate_prep_lab/fr_risk_fwd_events.csv)

| 事件 | 时间 | 原始 | 判级 | 取证要素 |
|------|------|------|------|----------|
| FWD-501-001 | 06:15:01 | ORANGE_HINT (bear_ratio=0.75 > 0.60) | HIGH / ORANGE | 快照 md5 + 头寸日志 md5 + 接收行 |
| FWD-501-002 | 06:17:30 | ORANGE_HINT (窗口内第 2 次) | CRITICAL / RED | 升级链 STOP_LINE (escalation) |

### 3.2 全链路取证要素 (证据绑定)

| 环节 | 取证 | 值 |
|------|------|-----|
| 1. 快照样本 | cu_bear_snapshot.csv (CU 5t x5, F39/F40=5/5, 规格正确) | md5 `51dd8601796dc8bce3bc6ad35873ead9` |
| 2. 头寸日志 | cu_bear_position_log.csv (BEAR x3 / BILL x1, bear_ratio=0.75) | md5 `36d02c7a9923f0abb6972db2618f2b56` |
| 3. 接收行 1 | FWD-501-001 -> HIGH ORANGE (sla 1h) | record_md5 `0712567035d4fa23dcadfd1020f20571` |
| 4. 接收行 2 | FWD-501-002 -> CRITICAL RED STOP_LINE (escalation) | record_md5 `f7e12676307761e45f6fe129179c34c6` |
| 5. 巡检联动 | phase1_live_monitor_log.csv FR_RISK_RECEIVE 汇总行 (2 轮) | PASS x2, receive rows=9 |
| 6. 审计留痕 | fr_risk_receive_log.csv 只追加 9 行, 全部 record_md5 | md5 `a7f129371817988e941dbd0d2fc33fea` |

> 口径注记: 501 触发维度为**空头区集中度** (bear_ratio), 与 position_verify 模块的 CHECK-3 (pos_positive>0 硬门) 正交; 本样本 pos_positive=4 模块级 PASS, 501 事件为 DSHC 转发区制风险, 不冲突。

### 3.3 告警分级上报

- ORANGE (HIGH): 通知负责人 + 1h SLA 闭环; 触发同码连续计数。
- RED (CRITICAL): STOP_LINE 停线 (演练隔离 lab, 不触碰归档树); 恢复走 R5 全链复核流程 (定位 -> 恢复 RO/锁 -> 全链复核 -> 审计链更新)。

## 4. 接收/分级执行结果 (9 事件全通过)

| 事件 | 码 | 品种 | 判级 | 颜色 | 动作 |
|------|----|------|------|------|------|
| FWD-501-001 | FR-RISK-501 | CU | HIGH | ORANGE | 记录 (窗口首发) |
| FWD-501-002 | FR-RISK-501 | CU | CRITICAL | RED | STOP_LINE (escalation) |
| FWD-502-001 | FR-RISK-502 | AL | CRITICAL | RED | STOP_LINE |
| FWD-503-001 | FR-RISK-503 | PB | CRITICAL | RED | STOP_LINE |
| FWD-504-001 | FR-RISK-504 | CU | HIGH | ORANGE | 记录 |
| FWD-505-001 | FR-RISK-505 | ALL | MEDIUM | YELLOW | 记录 |
| FWD-506-001 | FR-RISK-506 | ALL | MEDIUM | YELLOW | 记录 |
| FWD-507-001 | FR-RISK-507 | ZN | HIGH | ORANGE | 记录 (只读完整性族) |
| FWD-508-001 | FR-RISK-508 | ALL | CRITICAL | RED | 记录 (2h SLA) |

统计: total=9, RED=4, ORANGE=3, YELLOW=2, STOP_LINE=3 — 与接收器实测输出一致。

## 5. 升级链验证

- FR-RISK-501: 首发 ORANGE (无停线) -> 窗口内第 2 次 -> RED STOP_LINE (escalation) — **实测通过** (接收器 escalate_after=2 分支)。
- 沿 v868 升级表口径 (MEDIUM->HIGH 连续 2 次 / HIGH->CRITICAL 缺失+泄漏同发), 本族以 mapping 显式 escalate 字段落地, 无继承冲突。

## 6. 审计留痕

- fr_risk_receive_log.csv: 只追加 9 行 + record_md5, 无历史行改写 (R6)。
- phase1_live_monitor_log.csv: 89 行只追加, 含 2 条 FR_RISK_RECEIVE 汇总行。
- 卷式轮转: 活动卷 0001 (9 < 1000), 未触发切卷; ME-04 轮转规则就绪。

## 7. 遗留项与移交

| 项 | 状态 | 移交 |
|----|------|------|
| 502~508 映射确认 | PENDING_MAINLOOP | 主循环按 mapping 复核/调整走新槽位 |
| 501 CU BEAR 阈值 (0.60) 校准 | PENDING_MAINLOOP | TD002 真实数据到位后回放校准 |
| 真实 DSHC 转发接入 | 预留 | 主循环接真实转发通道, 本工单以 fixture 实弹验证链路 |

## 8. 证据绑定

| 引用 | 路径 | MD5 |
|------|------|-----|
| 映射配置 | fr_risk_501_508_mapping.json | 41efa5a041de70446a0732665a4d42f6 |
| 接收器 | v869_d_fr_risk_receiver.py | 3b4e7c7fdf275341f55f93a28602db80 |
| 转发报文 fixture | gate_prep_lab\fr_risk_fwd_events.csv | 425ea1f7656e640072fa2cc5ce949511 |
| 接收日志 | fr_risk_receive_log.csv | a7f129371817988e941dbd0d2fc33fea |
| CU 快照样本 | gate_prep_lab\cu_bear_snapshot.csv | 51dd8601796dc8bce3bc6ad35873ead9 |
| CU 头寸样本 | gate_prep_lab\cu_bear_position_log.csv | 36d02c7a9923f0abb6972db2618f2b56 |
| 值守日志 | phase1_live_monitor_log.csv | addb564b39c0df3621e14c04c5d2f8f0 |

---

## 9. P4 续记（工单 G 追加：持续接收 + e2e 全链取证）

| Property | Value |
|----------|-------|
| 追加来源 | JOB_ID DSHD-P1-AL-CU-PB-GRAY-PHASE1-GATE-PREP (P4-1 持续接收写入) |
| Fixed Slot | 2026-10-10T08:45:00+08:00 (e2e) / 10:30:00 (归档) |
| 追加前 md5 | b8ce53a196d89c224fbf76fc69a59af7（工单 F 版本, 字节不变） |
| 追加后 md5 | 见本工单交付复核表（快照语义: 归档持续追加, 每次快照记录） |

### 9.1 持续接收状态

- fr_risk_receive_log.csv 由 9 行扩展至 **22 行**（F 轮 9 行字节不变 + e2e 轮 13 行追加）; 全部 append-only + record_md5 (R6)。
- e2e 轮 (gate_prep_lab/fr_risk_e2e_events.csv) 13 事件判级全链实测 **13/13 零失配**:

| 码 | 链 | 实测序列 |
|----|----|----------|
| FR-RISK-501 | 3 连 | ORANGE -> RED (STOP_LINE escalation) -> ORANGE (计数归零复位验证) |
| FR-RISK-504 | 2 连 | ORANGE -> RED (escalate_after=2) |
| FR-RISK-505 | 3 连 | YELLOW -> YELLOW -> ORANGE (escalate_after=3) |
| FR-RISK-502/503 | 单发 | RED STOP_LINE x2 |
| FR-RISK-506 | 单发 | YELLOW |
| FR-RISK-507 | 单发 | ORANGE (只读完整性族) |
| FR-RISK-508 | 单发 | RED |

### 9.2 全链路取证快照留存

- 取证要素链: e2e 报文 (fr_risk_e2e_events.csv) -> 接收行 (record_md5) -> 分级判级 -> 归档 (本节) -> 值守日志汇总。
- 触发器族部署: fr_risk_triggers_deploy.json (8 触发器 ACTIVE, 与 mapping escalate 字段完全一致) — 见校准报告 §5。
- 生产局限披露: 同码连续计数为进程内状态, 跨调用归零; 真实转发须 V87-03 常驻服务持持久计数 (移交项)。

### 9.3 遗留项更新

| 项 | 状态 | 移交 |
|----|------|------|
| 502~508 映射确认 | **DONE** (本工单 e2e 13/13 零失配) | 真实转发通道接入后复验 |
| 501 bear_ratio 0.60 校准 | **DONE** (校准报告; 安全带 [0.40,0.70] 零 FP/FN) | TD002 真实数据 20 日窗再校准 |
| 真实 DSHC 转发接入 | 预留 | V87-03 常驻服务 + 持久计数 |

---

## 10. P2 续记（工单 H 追加：持续接收 + 跨调用持久计数实证）

| Property | Value |
|----------|-------|
| 追加来源 | JOB_ID DSHD-P2-AL-CU-PB-GRAY-PHASE3-GATE-RUN (P3-3 持续接收写入) |
| Fixed Slot | 2026-10-10T11:45:00+08:00 (持久验证轮) / 13:00:00 (归档) |
| 追加前 md5 | ed727a6523ca004dc4166efe6f7ecc1c（工单 G 版本, 字节不变） |
| 追加后 md5 | 见本工单交付复核表（快照语义） |

### 10.1 持续接收状态

- fr_risk_receive_log.csv 由 22 行扩展至 **24 行**（F 轮 9 + e2e 轮 13 + P2 轮 2）; 全部 append-only + record_md5 (R6)。
- P2 轮 (跨调用持久计数验证):

| 事件 | 调用 | 实测 | 说明 |
|------|------|------|------|
| P2-501-001 | CALL A (--persist) | HIGH / ORANGE | counter=1 落盘 fr_risk_escalation_state.json |
| P2-501-002 | CALL B (--persist) | **CRITICAL / RED STOP_LINE (escalation)** | counter 跨调用载入 1->2, 升级链延续 |

### 10.2 跨调用持久计数修复实证 (V87-03 核心)

- **缺陷**: 进程内计数跨调用归零 (工单 G 披露局限)。
- **修复**: 接收器 `--persist` 模式, 计数状态写入 `fr_risk_escalation_state.json` (V87-03 方案落地原型)。
- **实证**: 两次独立进程调用, 501 升级链跨调用延续 (ORANGE -> RED) — 与 V87-03 设计文档 §2 一致。
- 状态文件快照: CALL A 后 `{"FR-RISK-501": {"count": 1, "last_event_id": "P2-501-001"}}`; CALL B 后 `count: 0` (升级归零留痕)。

### 10.3 遗留项更新

| 项 | 状态 | 移交 |
|----|------|------|
| 进程内计数缺陷 | **FIXED** (持久计数实测) | V87-03 daemon 落地 (设计文档 D2) |
| 统一事件 schema | **DONE** (event_schema.json + 示例合规) | 三方接入时启用 |
| 真实 DSHC 转发接入 | 预留 | V87-03 daemon + 7 日 0 丢失 (GATE-P2-04) |

## 11. Phase4 持续取证 (DSHD-P3, 2026-10-12)

### 11.1 接收链路续记

- receive log 追加 Phase4 轮 3 行 (P4-501-001/002, P4-504-001), 新槽位
  `2026-10-12T14:45:00+08:00` / `14:46:00`; 前 24 行历史字节不变
  (重建后 27 行, 历史子集 md5=92096cd1... 保持工单 H 状态)。
- 跨调用升级链 (Phase4 轮): CALL A 501 -> ORANGE (count=1);
  CALL B 501 载入 1 -> 2 -> **RED STOP_LINE**; 504 首击 ORANGE。
- 状态文件快照 (CALL B 后): `{"FR-RISK-501": {"count": 0, "last_event_id": "P4-501-002"},
  "FR-RISK-504": {"count": 1, "last_event_id": "P4-504-001"}}` (升级归零留痕 + 新码计数)。

### 11.2 V87-03 daemon 落地实证 (P1-1)

- daemon 实现: `v87_03_monitor_service.py` (事件接入/schema 校验/分级映射/持久计数/
  事件持久存储卷式轮转/告警出口/调度器/恢复);
- 单元测试 6/6 PASS; 集成测试 5 事件 stored + recover_ok=True + chain=OK;
- 集成跨批升级: 501/504 batch B 延续 -> RED STOP_LINE (进程内计数缺陷修复实证);
- 事件存储卷 `gate_prep_lab/v87_03_event_store/vol_0001.csv` + manifest (record_md5 链)。

### 11.3 501 再校准流程落地 (P1-2)

- `v87_04_playback.py` 就绪: R1~R6 前置检查 + real 回放 dry-run 3/3 + 20 日窗再校准;
- 双场景实测: 保守分布 p90=0.35 -> MAINTAIN_0.60; 偏高分布 p90=0.57 -> ADOPT 0.67;
- 真实 20 日窗待 TD002 数据 (PENDING 已知状态, runbook 步骤就绪)。

### 11.4 遗留项更新

| 项 | 状态 | 移交 |
|----|------|------|
| V87-03 daemon | **IMPLEMENTED** (本工单, 6/6 单测 + 集成 + 恢复) | 生产部署 (事件源接入) |
| V87-04 回放+再校准 | **SCRIPT_READY** (本工单) | 真实窗口采集 + 回写 (TD002 后) |
| J21 联网核验 | PENDING_ONLINE (第 4 次尝试 Insufficient Balance) | 主循环 |
| GATE-P2-01/02/03/04 | PENDING (TD002 数据/巡检轮/转发接入) | 数据就位自动转 PASS |
| PHASE4_DONE.flag | **ABSENT (DSHA 侧交付物未产出)** | 主循环确认 (依赖部分满足) |

## 12. Phase7 持续取证 (DSHD-P7, 2026-10-23)

### 12.1 接收链路维持 (P1-1)

- receive log **保持 27 行不变** (md5=fe1e3c51959cac4d95c6f5e7aa518d23),
  Phase7 槽位窗内无新增 DSHC 转发事件 (真实转发通道未接入, 已知状态);
- 持久升级链状态文件随 Phase7 integtest 落盘更新 (md5=7a09ee8caca78b7c83d91bc3f1761c71),
  升级归零 + 末事件 ID 留痕语义维持;
- FR-RISK 501~508 映射 (41efa5a0..., READ-ONLY) 维持, 三色语义
  RED=STOP_LINE / ORANGE=NOTIFY_1H / YELLOW=RECORD_4H 不变。

### 12.2 告警链路与升级实证 (P0-2)

- V87-03 daemon 值守复验: **selftest 6/6 PASS** (U1 schema / U2 501->ORANGE /
  U3 连续 2 次->RED STOP_LINE / U4 502->STOP_LINE / U5 evidence 前缀 / U6 卷上限);
- **集成测试 stored=5, recover_ok=True, chain=OK, tail_ok=True**;
  跨批次升级链延续: 501/504 batch B 延续 -> **RED STOP_LINE**
  (进程内计数归零缺陷修复实证持续有效);
- 事件卷 `vol_0001.csv` (1,856B / dffb56e7...) + manifest (277B / 551b09d9...)
  record_md5 链 5/5 校验通过, tail_md5=ba9d4e4369e65f161d577f465ee11d18;
- 调度器: gray_patrol 37 项全 PASS, 0.14s (<60s J14 线);
- recover 模式: vols=1 rows=5 chain=OK tail_ok=True。

### 12.3 V87-04 回放 + 20 日窗再校准 (P0-3)

- real 回放 dry-run **3/3 PASS** (RISK-01/02 关闭逻辑就绪, 真实回放待 TD002);
- R1~R6 前置检查 **4/6 PASS** (真实数据未到位项 PENDING, 已知状态, 自动转 PASS 机制就绪);
- 20 日窗再校准双场景复验: 保守分布 p90=0.35 -> **MAINTAIN_0.60**;
  偏高分布 p90=0.57 -> **ADOPT_T_NEW 0.67** (未触 0.75 漏检边界);
- 501 动态阈值重算逻辑在线, 真实 20 日窗口仍待 TD002 数据。

### 12.4 可视化告警导出接口 (P1-2, 新增)

- `vis_alert_export_api.py` (24,797B / 6b1a58ea...) 上线,
  三模式 export / timeline / validate + 三格式 json / jsonl / csv;
- 导出 **127 条告警** (receive log 27 + 周期门禁 95 + 事件卷 5, 去重后 127):
  - 颜色分布: GRAY 59 / ORANGE 49 / RED 14 / YELLOW 5
  - 动作分布: PASS 59 / HOLD 36 / STOP_LINE 13 / NOTIFY_1H 13 / RECORD_4H 5 / RECORD 1
  - 升级链: FR-RISK-501/502/503/504/508 (共 14 条升级事件, 13 条 STOP_LINE)
- **时序图风险标记**: 5 个小时桶 markers (2026-10-10-11 / 2026-10-12-14 /
  2026-10-23-14 / 2026-10-23-15 / 2026-10-23-16), 含 count_by_color / max_level /
  escalated / stop_line / pending_gates, 直接供 DSHA 可视化工作台时间轴渲染;
- **三端字段对齐** (risk_id / severity / action):
  - risk_id 域: FR-RISK-501..508 + GATE-P2-01..11 (域校验 PASS)
  - severity 域: CRITICAL/HIGH/MEDIUM/LOW/INFO/WARN (域校验 PASS)
  - action 域: STOP_LINE/NOTIFY_1H/NOTIFY_2H/RECORD_4H/RECORD/PASS/HOLD/BLOCK (域校验 PASS)
  - 颜色->动作一致性 **32/32 PASS** (颜色为一等依据, sla_h 仅作承诺时窗不覆盖颜色语义)
  - 三端锚点: DSHD=FR-RISK-5xx 接收+GATE-P2-xx 门禁; DSHA=EVM/FR-RISK 因子标签 (risk_id 反引);
    DSHC=BLK/PC-003 流水线解锁 (upstream_ref 反引)
- 导出结构 27 字段稳定, event_schema.json REV1 对齐校验 **verdict=PASS**
  (field_count=27, evidence 路径 + record_md5 32 位全合规)。

### 12.5 PC-003 解锁事件监听 + 4 品种规则加载 (P2-2, 新增)

- `v87_03_monitor_service.py --mode pc003` 新增 (daemon md5 3d24a695 -> **dc8bc1a6**);
- 双门禁模型 (来源 PHASE7_FACTOR_APPROVE.flag):
  TD002 = TD002_PENALTY_CALC_RULES_VERIFIED (DATA_INGESTION_GATE) +
  TD014 = TD014_DQ_RULES_VERIFIED (DATA_QUALITY_GATE);
- **真实 DSHC 事件路径** (`pc003_dshc_event.json`): **verdict=BLOCKED**
  (TD002 BLOCKED / TD014 BLOCKED / REAL_DATA_INGESTION BLOCKED),
  ZN/NI/SN/SI 全部保持 **RESERVED -> RESERVED**, activated=0,
  SI 额外缺 CONDITIONAL_APPROVAL (PHASE7_APPROVED_WITH_CONDITIONS);
- **正路径证明** (`pc003_dshc_event_unlocked.json`, lab 假设路径): **verdict=ACTIVATED**,
  ZN/NI/SN/SI **RESERVED -> ACTIVE**, 每品种 8 项校验模板全加载,
  版本锁 4/4 LOCKED 校验通过 — 证明解锁后可自动激活 4 品种监控模板;
- 审计清单: `pc003_activation_manifest.json` (7,752B / 922190f3...) +
  `pc003_activation_manifest_labpos.json` (7,375B / 5133626e...)。

### 12.6 J21 第 5 次联网重试 (P3-1)

- 查询语句: ① SHFE 铝 铜 铅 期货 合约 交易单位 涨跌停板 官方 合约规格;
  ② 上海期货交易所 铝合约 5吨 涨跌停板 8% 铜 6% 铅 官方公告;
- 结果: **Insufficient Balance (request 59b3f2fb-e6b0-47e0-8932-2186f24110e1)**;
- 连续 5 次失败 -> 判定为执行环境在线检索额度/网关不可用 (非查询语句问题);
- PENDING_ONLINE=RETAINED (第 5 次保留, 移交主循环), SEALED 生效值不变。

### 12.7 遗留项更新

| 项 | 状态 | 推进 |
|----|------|------|
| V87-03 daemon | **STABLE** (值守复验全绿 + pc003 监听扩展) | 生产部署 (真实事件源) |
| V87-04 回放+再校准 | **SCRIPT_READY** (回放 3/3 + 双场景校准复验) | 真实窗口采集 + 回写 (TD002 后) |
| VIS 告警导出接口 | **ONLINE** (127 告警 + 5 markers + 对齐 PASS) | 接入 DSHA 可视化工作台时序图 |
| PC-003 解锁监听 | **READY** (双路径实证, 当前 BLOCKED 合规) | DSHC 在 TD002+TD014 达标后推送 |
| ZN/NI/SN/SI 槽位 | **RESERVED 4/4 + LOCKED 4/4** (GATE-P2-11 PASS) | 主循环签发解锁 |
| J21 联网核验 | PENDING_ONLINE (第 5 次 Insufficient Balance) | 主循环 |
| GATE-P2-01/02/03/04 | PENDING_DATA (TD002 数据/巡检轮/转发通道) | 数据就位自动转 PASS |
| PHASE7_FACTOR_APPROVE.flag | **PRESENT** (69f6a51e..., APPROVED_WITH_CONDITIONS) | - |
| PHASE7_DONE.flag | **ABSENT (DSHA 侧交付物未产出)** | 主循环确认 (依赖部分满足) |

## 13. Phase9 值守取证 (DSHD-P9, 2026-10-25, 新槽位 append-only)

| Property | Value |
|----------|-------|
| Phase9 Slot (daemon) | 2026-10-25T09:00:00+08:00 |
| Phase9 Slot (门禁巡检) | 2026-10-25T14:30 / 14:45 / 15:00 (PG9-R1/R2/R3) |
| Phase9 Slot (VIS 导出) | 2026-10-25T16:30:00+08:00 |
| Seed | 42 |
| 工单 | DSHD-P9-AL-PB-CU-GATE-MONITOR-VIS-ALERT-ARCHIVE |

### 13.1 依赖复核 (新增 PHASE9_DONE.flag 产出)

| 依赖 | 位置 | 大小 | MD5 | 状态 |
|------|------|------|-----|------|
| PHASE8_DONE.flag | `github工作\回测\factor_exp_workspace\dshc_adaptor_ops_prep\v869_gray_launch_plan\` | 14,949B | c2f33b17c32e... | **PRESENT** (COMPLETED) |
| PHASE9_FACTOR_APPROVE.flag | `...\dsha_factor_rating\` | 14,955B | 218e7759939d... | **PRESENT** (APPROVED_WITH_CONDITIONS, ACCEPTANCE 12/12) |
| **PHASE9_DONE.flag** | `...\dshc_adaptor_ops_prep\v869_gray_launch_plan\` | 15,039B | **f3789766b206c847b6806de81d28a592** | **PRESENT** (STATUS=COMPLETED, PRECHECK 15/15 PASS, LAUNCH_FLOW 13 步全 PASS) |
| PHASE7_GATE_RUN_READY.flag | 本目录 | 13,885B | aec5a274cfaa8a5f153dc266cdf58149 | **PRESENT** |

> **更正记录**: 工单 J 记录 `PHASE9_DONE.flag` 全盘 0 命中。本工单重新全盘 glob 命中 1 处 (git 镜像树
> `github工作\回测\factor_exp_workspace\dshc_adaptor_ops_prep\v869_gray_launch_plan\PHASE9_DONE.flag`)。
> 早前 0 命中系首次探测仅检索 DSHD 主树 (`factor_exp_workspace\`) 所致, 非依赖未产出。
> 现 4 项依赖 **全部满足**。DSHC 编排器 JOB_ID=DSHC-P9-AL-PB-CU-GRAY-ORCHESTRATOR-PC003-DUAL-GATE-WATCH,
> PC_003_STATUS=BLOCKED, PIPELINE_FRAMEWORK=FINAL_ACCEPTANCE (5/6 PASS + 1 PC_003_BLOCKED),
> FROZEN_VARIETIES=ZN,NI,SN,SI (ALL DISABLED)。

### 13.2 Daemon 常驻运维复核 (P0-1)

- `--mode selftest`: **6/6 PASS** (修复后复跑, 无回归);
- `--mode integtest`: Phase9 独立卷 `gate_prep_lab/v87_03_event_store_p9/` (clean-room 语义, 不触碰 Phase7 冻结卷), stored=5, recover_ok=True, chain=OK, tail_ok=True;
- `--mode recover`: Phase7 冻结卷只读复核 ok=True, vols=1, rows=5, chain=OK, tail_ok=True;
- `--mode patrol`: **37 项全 PASS**, 耗时 0.10s (AL/CU/PB 各 CHECK-1 CONTRACT_SIZE ref=mult5 size5 / CHECK-2 LIMIT 双轨 A normal+ext / CHECK-3 POSITION_PATH); run_id a73dfbcca471 / c694f4bba84f / 70652be60be8;
- **append-only 合规**: Phase7 冻结卷字节二次确认不变 (见 §13.10)。

### 13.3 Phase9 门禁周期巡检 (P0-2)

- 轮次: PG9-R1 (14:30) / PG9-R2 (14:45) / PG9-R3 (15:00), 每轮 11 门禁 = **33 行**;
- 结果分布: **21 PASS + 12 PENDING + 0 FAIL**; `status_change` 33/33 = **NO_CHANGE**;
- PASS: GATE-P2-05/06/07/08/09/10/11 (卷链/卷轮转/真实回放/冻结复核/J21 复核/性能/预留槽位);
- PENDING (已知数据依赖, 非缺陷): 01 REAL_TREE (TD002 数据) / 02 WHITELIST (TD002 数据) / 03 PATROL_3D (巡检 3 日轮次) / 04 FR_RISK_7D (真实转发 7 日 0 丢失);
- **0 FAIL → 未触发 GATE-P2-BLOCKED**, 告警推送链待命中;
- 台账: `gate_periodic_check_log.csv` 95 → **128 行** (26,683B / 45b58c81...), Phase3/4/7/9 共 4 阶段 10 轮 + 首轮基线。

### 13.4 DEFECT-P9-001 — daemon RED 分支缺失 (真实缺陷, 已双修)

**发现途径**: 新增 R3-SLA_ACTION 回归用例 `red_fr_alerts_all_STOP_LINE=False` (14 条 RED FR-RISK 中 1 条不符)。

**取证记录**:
`VIS-VOL-2026102516-FR-RISK-508-ALL-20261023-B | action='RECORD' | raw='RECORD' | color=RED | severity=CRITICAL | sla=2`

**根因**: `v87_03_monitor_service.py:map_event` 分支序列为
`"直接 STOP_LINE" in escalation_rule → STOP_LINE; elif color=="ORANGE" → NOTIFY_1H; elif color=="YELLOW" → RECORD_4H; else → RECORD`
—— **缺少 `color=="RED"` 显式分支**。FR-RISK-508 的 `escalation_rule='缺失+探针泄漏同发 -> CRITICAL (升级触发)'`
不含该字面量 → 落入 `else → RECORD`, 与 `severity=CRITICAL` / `color=RED` 语义冲突。
FR-RISK-502/503 因 `escalation_rule` 含"直接 STOP_LINE"字面量而**侥幸正确**, 缺陷被掩盖至 Phase9 暴露。

**修复 (双修)**:
1. **源头修复 (daemon)**: `map_event` 在 ORANGE 分支前插入 `elif color == "RED": action = "STOP_LINE"`,
   附 DEFECT-P9-001 溯源注释。三色语义硬约束: RED=STOP_LINE / ORANGE=NOTIFY_1H / YELLOW=RECORD_4H。
2. **导出层防御**: `vis_alert_export_api.py:canon_action` 改为**颜色优先** (颜色有映射即返回颜色语义,
   不改动上游只读事件卷字节)。

**修复验证**:
- selftest 6/6 PASS;
- Phase9 新卷 FR-RISK-508 → `action='STOP_LINE'`, 卷内 STOP_LINE 行 code 集合 = {FR-RISK-501, FR-RISK-504, FR-RISK-508} (3/5 行);
- 卷链 chain=OK, tail_ok=True;
- **Phase7 冻结卷字节不变** (历史偏差保留, 见 §13.10)。

**影响面**: RED 告警 action 由 13 STOP_LINE + 1 RECORD → **14 STOP_LINE + 0 RECORD**;
`by_action` 中 `RECORD` 键消失; VIS-001 峰值桶 `stop_line` 13 → 14, `escalated` 13 → 14。

### 13.5 DEFECT-P9-002 — pc003 audit_id 同槽位碰撞 (真实缺陷, 已修)

**发现途径**: P2 全链路自检 `manifest_audit_ids_distinct=False`。

**根因**: `v87_03_monitor_service.py` pc003 模式 `audit_id = "PC-003-LISTEN-" + slot[:12]`,
同槽位两次运行 (BLOCKED + labpos ACTIVATED) 产生**完全相同的 audit_id**,
两份审计清单 (`01cb09d6...` / `a50f28b0...`) 不可区分。

**修复**: `audit_id` 追加 dshc event_id 尾部 12 位, 保证每次推送事件唯一可溯:
`PC-003-LISTEN-20261025T153-<event_id tail>`。

**修复验证**: 两份清单 audit_id 已区分; 全链路自检 UPSTREAM_IMMUTABILITY 10/10 PASS。

### 13.6 FR-RISK 告警分级/升级/导出 (P1-1, 修复后复跑)

| 维度 | 修复前 | 修复后 |
|------|--------|--------|
| alerts 总数 | 160 | **160** |
| markers | 7 | **7** |
| by_color | GRAY 80 / ORANGE 61 / RED 14 / YELLOW 5 | **不变** |
| by_action STOP_LINE | 13 | **14** |
| by_action RECORD | 1 | **0 (键消失)** |
| escalation_count | 13 | **14** |
| stop_line_count | 13 | **14** |

- 字段数: **27/27 稳定** (schema_ref=`DSHD-PHASE3-UNIFIED-EVENT-SCHEMA-1-REV1`);
- 三端对齐: `risk_id` 域 (FR-RISK-501..508 + GATE-P2-01..11) / `severity` 域 (CRITICAL/HIGH/MEDIUM/LOW/INFO/WARN) /
  `action` 域 (STOP_LINE/NOTIFY_1H/NOTIFY_2H/RECORD_4H/RECORD/PASS/HOLD/BLOCK) **全部 PASS**;
- `color_action_align = 32/32` PASS (颜色语义为一等依据);
- 校验 verdict = **PASS**;
- 升级链: FR-RISK-501/502/503/504/508 共 5 族触发, `escalation_count=14`;
- 三格式输出 (json/jsonl/csv) 均 160 alerts / 7 markers, **CRLF=0 / CR 字节=0**, jsonl 逐行解析 160/160, csv 27 列宽一致。

### 13.7 回归三件套 (P1-4, 持续回归不引入新缺陷)

| 用例 | 覆盖点 | 结果 |
|------|--------|------|
| R1-CRLF | Windows 文本模式写盘字节精确性 (write_body 探针: cr_byte_absent / crlf_absent / lf_count_match / size_match / md5_match) | **PASS** |
| R2-RISKFAMILY | `risk_family` 不得 `code.split("-")[1]` 切片 (防 FR-RISK-501 → "RISK"), 全部 27 条 FR-RISK 家族 = 'FR-RISK' | **PASS** |
| R3-SLA_ACTION | SLA_ACTION 分支: RED/ORANGE/YELLOW 映射 + sla_h 不覆盖颜色 + 颜色优先于冲突 raw + 未知 raw 归一 + `red_fr_alerts_all_STOP_LINE` + `daemon_RED_branch_present` | **PASS** |

- 回归 verdict = **PASS** (3/3), 输出 `vis_alert_regression.json` (2,614B / 5ad444b2...);
- R1 探针写盘后 `os.unlink` 清理, 不污染交付目录;
- R3 同时做**源码级断言** `daemon_RED_branch_present`, 防止 DEFECT-P9-001 回退。

### 13.8 DSHA VIS-001 可视化工作台时序模块联调 (P1-2)

`gate_prep_lab/vis_001_integration.json` (115,452B / 27f872a198b7a761ec55fc251338c02f)

- `workbench_id=VIS-001`, `chart.module="时序模块 (timeseries risk markers)"`;
- `x_axis=bucket (YYYYMMDD-HH)`, `y_axis=max_level (0=NONE 1=YELLOW 2=ORANGE 3=RED)`;
- **series 7 点 / tooltip entries 7 条 / series_point_total=160**, 与 export 完全一致;
- **悬浮弹窗事件溯源**: 每桶 `popup_title` + `level` + `stop_line` + `escalated` + `items[]`,
  每项含 `alert_id / risk_id / risk_family / symbol / severity / color / action / status /
  fixed_slot / round_no / event_id / fwd_id / upstream_ref / evidence_path / evidence_md5`;
- **render_check 11/11 全 True**: axis_monotonic / series_marker_aligned / tooltip_bucket_aligned /
  every_point_has_backing_event / level_domain_ok / color_domain_ok / severity_domain_ok /
  action_domain_ok / evidence_md5_all_32hex / hover_traceability_ok / popup_level_consistent;
- 图表渲染 verdict = **PASS**;
- 峰值桶 `2026-10-25-16`: count=32, level=3, `stop_line=14`, `escalated=14`,
  colors={ORANGE:13, RED:14, YELLOW:5}, risk_ids 全 8 族 FR-RISK-501..508, symbols={AL,ALL,CU,PB,ZN}。

### 13.9 FAIL 门禁 → 告警推送链 (P0-2 / P1-2)

- 推送目标固化: `FAIL_PUSH_TARGETS = ["DSHA:VIS-001", "DSHC:DUTY", "GATE-P2-BLOCKED"]`;
- **语义边界**: 仅 `status=FAIL` → P0 级推送; `PENDING` 走 `HOLD` 不进推送链 (数据依赖非缺陷);
- 当前 0 FAIL → `push.fail_alert_count=0`, 链路待命中;
- 推送链路可达性验证 (`gate_prep_lab/p9_fail_push_verify.py`, lab 合成 fixture, **不改写真实台账**):
  注入 1 FAIL + 1 PASS + 1 PENDING, 通过 monkeypatch 模块常量 `GATE_LOG` 指向 fixture, 运行后还原;
  - 结果 **21/21 checks PASS**, verdict = **PASS**, 输出 `gate_prep_lab/vis_fail_push_verify.json`;
  - 推送 1 条: `push_id=PUSH-FAIL-VIS-GATE-2026102514-GATE-P2-05`, `risk_id=GATE-P2-05`,
    `round_no=PG9-DRILL`, `status_change=DEGRADED`, `severity=CRITICAL`, `color=RED`,
    `action=BLOCK`, `priority=P0`, `pushed_to=[DSHA:VIS-001, DSHC:DUTY, GATE-P2-BLOCKED]`,
    evidence.record_md5 = 32 hex;
  - **边界验证**: `pending_not_pushed=True` (PENDING→HOLD 不进链) /
    `pass_not_pushed=True` / `pushed_count_is_1=True` / `fail_pushed_exactly_once=True`;
  - **零改写验证**: `real_gate_log_md5_unchanged=True` (45b58c81... 前后一致),
    `fixture_not_written_to_real_log=True`, fixture 用后删除 (`deleted=True`);

### 13.10 PC-003 双门禁监听 (P2)

**Phase9 事件 fixture** (新槽位, 与 Phase7 历史 fixture 分离):
- `gate_prep_lab/pc003_dshc_event_p9.json` (1,503B / da9c80e0...) — 真实语义 BLOCKED,
  upstream_ref 引用 `DSHA:PHASE9_FACTOR_APPROVE(218e7759)`;
- `gate_prep_lab/pc003_dshc_event_unlocked_p9.json` (1,375B / 95d43e9e...) — **LAB POSITIVE-PATH PROOF**,
  `note` 字段明确标注"假设路径, 非真实推送"。

| 路径 | verdict | gates_verified | activated | locks |
|------|---------|----------------|-----------|-------|
| P2-1 BLOCKED (真实语义) | **BLOCKED** | False | - (0/4) | LOCKED 4/4 |
| P2-2/3 ACTIVATED (lab 正路径) | **ACTIVATED** | True | ZN,NI,SN,SI (4/4) | LOCKED 4/4 |

- BLOCKED 明细: TD002 BLOCKED / TD014 BLOCKED; ZN/NI/SN `missing=TD002,TD014,REAL_DATA_INGESTION`;
  SI 额外 `missing=...,CONDITIONAL_APPROVAL` (SI_UNFREEZE_CONDITIONS); `blocked_reason` 非空;
- ACTIVATED 明细: 4 品种 `current=RESERVED → target=ACTIVE`, `template=8` 项全加载, `missing=-`;
- **全链路回归自检** `gate_prep_lab/pc003_post_unlock_selfcheck.json` (3,219B / e4cf06b0...):
  BLOCKED_PATH 14/14 + ACTIVATED_PATH 16/16 + UPSTREAM_IMMUTABILITY 10/10 = **40/40 PASS**;
- 8 项模板键: CONTRACT_RECHECK / FROZEN_RECHECK / FR_RISK_7D / PATROL_3D / PERF / REAL_REPLAY /
  REAL_TREE / WHITELIST;
- **上游不可变校验**: 激活为"建议态", `phase4_reserved_slots_config.json` 仍 4/4 RESERVED + 8 项模板不变
  (acb5c9fb...), 无上游改写;
- lab 正路径 fixture 每轮可达性验证 = **PASS** (P2-3)。

### 13.11 遗留跟踪 (P3)

**J21 第 6 次联网重试** — `web_search` 返回 **Insufficient Balance (request d48139de-7702-4826-b64a-da06933332dc)**。
- **失败分类 6/6 网关额度类 (gateway quota), 0/6 业务查询错误**: 错误串恒定 `Insufficient Balance`,
  仅 request_id 变化; 跨 4 工单 6 次、查询语句多次变换结果一致; 返回 request_id 但**无任何结果 URL/片段**,
  请求在网关计费阶段即被拒, 未进入检索执行阶段, 故不可能返回业务级错误;
- **不阻断主流程**: GATE-P2-09 判定依据为三重来源复核结论而非在线检索结果, 门禁持续 PASS (累计 10 轮实证);
- PENDING_ONLINE=RETAINED (第 6 次保留), SEALED 生效值不变, 台账 `j21_contract_final_recheck_record.md` 追加 §9 + §8 第 6 行。

**DSHC 转发通道连通性探测** — `gate_prep_lab/p9_channel_probe.py`:
- 通道定义: `fr_risk_receive_log.csv` 入站事件写入流; 活性判定 = 阶段窗内是否产生新行;
- 3 轮全部 **IDLE_NO_INBOUND**: Phase4 最后入站 2026-10-12T14:46:00+08:00 以来 **0 新增**,
  跨 Phase7+Phase9 两阶段; `rows_since_phase4=0`;
- 分类: **属数据源未就位而非链路故障** (TD002 PENDING_DATA_VERIFICATION, GATE-P2-01 REAL_TREE=PENDING);
- 断连告警台账 `gate_prep_lab/dshc_channel_disconnect_ledger.csv` (2,684B / b2066ea1..., 3 行 append-only, CRLF=0):
  每轮 `ALERT-CHANNEL-IDLE-<slot>` severity=WARN priority=P1, targets=`DSHA:VIS-001;DSHC:DUTY;DSHD:MONITOR`;
- 台账 record_md5 链: 61db16b9 / 3ea5f49c / 39830545。

### 13.12 证据包 (MD5 绑定)

| 引用 | 路径 | 大小 | MD5 |
|------|------|------|-----|
| V87-03 监控守护 (含 DEFECT-P9-001/002 修复) | `v87_03_monitor_service.py` | 27,012B | **e2f0d4ccd65eea44f56578c33bec27fe** |
| VIS 告警导出接口 (含 R1~R3 + vis001 + FAIL 推送) | `vis_alert_export_api.py` | 40,226B | **474ff0aea6692d5e912553aa03e736d4** |
| 门禁脚本 (未改) | `phase2_gate_check_script.py` | 19,953B | 32c6403f5c66efd72ceb1d16d2a06f55 |
| 周期门禁台账 (128 行) | `gate_periodic_check_log.csv` | 26,683B | 45b58c81f72fee849f19a3359b975476 |
| VIS 告警导出 (json) | `gate_prep_lab/vis_alert_export.json` | 165,715B | 3f7736c0b3b489e36e7e62f701341be0 |
| VIS 告警导出 (jsonl) | `gate_prep_lab/vis_alert_export.jsonl` | 126,337B | 320754085b86a1c1646e247694cbef0f |
| VIS 告警导出 (csv) | `gate_prep_lab/vis_alert_export.csv` | 60,428B | 58c37c1a0c176ccf9e15e77b41def82a |
| VIS 时序聚合 | `gate_prep_lab/vis_alert_timeline.json` | 4,718B | 6c9d634c56cd770333e416b99c9d8eae |
| VIS 校验报告 | `gate_prep_lab/vis_alert_validate.json` | 1,757B | b2cc271e24fa78c10ceffb5b4f51ab61 |
| VIS 回归报告 | `gate_prep_lab/vis_alert_regression.json` | 2,614B | 5ad444b26cddc300f775b481032d660a |
| VIS-001 联调包 | `gate_prep_lab/vis_001_integration.json` | 115,452B | 27f872a198b7a761ec55fc251338c02f |
| PC-003 BLOCKED 清单 (Phase9) | `gate_prep_lab/pc003_activation_manifest_p9.json` | 7,798B | 01cb09d6047fa12500300b7a4ffddfdf |
| PC-003 ACTIVATED 清单 (Phase9 lab) | `gate_prep_lab/pc003_activation_manifest_p9_labpos.json` | 7,394B | a50f28b085017e718916d7073dfc879b |
| PC-003 全链路自检 | `gate_prep_lab/pc003_post_unlock_selfcheck.json` | 3,219B | e4cf06b01b3ea256a3cbabfb70645e33 |
| 通道断连告警台账 | `gate_prep_lab/dshc_channel_disconnect_ledger.csv` | 2,684B | b2066ea131113f9d72e0a42526656b29 |
| FAIL 推送链验证 (脚本) | `gate_prep_lab/p9_fail_push_verify.py` | 8,767B | 097e17fbca3c78a217ba28f6d555ae8f |
| FAIL 推送链验证 (结果) | `gate_prep_lab/vis_fail_push_verify.json` | 2,317B | ed99f24496c3a15cd37f5bcd9aea1cf6 |
| 通道探测脚本 | `gate_prep_lab/p9_channel_probe.py` | 9,034B | 758217601ce076b0ae9d1b8fd2485384 |
| PC-003 自检脚本 | `gate_prep_lab/p9_post_unlock_selfcheck.py` | 10,270B | cec4566b47593eae0a3775a914446a7b |
| Phase9 事件卷 (**可再生测试卷**, integtest clean-room 重建) | `gate_prep_lab/v87_03_event_store_p9/vol_0001.csv` | 1,859B | a057fe35b03d2e72b230a3778e084730 |
| Phase9 卷 manifest (可再生) | `gate_prep_lab/v87_03_event_store_p9/manifest.json` | 277B | 8193ed08c6d032eac2bb435bf79394f8 |
| **Phase7 冻结卷 (append-only 未变)** | `gate_prep_lab/v87_03_event_store/vol_0001.csv` | 1,856B | **dffb56e7ae4678e1ebd4f7659b20beb0** |
| **Phase7 冻结卷 manifest (未变)** | `gate_prep_lab/v87_03_event_store/manifest.json` | 277B | **551b09d938b90c08cb41ebeeddd6eee4** |
| J21 复核台账 (含 §9 Phase9) | `j21_contract_final_recheck_record.md` | 10,315B | 19b02a0a6badcc0f47fefa6cf0bb1ebc |
| 预留槽位配置 (上游只读未变) | `phase4_reserved_slots_config.json` | 4,392B | acb5c9fb80ce513dc45916e3c3b21742 |
| FR-RISK 映射 (上游只读未变) | `fr_risk_501_508_mapping.json` | 5,759B | 41efa5a041de70446a0732665a4d42f6 |
| 事件接收日志 (上游只读未变, 27 行) | `fr_risk_receive_log.csv` | 8,895B | fe1e3c51959cac4d95c6f5e7aa518d23 |
| 事件 schema (上游只读未变) | `event_schema.json` | 3,491B | 09c7a4e8df53aca7dd1d861abaa10ccc |

**append-only 复核结论**: 上游只读交付物 md5 全部与 Phase7 基线一致 (事件卷 dffb56e7/551b09d9、
映射 41efa5a0、接收日志 fe1e3c51、槽位配置 acb5c9fb、schema 09c7a4e8、C 实表 d9d64fea),
本工单仅**新增** Phase9 槽位文件与 **修复** 2 个自有脚本 (v87_03_monitor_service.py / vis_alert_export_api.py),
未改写任何上游历史字节。

**Phase9 事件卷可再生性说明**: `v87_03_event_store_p9/` 为 `--mode integtest` 的 clean-room 测试卷,
每次运行按当前槽位时间戳重新生成, **md5 非确定性** (仅行数 5 / 字节 1,859 / manifest 277 稳定,
chain=OK / tail_ok=True 恒定)。上表 md5 为最终一次运行值; 该卷不参与任何下游导出
(VIS 导出数据源为 Phase7 冻结卷), 故其 md5 变化不构成交付物漂移。
Phase7 冻结卷 `v87_03_event_store/` 才是 append-only 审计基线, 全工单字节恒定。

### 13.13 移交主循环

| 项 | 状态 | 推进 |
|----|------|------|
| V87-03 daemon | **STABLE** (值守复验全绿 + DEFECT-P9-001/002 已修) | 生产部署 (真实事件源) |
| Phase9 门禁巡检 | **7 PASS / 4 PENDING / 0 FAIL** (33 行全 NO_CHANGE) | 数据就位自动转 PASS |
| VIS 告警导出接口 | **ONLINE** (160 告警 + 7 markers + 27 字段 + 校验 PASS + 三格式) | 接入 DSHA 可视化工作台时序图 |
| VIS-001 联调 | **VERIFIED** (render_check 11/11 + 悬浮弹窗溯源 + FAIL 推送链 PASS) | 主循环签发工作台对接 |
| PC-003 双门禁 | **READY** (BLOCKED 合规 + ACTIVATED 可达 + 全链路 40/40) | DSHC 在 TD002+TD014 达标后推送 |
| ZN/NI/SN/SI 槽位 | **RESERVED 4/4 + LOCKED 4/4** (GATE-P2-11 PASS) | 主循环签发解锁 |
| J21 联网核验 | PENDING_ONLINE (第 6 次 Insufficient Balance, 网关额度类) | 主循环 |
| GATE-P2-01/02/03/04 | PENDING_DATA (TD002 数据/巡检轮次/转发通道) | 数据就位自动转 PASS |
| DSHC 转发通道 | **IDLE_NO_INBOUND** (Phase4 以来 0 新增, 3 轮断连告警已入账) | 真实快照数据接入后复探 |
| PHASE8/9_DONE + PHASE9_FACTOR_APPROVE.flag | **全部 PRESENT** (f3789766 / c2f33b17 / 218e7759) | - |
| **DEFECT-P9-001 / P9-002** | **已双修并回归通过** | 建议主循环确认缺陷登记入库 |

---

## 14. Phase12 值守取证 (DSHD-P12, 2026-11-16, 新槽位 append-only)

**新槽位锁定**: PG12-R1 `2026-11-16T14:30:00+08:00` / R2 `14:45:00+08:00` / R3 `15:00:00+08:00`,
VIS 导出 `2026-11-16T16:30:00+08:00`, PC-003 监听 `2026-11-16T15:30:00+08:00`. `SEED=42`.
上一槽位 Phase9 (2026-10-25) 全部产物字节不变, 本工单仅 append-only 新增 Phase12 轮次行与独立 `_p12` 命名产物。

### 14.1 依赖复核 (新增 PHASE11_DONE.flag 产出)

| 依赖 | 路径 | 状态 |
|------|------|------|
| PHASE11_DONE.flag | `github工作/回测/factor_exp_workspace/dshc_adaptor_ops_prep/v869_gray_launch_plan/PHASE11_DONE.flag` | **PRESENT** 15,322B `c722907048f1` — JOB `DSHC-P11-AL-PB-CU-GRAY-ORCHESTRATOR-PC003-DUAL-GATE-WATCH`, PRECHECK 15/15 PASS, LAUNCH_FLOW 13 步全 PASS, STATUS=COMPLETED |
| PHASE12_FACTOR_APPROVE.flag | `github工作/回测/factor_exp_workspace/dsha_factor_rating/PHASE12_FACTOR_APPROVE.flag` | **PRESENT** 15,731B `1f1fae65a470` — PHASE12_FACTOR_APPROVE=TRUE, APPROVED_WITH_CONDITIONS, AL 1 / PB CONDITIONAL 1 / CU DEFERRED 1 |
| PHASE9_GATE_RUN_READY.flag | `dshd_arch_gate_prep/PHASE9_GATE_RUN_READY.flag` | **PRESENT** 20,956B `b37c0c2f9a33` (未变) |

Phase11 语义确认: AL FULL_PRODUCTION_STABLE (IC=0.0600, IR=48.08, VIF=1.0059, IC_DELTA=-0.0012 在 ±0.005 容差内),
PB CONDITIONAL (BEAR_IC=0.0294), CU DEFERRED (BEAR_IC=0.0236), 冻结 4 品种 ZN/NI/SN/SI ALL DISABLED,
PC-003 BLOCKED (TD002+TD014 双门禁持续锁定), TD002/TD014=READY_FOR_DATA (ACTIVE_MONITORING)。

### 14.2 Daemon 常驻运维复核 (T0 / P0-1)

| 检查 | 结果 |
|------|------|
| selftest | **6 / 6 PASS** (U1-SCHEMA / U2-501-ORANGE / U3-ESC-RED / U4-502-STOP / U5-EVIDENCE-PREFIX / U6-VOL-LIMIT=1000) |
| integtest (新槽位 `v87_03_event_store_p12/`) | stored=5, recover_ok=True, **chain=OK tail_ok=True**, STOP_LINE={FR-RISK-501, FR-RISK-504, FR-RISK-508} |
| recover (P12 卷) | ok=True, vols=1 rows=5 chain=OK tail_ok=True |
| recover (Phase7 冻结卷, 只读) | ok=True, vols=1 rows=5 chain=OK tail_ok=True (**字节未变**, md5 仍 dffb56e7) |
| patrol | **checks=37, 37/37 PASS, elapsed=0.11s** (<60s J14 门限) |

**关键**: integtest 的 STOP_LINE 码集合含 **FR-RISK-508** — 该码是 DEFECT-P9-001 的暴露码,
写入面正确性已确认。

### 14.3 缺陷回归验证 — DEFECT-P9-001 / DEFECT-P9-002 均无复现 (T0 / AC2)

`gate_prep_lab/p12_defect_regression.py` (12,308B `3b5901694a58`) → `defect_regression_p12.json`
(3,519B `cddc6afbc0d2`), **18 / 18 PASS, verdict=PASS**。

**DEFECT-P9-001 (daemon RED 分支缺失) — 9 / 9 PASS**:

| check_id | 结果 |
|----------|------|
| D1-CANON-RED-OVERRIDES-RAW | `canon_action(raw='RECORD', color='RED', sla=2) = 'STOP_LINE'` (FR-RISK-508 原始缺陷输入) |
| D1-MAPPING-8CODES-COLOR-ACTION | 8/8 码颜色→动作全量对齐 (RED→STOP_LINE / ORANGE→NOTIFY_1H / YELLOW→RECORD_4H) |
| D1-RED-CRITICAL-NEVER-RECORD | RED/CRITICAL 码 (502/503/508) 全 STOP_LINE |
| D1-DAEMON-RED-BRANCH-PRESENT | daemon 源码含 `elif color == "RED": action = "STOP_LINE"` 显式分支 |
| D1-DAEMON-508-STOP-LINE | `map_event(FR-RISK-508)` → action=STOP_LINE severity=CRITICAL color=RED |
| D1-DAEMON-508-REPEATED-STABLE | 同槽位二次投递仍 STOP_LINE (升级计数路径稳定) |
| D1-FROZEN-VOLUME-BYTE-STABLE | 冻结卷 md5=dffb56e7ae46 (Phase7 锚点, 未被本轮改写) |
| D1-HISTORICAL-DEFECT-EVIDENCE-INTACT | 残留 RED/RECORD 历史证据行**有且仅有 1 条** `FR-RISK-508-ALL-20261023-B` (DEFECT-P9-001 原始证据, 保留不改写) |
| D1-EXPORT-LAYER-DEFENSIVE-CORRECTION | 冻结卷内全部 RED 行经 `canon_action` 修正为 STOP_LINE |

**DEFECT-P9-002 (audit_id 同槽位碰撞) — 8 / 8 PASS**:

| check_id | 结果 |
|----------|------|
| D2-SAME-SLOT-DIFF-EVENT-DISTINCT | 同槽位两个 event_id → audit_id `…20261116-001` / `…20261116-002` 不冲突 |
| D2-AUDIT-ID-SHAPE | 格式 `PC-003-LISTEN-<slot12>-<event_tail12>` 双清单符合 |
| D2-SLOT-SEGMENT-12 | slot 段 `20261116T153` = 槽位去冒号去连字符前 12 位 |
| D2-EVENT-SEGMENT-12 | event 段 = dshc event_id 尾部 12 位 |
| D2-DETERMINISTIC-SAME-INPUT | 同输入产出一致 (可重现) |
| D2-MANIFEST-MATCHES-FORMULA | 实产 manifest audit_id 与公式复现值逐位一致 |
| D2-MANIFEST-DISTINCT | BLOCKED vs ACTIVATED 两份清单 audit_id 不冲突 |
| D2-LEGACY-FORMULA-DETECTABLE | 旧公式(仅槽位)在同等输入下必然冲突=True → 本测试可检出原缺陷 |

**历史证据保留说明 (追加不篡改)**: Phase7 冻结卷 `v87_03_event_store/vol_0001.csv` 内
`FR-RISK-508-ALL-20261023-B` (color=RED, severity=CRITICAL, action=**RECORD**) 是 DEFECT-P9-001
发生时的原始落库行。按 append-only 纪律, 该行**不回写、不改字节** (卷 md5 全程 dffb56e7),
语义纠偏发生在导出层 (`canon_action` 颜色优先) 与写入面 (daemon RED 分支)。该证据行现由
`D1-HISTORICAL-DEFECT-EVIDENCE-INTACT` 固化, 防止后续被"顺手修复"成无痕状态。

### 14.4 Phase12 门禁周期巡检 (PG12-R1~R3, T1)

`phase2_gate_check_script.py` 版本锁定未改 (`32c6403f`, 19,953B)。
`gate_periodic_check_log.csv` **95→128→161 行**, append-only 追加 33 行 (3 轮 × 11 条)。

| 轮次 | 槽位 | 行数 | PASS | PENDING | FAIL | status_change |
|------|------|------|------|---------|------|---------------|
| PG12-R1 | 2026-11-16T14:30:00+08:00 | 11 | 7 | 4 | **0** | 11/11 NO_CHANGE |
| PG12-R2 | 2026-11-16T14:45:00+08:00 | 11 | 7 | 4 | **0** | 11/11 NO_CHANGE |
| PG12-R3 | 2026-11-16T15:00:00+08:00 | 11 | 7 | 4 | **0** | 11/11 NO_CHANGE |

**FAIL=0 → 未触发 GATE-P2-BLOCKED**。7 PASS = GATE-P2-05(CHAIN_4_4) / 06(VOLUME_ROTATION) /
07(REAL_REPLAY) / 08(FROZEN_RECHECK 锁 4/4) / 09(J21_RECHECK SEALED) / 10(PERF 0.07s<60s) /
11(RESERVED_SLOTS 4/4)。4 PENDING = GATE-P2-01(REAL_TREE, AL/CU/PB 真实树 ABSENT) /
02(WHITELIST, TD002 数据未就位) / 03(PATROL_3D, 累计 3 轮已达成但数据依赖未闭合) /
04(FR_RISK_7D, 转发 7 日窗仍 0 入站)。**PENDING 为已知数据依赖状态, 非缺陷**,
与 Phase9 结论一致, 数据就位后自动转 PASS。

### 14.5 FR-RISK 告警分级/升级/导出 (T2 / T4)

`vis_alert_export_api.py` 版本锁定未改 (`474ff0ae`, 40,226B)。P12 槽位重导出至独立 `_p12` 命名产物
(Phase9 的 `vis_alert_export.*` 三个文件字节未变)。

| 指标 | Phase9 (2026-10-25) | **Phase12 (2026-11-16)** |
|------|--------------------|--------------------------|
| 告警总数 | 160 | **193** |
| markers | 7 | **9** (新增 `2026-11-16-14` / `-15` / `-16`) |
| 字段数 | 27 | **27** |
| color_action_align | 32/32 | **32/32** |
| STOP_LINE | 14 | **14** |
| escalation | 14 | **14** |
| 导出 md5 | `3f7736c0` (165,715B) | `e2466256d7b5` (**200,057B**) |

颜色分布: GRAY 101 / ORANGE 73 / RED 14 / YELLOW 5。
动作分布: PASS 101 / HOLD 60 / STOP_LINE 14 / NOTIFY_1H 13 / RECORD_4H 5。
升级链: FR-RISK-501/502/503/504/508 五码, escalation_count=14。
Phase12 FR-RISK marker (`2026-11-16-16`, level 3): RED 14 / ORANGE 13 / YELLOW 5,
stop_line=14, escalated=14 — 覆盖 501~508 全部 8 码。

**颜色分支与 STOP_LINE 动作对齐 (工单 T2 硬约束)**: 三色彩色语义为一等动作约束
(RED=STOP_LINE / ORANGE=NOTIFY_1H / YELLOW=RECORD_4H), `sla_h` 仅作响应承诺时窗不覆盖颜色。
本轮 14 条 RED 告警 action **全部** 为 STOP_LINE (0 条 RECORD / 0 条其他), 对齐 14/14。

### 14.6 VIS-001 可视化工作台时序模块联调 (T4 / AC4)

`vis_001_integration_p12.json` 139,417B `36bf831b2edf`。

| render_check 项 | 结果 |
|-----------------|------|
| axis_monotonic | TRUE |
| series_marker_aligned | TRUE |
| tooltip_bucket_aligned | TRUE |
| every_point_has_backing_event | TRUE |
| level_domain_ok | TRUE |
| color_domain_ok | TRUE |
| severity_domain_ok | TRUE |
| action_domain_ok | TRUE |
| evidence_md5_all_32hex | TRUE |
| hover_traceability_ok | TRUE (悬浮弹窗事件溯源) |
| popup_level_consistent | TRUE |
| **合计** | **11 / 11 全 True, verdict=PASS** |

时序序列 **9 条** (Phase9 为 7 条), 点位总数 **193** (与告警总数一致, 每点均有支撑事件)。

### 14.7 回归三件套 (T4 / 持续回归不引入新缺陷)

`vis_alert_regression_p12.json` 2,614B `e96af2455f6b`, **3 / 3 PASS**:

| case_id | 场景 | 结果 |
|---------|------|------|
| R1-CRLF | 接收日志 CRLF 行尾混入 / 空行 / BOM 容错 | PASS |
| R2-RISKFAMILY | FR-RISK 家族码 (501~508) 全家族覆盖 + 未知码拒绝 | PASS |
| R3-SLA_ACTION | SLA 与动作域一致性 (RED→STOP_LINE / ORANGE→NOTIFY_1H / YELLOW→RECORD_4H) | PASS |

校验报告 `vis_alert_validate_p12.json` 1,757B `10c2ee42bdf8`, verdict=PASS, field_count=27,
color_action_align=32/32。

### 14.8 FAIL 门禁 → 告警推送链 (T3-c / AC6)

`gate_prep_lab/p12_fail_push_verify.py` (8,781B `73e61383fe04`) →
`vis_fail_push_verify_p12.json` (2,319B `c4eec578d2dd`), **21 / 21 PASS**。

隔离 lab fixture 模拟 1 条 FAIL 行 (GATE-P2-05 CHAIN_4_4 由 PASS→FAIL), 驱动真实
`build_alerts_from_gates` + `gate_fail_alerts` 链路:

- 推送报文: `push_id=PUSH-FAIL-VIS-GATE-2026111614-GATE-P2-05`, risk=GATE-P2-05,
  severity=**CRITICAL**, color=**RED**, action=**BLOCK**, priority=**P0**,
  round_no=PG12-DRILL, status_change=**DEGRADED**
- 推送目标 (3): `DSHA:VIS-001` / `DSHC:DUTY` / `GATE-P2-BLOCKED`
- evidence_md5 32 hex, 指向 lab fixture (非真实台账)
- **`real_gate_log_md5_unchanged=True`** — 演练未污染真实 `gate_periodic_check_log.csv`

### 14.9 PC-003 双路径持续自检 (T3-b / AC3)

**BLOCKED 真实路径** (`pc003_dshc_event_p12.json` → `pc003_activation_manifest_p12.json` 7,802B `2715314cba4e`):
verdict=**BLOCKED**, `all_gates_verified=False`, `locks_ok=True`, `activated_count=0`,
audit_id=`PC-003-LISTEN-20261116T153-20261116-001`。
TD002 BLOCKED / TD014 BLOCKED / REAL_DATA_INGESTION BLOCKED / CONDITIONAL_APPROVAL BLOCKED;
ZN/NI/SN/SI 全部 RESERVED → RESERVED, 8 项模板全载, **LOCK 4/4**。
`blocked_reason = TD002+TD014 双门禁未全达标 (TD002,TD014) / LOCK 4/4 / 无可激活品种`。

**ACTIVATED 实验室正路径** (`pc003_dshc_event_unlocked_p12.json` →
`pc003_activation_manifest_p12_labpos.json` 7,396B `d42196124452`):
verdict=**ACTIVATED**, `all_gates_verified=True`, `locks_ok=True`, `activated_count=4`
(ZN/NI/SN/SI 全部 RESERVED → ACTIVE), audit_id=`PC-003-LISTEN-20261116T153-20261116-002`。
**两份清单同槽位 audit_id 不冲突** (DEFECT-P9-002 修复持续有效)。

**全链路自检** (`p12_post_unlock_selfcheck.py` → `pc003_post_unlock_selfcheck_p12.json`
3,222B `dee99fef55bb`): **40 / 40 PASS** —
BLOCKED_PATH 14/14 + ACTIVATED_PATH 16/16 + UPSTREAM_IMMUTABILITY 10/10。

> 真实状态仍为 BLOCKED: ACTIVATED 路径仅为 lab 正路径可达性证明, 不代表 DSHC 真实推送。

### 14.10 DSHC 事件转发通道探测 + 告警分级 (T3-a)

`gate_prep_lab/p12_channel_probe.py` (12,064B `fcc8b6670700`) →
`dshc_channel_disconnect_ledger_p12.csv` (3,432B `97d7e1e38845`, **3 行 append-only**,
`record_md5` 链 4a49b155 → 01081fed → 87324942 自洽)。
独立台账文件, Phase9 台账 `dshc_channel_disconnect_ledger.csv` (2,684B `b2066ea1`, 3 行) **未变**。

| 轮次 | 槽位 | 入站 | 断连阶段 | 分级 | escalated |
|------|------|------|----------|------|-----------|
| PG12-R1 | 2026-11-16T14:30:00+08:00 | 0/1 | 4/4 | **CRITICAL / P0** | **TRUE** |
| PG12-R2 | 2026-11-16T14:45:00+08:00 | 0/1 | 4/4 | **CRITICAL / P0** | **TRUE** |
| PG12-R3 | 2026-11-16T15:00:00+08:00 | 0/1 | 4/4 | **CRITICAL / P0** | **TRUE** |

`channel_status=IDLE_NO_INBOUND`; `receive_log_rows=27` md5 `fe1e3c51` (与 Phase4 基线一致, 未新增);
`last_inbound_ts=2026-10-12T14:46:00+08:00` (Phase4 最后入站, 此后跨 Phase7/9/11/12 四阶段 0 新增);
`phase11_done_flag_present=TRUE` md5 `c722907048f1`。

**告警分级与自动升级规则** (本轮新增并实装): DSHC 编排器风险事件接收 → DSHD 网关分级 →
推送至 VIS-001 告警面板; **CRITICAL 级别自动升级通知**。分级策略基于可观测事实
(入站行数 + 断连阶段窗计数), 非主观判定:

| 条件 | severity | priority | escalated | 推送目标 |
|------|----------|----------|-----------|----------|
| CONNECTED | INFO | P3 | FALSE | — |
| IDLE, 断连阶段 1~2 | WARN | P1 | FALSE | `DSHA:VIS-001;DSHC:DUTY;DSHD:MONITOR` |
| IDLE, 断连阶段 ≥3 | **CRITICAL** | **P0** | **TRUE** | `DSHA:VIS-001;DSHC:ORCHESTRATOR;DSHD:DUTY` |

本轮断连阶段数 = 4 (Phase7/9/11/12 均 0 入站) ≥ 阈值 3 → **CRITICAL/P0 自动升级通知** 3 次。
**诚实披露**: 通道 IDLE 系真实快照数据未接入 (TD002 PENDING_DATA_VERIFICATION,
GATE-P2-01 REAL_TREE=PENDING), 属**数据源未就位而非链路故障** —
DSHC 编排器侧 PHASE11_DONE.flag 已签发且 PRECHECK 15/15 PASS, 上游运行正常,
缺的是 TD002/TD014 数据侧的就位条件。

### 14.11 事件卷锚点维护 — 确定性归档卷 vs 非确定性测试卷 (T5)

`gate_prep_lab/p12_md5_recheck.py` (21,601B `43ac576a18a5`) 首次将事件卷按**确定性分类**校验:

| 卷 | 分类 | anchor | chain | tail | md5 断言 | 结果 |
|----|------|--------|-------|------|----------|------|
| `v87_03_event_store/` (Phase7) | **DETERMINISTIC_ARCHIVE** (确定性归档) | TRUE | TRUE | TRUE | **强校验** `dffb56e7` | **OK** 字节恒定 |
| `v87_03_event_store_p9/` (Phase9) | **NONDETERMINISTIC_ARCHIVE_FROZEN** (可再生后签收冻结) | TRUE | TRUE | TRUE | **强校验** `a057fe35` | **OK** 签收后字节冻结 |
| `v87_03_event_store_p12/` (Phase12) | **NONDETERMINISTIC_REGENERATED** (本轮 clean-room 现生成) | TRUE | TRUE | TRUE | **仅时点记录** `132887a7` | **OK** 仅结构校验 |

`anchor=V87-03-CHAIN-ANCHOR` 三卷一致; 各卷 5 行, `record_md5 = md5(prev_md5|event_id|severity|action|ts)`
逐行独立复核通过; `tail_md5` 与 manifest 一致。
`frozen_ok=True` (两冻结卷 md5 全部匹配锚点) / `test_chain_ok=True` (P12 卷结构完整)。

**三类卷的语义差异 (本工单固化)**:

1. **确定性归档卷** — Phase7 冻结卷, 作为 append-only 审计基线, 全工单字节恒定, md5 强校验;
   内含 DEFECT-P9-001 原始证据行, 故意不改写 (见 14.3)。
2. **可再生后签收冻结卷** — Phase9 `integtest` clean-room 产出, 生成时 md5 不可复现,
   但 Phase9 签收后字节即冻结, 从 Phase12 视角仍是可校验的 md5 锚点。
3. **非确定性测试卷** — 本轮 `integtest` 现生成, `shutil.rmtree` 后重建, md5 每轮变化
   (`132887a7` ≠ Phase9 的 `a057fe35`), **不作 md5 断言**, 仅校验 anchor/chain/tail 结构,
   不参与任何下游导出 (VIS 导出数据源恒为 Phase7 冻结卷)。

### 14.12 MD5 独立复核 + 上游零改动 (T5 / AC5)

`p12_md5_recheck_ledger.csv` (697B `ec5c76c540ba`, 4 行 append-only, record_md5 链
41bedd35 → fb86378a → 54e68111 → c4d0f9ab, 链自洽复核 OK) +
`p12_md5_recheck_inventory.json` (19,564B `ca891f718d38`),
**4 / 4 verdict=PASS**。

| 轮次 | 槽位 | 上游只读 | 历史基线 | 冻结卷 | 测试卷 | verdict | record_md5 |
|------|------|----------|----------|--------|--------|---------|------------|
| PG12-R1 | 2026-11-16T14:30:00+08:00 | **17/17** | **17/17** | OK | OK | **PASS** | 41bedd35... |
| PG12-R2 | 2026-11-16T14:45:00+08:00 | **17/17** | **17/17** | OK | OK | **PASS** | fb86378a... |
| PG12-R3 | 2026-11-16T15:00:00+08:00 | **17/17** | **17/17** | OK | OK | **PASS** | 54e68111... |
| PG12-FINAL | 2026-11-16T17:00:00+08:00 | **17/17** | **17/17** | OK | OK | **PASS** | c4d0f9ab... |

上游只读 17 项 (与 Phase9 同集, 全部零改动): 映射 `41efa5a0` / 触发器 `8c43a487` /
TD002 prep `e4ba415e` / TD014 预配置 `f77bcde8` / J21 复核 `c236a0f3` / 合约规格 `d8df79a0` /
门禁规格 `88803c9d` / 501 校准报告 `3b74c1ca` / 20 日再校准规格 `b8699329` / V87-04 清单 `1103a800` /
V87-03 设计书 `c6d27056` / Phase2 门禁结果 `c9d06c9c` / 持仓校验模块 `ecf8e33c` /
锚点与字段预留 `5ce88d0e` / 灰度巡检配置 `25668191` / PHASE3 旗标 `12c22e49` / PHASE2 旗标 `fcd25d33`。

**历史基线 17 项** (6 项原有 + 8 项本轮新增 + 3 项事件卷结构 = 17):

| 新增基线项 | md5 前缀 | 说明 |
|-----------|----------|------|
| `v87_03_monitor_service.py` | `e2f0d4cc` | 版本锁定 (工单交付物 5) |
| `vis_alert_export_api.py` | `474ff0ae` | 版本锁定 (工单交付物 6) |
| `phase2_gate_check_script.py` | `32c6403f` | 版本锁定 |
| `phase7_gate_summary_report.md` | `cf09d108` | Phase7 冻结归档 |
| `PHASE7_GATE_RUN_READY.flag` | `aec5a274` | Phase7 冻结归档 |
| `phase9_gate_summary_report.md` | `aa0ab9fe` | Phase9 冻结归档 |
| `PHASE9_GATE_RUN_READY.flag` | `b37c0c2f` | Phase9 冻结归档 |
| `j21_contract_final_recheck_record.md` | `19b02a0a` | J21 冻结归档 |
| 事件卷 ×3 | — | anchor/chain/tail 结构 (见 14.11) |

接收日志 `fr_risk_receive_log.csv` md5 `fe1e3c51`, 27 行, 首行 `FWD-501-001`, 末行 `P4-504-001` —
Phase4 基线恒定, Phase12 无新增入站 (与 14.10 通道探测结论一致)。
交付物清单 35 项全部存在 (missing=0)。

### 14.13 证据包 (MD5 绑定)

| 引用 | 路径 | 大小 | MD5 |
|------|------|------|-----|
| V87-03 监控守护 (**版本锁定未改**) | `v87_03_monitor_service.py` | 27,012B | **e2f0d4ccd65eea44f56578c33bec27fe** |
| VIS 告警导出接口 (**版本锁定未改**) | `vis_alert_export_api.py` | 40,226B | **474ff0aea6692d5e912553aa03e736d4** |
| 门禁脚本 (未改) | `phase2_gate_check_script.py` | 19,953B | 32c6403f5c66efd72ceb1d16d2a06f55 |
| 周期门禁台账 (**161 行**, 本轮 +33) | `gate_periodic_check_log.csv` | 33,586B | 30be8d668cff765ce0731cb8ec493f96 |
| 缺陷回归脚本 (T0) | `gate_prep_lab/p12_defect_regression.py` | 12,308B | 3b5901694a58435441d29ef8757b6583 |
| 缺陷回归结果 (18/18) | `gate_prep_lab/defect_regression_p12.json` | 3,519B | cddc6afbc0d2ca3b0c61426e5e4ff174 |
| 通道探测脚本 (T3-a) | `gate_prep_lab/p12_channel_probe.py` | 12,064B | fcc8b667070048fc6b71649baec32d51 |
| 通道断连告警台账 (P12, 3 行) | `gate_prep_lab/dshc_channel_disconnect_ledger_p12.csv` | 3,432B | 97d7e1e3884599a494e719b87d7ce6c6 |
| MD5 复核脚本 (T5, 卷分类版) | `gate_prep_lab/p12_md5_recheck.py` | 21,601B | 43ac576a18a591d8a28fbd6bb44d2f4f |
| MD5 复核台账 (P12, 4 行) | `gate_prep_lab/p12_md5_recheck_ledger.csv` | 697B | ec5c76c540ba8f8a5b7de2d64760b973 |
| MD5 复核清单快照 (35 项) | `gate_prep_lab/p12_md5_recheck_inventory.json` | 19,564B | ca891f718d38d1921e1b017948d7cea1 |
| PC-003 全链路自检脚本 | `gate_prep_lab/p12_post_unlock_selfcheck.py` | 10,282B | 3bd34d057da4e9c037cba6c71d414c63 |
| PC-003 全链路自检结果 (40/40) | `gate_prep_lab/pc003_post_unlock_selfcheck_p12.json` | 3,222B | dee99fef55bb51283b3a5c5f34cc0400 |
| FAIL 推送链验证脚本 | `gate_prep_lab/p12_fail_push_verify.py` | 8,781B | 73e61383fe044301cfccab4a68cc8063 |
| FAIL 推送链验证结果 (21/21) | `gate_prep_lab/vis_fail_push_verify_p12.json` | 2,319B | c4eec578d2dde4ade5703d0a1795a653 |
| PC-003 DSHC 事件 (BLOCKED 真实路径) | `gate_prep_lab/pc003_dshc_event_p12.json` | 1,509B | 6518a84aa77de60bf9fc3eb6c60d8d64 |
| PC-003 DSHC 事件 (ACTIVATED lab 正路径) | `gate_prep_lab/pc003_dshc_event_unlocked_p12.json` | 1,376B | cf8dd1f6caf5f7ce3aa5c31b1a62fcaf |
| PC-003 BLOCKED 清单 (Phase12) | `gate_prep_lab/pc003_activation_manifest_p12.json` | 7,802B | 2715314cba4ed831d1e2ae2ac9bc37aa |
| PC-003 ACTIVATED 清单 (Phase12 lab) | `gate_prep_lab/pc003_activation_manifest_p12_labpos.json` | 7,396B | d4219612445289cd69fd08ce008bc2a1 |
| VIS 告警导出 P12 (json, 193 告警) | `gate_prep_lab/vis_alert_export_p12.json` | 200,057B | e2466256d7b5edf20b262ea273acdc1e |
| VIS 时序聚合 P12 (9 markers) | `gate_prep_lab/vis_alert_timeline_p12.json` | 6,081B | bc1517f15ccbd6b076951e4d7612971c |
| VIS 校验报告 P12 | `gate_prep_lab/vis_alert_validate_p12.json` | 1,757B | 10c2ee42bdf823253a6dd5f5b42e9da7 |
| VIS 回归报告 P12 (3/3) | `gate_prep_lab/vis_alert_regression_p12.json` | 2,614B | e96af2455f6b044a1bb37596094566a4 |
| VIS-001 联调包 P12 (render 11/11) | `gate_prep_lab/vis_001_integration_p12.json` | 139,417B | 36bf831b2edf68b583443e5a414de5f6 |
| Phase12 事件卷 (**非确定性测试卷**, clean-room 重建) | `gate_prep_lab/v87_03_event_store_p12/vol_0001.csv` | 1,859B | 132887a7ba6b2ede38c3df71630fb3f0 |
| Phase12 卷 manifest (可再生) | `gate_prep_lab/v87_03_event_store_p12/manifest.json` | 277B | 918e687a50de5c5680de004977d1977e |
| **Phase9 事件卷 (签收后冻结, 未变)** | `gate_prep_lab/v87_03_event_store_p9/vol_0001.csv` | 1,859B | **a057fe35b03d2e72b230a3778e084730** |
| **Phase7 冻结卷 (append-only 未变)** | `gate_prep_lab/v87_03_event_store/vol_0001.csv` | 1,856B | **dffb56e7ae4678e1ebd4f7659b20beb0** |
| **Phase7 冻结卷 manifest (未变)** | `gate_prep_lab/v87_03_event_store/manifest.json` | 277B | **551b09d938b90c08cb41ebeeddd6eee4** |
| Phase9 VIS 导出 (**未变**, P12 单独出 `_p12`) | `gate_prep_lab/vis_alert_export.json` | 165,715B | **3f7736c0b3b489e36e7e62f701341be0** |
| Phase9 VIS-001 联调包 (**未变**) | `gate_prep_lab/vis_001_integration.json` | 115,452B | **27f872a198b7a761ec55fc251338c02f** |
| Phase9 通道台账 (**未变**, P12 单独出 `_p12`) | `gate_prep_lab/dshc_channel_disconnect_ledger.csv` | 2,684B | **b2066ea131113f9d72e0a42526656b29** |
| FR-RISK 映射 (上游只读未变) | `fr_risk_501_508_mapping.json` | 5,759B | 41efa5a041de70446a0732665a4d42f6 |
| 事件接收日志 (上游只读未变, 27 行) | `fr_risk_receive_log.csv` | 8,895B | fe1e3c51959cac4d95c6f5e7aa518d23 |
| 事件 schema (上游只读未变) | `event_schema.json` | 3,491B | 09c7a4e8df53aca7dd1d861abaa10ccc |
| 预留槽位配置 (上游只读未变) | `phase4_reserved_slots_config.json` | 4,392B | acb5c9fb80ce513dc45916e3c3b21742 |
| Phase9 汇总报告 (冻结归档未变) | `phase9_gate_summary_report.md` | 22,640B | aa0ab9fef7703e90074d49b6fbea1a5d |
| Phase9 门禁就绪旗标 (冻结归档未变) | `PHASE9_GATE_RUN_READY.flag` | 20,956B | b37c0c2f9a338d6a1b23bfcdb7872579 |

**append-only 复核结论**: 上游只读 17 项 md5 全部与 Phase7 基线一致 (零改动);
历史基线 17 项全部匹配, 含 Phase7 冻结卷 `dffb56e7`/`551b09d9`、Phase9 冻结卷 `a057fe35`、
Phase9 VIS 导出 `3f7736c0`/`27f872a1`/`b2066ea1` 三项 (P12 另出 `_p12` 命名产物, 未覆盖);
版本锁定文件 `v87_03_monitor_service.py` `e2f0d4cc` / `vis_alert_export_api.py` `474ff0ae` /
`phase2_gate_check_script.py` `32c6403f` 三项**本轮零改动**。
`gate_periodic_check_log.csv` 由 26,683B → 33,586B (+6,903B, 33 行 append-only, 历史 128 行字节未变)。
本工单未改写任何上游历史字节。

### 14.14 遗留跟踪 + 移交主循环

| 项 | 状态 | 推进 |
|----|------|------|
| V87-03 daemon | **STABLE** (P12 复验 selftest 6/6 + integtest chain OK + patrol 37/37 @ 0.11s) | 生产部署 (真实事件源) |
| DEFECT-P9-001 / P9-002 | **回归通过 18/18, 无复现** | 建议主循环确认缺陷登记入库并关闭 |
| Phase12 门禁巡检 | **7 PASS / 4 PENDING / 0 FAIL** (33 行全 NO_CHANGE) | 数据就位自动转 PASS |
| VIS 告警导出接口 | **ONLINE** (193 告警 + 9 markers + 27 字段 + 校验 PASS + color_action_align 32/32) | 接入 DSHA 可视化工作台时序图 |
| VIS-001 联调 | **VERIFIED** (render_check 11/11 + 悬浮弹窗溯源 + 9 序列 193 点) | 主循环签发工作台对接 |
| PC-003 双门禁 | **READY** (BLOCKED 合规 + ACTIVATED 可达 + 全链路 40/40 + audit_id 无冲突) | DSHC 在 TD002+TD014 达标后推送 |
| ZN/NI/SN/SI 槽位 | **RESERVED 4/4 + LOCKED 4/4** (GATE-P2-11 PASS) | 主循环签发解锁 |
| GATE-P2-01/02/03/04 | PENDING_DATA (TD002 数据/白名单/巡检闭合/转发 7 日窗) | 数据就位自动转 PASS |
| DSHC 转发通道 | **IDLE_NO_INBOUND, CRITICAL/P0 自动升级** (四阶段 0 入站, 3 轮告警已入账) | 真实快照数据接入后复探 |
| J21 联网核验 | PENDING_ONLINE (网关额度类, 本轮未重试) | 主循环 |
| PHASE11_DONE + PHASE12_FACTOR_APPROVE.flag | **全部 PRESENT** (`c7229070` / `1f1fae65`) | - |
| 事件卷锚点分类 | **3 类卷 anchor/chain/tail 全 OK** (确定性归档 vs 非确定性测试卷首次固化区分) | - |

**主循环移交累计清单 (Phase9 + Phase12 合并, 去重)**:

1. TD002 真实数据就位 (REAL_TREE / WHITELIST / 罚金计算规则验证) — 最高优先级, 4 项 PENDING 与通道 IDLE 的共同根因;
2. TD014 SI 解冻条件 (硬门禁 + CONDITIONAL_APPROVAL 签发);
3. V87-03 生产部署 (真实事件源, 非 lab 卷);
4. V87-04 真实回放 + 20 日窗口 + 映射/触发器回写;
5. J21 联网复核 (网关额度恢复后);
6. ZN/NI/SN/SI RESERVED→ACTIVE (主循环签发解锁);
7. **DSHA VIS-001 工作台对接签发** (render_check 11/11 已满足对接条件);
8. **DSHC 真实前向通道建立** (本轮 3 次 CRITICAL/P0 自动升级告警已记录, 通道侧无阻塞证据);
9. **DEFECT-P9-001 / P9-002 缺陷登记入库并关闭** (双修已生效, P12 回归 18/18 无复现)。
