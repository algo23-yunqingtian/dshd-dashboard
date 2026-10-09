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
