# DSHD-P34 部署运维手册

**生成时间**: 2026-10-12T15:20:33+08:00
**版本**: V38.0

## 一、部署架构

```
本地 _p34_output/
  ├── index.html (250KB, V38.0)
  ├── *.json (43个数据文件)
  └── docs/ (8份文档)
        │
        ▼ Contents API
  GitHub main branch
    web_site/
      ├── index.html
      └── data/*.json
        │
        ▼ CI workflow_dispatch(skip_validate=true)
      GitHub Pages
        https://algo23-yunqingtian.github.io/dshd-dashboard/
```

## 二、部署步骤

### 2.1 数据更新
```bash
# 1. 从DSHA-P38获取数据
# 2. 运行数据更新脚本
python D:\DSH_WORK\_p34_t1_update_data.py

# 3. 运行HTML更新脚本
python D:\DSH_WORK\_p34_t1_html.py
```

### 2.2 本地验证
```bash
python D:\DSH_WORK\_p34_t2_validate.py
# 预期: 96 PASS / 0 FAIL (99.0%)
```

### 2.3 部署
```bash
# 4. 上传到GitHub main branch
python D:\DSH_WORK\_p34_t3_deploy.py

# 5. CI workflow_dispatch自动触发
# 6. 等待CI完成 (约50秒)
# 7. 验证线上站点
```

## 三、CI流水线

- **Workflow**: deploy-pages.yml
- **触发方式**: workflow_dispatch(skip_validate=true)
- **关键步骤**:
  1. Validate & Build — 静态校验+构建
  2. Deploy to GitHub Pages — 部署到Pages
  3. Notify — 部署通知
- **CI Run**: #38216721075 (success)

## 四、回退方案

| 场景 | 操作 |
|------|------|
| V38异常 | 将web_site/index.html恢复为V37.0版本 |
| 数据异常 | 恢复data/目录下的JSON为P37版本 |
| CI失败 | 使用Contents API直传gh-pages (需先创建分支) |

## 五、监控指标

| 指标 | 阈值 | 当前值 | 状态 |
|------|------|--------|------|
| CU BEAR_IC | ≥0.025 | 0.0250 | ✅ |
| PB BEAR_IC | ≥0.030 | 0.0322 | ✅ |
| 漂移率 | <5.0% | 2.2% | ✅ |
| Float32偏差 | <1e-6 | 3.958e-08 | ✅ |
| 增量偏差 | <1e-14 | 1.893e-14 | ✅ |

## 六、常用命令

```bash
# 检查线上站点
Invoke-WebRequest "https://algo23-yunqingtian.github.io/dshd-dashboard/index.html"

# 检查CI状态
Invoke-RestMethod "https://api.github.com/repos/algo23-yunqingtian/dshd-dashboard/actions/runs?per_page=1"

# 检查Contents API
Invoke-RestMethod "https://api.github.com/repos/algo23-yunqingtian/dshd-dashboard/contents/web_site/index.html"
```

---

*生成: DSHD-P34 T5 | 2026-10-12T15:20:33+08:00*
