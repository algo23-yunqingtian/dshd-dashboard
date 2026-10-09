# Phase1 灰度监控值守总结（Phase1 Monitor Runtime Summary）

| Property | Value |
|----------|-------|
| **JOB_ID** | DSHD-P0-AL-CU-PB-GRAY-PHASE1-MONITOR-RUNTIME |
| **JOB_READY** | TRUE |
| **Fixed Slot** | 2026-10-10T05:30:00+08:00 |
| **SEED** | 42 |
| **前置依赖** | AL_CU_PB_MONITOR_GATE_READY.flag（5d343933…，只读）+ j15_drill_report.md + alcupb_contract_spec_final_manifest.md（本工单） |
| **Phase** | Phase1 灰度运行期（AL/CU/PB ACTIVE；ZN/NI/SN/SI FROZEN） |

---

## 0. 值守总览

| 指标 | 值 |
|------|-----|
| 巡检轮次（本工单实测） | 2 轮（P1-0001 / P1-0002） |
| 每轮检查项 | 37 项（基线篡改/mtime/权限/目录探针/头寸/跨端差异） |
| 检查结果 | 74/74 PASS（0 FAIL，0 告警——正常值守状态） |
| 头寸在线校验 | AL/CU/PB real PASS×3；注入 K11 偏离/头寸缺失 → FAIL rc=1 CRITICAL×2 |
| J15 实弹演练 | 8 事件全链路通过（RED×2 停线 / ORANGE×2 / YELLOW×2 / 升级链×2） |
| CHAIN-001-REPAIRED-1 | 4/4 完全匹配（多轮复检） |
| 冻结品种 | ZN/NI/SN/SI 仅只读完整性（LOCK/RO 全 PASS），0 投产告警 |
| 审计日志 | 巡检 74 行 + 告警 8 行 + 头寸审计 30 行，全部 append-only（R6） |

---

## 1. P0 灰度运行期值守

### 1.1 ME-01~ME-06 全套探针持续运行

| 增强项 | Phase1 运行状态 |
|--------|-----------------|
| ME-01 create 探针 | 9 树（AL/CU/PB × Live/RO/入站）写-删-验原子，**0 残留**（巡检实证） |
| ME-02 SI 状态机 | 不适用（SI 冻结；AL/CU/PB 历史充足走标准容差） |
| ME-03 滚动 IC | AL/CU/PB 3 年窗配置就绪（灰度数据累积后启用采样） |
| ME-04 卷式轮转 | 活动卷 0001（`v869_d_alcupb_gray_alarm_log.csv` / `_patrol_result.csv`）；达 1000 条切卷 + 旧卷 RO 锁定 |
| ME-05 跨机路线 | P0 回执协议就绪（灰度数据接入后启用回执新鲜度检查） |
| ME-06 差异绑定 | 7 项登记生效（K11/K12/25vs27/A 评级/C-DEV/PnL/CHAIN-001） |

### 1.2 头寸校验（在线）

- `position_verify_alcupb_module.py` real 模式：AL/CU/PB 灰度正样本 **PASS×3**（规格 0 误差 + 头寸>0 + 0 移仓错误）。
- 故障注入实证：AL K11 偏离（F39=3）→ `ALARM-R04-K11-*` CRITICAL（STOP_LINE）；CU 头寸>0 缺失 → `ALARM-POS-*` CRITICAL（STOP_LINE）。审计日志只追加。

### 1.3 CHAIN-001 持续维护 + 卷式轮转

- CHAIN-001-REPAIRED-1 4/4 复检 PASS（bbf887d0/3156d823/1df98028/c359ab98）。
- 日志卷：活动卷 0001 当前行数（告警 8 / 巡检 74 / 头寸审计 30），未达 1000 切卷阈值；切卷规则（旧卷 RO + 卷清单 manifest 入链）随 ME-04 生效。

### 1.4 ZN/NI/SN/SI 冻结

- 投产触发器禁用状态复核：JSON disabled_trigger_groups 8 组生效；版本锁 LOCKED=TRUE + NO_OVERWRITE 全 PASS；RO 金标只读抽查 8/8。
- **0 投产类告警**（保留仅只读完整性检查）。

---

## 2. P1 高优先级一次性任务

### 2.1 J15 实弹演练 ✅（详见 j15_drill_report.md）

RED/ORANGE/YELLOW 三级注入 + 升级链（YELLOW×3→ORANGE、ORANGE+LEAK→RED）+ 停线逻辑全部实测通过；8 事件告警日志只追加。

### 2.2 J21 合约规格复核固化 ✅（详见 alcupb_contract_spec_final_manifest.md）

AL/CU/PB K11/K12 参数 **SEALED（FINAL）**：AL 5 吨×5、±5/±8；CU 5 吨×5、±6/±9；PB 5 吨×5、±5/±8。PRE-SEALED_PENDING_RECHECK 标记移除（历史值归档，生效值以 final manifest 为准）；复核局限诚实披露（官方原文在线检索受限，基于公开标准 + 体系实证交叉验证）。

### 2.3 J22 25/27 双源对账统一 ✅

| 数据源 | 行数 | 内容 |
|--------|------|------|
| C 实表（d9d64fea） | **27** | DRI-001..011 + ALIGN-001..012 + SCHED-001..004 |
| A-SYN 映射 | **39** | FR-RISK 20 条 + TD 19 条（风险编码映射层） |
| C flag 注记口径 | 25 | 4 CRITICAL / 7 HIGH / 12 MEDIUM / 4 LOW（严重度汇总） |

**统一结论**：
1. **D 侧巡检以 C 实表 27 行为载入基准**（巡检 RISK_CODE_27 = 27 PASS 实证）。
2. A-SYN 39 行为 A-C 风险编码映射层（FR-RISK/TD 编码族 ↔ DRI/ALIGN/SCHED 无冲突，分类 DATA/PIPELINE/ALIGNMENT/SCHEDULE 对齐）。
3. 25 vs 27 差异 = **注记口径（严重度汇总）vs 实表行数（编码明细）**，非数据缺陷；25 项注记保留为工单口径，27 行实表为数据基准。
4. 台账续记：本工单对账结论已追加（历史台账 J22 行不改写）；主循环 A-SYN（64f64110）+ C 实表（d9d64fea）双源对账统一后基线更新。

---

## 3. P2 长期预留

### 3.1 TD002/TD014 扩展入口（维护中）

| 技术债 | 状态 | 启用门 |
|--------|------|--------|
| TD002（金属影子数据） | RESERVED_ENTRY | AL/CU/PB 真实数据就位 → 白名单切换（已就绪）+ 规格已固化 → 完整监控启用 |
| TD014（SI 数据不足） | RESERVED_ENTRY | SI 数据扩充至标准窗口 → 解除 FROZEN → SI 专项（ME-02）启用 |

> AL/CU/PB 的 K11/K12 规格已在本工单固化（SEALED），TD002 数据就位后可**快速启用**（探针 9 树已配置、头寸校验已实证、审计链路已就绪）。

### 3.2 V87 架构迭代排期（持续推进）

| 阶段 | 任务 | 状态 |
|------|------|------|
| V86.9 灰度前置 | P-01/P-02/P-04/P-05/P-06/P-08 + P-07 | ✅ 本工单 J15 演练（P-08）完成 |
| V86.9-R2 | P-09/P-10 + ME-03/04/05-P0 + V87-05 试点 | Phase1 后 |
| V87.0 | V87-01/02/03/**04**/07 | V87-04 待灰度真实数据（TD002） |
| V87.1+ | V87-05 全量 / 06 / 08 | 后续 |

---

## 4. 审计日志与不可变性

| 日志 | 行数 | 模式 | 卷状态 |
|------|------|------|--------|
| v869_d_alcupb_gray_patrol_result.csv | 74 | append-only | 活动卷 0001（<1000） |
| v869_d_alcupb_gray_alarm_log.csv | 8 | append-only | 活动卷 0001 |
| position_verify_audit_log_alcupb.csv | 30 | append-only | 活动卷 0001 |
| position_verify_result_alcupb.csv | 30 | append-only | 活动卷 0001 |

> 全部记录含 record_md5；卷式轮转（1000 条/卷 + 旧卷 RO + 卷清单 manifest 入链）随 ME-04 生效；禁止覆盖/修改历史行（R6）。

---

## 5. 验收对照

| 验收标准 | 达成证据 |
|----------|----------|
| ✅ 灰度期间基线、头寸、目录探针告警正常触发，审计日志只追加 | 巡检 74/74 PASS；头寸注入 FAIL rc=1 CRITICAL×2（RED 实证）；探针 0 残留；日志 append-only + record_md5 |
| ✅ J15 实弹演练全链路验证通过 | 8 事件全通过（RED/ORANGE/YELLOW + 升级链 + 停线），j15_drill_report.md |
| ✅ AL/CU/PB 合约规格完成复核固化，移除待复核标记 | SEALED（FINAL），alcupb_contract_spec_final_manifest.md |
| ✅ ZN/NI/SN/SI 投产通道持续冻结 | 8 组触发器禁用；LOCK/RO 全 PASS；0 投产告警 |

---

## 6. 证据绑定

| 引用 | 路径 | 说明 |
|------|------|------|
| 巡检脚本 | v869_d_gray_patrol.py | 37 项/轮 |
| 巡检结果 | v869_d_alcupb_gray_patrol_result.csv | 74 行（P1-0001/0002） |
| 演练报告 | j15_drill_report.md | 8 事件全通过 |
| 规格固化清单 | alcupb_contract_spec_final_manifest.md | SEALED |
| 头寸模块/审计 | position_verify_alcupb_module.py + _audit_log_alcupb.csv | 自测 6/6 + 在线实证 |
| CHAIN 修复基线 | ch001_repair_baseline\ch001_repair_baseline_manifest.md5 | 4/4 复检 |
| 告警规则 | v868_d_baseline_monitor\v868_d_alarm_rule_config.md | 分级/升级表（只读） |
| C 实表 / A-SYN | v869c_3way_risk_code_mapping.csv / v869a_ad_risk_code_mapping.csv | 27 行 / 39 行（只读） |

---

Generated by DSHD | JOB_ID DSHD-P0-AL-CU-PB-GRAY-PHASE1-MONITOR-RUNTIME | 2026-10-10T05:30:00+08:00 | SEED=42
