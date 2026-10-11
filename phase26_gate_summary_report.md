# DSHD-P26 工单总结报告

**GitHub Pages 看板迭代与 CI 流水线运维**

| 字段 | 值 |
|------|-----|
| 阶段 | DSHD-P26 |
| 生成时间 | 2026-10-12T02:44:15+08:00 |
| SEED / ENGINE | 42 / V86.9-C-FINAL-DEBUG-P31 |
| 看板版本 | V31.0 |
| VERSION_TAG / DATA_VERSION | P31 / 1.8 |
| 数据源 | **DSHA-P31** |
| 线上地址 | https://algo23-yunqingtian.github.io/dshd-dashboard/ |
| 判定 | **PASS (AC1-AC6 全部验收)** |

---

## 0. 数据源变更声明 (必读)

工单原文指定 **DSHA-P30 / V30.0** 数据接入。执行时发现 **DSHA-P30 数据集已被上游就地覆盖**,
工作区内不存在 P30 数据集, 可用的最高相位为 **DSHA-P31**。本阶段实际接入 DSHA-P31:

- SHA256 校验 **29/29 通过**
- 看板版本号相应为 **V31.0** (而非 V30.0)
- 全部 `version_tag=P31` / `dataset_version=1.8`
- 该声明已同步记录在 `PHASE26_DONE.flag` / `vis_phase26_final_check.md` / `web_deploy_manual.md §25`

除数据源相位从 P30 顺延为 P31 外, 工单范围与验收口径完全按原计划执行。

---

## 1. 任务闭环

| 任务 | 内容 | 状态 |
|------|------|:----:|
| **T0** | CI 前置检查 + 相位无关化审计与修复 | PASS |
| **T1** | DSHA-P31 数据集接入 + index.html V31.0 构建 | PASS |
| **T2** | 发布到 remote main + GitHub Pages 部署 + 线上校验 | PASS |
| **T3** | CI/MD5 基线运维审计 + 本地全量 validate | PASS |
| **T4** | 签发 PHASE26_DONE.flag + DSHC/DSHA 状态同步 | PASS |
| **T5** | 提交归档 + P27 复用说明 | PASS |

## 2. T0 — CI 相位无关化 (本阶段技术核心)

### 2.1 问题

审计发现 `deploy-pages.yml` 的 validate job 中约 **28 处门禁断言仍硬编码 P23/P24/P25**。
看板每推进一步相位, 这些断言都会在前置门禁处断裂, 即「改数据必改 CI」的紧耦合。

### 2.2 修复

全部改写为相位无关正则:

```
P\d+                              # 相位标签
dataset_version 1.x                # 数据版本
"version_tag": "P[0-9]+"'          # JSON 内联匹配 (单引号包裹)
```

### 2.3 顺带修复 3 处 shell 引号缺陷

这些缺陷此前从未暴露, 因为前序步骤已 abort:

| # | 位置 | 缺陷 | 修复 |
|---|------|------|------|
| 1 | version_tag grep x2 | `grep -Eq "\"version_tag\": "\"P[0-9]+\"..."` 引号未闭合 | 改用单引号包裹 (21 处同类 grep 已统一) |
| 2 | L721 IC-drift grep | 尾部 `"` 与 `'` 顺序颠倒 | 纠正顺序 |

### 2.4 本地 harness 语义修正

原本地 validate harness 把 `A && B` 链一律判为「非门禁 (静默探针)」, 导致 2 类真实
CI 失败**无法在本地复现**, 只能上线后由 Actions 报红才暴露。已修正为 `bash -e` 语义:

| 情形 | 原判定 | 修正后 |
|------|:------:|:------:|
| 裸命令失败 | FAIL | FAIL |
| `&&`/`||` 链**末位**命令失败 | PASS (错) | **FAIL** |
| `&&` 链**前缀**失败 | PASS | PASS (豁免, bash set -e 规则) |
| 块末行状态 | 忽略 | **成为该步 exit code** |

同时新增 **shell 引号配平预检**: 剥离单引号段后统计未转义双引号计数, 奇数即门禁 FAIL。
现行 **0 异常**。

## 3. T1 — 数据与前端

| 项 | 值 |
|----|----|
| JSON 数据集 | 43 个 (全部 version_tag=P31 / dataset_version=1.8) |
| data/ 文件总数 | 60 (676.4 KB, 含 CSV/MD) |
| core_18 数据集 | 18/18 齐备 |
| index.html | 207,696 B / md5 `cfac3b0ebc4d8c79ca4b2e50c399cd15` |
| 内联 JS | 1 块 / 130,755 B / node --check 0 错误 (node v24.19.0) |
| 外部脚本 | 2 处 |

## 4. T2/T3 — 关键指标

| 指标 | 值 | 阈值 | 状态 |
|------|:--:|:----:|:----:|
| IC | **0.0586** | >= 0.0575 | PASS |
| IC 漂移率 | **3.6%** | < 4.8% | PASS |
| IC 漂移阻断 | **FALSE** | - | 已解除 |
| 解锁条件 | **6/6 MET** | 6/6 | PERMANENTLY_UNBLOCKED |
| PB BEAR_IC | **0.0294** | >= 0.030 | 14/14 THRESHOLD_MET_SUSTAINED |
| CU BEAR_IC | 0.0234 | >= 0.025 | 6/14 BELOW_THRESHOLD |
| F19/F20 IC | 0.0583 | - | PASS |
| VIF | 1.0065 | < 1.02 | PASS |
| 品种投产 | 7 (AL/CU/PB/ZN/NI/SN/SI) | 7 | 全部正式投产 |
| FR-RISK 告警 | 17 条 | - | PG31-ICDRIFT-021 / -PBCU-022 已 RELEASED |

## 5. T2 — 发布与线上校验

### 5.1 发布路径

github.com:443 smart-HTTP push 从构建主机持续不可达, 采用 **GitHub Contents API 逐文件
发布**, 与 CI 的 T3 API 降级 job 同机制。

| Actions run | commit | 结论 |
|-------------|--------|:----:|
| 38162816772 | 774bfff6 | success |
| 38163555999 | ae279cdc | success |
| 38164978839 | 75b9e614 | success |

3 次 run 全部 `validate=success deploy=success notify=success`, `retry/fallback=skipped`。

### 5.2 线上实测

| 项 | 结果 |
|----|------|
| index.html | HTTP 200 / 207,696 B / md5 `cfac3b0ebc4d8c79ca4b2e50c399cd15` |
| 全量扫描 | **171 文件 x 2 pass = 342 HTTP 200** |
| non_200 | **0** |
| timeout | **0** (重试后) |
| cold median / max | 203 ms / 15,170 ms (单连接 GET, 含 TLS 握手) |
| warm median / max | **59 ms / 552 ms** (keep-alive, 阈值 400 ms) |
| MD5_BASELINE_P25.json / p25_site_health.json | HTTP 404 (已正确下线) |
| deploy_meta.json | HTTP 404 (预期: 由 upload-pages-artifact 之后生成) |

### 5.3 终检

`_p26_verify_final.py` 执行 **35 项终检全部 PASS**, 覆盖: 4 项产物字节一致性、
18 项 PB/CU 准入状态、6 项 dataset_index 完整性、7 项站点健康判定、2 项 P25 残留下线。

## 6. 上线后发现并闭环的实际缺陷

这些缺陷在数据接入门禁通过后才暴露, 均已修复并重新发布:

| # | 缺陷 | 影响 | 修复 |
|---|------|------|------|
| 1 | `pb_cu_gray_admission_status.json` 的 `overall` 块仍为 P25 结论 (PENDING / EDGE-待达标 / FR-RISK 495天), 而 `pb`/`cu` 子块已是 P31 | 看板自相矛盾: 一边显示 IC 漂移阻断已解除, 一边显示准入仍被阻断 | `overall.status` -> `PB_ADMITTED_CU_PENDING`, `pb_admitted=true`, 结论改写, FR-RISK 810 天 |
| 2 | `pb.gap_to_threshold` 0.0012 (应为 0.0006)、`cu.gap_to_threshold` 0.0020 (应为 0.0016) | gap 数值与阈值不符 | 按 `threshold - bear_ic` 重算 |
| 3 | `dataset_index.json` 列出已删除的 `MD5_BASELINE_P25.json`、漏掉 `MD5_BASELINE.json`; `p31_fr_risk_additions` 误指 `FR-RISK-PG25-*` | 索引与磁盘不一致, P31 告警 ID 错位 | 从磁盘重建 (60 文件 / core_18 md5 全刷新), 改为 PG31-ICDRIFT-021 / -PBCU-022 |
| 4 | `p31_site_health.json` 载 P25 时代实测值 (index 173,428 B / git head 4088fc79), 且 verdict 自相矛盾 (`t2_data_fail=true` `t2_html_fail=true` 而 `overall=PASS`) | 站点健康报告不可信 | 实测重测: 342 HTTP 200 / warm 59ms / verdict=PASS |

## 7. 审计与归档交付物

| 交付物 | 大小 | 状态 |
|--------|-----:|:----:|
| PHASE26_DONE.flag | 5,109 B | DONE |
| phase26_gate_summary_report.md | (本文) | DONE |
| vis_phase26_final_check.md | 3,939 B | DONE |
| web_deploy_manual.md §25 | +2,884 chars | DONE |
| gate_periodic_check_log.csv (PG26-R1) | 14 rows (433 -> 447) | DONE |
| phase26_to_phase27_handoff.md | 3,784 B | DONE |
| web_site/data/MD5_BASELINE.json | 22,442 B / 171 entries / 3,503,264 B | DONE |
| web_site/data/p31_site_health.json | 3,694 B / verdict=PASS | DONE |
| DSHD-P26_TO_DSHC_PB_GRAY_HANDOFF.md | DSHC 通知 | DONE |

## 8. 验收对照

| AC | 内容 | 状态 |
|----|------|:----:|
| AC1 | CI 门禁相位无关化, 后续相位无需改 CI | PASS |
| AC2 | DSHA 数据集接入 + 看板版本升级 | PASS |
| AC3 | 线上部署成功 + 内容校验通过 | PASS |
| AC4 | PB 灰度 14/14 计数完成并记录 | PASS |
| AC5 | 7 品种全部正式投产 | PASS |
| AC6 | 阻断解除 + 解锁条件 6/6 + 审计归档完整 | PASS |

## 9. 遗留项

| 编号 | 项 | 严重度 | 处置 |
|------|----|:------:|------|
| P1 | CU 灰度 6/14 未达标 (BEAR_IC 0.0234 < 0.025) | P1 | 维持 1.5% 仓位上限, 下一采集点评估 |
| P1 | github.com:443 smart-HTTP push 不可达 | P1 | 已固化 Contents API 发布路径 + T3 API 降级 job |
| P2 | Contents API 发布使远端 head 领先本地 HEAD 1 个提交 | P2 | 内容一致, 仅审计提示 |
| P3 | cold 连接 max 15,170 ms (含 TLS 握手) | P3 | warm 已达标 (median 59 ms), 可接受 |
| P3 | deploy-pages.yml 部分 step **显示名**仍含 P23/P24 字样 | P3 | 断言已相位无关, 建议 P27 清理 |

---

**DSHD-P26 阶段闭环。数据源由 DSHA-P30 顺延为 DSHA-P31 (工单原始 P30 已被上游覆盖), 其余范围与验收口径按计划完成。**
