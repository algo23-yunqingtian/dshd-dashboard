# DSHD-P35 Deployment Manual

## Deployment Steps

### 1. Data Generation
```bash
cd github工作/回测
python dsha_p39_exec.py 2>&1 | Out-File dsha_p39_exec_out.log
```

### 2. Data Update
```bash
cd D:\DSH_WORK
python _p35_t1_update.py      # Update JSON files
python _p35_fix_data.py       # Fix structures
python _p35_t1_html.py        # Update HTML
```

### 3. Validation
```bash
python _p35_t2_validate.py    # Local validation (75/75 PASS)
python _p35_t4_defects.py     # Defect checks
python _p35_t4b_fix.py        # Fix defects
```

### 4. Deployment
```bash
python _p35_t3_deploy.py           # Deploy to main branch
python _p35_t3_deploy_ghpages.py  # Deploy to gh-pages branch
```

### 5. Verification
```bash
python _check_live.py     # Check live site
python _verify_deploy.py  # Verify all branches
```

## Deployment Details
- Method: GitHub Contents API (no git push)
- Main branch: 48 files uploaded
- gh-pages branch: 47 files uploaded
- CI workflow: deploy-pages.yml (workflow_dispatch)
- Live site: https://algo23-yunqingtian.github.io/dshd-dashboard/

## Rollback
To rollback to V38.0:
1. Restore from web_site/index.html.bak_p24
2. Restore data/ from web_site/data/ (P38 versions)
3. Restore PHASE38_DATA_READY.flag
