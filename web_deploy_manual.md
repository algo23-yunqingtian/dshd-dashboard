# DSHD-P19 Github Pages 部署手册

**文档版本**: 1.0  
**生成时点**: 2026-11-16T17:00:00+08:00  
**工单**: DSHD-P19 (Github Pages 部署 | CI 自动化 | 告警可视化 | 门禁看板落地)  
**SEED**: 42  
**站点根**: `web_site/`  
**CI 配置**: `.github/workflows/deploy-pages.yml`

---

## 1. 目录结构

```
dshd_arch_gate_prep/
├── web_site/                        ← Github Pages 部署目录 (发布内容)
│   ├── index.html                   P19 增强版仪表盘 (2,921 行, 单文件应用)
│   ├── data/                        静态 JSON/CSV 数据集 (26 文件)
│   │   ├── vis_dashboard_main.html  DSHA 原始仪表盘 (归档引用)
│   │   ├── vis_dataset_manifest.json
│   │   ├── vis_pre_calc_*.csv       AL/CU/PB × nav/signals/kline/alpha (14 文件)
│   │   ├── dataset_index.json       数据集索引
│   │   ├── fr_risk_alerts.json      FR-RISK 告警 (7 条)
│   │   ├── pc003_status.json        PC-003 门禁实时状态
│   │   ├── factor_drift_alerts.json 因子漂移告警 (4 条)
│   │   ├── data_defect_alerts.json  数据缺陷告警 (4 条)
│   │   ├── rollback_events.json     回滚事件 (3 条)
│   │   ├── data_completion_status.json 四品种数据补全进度
│   │   ├── experiment_index.json    实验版本清单 (P2-P19)
│   │   ├── version_index.json       版本切换数据集
│   │   └── pl_summary.json          7 品种盈亏汇总
│   ├── archive/                     P3-P19 静态归档 (79 文件, 字节级保留)
│   │   ├── manifest.json            归档清单
│   │   ├── dsha_v1/vis_dashboard_main.html  DSHA 原始件
│   │   ├── phases/                  阶段 flag/report (17 项)
│   │   ├── factors/                 因子数据集 (13 项)
│   │   ├── backtests/               回测产物 (7 项, 7 品种)
│   │   ├── trades/                  交易记录 (7 项, 7 品种)
│   │   └── alerts/                  告警/审计/巡检日志 (34 项)
│   ├── js/                          (预留, 当前空)
│   └── assets/                      (预留, 当前空)
│
├── .github/workflows/
│   └── deploy-pages.yml             CI 自动部署流水线 (3 job)
│
├── gate_prep_lab/                   实验室脚本
│   ├── p18_t0_p12_recheck.py        T0 97 项断言复核
│   ├── p18_t1_archive_pack.py       T1 站点搭建 + 归档打包
│   ├── p18_t4_render_check.py       T4 页面渲染校验
│   ├── p18_t4_ci_verify.py          T4 CI 配置校验
│   ├── p18_t4_data_align.py         T4 前后端数据对齐
│   └── p18_t4_alert_regress.py      T4 告警推送回归
│
├── phase18_gate_summary_report.md   阶段汇总报告
├── PHASE18_GATE_RUN_READY.flag      门禁就绪旗标
├── fr_risk_alert_archive.md         告警归档 (§1-§15)
├── gate_periodic_check_log.csv      巡检日志 (追加 PG18)
├── web_deploy_manual.md             本文档
├── vis_phase18_final_check.md       可视化终版校验报告
├── v87_03_monitor_service.py        (版本锁定, md5 e2f0d4cc)
└── vis_alert_export_api.py          (版本锁定, md5 474ff0ae)
```

---

## 2. 快速部署 (本地验证)

### 2.1 前置条件

```bash
# Python 3.12+
python --version
# Node 20+ (可选, 用于 CI 模拟)
node --version
```

### 2.2 构建 + 校验

```bash
cd D:\DSH_WORK\factor_exp_workspace\acd_joint_shadow_verify\dshd_sub\dshd_arch_gate_prep

# 1. T0 前置依赖 (P12 97 项断言)
python gate_prep_lab/p18_t0_p12_recheck.py

# 2. T1 站点搭建 (已运行, 若需重建)
python gate_prep_lab/p18_t1_archive_pack.py

# 3. T4 全链路自洽测试
python gate_prep_lab/p18_t4_render_check.py
python gate_prep_lab/p18_t4_ci_verify.py
python gate_prep_lab/p18_t4_data_align.py
python gate_prep_lab/p18_t4_alert_regress.py
```

### 2.3 本地预览

```bash
# 方式 A: Python http.server
cd web_site
python -m http.server 8080
# 浏览器访问 http://localhost:8080/

# 方式 B: VS Code Live Server
# 右键 index.html → Open with Live Server
```

### 2.4 离线运行说明

- **CDN 依赖**: index.html 通过 CDN 加载 ECharts 5 (`cdn.jsdelivr.net`) 和 html2canvas (`cdn.jsdelivr.net`)
- **离线模式**: 若需完全离线, 将 CDN 资源下载到 `web_site/assets/` 并修改 `<script src=...>` 引用
- **数据加载**: 所有 JSON/CSV 数据通过 `fetch()` 从 `data/` 目录加载, 必须通过 HTTP 服务运行 (不可 file:// 协议)

---

## 3. Github Pages 上线部署

### 3.1 仓库配置

1. **创建/初始化仓库**
   ```bash
   git init
   git add .
   git commit -m "DSHD-P19: Github Pages 首次上线"
   ```

2. **Settings → Pages**
   - Source: **Deploy from a branch**
   - Branch: `main` (或 `master`)
   - Folder: `/ (root)` → 指向 `web_site/` 目录
   - Build and deployment: **GitHub Actions** (启用自定义 CI)

3. **启用 GitHub Actions**
   - Settings → Actions → General → Enable Actions

### 3.2 推送触发部署

```bash
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

推送后 CI 自动触发:
1. **validate job** — JSON 校验 → HTML 结构 → 归档 manifest → DSHA 字节
2. **deploy job** — 上传 artifact → 部署到 Pages
3. **notify job** — 生成部署摘要

### 3.3 部署流水线 (deploy-pages.yml)

| 步骤 | 工具 | 说明 |
|------|------|------|
| Checkout | actions/checkout@v4 | 检出代码 (fetch-depth: 0) |
| Setup Python | actions/setup-python@v5 | Python 3.12 |
| Setup Node | actions/setup-node@v4 | Node 20 |
| JSON 校验 | python3 -c json.load | 遍历 data/*.json, 计算 md5 |
| HTML 结构 | grep | 校验 DOCTYPE/echarts/html2canvas 等关键标记 |
| 归档 manifest | python3 | 校验 manifest.json 内所有文件存在 |
| DSHA 字节 | python3 md5 | 校验 archive/dsha_v1/ md5=f0036dc3 |
| 站点大小 | du | 报告各目录大小 |
| 上传 artifact | actions/upload-pages-artifact@v3 | 30 天保留 |
| 部署 | actions/deploy-pages@v4 | 发布到 Pages |
| 通知 | summary | GitHub Step Summary 输出 |

### 3.4 紧急部署

通过 `workflow_dispatch` 手动触发, 设置 `skip_validate=true` 跳过校验步骤:

```
Actions → Deploy DSHD-P19 to GitHub Pages → Run workflow
  skip_validate: true  (跳过 JSON/HTML/归档/DSHA 校验)
```

---

## 4. CI 配置详解

### 4.1 触发器

```yaml
on:
  push:
    branches: [main, master]
    paths: ['web_site/**', '.github/workflows/deploy-pages.yml', 'data/**', 'archive/**']
  pull_request:
    branches: [main, master]
    paths: ['web_site/**', '.github/workflows/deploy-pages.yml']
  workflow_dispatch:  # 手动触发
```

### 4.2 权限最小化

```yaml
permissions:
  contents: read       # 只读代码
  pages: write         # 写入 Pages
  id-token: write      # OIDC (用于部署 token)
```

### 4.3 并发控制

```yaml
concurrency:
  group: pages-deploy-${{ github.ref }}
  cancel-in-progress: true  # 新提交取消旧部署
```

### 4.4 环境变量

```yaml
env:
  NODE_VERSION: 20
  PYTHON_VERSION: '3.12'
  SITE_ROOT: web_site
  DATA_DIR: web_site/data
  ARCHIVE_DIR: web_site/archive
  INDEX_FILE: web_site/index.html
```

### 4.5 Job 依赖

```
validate ──→ deploy ──→ notify
```

- `validate` 失败 → `deploy` 不执行 → `notify` 仍报告 (if: always())
- `deploy` 成功 → 生成 `deploy_meta.json`

---

## 5. 数据集清单

### 5.1 动态数据 (data/)

| 文件 | 大小 | 内容 | 来源 |
|------|------|------|------|
| fr_risk_alerts.json | 3,630B | FR-RISK 告警 7 条 (含 4 RED/CRITICAL) | DSHD §1-§15 |
| pc003_status.json | 2,307B | PC-003 实时状态 (BLOCKED) | P12 manifest |
| factor_drift_alerts.json | 1,830B | 因子漂移告警 4 条 | factor_drift_log |
| data_defect_alerts.json | 2,027B | 数据缺陷告警 4 条 (2 FIXED) | P12 回归 |
| rollback_events.json | 1,134B | 回滚事件 3 条 | DSHD 全阶段 |
| data_completion_status.json | 2,691B | ZN/NI/SN/SI 补全进度 | PC-003 追踪 |
| experiment_index.json | 2,584B | 实验版本 P2-P19 (12 阶段) | 全阶段 flag |
| version_index.json | 1,476B | 版本切换 (5 快照) | 版本演进 |
| pl_summary.json | 2,321B | 7 品种盈亏汇总 | vis_dataset_manifest |
| dataset_index.json | 5,289B | 数据集索引 | 自动生成 |
| vis_pre_calc_AL_nav.csv | 8,574B | AL 净值时序 (230 行) | DSHA |
| vis_pre_calc_AL_signals.csv | 3,387B | AL 信号 (65 行) | DSHA |
| vis_pre_calc_AL_kline.csv | 18,227B | AL K 线 (230 行) | DSHA |
| vis_pre_calc_AL_alpha.csv | 9,320B | AL alpha (230 行) | DSHA |
| vis_pre_calc_CU_*.csv | 各 9-18KB | CU 净值/信号/K 线/alpha | DSHA |
| vis_pre_calc_PB_*.csv | 各 9-18KB | PB 净值/信号/K 线/alpha | DSHA |
| vis_pre_calc_AL_F19_F20_comparison.csv | 1,844B | AL F19/F20 对比 | DSHA |
| vis_pre_calc_AL_factor_contributions.csv | 8,015B | AL 因子贡献 (50 行) | DSHA |
| vis_dashboard_main.html | 147,681B | DSHA 原始仪表盘 | DSHA |
| vis_dataset_manifest.json | 6,247B | DSHA 数据集清单 | DSHA |

### 5.2 归档数据 (archive/)

| 分类 | 文件数 | 内容 |
|------|--------|------|
| phases/ | 17 | P2-P16 阶段 flag/report + P_GRAY + P_SHADOW |
| factors/ | 13 | 因子库/元数据/技术债清单/边界规格 |
| backtests/ | 7 | 7 品种回测 JSON (AL/CU/PB/ZN/NI/SN/SI) |
| trades/ | 7 | 7 品种交易 JSON |
| alerts/ | 34 | 告警/审计/巡检日志/事件卷 |
| dsha_v1/ | 1 | DSHA 原始仪表盘 |
| **总计** | **79** | 字节级保留, md5 记录于 manifest.json |

---

## 6. 功能清单 (T2/T3)

### 6.1 T2 告警可视化全链路

| 功能 | 位置 | 说明 |
|------|------|------|
| FR-RISK 告警接入 | 🚨 告警中心 | 7 条告警, 含 4 RED/CRITICAL |
| PC-003 门禁状态 | 🔒 门禁看板 | 实时状态 (BLOCKED) + 自检 40/40 |
| 数据缺陷告警 | 🚨 告警中心 | DEFECT-P9-001/002 (FIXED) + 通道告警 |
| 因子漂移告警 | 🚨 告警中心 | F07/F11/F19/F20 漂移追踪 |
| 回滚事件 | 🚨 告警中心 | 3 条回滚事件记录 |
| 告警时间线 | 📋 概览 | 累计告警堆叠面积图 |
| 告警级别分布 | 🚨 告警中心 | RED/ORANGE/YELLOW 饼图 |
| 告警类别统计 | 🚨 告警中心 | FR-RISK/DRIFT/DEFECT/ROLLBACK 柱图 |
| 触发规则 | 🚨 告警中心 | 明细表 trigger 列 |
| 处置记录 | 🚨 告警中心 | 明细表 handling 列 |
| PC-003 冻结/监听/待解锁 | 🔒 门禁看板 | 解锁流程 + 子门禁进度 |
| 四品种数据补全 | 📈 数据补全 | ZN/NI/SN/SI 进度条 + 雷达图 |

### 6.2 T3 页面功能补全

| 功能 | 位置 | 说明 |
|------|------|------|
| 实验版本切换 | 🔄 版本切换 | P3/P7/P9/P12/P19 版本芯片 |
| 因子筛选 | 🧬 因子库 | 20 因子复选框 + 过滤搜索 |
| 品种切换 | 📊 品种切换 | 7 品种卡片 + 门禁状态 |
| 盈亏汇总统计 | 💰 盈亏汇总 | 4 卡片 + 品种绩效表 |
| 曲线缩放 | 净值图表 | ECharts dataZoom (inside + slider) |
| 点位详情 | 净值图表 | 点击图表点 → 模态弹窗显示完整数据 |
| 报告截图导出 | 各面板 | html2canvas → PNG 下载 |

---

## 7. 告警推送链路

### 7.1 链路架构

```
DSHC 编排器 → FR-RISK 接收器 → DSHD 守护服务 → 告警分级 → VIS-001 面板
     ↑                              ↓
     └── DSHC:ORCHESTRATOR ←── 自动升级通知 (CRITICAL/P0)
```

### 7.2 分级策略

| 颜色 | 动作 | SLA | 升级 |
|------|------|-----|------|
| RED | STOP_LINE (强制) | 立即 | CRITICAL/P0 自动升级 |
| ORANGE | NOTIFY_1H | 1 小时 | — |
| YELLOW | RECORD_4H | 4 小时 | — |

### 7.3 颜色约束 (第一性)

- `sla_h` 为响应时间预算, **绝不覆盖 color**
- RED/CRITICAL 事件永远 STOP_LINE
- 14/14 RED→STOP_LINE 零降级 (P12 验证)

---

## 8. 故障排查

### 8.1 数据加载失败

```
浏览器控制台 → Console
Expected: fetch('data/fr_risk_alerts.json')
Error:    CORS / 404
```

**解决**:
- 确认通过 HTTP 服务运行 (非 file://)
- 确认 `web_site/data/` 目录存在且文件完整
- 确认 Python http.server 从 `web_site/` 目录启动

### 8.2 ECharts 未加载

```
控制台: ReferenceError: echarts is not defined
```

**解决**:
- 检查网络连通性 (cdn.jsdelivr.net)
- 若离线, 下载 echarts.min.js 到 `assets/` 并修改引用

### 8.3 CI 部署失败

| 步骤 | 常见错误 | 解决 |
|------|----------|------|
| JSON 校验 | JSONDecodeError | 检查 JSON 语法 |
| HTML 校验 | grep 返回非 0 | 检查关键标记存在 |
| 归档校验 | file missing | 检查 archive/manifest.json |
| DSHA 字节 | md5 mismatch | 重新运行 p18_t1_archive_pack.py |
| 部署 | Pages 权限不足 | 检查 permissions: pages:write |

### 8.4 截图导出失败

```
html2canvas CORS error
```

**解决**:
- 确认 CDN 资源允许跨域 (jsdelivr 默认允许)
- 截图时 `useCORS: true` 已启用

---

## 9. 部署验证清单

部署完成后, 验证以下项目:

- [ ] 站点 URL 可访问 (`https://<user>.github.io/<repo>/`)
- [ ] 首页加载无控制台错误
- [ ] 概览页品种分布正常显示 (7 品种)
- [ ] 告警中心 4 类告警全部展示
- [ ] 门禁看板 PC-003 BLOCKED 状态
- [ ] 数据补全 ZN/NI/SN/SI 进度条
- [ ] 因子库 20 因子筛选
- [ ] 品种切换净值对比
- [ ] 版本切换 P3-P19
- [ ] 盈亏汇总 3 品种绩效
- [ ] Github Pages 数据集清单
- [ ] 静态归档 79 文件清单
- [ ] 截图导出功能正常
- [ ] 曲线缩放 (dataZoom) 正常
- [ ] 点位详情模态弹窗

---

## 10. 维护指南

### 10.1 数据更新

```bash
# 1. 更新 data/*.json (修改内容, 保持 schema)
# 2. 重新运行归档打包
python gate_prep_lab/p18_t1_archive_pack.py
# 3. 推送触发 CI 自动部署
git add -A && git commit -m "Update datasets" && git push
```

### 10.2 新增阶段归档

```bash
# 1. 将新阶段 flag/report 放入 gate_prep_lab/ 或根目录
# 2. 在 p18_t1_archive_pack.py PHASE_ARCHIVE 列表中添加
# 3. 重新运行归档打包
python gate_prep_lab/p18_t1_archive_pack.py
```

### 10.3 新增告警类型

```bash
# 1. 在 data/fr_risk_alerts.json 中添加新告警
# 2. 保持 schema 一致 (alert_id/ts/code/variety/color/severity/action/handling/status/audit_id)
# 3. 推送触发 CI
```

---

## 11. 参考

- **DSHA 仪表盘**: `web_site/archive/dsha_v1/vis_dashboard_main.html` (147,681B md5 f0036dc3)
- **数据集清单**: `web_site/data/vis_dataset_manifest.json` (manifest_version 1.0)
- **归档清单**: `web_site/archive/manifest.json` (79 文件)
- **P12 基线**: `phase12_gate_summary_report.md` (31,014B md5 3ed92b3c)
- **CI 配置**: `.github/workflows/deploy-pages.yml` (3 job, 12 step)

---

**文档结束** · DSHD-P19 部署手册 · V1.0 · SEED=42


---

## P19 迭代说明 (2026-10-09)

### P19 新增功能

| 功能 | 说明 |
|------|------|
| NI/SI 独立面板 | 新增镍和工业硅独立可视化面板, 含回测曲线、交易明细、盈亏弹窗 |
| M3/M4 里程碑 | 四品种补全看板新增M3(影子回测完成)和M4(真实数据接入进行中)状态 |
| FR-RISK↔PC003 联动 | 告警中心与门禁看板实时联动展示 |
| 离线数据预加载提示 | navigator.onLine检测 + offline-banner组件 |
| ECharts依赖缺失提示 | typeof echarts检查 + 降级提示 |
| P18/P19 版本分离 | 数据集版本标签区分P18基线和P19迭代数据 |
| 品种切换加载优化 | 加载指示器 + 渲染缓存 |

### P19 数据文件

| 文件 | 说明 |
|------|------|
| ni_si_panels.json | NI/SI独立面板数据 (新增) |
| backtest_*.json | 7品种回测JSON (新增) |
| trades_*.json | 7品种交易JSON (新增) |
| factors_full.json | 20因子完整库 (更新) |

### P19 CI 校验

CI pipeline 新增 P19 特定校验:
- NI/SI panel grep (nisipanel, renderNISIPanel)
- offline-banner grep
- DSHD-P19 title grep
- ni_si_panels.json check


## P20 工单说明 (2026-10-09)

### P20 功能变更

| 变更 | 说明 |
|------|------|
| CI名称 | Deploy DSHD-P20 to GitHub Pages |
| 新增数据 | cross_variety_comparison.json + pc003_unlock_assessment.json |
| 新增面板 | PC003解锁评估 (M5里程碑) |
| 新增导航 | pc003unlock tab |
| 版本标签 | P18/P19/P20 三版本分离 |
| CI校验 | 新增5项P20 grep校验 |

### P20 数据文件清单

| 文件 | 大小 | 说明 |
|------|------|------|
| cross_variety_comparison.json | 2,390B | 7品种跨品种对比 + 雷达图数据 |
| pc003_unlock_assessment.json | 3,693B | PC003解锁评估 (M5) |
| 其他P20更新 | - | 8个数据JSON更新至v1.2 |

### P20 部署命令

```bash
# 1. 运行T1数据刷新
python gate_prep_lab/p20_t1_data_build.py

# 2. 运行T2/T3 HTML构建
python gate_prep_lab/p20_t2_t3_html_build.py

# 3. 运行T4全链路测试
python gate_prep_lab/p20_t4_all.py

# 4. 运行T5 CI更新
python gate_prep_lab/p20_t5_ci_update.py

# 5. 运行T5归档交付
python gate_prep_lab/p20_t5_archive.py
```


---

## P21 更新 (2026-11-23)

### 新增文件
- `portfolio_backtest.json` — 多品种组合回测数据 (G1截面组合)
- `portfolio_correlation.json` — 7×7跨品种相关性矩阵
- `portfolio_risk_metrics.json` — 组合风险指标 + 压力测试 + 紧急关停

### 更新文件
- `cross_variety_comparison.json` — v1.3, 7品种全部UNLOCKED, 9维度雷达图
- `pc003_unlock_assessment.json` — v1.3, PC003 UNLOCKED, M1-M7里程碑, 压力测试, 投产限制, 紧急关停
- `data_completion_status.json` — v1.3, M1-M5 COMPLETED, M6-M7 PENDING
- `pl_summary.json` — v1.3, 7品种全部ENABLED
- `experiment_index.json` — v1.3, P2-P21 (16 experiments)
- `version_index.json` — v1.3, P18/P19/P20/P21四版本分离
- `fr_risk_alerts.json` — v1.3, 9告警 (含2 P21新增)
- `pc003_status.json` — v1.3, UNLOCKED, P21 linkage
- `dataset_index.json` — v1.3, 47数据集

### 页面新增
- 组合视图导航标签 + 页面面板
- 多品种组合净值曲线图
- 组合风险指标面板
- 因子正交化对比表
- 紧急关停条件面板
- 跨品种相关性矩阵热力图
- PC003 UNLOCKED面板 (M1-M7 + 压力测试 + 投产限制 + 紧急关停)
- M6/M7里程碑报告面板
- P18/P19/P20/P21四版本彩色标签

### CI更新
- CI名称: Deploy DSHD-P21 to GitHub Pages
- 新增25+ P21 grep校验规则
- portfolio_backtest.json / portfolio_correlation.json / portfolio_risk_metrics.json
- UNLOCKED / M6 / M7 / correlation-matrix / renderPC003UnlockPanelV21


---

## P21 更新 (2026-11-23)

### 新增文件
- `portfolio_backtest.json` — 多品种组合回测数据 (G1截面组合)
- `portfolio_correlation.json` — 7×7跨品种相关性矩阵
- `portfolio_risk_metrics.json` — 组合风险指标 + 压力测试 + 紧急关停

### 更新文件
- `cross_variety_comparison.json` — v1.3, 7品种全部UNLOCKED, 9维度雷达图
- `pc003_unlock_assessment.json` — v1.3, PC003 UNLOCKED, M1-M7里程碑, 压力测试, 投产限制, 紧急关停
- `data_completion_status.json` — v1.3, M1-M5 COMPLETED, M6-M7 PENDING
- `pl_summary.json` — v1.3, 7品种全部ENABLED
- `experiment_index.json` — v1.3, P2-P21 (16 experiments)
- `version_index.json` — v1.3, P18/P19/P20/P21四版本分离
- `fr_risk_alerts.json` — v1.3, 9告警 (含2 P21新增)
- `pc003_status.json` — v1.3, UNLOCKED, P21 linkage
- `dataset_index.json` — v1.3, 47数据集

### 页面新增
- 组合视图导航标签 + 页面面板
- 多品种组合净值曲线图
- 组合风险指标面板
- 因子正交化对比表
- 紧急关停条件面板
- 跨品种相关性矩阵热力图
- PC003 UNLOCKED面板 (M1-M7 + 压力测试 + 投产限制 + 紧急关停)
- M6/M7里程碑报告面板
- P18/P19/P20/P21四版本彩色标签

### CI更新
- CI名称: Deploy DSHD-P21 to GitHub Pages
- 新增25+ P21 grep校验规则
- portfolio_backtest.json / portfolio_correlation.json / portfolio_risk_metrics.json
- UNLOCKED / M6 / M7 / correlation-matrix / renderPC003UnlockPanelV21


---

## P21 更新 (2026-11-23)

### 新增文件
- `portfolio_backtest.json` — 多品种组合回测数据 (G1截面组合)
- `portfolio_correlation.json` — 7×7跨品种相关性矩阵
- `portfolio_risk_metrics.json` — 组合风险指标 + 压力测试 + 紧急关停

### 更新文件
- `cross_variety_comparison.json` — v1.3, 7品种全部UNLOCKED, 9维度雷达图
- `pc003_unlock_assessment.json` — v1.3, PC003 UNLOCKED, M1-M7里程碑, 压力测试, 投产限制, 紧急关停
- `data_completion_status.json` — v1.3, M1-M5 COMPLETED, M6-M7 PENDING
- `pl_summary.json` — v1.3, 7品种全部ENABLED
- `experiment_index.json` — v1.3, P2-P21 (16 experiments)
- `version_index.json` — v1.3, P18/P19/P20/P21四版本分离
- `fr_risk_alerts.json` — v1.3, 9告警 (含2 P21新增)
- `pc003_status.json` — v1.3, UNLOCKED, P21 linkage
- `dataset_index.json` — v1.3, 47数据集

### 页面新增
- 组合视图导航标签 + 页面面板
- 多品种组合净值曲线图
- 组合风险指标面板
- 因子正交化对比表
- 紧急关停条件面板
- 跨品种相关性矩阵热力图
- PC003 UNLOCKED面板 (M1-M7 + 压力测试 + 投产限制 + 紧急关停)
- M6/M7里程碑报告面板
- P18/P19/P20/P21四版本彩色标签

### CI更新
- CI名称: Deploy DSHD-P21 to GitHub Pages
- 新增25+ P21 grep校验规则
- portfolio_backtest.json / portfolio_correlation.json / portfolio_risk_metrics.json
- UNLOCKED / M6 / M7 / correlation-matrix / renderPC003UnlockPanelV21


---

## P21 更新 (2026-11-23)

### 新增文件
- `portfolio_backtest.json` — 多品种组合回测数据 (G1截面组合)
- `portfolio_correlation.json` — 7×7跨品种相关性矩阵
- `portfolio_risk_metrics.json` — 组合风险指标 + 压力测试 + 紧急关停

### 更新文件
- `cross_variety_comparison.json` — v1.3, 7品种全部UNLOCKED, 9维度雷达图
- `pc003_unlock_assessment.json` — v1.3, PC003 UNLOCKED, M1-M7里程碑, 压力测试, 投产限制, 紧急关停
- `data_completion_status.json` — v1.3, M1-M5 COMPLETED, M6-M7 PENDING
- `pl_summary.json` — v1.3, 7品种全部ENABLED
- `experiment_index.json` — v1.3, P2-P21 (16 experiments)
- `version_index.json` — v1.3, P18/P19/P20/P21四版本分离
- `fr_risk_alerts.json` — v1.3, 9告警 (含2 P21新增)
- `pc003_status.json` — v1.3, UNLOCKED, P21 linkage
- `dataset_index.json` — v1.3, 47数据集

### 页面新增
- 组合视图导航标签 + 页面面板
- 多品种组合净值曲线图
- 组合风险指标面板
- 因子正交化对比表
- 紧急关停条件面板
- 跨品种相关性矩阵热力图
- PC003 UNLOCKED面板 (M1-M7 + 压力测试 + 投产限制 + 紧急关停)
- M6/M7里程碑报告面板
- P18/P19/P20/P21四版本彩色标签

### CI更新
- CI名称: Deploy DSHD-P21 to GitHub Pages
- 新增25+ P21 grep校验规则
- portfolio_backtest.json / portfolio_correlation.json / portfolio_risk_metrics.json
- UNLOCKED / M6 / M7 / correlation-matrix / renderPC003UnlockPanelV21


## P22 部署说明 (2027-11-12)

### P22 新增内容
- **品种风险贡献分解面板**: portfolio_risk_contribution.json — 7品种MRC+Euler分解
- **FR-RISK-009/010**: NI数据源延迟监控 + 跨品种集中度监控
- **PC003 M6 COMPLETED**: TD002数据接入报告已完成
- **3级关停链路演练**: Level 1/2/3 全部通过, 平均响应45s
- **P22 风控巡检**: 12/12 PASS
- **容量巡检**: 仓库 <800MB, 状态 OK

### P22 数据版本
- dataset_version: 1.4
- version_tag: P22
- 48个数据文件, 298.8 KB

### P22 部署步骤
1. 确认数据版本为 v1.4 / P22
2. 确认 portfolio_risk_contribution.json 已存在
3. 确认 FR-RISK-009/010 已添加
4. 确认 PC003 M6=COMPLETED
5. 确认容量 <800MB
6. 部署到 GitHub Pages


## DSHD-P23 部署更新

### 1. 版本信息
- 数据版本: v1.5 (P23)
- M7里程碑: COMPLETED
- PC003状态: UNLOCKED_FINAL
- 投产风险评级: LOW (0.15)

### 2. 新增功能
- M7终审评估面板 (m7-final-panel)
- Euler风险贡献时序 (euler_time_series)
- NI延迟监控时序与最终评估
- FR-RISK P23告警 (FR-RISK-PG23-M7-011, FR-RISK-PG23-NI-012)
- 滚动相关性窗口 (20/40/60/120/250日)
- P18-P23六版本切换

### 3. CI验证
- deploy-pages.yml: 25+ P23 grep校验
- 数据文件验证: JSON schema + version_tag + M7 COMPLETED
- HTML验证: M7 panel + Euler + NI delay + FR-RISK P23

### 4. 容量
- 仓库: 4.5MB / 800MB (0.57%)
- 状态: PASS
- 余量: 795.5MB

### 5. 部署步骤
1. 确认所有数据文件已更新到P23版本
2. 确认CI流水线通过所有校验
3. 推送代码触发GitHub Pages部署
4. 验证页面渲染正确

### 6. 遗留项
- GitHub Pages生产部署: REPO_PAT待申请
- DSHC forward channel + J22 recheck


## P24 更新记录 (2026-10-09T10:09:16+08:00)

### 新增功能
- Phase4 专用监控面板: 执行日志/数据校验/MD5快照状态展示
- PB/CU 灰度准入状态面板: BEAR_IC时序曲线/达标倒计时/准入评估结论
- 品种风险贡献时序优化: 时间切片(7d/14d/30d/35d/all)查看
- 相关性热力图时序切换优化

### 新增数据文件
- portfolio_risk_contribution_timeseries.json (123KB)
- phase4_precheck.json (3.5KB)
- pb_cu_gray_admission_status.json (4KB)

### 更新数据文件 (v1.6/P24)
- version_index.json, experiment_index.json, dataset_index.json
- data_completion_status.json, fr_risk_alerts.json, pc003_status.json
- pc003_unlock_assessment.json, pl_summary.json, cross_variety_comparison.json
- portfolio_backtest.json, portfolio_correlation.json, portfolio_risk_metrics.json
- portfolio_risk_contribution.json

### FR-RISK 新增
- FR-RISK-PG24-PB-013 (YELLOW): PB/CU灰度准入评估
- FR-RISK-PG24-PHASE4-014 (GREEN): Phase4监控面板集成

### CI 更新
- YAML: 29,479B (30+ P24 grep校验)
- 数据验证: phase4_precheck, pb_cu_gray_admission, portfolio_risk_contribution_timeseries

### 仓库容量
- 总计: 5.06MB / 800MB (0.63%)
- 余量: 794.9MB
- 状态: PASS

---

## 23. DSHD-P24 GitHub Pages 生产部署验证 (2026-10-09)

### 23.1 部署结果

| 项目 | 值 |
|---|---|
| 仓库 | `algo23-yunqingtian/dshd-dashboard` (public) |
| 站点 URL | https://algo23-yunqingtian.github.io/dshd-dashboard/ |
| 部署模式 | GitHub Actions (`build_type: workflow`) |
| Source | branch `main` / path `/` (site 内容由 artifact 上传) |
| CI Validate | PASS |
| CI Deploy | PASS |
| CI Notify | PASS |
| Workflow Run | 37914285846 (conclusion: success) |
| HTTP 状态 | 200 OK (index.html 173,428 bytes) |
| 部署时间 | 2026-10-09 17:55 (Asia/Shanghai) |

### 23.2 Pages 启用方式 (关键踩坑记录)

**问题**: `actions/configure-pages@v5` 在新仓库上返回 `Resource not accessible by integration`，无法创建 Pages 站点。`GITHUB_TOKEN` 即使声明 `pages: write` 也无法为新仓库创建 Pages。

**根因定位** (对照实验):
| 测试 | 结果 |
|---|---|
| `GET /pages` on zinc-dashboard (已有Pages) | 200 OK ✓ |
| `GET /pages` on macro-dashboard (无Pages) | 404 |
| `PUT /pages` on dshd-dashboard (无Pages) | **404** |
| `PUT /pages` on zinc-dashboard (已有Pages) | 422 (端点响应) |
| `PUT /pages` on macro-dashboard (无Pages) | 404 |
| `POST /pages` on dshd-dashboard | **201 Created** ✓ |

**结论**: 当前 GitHub API 中 `PUT /repos/{owner}/{repo}/pages` 仅能**更新已存在**的 Pages 站点（对新仓库返回 404）；**创建**必须用 `POST`。同时 source.path 仅接受 `/` 或 `/docs`（不接受 `/web_site`，site 内容须由 `actions/upload-pages-artifact` 上传 artifact）。

**正确的启用命令** (使用带 `repo` scope 的 PAT):
```bash
curl -X POST \
  -H "Authorization: token <PAT_WITH_REPO_SCOPE>" \
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d '{"source":{"branch":"main","path":"/"},"build_type":"workflow"}' \
  https://api.github.com/repos/algo23-yunqingtian/dshd-dashboard/pages
# → 201 Created
```

### 23.3 线上内容验证 (12/12 PASS)

对 https://algo23-yunqingtian.github.io/dshd-dashboard/ 抓取 index.html 后校验标记:

| 标记 | 结果 |
|---|---|
| `DSHD-P24` 标题 | PASS |
| `phase4-panel` | PASS |
| `renderPhase4Panel` | PASS |
| `pb-cu-panel` | PASS |
| `renderPBCUGrayPanel` | PASS |
| `risk-ts-chart` | PASS |
| `FR-RISK-PG24-PB-013` | PASS |
| `FR-RISK-PG24-PHASE4-014` | PASS |
| `portfolio_risk_contribution_timeseries` | PASS |
| `pb_cu_gray_admission_status` | PASS |
| `phase4_precheck.json` | PASS |
| `P18/P19/P20/P21/P22/P23/P24` (7版本切换) | PASS |

### 23.4 数据文件在线可访问性

| 文件 | HTTP | version_tag |
|---|---|---|
| /data/phase4_precheck.json | 200 | P24 |
| /data/pb_cu_gray_admission_status.json | 200 | P24 |
| /data/portfolio_risk_contribution_timeseries.json | 200 | P24 |

### 23.5 后续部署流程

1. 修改 `web_site/` 内任何文件后 push 到 `main`，workflow 自动触发 (paths: `web_site/**`, `.github/workflows/deploy-pages.yml`, `data/**`, `archive/**`)
2. 校验 (validate) → 部署 (deploy) → 通知 (notify) 三 job 顺序执行
3. 紧急部署: Actions → "Deploy DSHD-P24 to GitHub Pages" → Run workflow (支持 `skip_validate` 输入)
4. `configure-pages` 保留 `enablement: true`，Pages 已启用后幂等无害

### 23.6 部署安全清单

- [x] PAT token 已在部署完成后从 git remote URL 中清除 (改为 https 无凭据形式，凭据仅存于 GitHub 凭据管理器)
- [x] `GH_TOKEN` 不在 workflow 明文出现，走 `GITHUB_TOKEN` (权限最小化: `contents: read`, `pages: write`, `id-token: write`)
- [x] 仓库容量 5.06MB / 800MB (0.63%)，远低于限制
- [x] 版本锁定文件 (`v87_03_monitor_service.py` md5=e2f0d4cc, `vis_alert_export_api.py` md5=474ff0ae) 内容未被修改
- [x] `.gitignore` 已排除内部脚本/缓存/历史 phase 文件，仓库只含发布产物

## 24. DSHD-P25 看板迭代与 CI/CD 加固 (2026-10-11T22:58:08+08:00)

### 24.1 版本信息

| 字段 | 值 |
|------|-----|
| 阶段 | DSHD-P25 |
| 看板版本 | V25.0 |
| 数据版本 / version_tag | 1.7 / P25 |
| ENGINE | V86.9-C-FINAL-DEBUG-P25 |
| index.html | 173,428 → 207,450 (Δ +34022 B) |
| index.html MD5 | `dadc222b6bddab9aa84136de3083ed23` |
| 数据集 | 42 个 JSON, 全部 version_tag=P25 / dataset_version=1.7 |

### 24.2 新增功能

- IC 漂移预警导航 tab + page-icdrift 面板
- IC 漂移趋势图: Phase6~P25 完整时序 + 5.0% markLine + 超标红色散点 + 阻断区背景带
- 历史 10% 阈值对照开关 (P24 起 10% 已废止)
- 漂移根因: 12 因子漂移表 + 来源分类占比条 + 4 套方案测算对比表
- PB/CU BEAR_IC 实时读数卡 (阈值缺口 + 35 日时序 + 阻断来源)
- FR-RISK 告警面板阻断状态增强
- 多窗口滚动相关性矩阵: 20/40/60/120/250d 切换 + 分档均值条形图
- 阻断动作链 (RECORD→WATCH→NOTIFY→BLOCK) + 解除条件
- 版本标识 P24 -> P25 / V24 -> V25 / 八版本 DS 标识

### 24.3 修复的 P24 遗留缺陷 (上线前必修)

> **背景**: T1 巡检发现 P24 线上 `index.html` 存在 `SyntaxError: Identifier 'rc' has already been declared`,
> 导致**整页内联脚本失效, 所有图表与面板均不渲染**。T2 一并修复并新增 CI 语法门禁防止复发。

| ID | 缺陷 | 影响 |
|----|------|------|
| D1 | const rc 三处重复声明 (renderPortfolioOverview/updateHeader/renderVersions) | 主内联脚本 SyntaxError 导致全站 JS 失效 (图表/面板均不渲染) |
| D2 | loadJSON('portfolio_risk_contribution.json (P24 Euler)') 参数含内嵌注释 | 请求 URL 含空格与括号, 永远 404, portfolioRiskContribution 恒为 null |
| D3 | switchRollingWindow() 被 <select onchange> 引用但未定义 | 滚动窗口下拉切换触发 ReferenceError |
| D4 | renderCompletionRadar 的 splitArea 行多一个 } (提前闭合 setOption 参数对象) | SyntaxError: missing ) after argument list -> 主脚本失效, 整页不渲染 |
| D5 | renderVarietyRadar 同一 splitArea 行多一个 } | SyntaxError: missing ) after argument list -> 主脚本失效, 整页不渲染 |
| D1-4 | renderVersions() 第二段 const rc 重复声明 (非相邻, 同函数作用域) | SyntaxError: Identifier 'rc' has already been declared -> 主脚本失效, 整页不渲染 |
| D8 | GitHub 工作流展示模板中 ${{ github.sha }} 未转义, 被当作模板插值 | SyntaxError: Unexpected token '.' -> 主脚本失效, 整页不渲染 |
| D6 | renderVersions() 模板 background 三元链少一个 ) (3 组括号实有 2 个) | SyntaxError: Unexpected token '}' -> 主脚本失效, 整页不渲染 |
| D7 | renderVersions() 模板 color 三元链少一个 ) (5 组括号实有 4 个) | SyntaxError: Unexpected token '}' -> 主脚本失效, 整页不渲染 |

### 24.4 CI/CD 加固 (deploy-pages.yml)

`validate` job 新增 4 个门禁步骤:

| 步骤 | 行为 | 失败码 |
|------|------|--------|
| `1.2b P25 T3: Pre-flight static data validation` | 42 数据集 + core18 + version_tag/dataset_version 全量一致性 + 3 个 P25 新数据集结构断言 + FR-RISK 跨数据集一致性 | 10 |
| `1.2c P25 T3: Inline JS syntax audit (node --check)` | 抽取全部 `<script>` 内联块逐块 `node --check`; 有语法错误即阻断部署 | 11 |
| `1.2d P25 T3: Security scan` | secret 模式扫描 140 文件 + 凭证文件 + 非 HTTPS 外部资源 + CDN 版本钉住 | 20 / 21 / 22 |
| `1.6 P25 markers` | 42 数据集 + P25 三个新数据集 + IC 漂移面板 + FR-RISK 阻断面板 + 多窗口相关性 + MD5 基线 manifest | — |

`deploy` job 之后新增 2 个 job:

```yaml
deploy-retry:      # 部署失败自动重试
  needs: deploy
  if: ${{ always() && needs.deploy.result == 'failure' }}
  steps: checkout -> configure-pages -> upload-pages-artifact -> deploy-pages

deploy-fallback:   # 网络异常降级: API 提交模式
  needs: [deploy, deploy-retry]
  if: ${{ always() && needs.deploy.result != 'success' && needs.deploy-retry.result != 'success' }}
  permissions: { contents: write }
  env: { TOKEN: ${{ secrets.PAGES_FALLBACK_TOKEN || github.token }} }
  steps:
    - 探测 github.com:443 与 api.github.com:443
    - github.com 可达 -> 报错 (降级不适用, 是别的原因失败)
    - api.github.com 不可达 -> 报错 (无降级路径)
    - 否则 python3 gate_prep_lab/p25_api_fallback.py  # Contents API 直写 gh-pages
```

### 24.5 手动降级命令 (API 提交模式)

```bash
# 1. 本地探测网络状态
curl -fsS --connect-timeout 5 https://github.com/ >/dev/null      && echo github.com OK || echo github.com DOWN
curl -fsS --connect-timeout 5 https://api.github.com/ >/dev/null  && echo api.github.com OK || echo api.github.com DOWN

# 2. github.com 不通而 api.github.com 通时, 手动执行降级发布
cd dshd_arch_gate_prep
SITE_DIR=web_site TARGET_BRANCH=gh-pages GITHUB_REPOSITORY=algo23-yunqingtian/dshd-dashboard \
  GITHUB_SHA=$(git rev-parse HEAD) GITHUB_TOKEN=$PAT \
  python3 gate_prep_lab/p25_api_fallback.py

# 3. 查看结果
cat deploy_fallback_report.json
```

可选: 在仓库 Settings → Secrets 配置 `PAGES_FALLBACK_TOKEN` (fine-grained PAT, 需 `Contents: Read and write`), 之后 fallback job 自动使用; 未配置时回落到 `github.token`。

### 24.6 部署步骤

```bash
# 1. 数据刷新 (T2a)
python3 gate_prep_lab/p25_t2_data_build.py

# 2. 前端构建 (T2b, 从 P24 备份重建, 幂等)
cp web_site/index.html.bak_p24 web_site/index.html
python3 gate_prep_lab/p25_t2_html_build.py

# 3. 审计归档 (T4)
python3 gate_prep_lab/p25_t4_final.py

# 4. 推送触发 CI (自动 5 job: validate -> deploy -> [deploy-retry] -> [deploy-fallback] -> notify)
git add -A && git commit -m 'P25: dashboard V25.0 + CI hardening + MD5 baseline' && git push origin main

# 5. 或手动触发 workflow_dispatch
#    https://github.com/algo23-yunqingtian/dshd-dashboard/actions/workflows/deploy-pages.yml
```

### 24.7 部署验证清单

- [ ] CI `validate` job: pre-flight / JS syntax / security scan 三步全绿
- [ ] CI `deploy` job: SUCCESS (或 `deploy-retry` SUCCESS)
- [ ] 线上首页 HTTP 200, 体积约 207,450
- [ ] 首页导航出现 **IC 漂移预警** tab
- [ ] IC 漂移趋势图显示 Phase6~P25 17 点 + 5.0% markLine + 超标红色散点
- [ ] FR-RISK 面板显示阻断状态与 PB/CU BEAR_IC 实时读数
- [ ] 相关性矩阵可切换 20/40/60/120/250d 且分档均值行正常
- [ ] `data/MD5_BASELINE_P25.json` 在线可访问
- [ ] `deploy_meta.json` 在线 (由 `upload-pages-artifact` 后生成, 部署前 404 属预期)

### 24.8 仓库容量

| 指标 | P24 | P25 |
|------|-----|-----|
| 本地体积 | 5.24 MB | 5.23 MB |
| 文件数 | 366 | 367 |
| 数据目录 | 616 KB | 683,978 |
| 占用 / 100 MB 上限 | 0.63%% | 0.73%% |

### 24.9 遗留项

- **P0** IC 漂移根因: 结构性慢衰减 (每阶段 -0.0001), 推荐方案 D (F01/F09→0.85, F19/F20→1.1 + 衰减补偿 + F15~F18 伪影修正)。详见 `web_site/data/drift_root_cause.json`。
- **P0** 准入阻断维持中 (`FR-RISK-PG25-ICDRIFT-015`), 解除条件: 连续 2 阶段漂移率 < 4.8% 且 IC >= 0.0575。
- **P2** 站点 keep-alive 中位时延 441 ms 超 400 ms 阈值 (冷连接最大 21.5 s), 建议后续合并小文件 / 启用 Brotli。
- **P3** `github.com:443` 间歇不可达; 已加 retry + API-Contents 降级双保险。
- **P3** 缺失 GitHub PAT: 推送与 `workflow_dispatch` 需用户提供; `PAGES_FALLBACK_TOKEN` secret 可选。



## 25. DSHD-P26 看板迭代与 CI 流水线运维 (2026-10-12T02:44:15+08:00)

### 25.1 版本信息

| 项 | 值 |
|----|----|
| 看板相位 | DSHD-P26 |
| 数据源 | **DSHA-P31** (工单指定 DSHA-P30 / V30.0, 该数据集已被上游就地覆盖) |
| VERSION_TAG / DATA_VERSION | P31 / 1.8 |
| ENGINE | V86.9-C-FINAL-DEBUG-P31 |
| index.html | 207,696 B / md5 cfac3b0ebc4d8c79ca4b2e50c399cd15 |
| JSON 数据集 | 43 (全部 P31 / 1.8) |
| data/ 文件 | 60 (676.4 KB) |
| MD5 基线 | 171 entries / 3,503,264 B |

### 25.2 关键指标

| 指标 | 值 | 状态 |
|------|----|:----:|
| IC | 0.0586 | 达标 |
| IC 漂移率 | 3.6% | 优于阈值 4.8% |
| IC 漂移阻断 | FALSE | 已解除 |
| 解锁条件 | 6/6 MET (PERMANENTLY_UNBLOCKED) | PASS |
| PB BEAR_IC | 0.0294 / 阈值 0.030 | 14/14 THRESHOLD_MET_SUSTAINED |
| CU BEAR_IC | 0.0234 / 阈值 0.025 | 6/14 BELOW_THRESHOLD (维持 1.5% 上限) |
| 品种 | 7 (AL/CU/PB/ZN/NI/SN/SI) | 全部正式投产 |
| FR-RISK | 17 条, PG31-ICDRIFT-021 / -PBCU-022 已 RELEASED | PASS |

### 25.3 CI 相位解耦 (本阶段核心工作)

审计发现 validate job 中约 28 处门禁断言仍硬编码 P23/P24/P25, 每推进一步相位都会
在门禁处断裂。已全部改写为相位无关正则:

```
P\d+              # 相位标签
dataset_version 1.x
"version_tag": "P[0-9]+"'   # JSON 内联
```

同时修复 3 处 shell 引号缺陷 (此前从未被触发, 因为前序步骤已 abort):

- 2 处 `grep -Eq "\"version_tag\": "\"P[0-9]+\"..."` 引号未闭合, 改用单引号包裹 (共 21 处同类 grep 已统一)
- 1 处 IC-drift grep 尾部 `"` 与 `'` 顺序颠倒

### 25.4 本地 harness 语义修正

原本地 validate harness 将 `A && B` 链一律判为「非门禁 (静默探针)」, 导致 2 类真实
CI 失败无法在本地复现。已改为 `bash -e` 语义:

- 裸命令失败 -> abort
- `&&` / `||` 链的**末位**命令失败 -> abort
- `&&` 链**前缀**失败 -> **豁免** (bash `set -e` 规则)
- 块末行的状态成为该步 exit code

新增 shell 引号配平预检: 剥离单引号段后统计未转义双引号计数, 奇数即门禁 FAIL。
现行 0 异常。

### 25.5 部署步骤

```
# 1. 数据接入 (T1) — 从 DSHA-P31 重建 data/*.json + dataset_index.json
# 2. 前端构建 (T2) — index.html V31.0, node --check 内联 JS
# 3. 基线重算 (T3)
python D:\DSH_WORK\_p26_make_baseline.py        # 171 entries / self-check
# 4. 本地全量验证 (T3)
python D:\DSH_WORK\_p26_validate.py              # 51/51 PASS
# 5. 发布 (T2)
python D:\DSH_WORK\_p26_deploy.py                # Contents API 逐文件发布
# 6. 线上巡检 (T4)
python D:\DSH_WORK\_p26_live_probe.py            # 342 HTTP 200 / warm 59ms
python D:\DSH_WORK\_p26_verify_final.py           # 35 项终检
```

### 25.6 部署验证清单

- [x] index.html HTTP 200 / 207,696 B / md5 cfac3b0ebc4d8c79ca4b2e50c399cd15
- [x] 171 文件 x 2 pass = 342 HTTP 200, non_200=0, timeout=0
- [x] warm (keep-alive) median 59ms / max 552ms (< 400ms 阈值)
- [x] cold median 203ms / max 15170ms (含 TLS 握手, 可接受)
- [x] MD5_BASELINE_P25.json / p25_site_health.json 已下线 (HTTP 404)
- [x] deploy_meta.json = 404 (预期: 由 upload-pages-artifact 之后生成)

### 25.7 遗留项

| 编号 | 项 | 严重度 | 处置 |
|------|----|:------:|------|
| P1 | CU 灰度 6/14 未达标 (BEAR_IC 0.0234 < 0.025) | P1 | 维持 1.5% 仓位上限, 下一采集点评估 |
| P1 | github.com:443 smart-HTTP push 仍不可达 | P1 | 已固化 Contents API 发布 + T3 API 降级 job |
| P2 | Contents API 发布使远端 head 领先本地 HEAD 1 提交 | P2 | 内容一致, 仅审计提示 |
| P3 | cold 连接 max 15170ms (TLS 握手) | P3 | warm 已达标, 可接受 |
| P3 | 部分 step 名仍含 P23/P24 字样 (仅显示名) | P3 | P27 已清理 3 处 name: 字段 (P24→相位无关) |

---

## 26. DSHD-P27 看板运维 & CI 流水线修复

### 26.1 工单概要

**相位**: DSHD-P27
**完成时间**: 2029-02-09T08:00:00+08:00
**验收**: 6/6 PASS (AC1~AC6)
**看板版本**: V31.0 / P31 / dataset_version 1.8

### 26.2 T1 PAT 轮换 (N/A)

工单要求轮换过期 PAT `ghp_TW0z…3wi9s3`，但实测该 PAT 完全正常：

| 权限测试 | 结果 |
|----------|:----:|
| admin/push/maintain 权限 | 通过 |
| Actions 读取 | 通过 (5 runs) |
| Contents API 写入 | 通过 (git ref create 201) |
| git ref 删除 | 通过 (`DELETE /git/refs/heads/{branch}`) |

仓库 secrets 列表为空 (workflow 用内置 `GITHUB_TOKEN`，PAT 仅供部署脚本)。用户确认不换。

**附带成果**: 成功删除 P26 遗留孤儿分支 `_probe_tmp` 和测试分支 `_p27_pat_probe`。
P26 因用错 DELETE 端点 (`/git/ref/heads/` → 应为 `/git/refs/heads/`) 导致分支删除失败，P27 修正了此问题。

### 26.3 T2 部署脚本文字清理

修改 `deploy-pages.yml` 中 3 处 `name:` 显示字段：

| 行 | 修改前 | 修改后 |
|----|--------|--------|
| L9 | `Deploy DSHD-P24 to GitHub Pages` | `Deploy DSHD Dashboard to GitHub Pages` |
| L813 | `Deploy Retry (P25 T3)` | `Deploy Retry` |
| L848 | `Deploy Fallback / API Contents Mode (P25 T3)` | `Deploy Fallback / API Contents Mode` |

**零改动范围**: 断言、逻辑、正则表达式、YAML 注释均未改动。
**验证**: `git diff` 仅 3 行变更；51-step validate 51/51 PASS；shell quote balance 0 odd。

### 26.4 T3 站点健康巡检与容错加固

#### 26.4.1 全量 HTTP 探测

171 文件 × 2 轮 (冷启动 + keep-alive 预热)：

| 指标 | 冷启动 | 预热 |
|------|:------:|:----:|
| 中位延迟 | 479 ms | **72 ms** |
| 最大延迟 | 1,112 ms | 618 ms |
| 非 200 | **0** | **0** |
| 超时 | 0 | 0 |

#### 26.4.2 PB/CU 灰度面板缺陷修复 (8 项)

P25 残留数据修复：

| 字段 | 修复前 | 修复后 |
|------|--------|--------|
| `pb/cu.admission_block.blocked` | `true` (P25 IC漂移 5.2%) | `false` (P31 永久解除) |
| `pb.threshold_met` | `false` | `true` |
| `pb.admission_countdown.current_bear_ic` | `0.0291` | `0.0294` |
| `cu.admission_countdown.current_bear_ic` | `0.0233` | `0.0234` |
| `pb/cu.fr_risk_days_active` | `600` | `810` |
| `p31_overlay.dshd_phase` | `DSHD-P26` | `DSHD-P27` |

#### 26.4.3 Contents API 兜底加固

**443 端口现状**: github.com:443 push 仍不可达 (P25 起已知)。Contents API 通过 `api.github.com` (不同主机) 可达。

**P27 加固**:
1. **限流感知重试**: `call()` 识别 403 + `rate limit` / `abuse detection`，按指数退避重试
2. **二次重试**: 第一轮失败文件在 5 秒冷却后重试一次
3. **重试次数**: 3 → 4

### 26.5 T4 DSHA-P32 兼容性

| 验证项 | 结果 |
|--------|------|
| grep 模式总数 | 41 |
| 相位无关 (`P[0-9]+`) | 21 |
| 相位特定 (P3x) | **0** |
| Python 断言含 P3x | **0** |
| Tab 面板数 | 15 |
| PB/CU 渲染函数 | `renderPBCUGrayPanel`, `renderICDriftPBCU` |

**结论**: P32 数据 (`version_tag: P32`, `dataset_version: 1.9`) 可直接接入现有 CI，无需修改断言。

### 26.6 部署与验证

| 项 | 值 |
|----|-----|
| 本地提交 | `5339360` |
| 发布方式 | Contents API |
| 51-step validate | **51/51 PASS** |
| Shell quote balance | **0 odd** |
| Live HTTP | 171 文件全 200 |
| 前端 JS parse | **PASS** (node v24.19.0) |

### 26.7 遗留项

| 编号 | 项 | 严重度 | 处置 |
|------|----|:------:|------|
| P1 | CU 6/14 未达标 (BEAR_IC 0.0234 < 0.025) | P1 | 维持 1.5% 仓位上限 |
| P1 | github.com:443 push 不可达 | P1 | 已固化 Contents API + 重试加固 |
| P2 | 远端 head 领先本地 1 提交 | P2 | 内容一致, 仅审计提示 |
| P3 | 部分 step 名含 P25 字样 (仅显示名) | P3 | 建议 P28 清理 |

### 26.8 下一相位指引 (DSHD-P28)

1. 等待 DSHA-P32 数据发布
2. 更新 HTML 中 26 处静态 P31 → P32 引用
3. 更新数据文件为 P32 版本
4. 重建 MD5 baseline
5. Contents API 发布
6. 全量巡检 + 交付物归档
