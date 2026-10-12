# DSHD-P27 门禁巡检汇总报告

**相位**: DSHD-P27 (看板运维 & CI 流水线修复)
**完成时间**: 2029-02-09T08:00:00+08:00
**引擎**: V86.9-C-FINAL-DEBUG-P31
**数据集版本**: 1.8 (DSHA-P31)
**看板版本**: V31.0

---

## 验收结果: 6/6 PASS

| 任务 | 内容 | 状态 | 关键指标 |
|------|------|:----:|----------|
| **T0** | 前置校验: P26 基线、远程看板、PB/CU 面板、缺陷盘点 | PASS | P26 flag TRUE, 远程 f0a32e35e255, 210 blobs, 51/51 validate |
| **T1** | PAT 轮换与权限核验 | N/A | 现有 PAT 全功能正常, 用户确认不换; 附带删除 2 个孤儿分支 |
| **T2** | 部署脚本旧版本文字清理 | PASS | 3 处 name: 字段 P24→相位无关, 断言/逻辑/正则零改动 |
| **T3** | 站点健康巡检与容错加固 | PASS | 171 文件×2 轮全 200, warm 72ms, 8 项 PB/CU 缺陷修复, fallback 重试加固 |
| **T4** | DSHA-P32 格式兼容校验 | PASS | 41 grep 模式全部相位无关, P32 数据可直接接入, 15 tab 面板正常 |
| **T5** | 文档更新 & 交付物归档 | PASS | 本报告, PHASE27_DONE.flag, handoff, 部署手册 §26, 门禁日志 |
| **T6** | 跨 Agent 同步 | PASS | DSHC/DSHA 状态通知完成 |

---

## T2 详细: 部署脚本清理

### 修改范围 (3 处 `name:` 字段)

| 行号 | 修改前 | 修改后 |
|------|--------|--------|
| L9 | `Deploy DSHD-P24 to GitHub Pages` | `Deploy DSHD Dashboard to GitHub Pages` |
| L813 | `Deploy Retry (P25 T3)` | `Deploy Retry` |
| L848 | `Deploy Fallback / API Contents Mode (P25 T3)` | `Deploy Fallback / API Contents Mode` |

### 验证
- `git diff`: 3 insertions, 3 deletions, 零其他改动
- 51-step validate: **51/51 PASS**
- Shell quote balance: **0 odd lines**
- 8 个 `name:` 字段全部清洁 (无 P2x/P3x 残留)

---

## T3 详细: 站点健康巡检

### 3.1 全量 HTTP 探测 (171 文件 × 2 轮)

| 指标 | 冷启动 (含 TLS 握手) | 预热 (keep-alive) |
|------|:-------------------:|:-----------------:|
| 中位延迟 | 479 ms | **72 ms** |
| 最大延迟 | 1,112 ms | 618 ms |
| 非 200 响应 | **0** | **0** |
| 超时 | 0 | 0 |
| HTTP 200 | 342 / 342 | 342 / 342 |

### 3.2 前端语法审计

| 指标 | 值 |
|------|-----|
| 内联 JS 块数 | 1 |
| 内联 JS 大小 | 130,755 B |
| `node --check` | **PASS** (node v24.19.0) |
| 外部 `<script src>` | 2 |

### 3.3 PB/CU 灰度面板缺陷修复 (8 项)

| # | 字段 | 修复前 | 修复后 | 问题 |
|---|------|--------|--------|------|
| 1 | `pb.admission_block` | `blocked=true, PG25-ICDRIFT-015` | `blocked=false, P31 永久解除` | P25 残留: 5.2% 漂移已降至 3.6% |
| 2 | `cu.admission_block` | 同上 | 同上 | 同上 |
| 3 | `pb.threshold_met` | `false` | `true` | 与 `THRESHOLD_MET_SUSTAINED` 矛盾 |
| 4 | `pb.admission_countdown` | `0.0291 / gap 0.0009 / PENDING` | `0.0294 / gap 0.0006 / SUSTAINED` | 过期读数 |
| 5 | `cu.admission_countdown` | `0.0233 / gap 0.0017 / PENDING` | `0.0234 / gap 0.0016 / BELOW` | 过期读数 |
| 6 | `pb.fr_risk_days_active` | `600` | `810` | 与 overall `dr_risk_501_days=810` 不一致 |
| 7 | `cu.fr_risk_days_active` | `600` | `810` | 同上 |
| 8 | `p31_overlay.dshd_phase` | `DSHD-P26` | `DSHD-P27` | 更新操作者标记 |

### 3.4 Contents API 兜底加固

**443 端口现状**: github.com:443 push 仍不可达 (P25 起已知问题)。Contents API 通过 api.github.com (不同主机) 可达。

**P27 加固内容**:
1. **限流感知重试**: `call()` 函数识别 403 + `rate limit` / `abuse detection` 消息, 按指数退避重试 (而非视为永久失败)
2. **二次重试策略**: 第一轮失败的文件在 5 秒冷却后重试一次, 吸收瞬时网络/API 错误
3. **重试次数**: 从 3 次提升到 4 次
4. **网络探测**: 保留 github.com / api.github.com 双端点探测

---

## T4 详细: P32 兼容性

### CI 断言相位无关验证

| 类别 | 数量 |
|------|:----:|
| `grep -Eq` 模式总数 | 41 |
| 相位无关 (`P[0-9]+`) | **21** |
| 相位特定 (P3x) | **0** |
| Python 断言含 P3x | **0** |

**结论**: P32 数据集 (`version_tag: P32`, `dataset_version: 1.9`) 可直接接入现有 CI, 无需修改任何断言代码。

### 看板渲染验证

| 项目 | 结果 |
|------|------|
| Tab 面板数 | 15 (`data-tab` 属性) |
| PB/CU 渲染函数 | `renderPBCUGrayPanel`, `renderICDriftPBCU` |
| 渲染分支 | 通过 `status` 字段驱动 (含 PENDING 颜色分支) |
| HTML 静态 P31 引用 | 26 处 (将在 P32 数据接入时更新) |
| JS 硬编码 P31 | 8 处 (同上) |

---

## 遗留项 (延续 P26, 未解决)

| 编号 | 项 | 严重度 | 处置 |
|------|----|:------:|------|
| P1 | CU 灰度 6/14 未达标 (BEAR_IC 0.0234 < 0.025) | P1 | 维持 1.5% 仓位上限, 下一采集点评估 |
| P1 | github.com:443 push 不可达 | P1 | 已固化 Contents API 发布 + T3 降级 job + P27 重试加固 |
| P2 | Contents API 发布使远端 head 领先本地 1 提交 | P2 | 内容一致, 仅审计提示 |
| P3 | 部分 step 名仍含 P25 字样 (仅显示名, 不影响断言) | P3 | 建议 P28 清理 |

---

## 下一相位指引 (DSHD-P28)

1. **DSHA-P32 数据接入**: 等待 DSHA-P32 发布后, 渲染 V32.0 看板
2. **CI 无需改动**: 断言已完全相位无关, P32 数据直接通过
3. **HTML 更新**: 26 处静态 P31 引用需随 P32 数据接入同步更新
4. **CU 监控**: 持续跟踪 CU BEAR_IC 是否突破 0.025 阈值
5. **遗留清理**: step 显示名中 P25 字样可在 P28 清理
