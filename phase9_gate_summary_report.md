# Phase9 门禁运行 + 告警归档 + VIS 联调 汇总报告

| Property | Value |
|----------|-------|
| JOB_ID | DSHD-P9-AL-PB-CU-GATE-MONITOR-VIS-ALERT-ARCHIVE |
| Phase | PHASE9_GATE-RUN (常驻守护巡检 + Phase9 门禁周期巡检 + FR-RISK 告警分级/导出/VIS-001 联调 + PC-003 双门禁监听 + DSHC 通道连通性 + 全量 MD5 复核) |
| Fixed Slot (门禁巡检) | 2026-10-25T14:30 / 14:45 / 15:00 (PG9-R1/R2/R3) |
| Fixed Slot (VIS 导出) | 2026-10-25T16:30:00+08:00 |
| Fixed Slot (签收旗标) | 2026-10-25T17:00:00+08:00 |
| Seed | 42 |
| Dependency | PHASE7_GATE_RUN_READY.flag (aec5a274..., VERIFIED) + PHASE8_DONE.flag (c2f33b17..., VERIFIED) + PHASE9_FACTOR_APPROVE.flag (218e7759..., VERIFIED) + PHASE9_DONE.flag (f3789766..., VERIFIED) |
| Authority | DSHD P9 门禁运行 + 告警归档 + VIS 接口联调 |

---

## 1. P0-1 Phase9 门禁周期巡检

`phase2_gate_check_script.py --periodic PG9-R{1,2,3}`，每轮 11 门禁 = **33 行**追加至 `gate_periodic_check_log.csv`。

| 轮次 | 槽位 | PASS | PENDING | FAIL | status_change |
|------|------|------|---------|------|---------------|
| PG9-R1 | 2026-10-25T14:30:00+08:00 | 7 | 4 | 0 | 11/11 NO_CHANGE |
| PG9-R2 | 2026-10-25T14:45:00+08:00 | 7 | 4 | 0 | 11/11 NO_CHANGE |
| PG9-R3 | 2026-10-25T15:00:00+08:00 | 7 | 4 | 0 | 11/11 NO_CHANGE |
| **合计** | | **21** | **12** | **0** | **33/33 NO_CHANGE** |

- **PASS (7)**: GATE-P2-05 CHAIN_4_4 / 06 VOLUME_ROTATION / 07 REAL_REPLAY / 08 FROZEN_RECHECK /
  09 J21_RECHECK / 10 PERF / 11 RESERVED_SLOTS;
- **PENDING (4, 已知数据依赖, 非缺陷)**:
  - GATE-P2-01 REAL_TREE — AL/CU/PB 真实快照树 ABSENT (TD002 数据未接入);
  - GATE-P2-02 WHITELIST — TD002 数据依赖;
  - GATE-P2-03 PATROL_3D — 巡检 3 日轮次未集齐;
  - GATE-P2-04 FR_RISK_7D — 真实转发通道 7 日 0 丢失未验证;
- **FAIL (0)** → **未触发 GATE-P2-BLOCKED**, 推送链待命中;
- 台账: `gate_periodic_check_log.csv` **128 行** (26,683B / 45b58c81...),
  Phase3/4/7/9 四阶段累计。

## 2. P0-2 V87-03 常驻 Daemon 值守复验

`v87_03_monitor_service.py` (27,012B / e2f0d4cc...)

| 模式 | 结果 |
|------|------|
| `--mode selftest` | **6/6 PASS** (U1 schema / U2 501→ORANGE / U3 升级 2 次→RED STOP_LINE / U4 502→STOP_LINE / U5 evidence http: 拒绝 / U6 VOL_LIMIT=1000) |
| `--mode integtest` | **PASS** stored=5, recover_ok=True, chain=OK, tail_ok=True, stop_line=FR-RISK-501,FR-RISK-504,FR-RISK-508 |
| `--mode recover` (Phase7 冻结卷, 只读) | **ok=True** vols=1 rows=5 chain=OK tail_ok=True |
| `--mode patrol` | **37 项全 PASS**, elapsed=0.08s (<60s J14), run_id=c694f4bba84f / 70652be60be8 |
| `--mode pc003` | 见 §8 |

- patrol 明细: AL/CU/PB 各 CHECK-1 CONTRACT_SIZE (ref=mult5 size5, bad=0) /
  CHECK-2 LIMIT 双轨 A normal+ext (CU 6.0/9.0, PB 5.0/8.0, dual_track_ok=True) /
  CHECK-3 POSITION_PATH (pos_positive=1, roll_error=0);
- **调度延迟**: 37 项 0.08s, 满足 J14 <60s 约束;
- **Phase9 独立卷**: `gate_prep_lab/v87_03_event_store_p9/` (5 行),
  与 Phase7 冻结卷物理隔离 (clean-room), 不触碰冻结字节。

## 3. P0-3 全量 MD5 独立复核 + 上游零改动

`gate_prep_lab/p9_md5_recheck.py` (15,480B / 2e69e78b...), 每轮一行 append-only 台账。

| 轮次 | 上游 | 基线 | 卷链 | 接收日志 | 通道台账 | 交付物 | verdict | record_md5 |
|------|------|------|------|----------|----------|--------|---------|------------|
| PG9-R1 | 17/17 | 7/7 | OK | OK | OK | 24 | **PASS** | 67942da6... |
| PG9-R2 | 17/17 | 7/7 | OK | OK | OK | 24 | **PASS** | 79623cbe... |
| PG9-R3 | 17/17 | 7/7 | OK | OK | OK | 24 | **PASS** | 73ff85d6... |
| PG9-FINAL | 17/17 | 7/7 | OK | OK | OK | 26 | **PASS** | 2b025669... |

- 4 轮全部 verdict=PASS (PG9-R1/R2/R3 巡检轮 + PG9-FINAL 签收轮);

- **上游只读 17/17 零改动**: 映射 41efa5a0 / 触发器 8c43a487 / td002_prep e4ba415e / td014 f77bcde8 /
  j21_recheck c236a0f3 / 规格清单 d8df79a0 / 门禁规格 88803c9d / 校准报告 3b74c1ca /
  再校准规格 b8699329 / 回放清单 1103a800 / 设计书 c6d27056 / 门禁结果 c9d06c9c /
  持仓模块 ecf8e33c / 锚点 5ce88d0e / 灰度配置 25668191 / PHASE3_READY 12c22e49 / PHASE2_READY fcd25d33;
- **历史审计基线 7/7**: Phase7 冻结卷 dffb56e7 + manifest 551b09d9 / 接收日志 fe1e3c51 (27 行,
  首行 FWD-501-001, 末行 P4-504-001) / schema 09c7a4e8 / 槽位配置 acb5c9fb / C 实表 d9d64fea +
  卷 record_md5 链 (anchor=V87-03-CHAIN-ANCHOR, 5/5 OK, tail_ok=True);
- **台账 md5 链自洽**: 4 行 record_md5 = md5(prev|round|slot|计数|verdict) 逐行独立复核 OK
  (67942da6 → 79623cbe → 73ff85d6 → 2b025669), append-only 只增不改;
- **C 实表口径澄清**: 本目录无该文件, 实际位于
  `github工作\回测\factor_exp_workspace\dshc_adaptor_ops_prep\v869_c_multi_comm_prep_syn\v869c_3way_risk_code_mapping.csv`
  (19,516B / d9d64fea...), 27 数据行不变。

### 3.1 历史笔记不可复现项 (如实披露)

早期笔记中的"接收日志历史 24 行 md5=92096cd1"**无法用任何标准重算口径复现**
(已验证 7 种: CRLF join / joinLF / 含表头 / rstrip 变体 ± EOL / 全 27 行, 均不匹配)。
该数值已弃用, 不做断言; 全文件 md5=fe1e3c51 已完整覆盖前 24 行字节, 为可核验基线。

## 4. P1-1 FR-RISK 告警分级/升级/导出

- **告警总数 160**, 时序桶 7, schema_ref=`DSHD-PHASE3-UNIFIED-EVENT-SCHEMA-1-REV1`;
- **字段数 27/27 稳定** (`field_stable=True`);
- 颜色分布: GRAY 80 / ORANGE 61 / RED 14 / YELLOW 5;
- 动作分布 (修复后): STOP_LINE **14** / NOTIFY_1H 13 / RECORD_4H 5 / PASS 80 / HOLD 48; **RECORD = 0 (键消失)**;
- 升级: `escalation_count=14`, `stop_line_count=14`, 升级链 5 族 (FR-RISK-501/502/503/504/508);
- 三端域校验 `verdict=PASS`: risk_id 域 (FR-RISK-501..508 + GATE-P2-01..11) /
  severity 域 (CRITICAL/HIGH/MEDIUM/LOW/INFO/WARN) / action 域 (STOP_LINE/NOTIFY_1H/NOTIFY_2H/
  RECORD_4H/RECORD/PASS/HOLD/BLOCK) **全部 PASS**, `color_action_align=32/32`;
- 三格式输出 (json/jsonl/csv) 均 160 alerts / 7 markers, **CRLF=0 / CR 字节=0**,
  jsonl 逐行解析 160/160, csv 27 列宽一致。

## 5. P1-2 可视化告警导出接口 + VIS-001 联调

`vis_alert_export_api.py` (40,226B / 474ff0ae...), 模式 `export/timeline/validate/all/regression/vis001/full`。

### 5.1 DSHA VIS-001 可视化工作台时序模块

`gate_prep_lab/vis_001_integration.json` (115,452B / 27f872a1...)

- `chart`: 时序模块 (timeseries risk markers), x=`bucket (YYYYMMDD-HH)`,
  y=`max_level (0=NONE 1=YELLOW 2=ORANGE 3=RED)`, **series 7 点 / tooltip 7 条 / 点总数 160**;
- **悬浮弹窗事件溯源**: 每桶 `popup_title` + `level` + `stop_line` + `escalated` + `items[]`,
  每项 15 字段 (`alert_id / risk_id / risk_family / symbol / severity / color / action / status /
  fixed_slot / round_no / event_id / fwd_id / upstream_ref / evidence_path / evidence_md5`);
- **render_check 11/11 全 True**: axis_monotonic / series_marker_aligned / tooltip_bucket_aligned /
  every_point_has_backing_event / level_domain_ok / color_domain_ok / severity_domain_ok /
  action_domain_ok / evidence_md5_all_32hex / hover_traceability_ok / popup_level_consistent;
- 峰值桶 `2026-10-25-16`: count=32, level=3, stop_line=14, escalated=14,
  colors={ORANGE:13, RED:14, YELLOW:5}, risk_ids 全 8 族, symbols={AL,ALL,CU,PB,ZN}, items=32。

### 5.2 FAIL 门禁 → 告警推送链 (P0-2 硬要求)

- 推送目标固化 `FAIL_PUSH_TARGETS = ["DSHA:VIS-001", "DSHC:DUTY", "GATE-P2-BLOCKED"]`;
- **语义边界**: 仅 `FAIL → BLOCK → P0 推送`; `PENDING → HOLD` 不进推送链 (已知数据依赖非缺陷);
  `PASS → 静默`;
- 当前 0 FAIL → `push.fail_alert_count=0`, 链路待命中;
- **可达性验证** (`gate_prep_lab/p9_fail_push_verify.py`, 21/21 checks PASS):
  lab 合成 fixture (1 FAIL + 1 PASS + 1 PENDING), monkeypatch `GATE_LOG` 指向 fixture, 运行后还原;
  推送 1 条 `PUSH-FAIL-VIS-GATE-2026102514-GATE-P2-05` (severity=CRITICAL / color=RED /
  action=BLOCK / priority=P0 / 3 目标全含 / evidence 32hex);
  `pending_not_pushed=True` / `pass_not_pushed=True` / `pushed_count_is_1=True`;
  **零改写**: `real_gate_log_md5_unchanged=True` (45b58c81 前后一致), fixture 用后删除。

### 5.3 边界异常回归 (P1-4, 持续回归不引入新缺陷)

`gate_prep_lab/vis_alert_regression.json` — **verdict=PASS (3/3)**

| 用例 | 覆盖点 | 结果 |
|------|--------|------|
| R1-CRLF | Windows 文本模式写盘字节精确性 (cr_byte_absent / crlf_absent / lf_count_match / size_match / md5_match, 5 项) | **PASS** |
| R2-RISKFAMILY | `risk_family` 不得 `code.split("-")[1]` 切片 (防 FR-RISK-501→"RISK"); 27 条全为 'FR-RISK' | **PASS** |
| R3-SLA_ACTION | 颜色映射 + sla_h 不覆盖颜色 + 颜色优先于冲突 raw + 未知 raw 归一 + `red_fr_alerts_all_STOP_LINE` (14/14) + **`daemon_RED_branch_present` 源码级断言** | **PASS (16 项)** |

- R1 探针写盘后 `os.unlink` 清理, 不污染交付目录。

## 6. P2 PC-003 双门禁监听 + 4 品种锁控

**Phase9 事件 fixture** (新槽位, 与 Phase7 历史 fixture 分离):
- `pc003_dshc_event_p9.json` (1,503B / da9c80e0...) — 真实语义,
  upstream_ref 引用 `DSHA:PHASE9_FACTOR_APPROVE(218e7759)`;
- `pc003_dshc_event_unlocked_p9.json` (1,375B / 95d43e9e...) — **LAB POSITIVE-PATH PROOF**,
  note 字段明确标注"假设路径, 非真实推送"。

| 路径 | verdict | gates_verified | activated | locks |
|------|---------|----------------|-----------|-------|
| P2-1 BLOCKED (真实语义) | **BLOCKED** | False | - (0/4) | LOCKED 4/4 |
| P2-2/3 ACTIVATED (lab 正路径) | **ACTIVATED** | True | ZN,NI,SN,SI (4/4) | LOCKED 4/4 |

- BLOCKED: TD002 BLOCKED / TD014 BLOCKED; ZN/NI/SN missing=TD002,TD014,REAL_DATA_INGESTION;
  SI 额外 missing CONDITIONAL_APPROVAL; `blocked_reason` 非空;
- ACTIVATED: 4 品种 current=RESERVED → target=ACTIVE, template=8 项全加载, missing=-;
- 8 项模板: CONTRACT_RECHECK / FROZEN_RECHECK / FR_RISK_7D / PATROL_3D / PERF / REAL_REPLAY /
  REAL_TREE / WHITELIST;
- **全链路回归自检** `pc003_post_unlock_selfcheck.json` — **40/40 PASS**:
  BLOCKED_PATH 14/14 + ACTIVATED_PATH 16/16 + UPSTREAM_IMMUTABILITY 10/10;
- **上游不可变**: 激活为"建议态", `phase4_reserved_slots_config.json` 仍 4/4 RESERVED + 8 项模板不变
  (acb5c9fb...), 无上游改写;
- **锁控**: ZN c5da7491 / NI d214d54f / SN 3086e197 / SI fa9da924 版本锁 4/4 LOCKED,
  `locked_syms=[NI,SI,SN,ZN]` (GATE-P2-11 PASS);
- **lab 正路径 fixture 每轮可达性**: PASS。

## 7. P3-1 J21 合约规格联网核验 (第 6 次重试)

- `web_search` → **Insufficient Balance (request d48139de-7702-4826-b64a-da06933332dc)**;
- **失败分类 6/6 网关额度类 (gateway quota), 0/6 业务查询错误**:
  - 错误串恒定 `Insufficient Balance`, 仅 request_id 变化;
  - 跨 4 工单 6 次, 查询语句多次变换 (官方规格书 / 公告 / 具体品种参数) 结果一致;
  - 返回 request_id 但**无任何结果 URL/片段** → 请求在网关计费阶段即被拒, 未进入检索执行阶段,
    故不可能返回业务级错误 (无结果/语法错误/超时);
- **不阻断主流程**: GATE-P2-09 判定依据为三重来源复核结论而非在线检索结果, 门禁持续 PASS
  (累计 10 轮实证);
- PENDING_ONLINE=RETAINED (第 6 次保留), SEALED 生效值不变;
- 台账 `j21_contract_final_recheck_record.md` (10,315B / 19b02a0a...): §1 尝试表 +1 行,
  §3 分类依据追加, §4 次数同步, §8 重试日志第 6 行, §9 Phase9 续记。

## 8. P3-2 DSHC 转发通道连通性探测 + 断连告警台账

`gate_prep_lab/p9_channel_probe.py` (9,034B / 75821760...)

- 通道定义: `fr_risk_receive_log.csv` 入站事件写入流; 活性判定 = 阶段窗内是否产生新行;
- **3 轮全部 IDLE_NO_INBOUND**: Phase4 最后入站 2026-10-12T14:46:00+08:00 以来 **0 新增**,
  跨 Phase7+Phase9 两阶段, `rows_since_phase4=0`;
- **分类: 数据源未就位, 非链路故障** (TD002 PENDING_DATA_VERIFICATION,
  GATE-P2-01 REAL_TREE=PENDING);
- 断连告警台账 `dshc_channel_disconnect_ledger.csv` (2,684B / b2066ea1..., 3 行 append-only, CRLF=0):
  每轮 `ALERT-CHANNEL-IDLE-<slot>`, severity=WARN, priority=P1,
  targets=`DSHA:VIS-001;DSHC:DUTY;DSHD:MONITOR`; record_md5 链 61db16b9 / 3ea5f49c / 39830545。

### 8.1 依赖完整满足 (更正工单 J 记录)

| 依赖 | 大小 | MD5 | 状态 |
|------|------|-----|------|
| PHASE8_DONE.flag | 14,949B | c2f33b17c32e... | **PRESENT** (COMPLETED) |
| PHASE9_FACTOR_APPROVE.flag | 14,955B | 218e7759939d... | **PRESENT** (APPROVED_WITH_CONDITIONS, ACCEPTANCE 12/12) |
| **PHASE9_DONE.flag** | 15,039B | **f3789766b206...** | **PRESENT** (STATUS=COMPLETED, PRECHECK 15/15, LAUNCH_FLOW 13 步全 PASS) |
| PHASE7_GATE_RUN_READY.flag | 13,885B | aec5a274cfaa... | **PRESENT** |

> **更正**: 工单 J 记录 `PHASE9_DONE.flag` 全盘 0 命中。本工单重新全盘 glob 命中 1 处
> (`github工作\回测\factor_exp_workspace\dshc_adaptor_ops_prep\v869_gray_launch_plan\`),
> 早前 0 命中系首次探测仅检索 DSHD 主树所致, 非依赖未产出。现 4 项依赖**全部满足**。

## 9. 新发现并修复的缺陷

| 缺陷 | 发现途径 | 根因 | 修复 | 验证 |
|------|----------|------|------|------|
| **DEFECT-P9-001** | R3 回归 `red_fr_alerts_all_STOP_LINE=False` (14 条 RED 中 1 条不符) | daemon `map_event` 分支**缺失 `color=="RED"` 显式分支**; FR-RISK-508 的 `escalation_rule='缺失+探针泄漏同发 -> CRITICAL (升级触发)'` 不含"直接 STOP_LINE"字面 → 落 `else → RECORD`, 与 RED/CRITICAL 语义冲突。502/503 因含该字面量侥幸正确, 缺陷被掩盖至 Phase9 暴露 | **双修**: ①daemon `map_event` 在 ORANGE 前插入 `elif color=="RED": action="STOP_LINE"` (附溯源注释); ②导出层 `canon_action` 改**颜色优先** (不改动上游只读事件卷字节) | selftest 6/6; Phase9 卷 FR-RISK-508→STOP_LINE, STOP_LINE 行 code={501,504,508}; chain=OK; Phase7 冻结卷字节不变; **action: 13 STOP_LINE+1 RECORD → 14 STOP_LINE+0 RECORD**; escalation/stop_line 13→14 |
| **DEFECT-P9-002** | P2 全链路自检 `manifest_audit_ids_distinct=False` | pc003 `audit_id = "PC-003-LISTEN-" + slot[:12]`, 同槽位两次运行 (BLOCKED + labpos ACTIVATED) 产生**相同 audit_id**, 审计清单不可区分 | `audit_id` 追加 dshc event_id 尾部 12 位 | 两份清单 audit_id 已区分 (`-20261025-001` / `-20261025-002`); 自检 UPSTREAM_IMMUTABILITY 10/10 |

## 10. 验收结论 (6/6)

| # | 验收项 | 证据 | 结论 |
|---|--------|------|------|
| 1 | Daemon 常驻 + 单元集成全绿 + 卷链完整 | selftest 6/6 PASS; integtest stored=5 chain=OK tail_ok=True; recover ok=True vols=1 rows=5 chain=OK tail_ok=True; patrol 37 项全 PASS 0.08s | **PASS** |
| 2 | Phase9 巡检稳定 + GATE-P2 台账 + FAIL 触发告警 | PG9-R1~R3 33 行, 7 PASS/4 PENDING/**0 FAIL**, 全 NO_CHANGE; 台账 128 行 45b58c81; FAIL 推送链 21/21 checks PASS (P0, 3 目标, PENDING 不进链) | **PASS** |
| 3 | FR-RISK 分级升级导出正常 + VIS-001 接入 + 三端对齐 | 160 alerts/7 markers/27 字段; verdict=PASS; color_action_align 32/32; 三端域全 PASS; VIS-001 render_check **11/11 全 True** + 悬浮弹窗 15 字段溯源 | **PASS** |
| 4 | PC003 双门禁 BLOCKED/ACTIVATED 双路径 + 锁控 | BLOCKED (真实) + ACTIVATED (lab 正路径) 双 verdict; 锁控 4/4 LOCKED; 模板 8/8; **全链路自检 40/40 PASS**; 上游槽位配置字节不变 | **PASS** |
| 5 | append-only + MD5 独立复核 + 上游零改动 | 上游 **17/17 零改动**; 历史基线 **7/7** (含 Phase7 冻结卷 dffb56e7 恒定); 卷链 5/5 anchor/tail OK; 接收日志 fe1e3c51 27 行; 4 轮台账 md5 链自洽 (67942da6→79623cbe→73ff85d6→2b025669) | **PASS** |
| 6 | 全部交付物 MD5 自洽 + flag 可被 DSHC/DSHA 读取校验 | 交付物 **26 项** md5 清单 (inventory JSON, 4/4 轮 verdict=PASS); 2 项缺陷已修复并回归通过; lab 归档包 MD5 独立复核 | **PASS** |

**总体验收: 6/6 PASS**

## 11. 交付物清单

### 11.1 主交付物

| # | 交付物 | 大小 | MD5 |
|---|--------|------|-----|
| 1 | `gate_periodic_check_log.csv` (128 行) | 26,683B | 45b58c81f72fee849f19a3359b975476 |
| 2 | `fr_risk_alert_archive.md` (§13 Phase9 续记) | 37,723B | 096e2d909f590962ed1e6737d822e945 |
| 3 | `vis_alert_export_api.py` (含 R1~R3 + vis001 + FAIL 推送) | 40,226B | 474ff0aea6692d5e912553aa03e736d4 |
| 4 | `v87_03_monitor_service.py` (含 DEFECT-P9-001/002 修复) | 27,012B | e2f0d4ccd65eea44f56578c33bec27fe |
| 5 | `phase9_gate_summary_report.md` (本文) | - | (本文) |
| 6 | `PHASE9_GATE_RUN_READY.flag` (签收) | - | (签收旗标) |
| 7 | `j21_contract_final_recheck_record.md` (§9 Phase9) | 10,315B | 19b02a0a6badcc0f47fefa6cf0bb1ebc |
| 8 | lab 归档包 (`gate_prep_lab/`, 见 §11.2) | - | 见 inventory |

### 11.2 lab 归档 (gate_prep_lab/)

| 交付物 | 大小 | MD5 |
|--------|------|-----|
| `vis_alert_export.json` | 165,715B | 3f7736c0b3b489e36e7e62f701341be0 |
| `vis_alert_export.jsonl` | 126,337B | 320754085b86a1c1646e247694cbef0f |
| `vis_alert_export.csv` | 60,428B | 58c37c1a0c176ccf9e15e77b41def82a |
| `vis_alert_timeline.json` | 4,718B | 6c9d634c56cd770333e416b99c9d8eae |
| `vis_alert_validate.json` | 1,757B | b2cc271e24fa78c10ceffb5b4f51ab61 |
| `vis_alert_regression.json` | 2,614B | 5ad444b26cddc300f775b481032d660a |
| `vis_001_integration.json` | 115,452B | 27f872a198b7a761ec55fc251338c02f |
| `vis_fail_push_verify.json` | 2,317B | ed99f24496c3a15cd37f5bcd9aea1cf6 |
| `pc003_activation_manifest_p9.json` (BLOCKED) | 7,798B | 01cb09d6047fa12500300b7a4ffddfdf |
| `pc003_activation_manifest_p9_labpos.json` (ACTIVATED) | 7,394B | a50f28b085017e718916d7073dfc879b |
| `pc003_post_unlock_selfcheck.json` (40/40) | 3,219B | e4cf06b01b3ea256a3cbabfb70645e33 |
| `dshc_channel_disconnect_ledger.csv` (3 行) | 2,684B | b2066ea131113f9d72e0a42526656b29 |
| `p9_md5_recheck_ledger.csv` (**4 行 append-only, md5 链 67942da6→79623cbe→73ff85d6→2b025669, 链自洽复核 OK**; 文件 md5 随时点变化, 以链值为准) | - | (链值为准) |
| `p9_md5_recheck_inventory.json` (**清单快照, 4/4 轮 verdict=PASS**; 上游 17/17 + 基线 7/7 + 交付物 26 项; 为时点快照, 以内部 verdict/counts 为准) | - | (快照为准) |
| `p9_channel_probe.py` | 9,034B | 758217601ce076b0ae9d1b8fd2485384 |
| `p9_md5_recheck.py` | 15,480B | 2e69e78b69245af130a94d5241c5b957 |
| `p9_post_unlock_selfcheck.py` | 10,270B | cec4566b47593eae0a3775a914446a7b |
| `p9_fail_push_verify.py` | 8,767B | 097e17fbca3c78a217ba28f6d555ae8f |
| `v87_03_event_store_p9/vol_0001.csv` (**可再生测试卷**) | 1,859B | a057fe35b03d2e72b230a3778e084730 |
| `v87_03_event_store_p9/manifest.json` (**可再生**) | 277B | 8193ed08c6d032eac2bb435bf79394f8 |
| `v87_03_event_store/vol_0001.csv` (**Phase7 冻结, append-only**) | 1,856B | dffb56e7ae4678e1ebd4f7659b20beb0 |
| `v87_03_event_store/manifest.json` (**Phase7 冻结**) | 277B | 551b09d938b90c08cb41ebeeddd6eee4 |

### 11.3 Phase9 事件卷可再生性说明

`v87_03_event_store_p9/` 为 `--mode integtest` 的 clean-room 测试卷, 每次运行按当前槽位时间戳
重新生成, **md5 非确定性** (仅行数 5 / 字节 1,859 / manifest 277 稳定, chain=OK / tail_ok=True
恒定)。该卷**不参与任何下游导出** (VIS 导出数据源为 Phase7 冻结卷), 故其 md5 变化不构成
交付物漂移。Phase7 冻结卷 `v87_03_event_store/` 才是 append-only 审计基线, 全工单字节恒定。

## 12. 移交主循环

| 项 | 状态 | 推进 |
|----|------|------|
| V87-03 daemon | **STABLE** (值守复验全绿 + DEFECT-P9-001/002 已修) | 生产部署 (真实事件源) |
| Phase9 门禁巡检 | **7 PASS / 4 PENDING / 0 FAIL** (33 行全 NO_CHANGE) | 数据就位自动转 PASS |
| VIS 告警导出接口 | **ONLINE** (160 告警 + 7 markers + 27 字段 + 校验 PASS + 三格式) | 接入 DSHA 可视化工作台时序图 |
| VIS-001 联调 | **VERIFIED** (render_check 11/11 + 悬浮弹窗溯源 + FAIL 推送链 21/21) | 主循环签发工作台对接 |
| PC-003 双门禁 | **READY** (BLOCKED 合规 + ACTIVATED 可达 + 全链路 40/40) | DSHC 在 TD002+TD014 达标后推送 |
| ZN/NI/SN/SI 槽位 | **RESERVED 4/4 + LOCKED 4/4** (GATE-P2-11 PASS) | 主循环签发解锁 |
| J21 联网核验 | PENDING_ONLINE (第 6 次 Insufficient Balance, 网关额度类) | 主循环 |
| GATE-P2-01/02/03/04 | PENDING_DATA (TD002 数据/巡检轮次/转发通道) | 数据就位自动转 PASS |
| DSHC 转发通道 | **IDLE_NO_INBOUND** (Phase4 以来 0 新增, 3 轮断连告警已入账) | 真实快照数据接入后复探 |
| PHASE8/9_DONE + PHASE9_FACTOR_APPROVE.flag | **全部 PRESENT** (f3789766 / c2f33b17 / 218e7759) | - |
| **DEFECT-P9-001 / P9-002** | **已双修并回归通过** | 建议主循环确认缺陷登记入库 |

## 13. 局限与已知状态 (诚实披露)

1. **联网不可用**: `web_search` 累计 6 次 Insufficient Balance (网关额度类), J21 官方原文核验仍
   不可执行, PENDING_ONLINE=RETAINED。降级三重来源复核 (SHFE 公开标准知识 + V86.7DF 30 样本实证 +
   C 实表 DRI-001 交叉验证) 结论稳定, SEALED 生效值不变。
2. **真实快照数据未就位**: GATE-P2-01/02 PENDING (TD002 数据依赖), 非链路或代码缺陷。
3. **DSHC 真实转发通道未连通**: Phase4 最后入站 2026-10-12T14:46:00+08:00 以来 0 新增,
   GATE-P2-04 PENDING; 断连已按 P1 级告警入账, 属数据源未就位而非链路故障。
4. **PC-003 ACTIVATED 路径为 lab 正路径证明**: 双门禁全 VERIFIED 仅用于证明解锁链路可达性与
   ACTIVATED 判定分支, **不代表 DSHC 真实推送**。真实解锁需 TD002+TD014 数据实际达标并由
   DSHC 正式推送。当前真实状态为 BLOCKED, 4 品种保持 RESERVED + LOCKED 4/4。
5. **巡检 3 日轮次未集齐**: GATE-P2-03 PATROL_3D PENDING, 需累计 3 个巡检日。
6. **Phase9 事件卷 md5 非确定性**: 见 §11.3, 系 integtest clean-room 语义, 不参与下游导出。
7. **历史笔记不可复现项**: "接收日志历史 24 行 md5=92096cd1" 已弃用, 见 §3.1。
8. **早期 0 命中更正**: 工单 J 的 `PHASE9_DONE.flag` 0 命中系探测范围仅及 DSHD 主树,
   非依赖未产出, 见 §8.1。
9. **ZW/NI/SN/SI 版本锁只读**: ZN c5da7491 / NI d214d54f / SN 3086e197 / SI fa9da924
   (LOCKED=TRUE & NO_OVERWRITE), 本工单未触碰。
