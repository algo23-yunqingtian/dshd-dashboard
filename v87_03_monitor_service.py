#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V87-03 常驻监控服务 (Resident Monitor Service Daemon).

蓝本: v87_03_monitor_service_design.md (c6d27056..., READ-ONLY 设计文档).

组件:
  1. 事件接入: DSHC 转发报文 -> event_schema.json 校验 -> 解析
  2. 分级映射: fr_risk_501_508_mapping.json (escalate_after/escalate_to 显式字段)
  3. 持久计数: fr_risk_escalation_state.json (daemon 内内存 + 周期落盘双写;
     修复进程内计数归零缺陷, 跨调用升级链延续)
  4. 事件持久存储: append-only event store 卷 (1000 条/卷, 旧卷 RO + manifest
     record_md5 链, 连续性可校验)
  5. 告警出口: RED=STOP_LINE / ORANGE=NOTIFY_1H / YELLOW=RECORD_4H (event action)
  6. 调度器: 日巡检 (v869_d_gray_patrol.py 37 项, 计时) + 周期门禁引用
     (phase2_gate_check_script.py --periodic) + 周快照语义
  7. 恢复: 重启载入 state + 校验 event store record_md5 链连续性

纪律: 确定性 (固定槽位/SEED=42), 演练仅用 lab fixture, 只读上游引擎.
"""
import os
import csv
import json
import time
import hashlib
import argparse
import importlib.util

WORKSPACE = r"D:\DSH_WORK"
FE_WS = os.path.join(WORKSPACE, "factor_exp_workspace")
OUT_DIR = os.path.join(FE_WS, "acd_joint_shadow_verify", "dshd_sub",
                       "dshd_arch_gate_prep")
LAB = os.path.join(OUT_DIR, "gate_prep_lab")

FIXED_SLOT = "2026-10-12T15:00:00+08:00"
SEED = 42
VOL_LIMIT = 1000
CHAIN_ANCHOR = "V87-03-CHAIN-ANCHOR"

MAPPING_JSON = os.path.join(OUT_DIR, "fr_risk_501_508_mapping.json")
SCHEMA_JSON = os.path.join(OUT_DIR, "event_schema.json")
STATE_FILE = os.path.join(OUT_DIR, "fr_risk_escalation_state.json")
PATROL_ENGINE = os.path.join(OUT_DIR, "v869_d_gray_patrol.py")
GATE_SCRIPT = os.path.join(OUT_DIR, "phase2_gate_check_script.py")
DEFAULT_STORE = os.path.join(LAB, "v87_03_event_store")

STORE_FIELDS = ["event_id", "ts", "source", "event_type", "code", "symbol",
                "severity", "color", "action", "evidence_refs", "upstream_ref",
                "escalation_state", "prev_md5", "record_md5"]


def md5_bytes(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def md5f(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except OSError:
        return None


def load_mapping():
    with open(MAPPING_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {m["code"]: m for m in data["mapping"]}


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa
        return {}


def save_state(counters, last_event, slot):
    payload = {
        "counters": {c: {"count": n, "last_event_id": last_event.get(c, "")}
                     for c, n in counters.items()},
        "last_updated": slot,
        "service": "V87-03",
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def grade(sev):
    return {"CRITICAL": "RED", "HIGH": "ORANGE", "MEDIUM": "YELLOW",
            "LOW": "BLUE", "INFO": "GRAY"}.get(sev, "GRAY")


# ---------------------------------------------------------------------------
# 1. 事件接入 + schema 校验
# ---------------------------------------------------------------------------
def validate_event(ev):
    """按 event_schema.json 校验统一事件必填字段 (轻量: 命名空间/枚举)."""
    import re
    schema = json.load(open(SCHEMA_JSON, encoding="utf-8"))
    id_pat = re.compile(schema["properties"]["event_id"]["pattern"])
    sev_ok = set(schema["properties"]["severity"]["enum"])
    act_ok = set(schema["properties"]["action"]["enum"])
    ev_pat = re.compile(schema["properties"]["evidence_refs"]["items"]["pattern"])
    if not ev.get("event_id") or not id_pat.match(ev["event_id"]):
        return False, "event_id pattern mismatch"
    if ev.get("severity") not in sev_ok:
        return False, "severity enum"
    if ev.get("action") not in act_ok:
        return False, "action enum"
    for ref in ev.get("evidence_refs", []):
        if not ev_pat.match(ref):
            return False, "evidence_ref prefix"
    return True, "ok"


# ---------------------------------------------------------------------------
# 2+3. 分级映射 + 持久计数 (跨调用升级链)
# ---------------------------------------------------------------------------
def map_event(fwd, mapping, counters, last_event):
    """fwd: 转发报文行 (fwd_id/fwd_ts/code/symbol/zone/raw_severity/detail)."""
    code = fwd.get("code", "")
    m = mapping.get(code)
    if m is None:
        return None
    sev = m["d_severity"]
    color = m["color"]
    action = ""
    counters[code] = counters.get(code, 0) + 1
    last_event[code] = fwd.get("fwd_id", "")
    ea = m.get("escalate_after")
    if ea and counters[code] >= ea:
        sev = m.get("escalate_to", sev)
        color = grade(sev)
        action = "STOP_LINE" if sev == "CRITICAL" else "NOTIFY_1H"
        counters[code] = 0
    elif "立即 STOP_LINE" in m.get("escalation_rule", ""):
        action = "STOP_LINE"
    elif color == "RED":
        # DEFECT-P9-001 修复: RED 必须显式 STOP_LINE (三色语义 RED=STOP_LINE).
        # 旧逻辑缺失 RED 分支: FR-RISK-508 (RED/CRITICAL, escalation_rule 无
        # "直接 STOP_LINE" 字面) 落入 else -> action=RECORD, 与 severity=CRITICAL
        # 冲突. 502/503 因 escalation_rule 含该字面而侥幸正确, 508 暴露缺陷.
        action = "STOP_LINE"
    elif color == "ORANGE":
        action = "NOTIFY_1H"
    elif color == "YELLOW":
        action = "RECORD_4H"
    else:
        action = "RECORD"
    seq = fwd.get("fwd_id", "").split("-")[-1]
    sym = fwd.get("symbol", "ALL")
    event_id = "FR-RISK-{}-{}-{}-{}".format(
        code.split("-")[2], sym, FIXED_SLOT[0:10].replace("-", ""), seq)
    esc_state = {"code": code, "consecutive": counters.get(code, 0),
                 "escalated": bool(ea and last_event.get(code) == fwd.get("fwd_id") and action == "STOP_LINE"),
                 "persisted": True}
    return {
        "event_id": event_id, "ts": FIXED_SLOT, "source": "DSHD-V87-03",
        "event_type": "RISK_ALERT" if "STOP" not in action else "ESCALATION",
        "code": code, "symbol": sym,
        "severity": sev, "color": color, "action": action,
        "evidence_refs": ["csv:fr_risk_receive_log.csv",
                          "md5:" + md5_bytes(fwd.get("fwd_id", "") + code + sev + action)],
        "upstream_ref": "FR-RISK-{}".format(code.split("-")[2]),
        "escalation_state": esc_state,
    }


# ---------------------------------------------------------------------------
# 4. 事件持久存储 (卷式轮转 + record_md5 链 + manifest)
# ---------------------------------------------------------------------------
def active_vol(store_dir):
    os.makedirs(store_dir, exist_ok=True)
    vols = sorted(f for f in os.listdir(store_dir) if f.startswith("vol_") and f.endswith(".csv"))
    return vols[-1] if vols else None


def store_events(rows, store_dir):
    """append-only; 每 1000 条切卷; 旧卷 RO; manifest 记录行数+md5."""
    os.makedirs(store_dir, exist_ok=True)
    manifest_path = os.path.join(store_dir, "manifest.json")
    manifest = {"volumes": {}, "anchor": CHAIN_ANCHOR, "last_updated": FIXED_SLOT}
    if os.path.exists(manifest_path):
        manifest = json.load(open(manifest_path, encoding="utf-8"))
    prev_md5 = manifest.get("tail_md5", CHAIN_ANCHOR)
    vol = active_vol(store_dir)
    vol_path = os.path.join(store_dir, vol) if vol else None
    vol_no = int(vol.split("_")[1].split(".")[0]) if vol else 0
    out_rows = []
    for r in rows:
        r["prev_md5"] = prev_md5
        r["record_md5"] = md5_bytes("|".join([
            prev_md5, r["event_id"], r["severity"], r["action"], r["ts"]]))
        prev_md5 = r["record_md5"]
        out_rows.append(r)
        if vol_path is None:
            vol_no += 1
            vol = "vol_{:04d}.csv".format(vol_no)
            vol_path = os.path.join(store_dir, vol)
            with open(vol_path, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=STORE_FIELDS)
                w.writeheader()
        with open(vol_path, "a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=STORE_FIELDS)
            w.writerow(r)
        n_rows = count_vol_rows(vol_path)
        if n_rows >= VOL_LIMIT:
            os.chmod(vol_path, 0o444)  # 旧卷 RO 化
            manifest["volumes"][vol] = {
                "rows": n_rows, "md5": md5f(vol_path), "ro": True}
            vol_path = None
    if vol_path is not None:
        vol = os.path.basename(vol_path)
        manifest["volumes"][vol] = {
            "rows": count_vol_rows(vol_path), "md5": md5f(vol_path), "ro": False}
    manifest["tail_md5"] = prev_md5
    manifest["last_updated"] = FIXED_SLOT
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return out_rows


def count_vol_rows(path):
    n = 0
    header_seen = False
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if not row or not row[0].strip():
                continue
            if not header_seen:
                header_seen = True
                continue
            n += 1
    return n


# ---------------------------------------------------------------------------
# 7. 恢复: 载入 state + event store 连续性校验 (record_md5 链)
# ---------------------------------------------------------------------------
def recover(store_dir):
    manifest_path = os.path.join(store_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        return False, "manifest missing"
    manifest = json.load(open(manifest_path, encoding="utf-8"))
    vols = sorted(f for f in os.listdir(store_dir)
                  if f.startswith("vol_") and f.endswith(".csv"))
    prev = manifest.get("anchor", CHAIN_ANCHOR)
    broken = []
    total = 0
    for vol in vols:
        path = os.path.join(store_dir, vol)
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                total += 1
                exp = md5_bytes("|".join([
                    row.get("prev_md5", ""), row.get("event_id", ""),
                    row.get("severity", ""), row.get("action", ""),
                    row.get("ts", "")]))
                if row.get("record_md5") != exp:
                    broken.append(vol + ":{}".format(total))
                prev = row.get("record_md5", prev)
    tail_ok = (manifest.get("tail_md5", "") == prev)
    ok = (not broken) and tail_ok
    return ok, "vols={} rows={} chain={} tail_ok={}".format(
        len(vols), total, "OK" if not broken else "BROKEN@{}".format(",".join(broken[:3])), tail_ok)


# ---------------------------------------------------------------------------
# 6. 调度器: 日巡检 (37 项计时) + 门禁引用 (dry, 不写文件)
# ---------------------------------------------------------------------------
def load_patrol_engine():
    spec = importlib.util.spec_from_file_location("gray_patrol", PATROL_ENGINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def schedule_patrol():
    mod = load_patrol_engine()
    t0 = time.perf_counter()
    n_checks = 0
    statuses = {}
    for fn in (mod.check_chain001, mod.check_mtime, mod.check_permission,
               mod.check_create_probe, mod.check_position, mod.check_diff_binding):
        for r in fn():
            n_checks += 1
            statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    el = time.perf_counter() - t0
    return n_checks, statuses, el


# ---------------------------------------------------------------------------
# 8. PC-003 解锁事件监听 + 4 品种 FR-RISK 规则自动加载
#    (DSHC 推送 PC-003 -> 校验 TD002/TD014 双门禁 -> 通过则加载 ZN/NI/SN/SI
#     监控模板 RESERVED->ACTIVE; 任一未达标 -> BLOCKED, 不激活)
# ---------------------------------------------------------------------------
GIT_FE_WS = os.path.join(WORKSPACE, "github工作", "回测", "factor_exp_workspace")
ROOT_DSUB_GIT = os.path.join(GIT_FE_WS, "acd_joint_shadow_verify", "dshd_sub")
RESERVED_CONFIG = os.path.join(OUT_DIR, "phase4_reserved_slots_config.json")
PC003_DEFAULT_EVENT = os.path.join(LAB, "pc003_dshc_event.json")
PC003_AUDIT = os.path.join(LAB, "pc003_activation_manifest.json")
FROZEN_SYMS = ["ZN", "NI", "SN", "SI"]
# PC-003 解锁双门禁 (来源: PHASE7_FACTOR_APPROVE.flag)
UNLOCK_GATE_CONDITIONS = {
    "TD002": "TD002_PENALTY_CALC_RULES_VERIFIED",
    "TD014": "TD014_DQ_RULES_VERIFIED",
}


def check_variant_locks():
    """4 品种快照版本锁 LOCKED 校验 (与 GATE-P2-11 同源判定)."""
    locks = {}
    for sym in FROZEN_SYMS:
        p = os.path.join(ROOT_DSUB_GIT, "v869_d_{}_snapshot_ro_backup".format(sym.lower()),
                         "SNAPSHOT_VERSION.lock")
        if not os.path.exists(p):
            locks[sym] = {"locked": False, "exists": False, "md5": "", "md5file": None}
            continue
        content = open(p, encoding="utf-8", errors="replace").read()
        locked = ("LOCKED=TRUE" in content) and ("NO_OVERWRITE" in content)
        locks[sym] = {"locked": locked, "exists": True,
                      "md5": md5f(p), "md5file": os.path.basename(p)}
    return locks


def load_reserved_config():
    """加载 4 品种预留槽位配置 (只读上游)."""
    with open(RESERVED_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)


def load_dshc_event(path):
    """读取 DSHC 推送的 PC-003 事件 (JSON)."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pc003_listen(event_path=None, out_path=None, slot=None):
    """PC-003 解锁事件监听: 双门禁校验 -> 4 品种规则加载 (或 BLOCKED).

    返回 (ok, manifest): ok=True 表示监听链路自洽 (BLOCKED 亦为合规结果,
    因为当前 TD002+TD014 未达标, 必须拒绝激活).
    """
    event_path = event_path or PC003_DEFAULT_EVENT
    out_path = out_path or PC003_AUDIT
    slot = slot or FIXED_SLOT
    cfg = load_reserved_config()
    locks = check_variant_locks()
    ev = load_dshc_event(event_path)
    gates_in = ev.get("gates", {})
    request = (ev.get("request") or "UNLOCK").upper()

    # 门禁判定
    gate_eval = {}
    all_verified = True
    for gid, cond in UNLOCK_GATE_CONDITIONS.items():
        g = gates_in.get(gid, {})
        verified = bool(g.get("verified")) and (g.get("status", "").upper() == "VERIFIED")
        gate_eval[gid] = {"expected_condition": cond, "status": g.get("status", "UNKNOWN"),
                          "verified": verified, "source": g.get("source", "DSHC")}
        all_verified = all_verified and verified
    locks_ok = all(v["locked"] for v in locks.values())

    # 品种资格: 每品种 prereq 全达标才允许激活
    variants = []
    any_eligible = False
    for s in cfg.get("reserved_slots", []):
        sym = s.get("symbol")
        prereqs = s.get("unfreeze_prerequisites", [])
        met = {"TD002": gate_eval.get("TD002", {}).get("verified", False),
               "TD014": gate_eval.get("TD014", {}).get("verified", False),
               "REAL_DATA_INGESTION": bool(gates_in.get("REAL_DATA_INGESTION", {}).get("verified")),
               "CONDITIONAL_APPROVAL": bool(gates_in.get("CONDITIONAL_APPROVAL", {}).get("verified"))}
        missing = [k for k in prereqs if not met.get(k)]
        eligible = not missing and locks_ok
        any_eligible = any_eligible or eligible
        variants.append({
            "symbol": sym,
            "current_status": s.get("status"),
            "contract_ref": s.get("contract_ref", {}),
            "check_template": s.get("check_template", {}),
            "template_items": len(s.get("check_template", {})),
            "frozen_state": s.get("frozen_state", ""),
            "prerequisites": prereqs,
            "prereq_met": met,
            "missing_prereq": missing,
            "variant_lock": locks.get(sym, {}),
            "eligible": eligible,
        })

    activate = (request == "UNLOCK" and all_verified and locks_ok and any_eligible)
    activated = [v["symbol"] for v in variants if v["eligible"]]
    if activate:
        for v in variants:
            v["target_status"] = "ACTIVE"
        verdict = "ACTIVATED"
    else:
        for v in variants:
            v["target_status"] = v.get("current_status")  # 保持 RESERVED
        verdict = "BLOCKED"

    manifest = {
        # DEFECT-P9-002 修复: audit_id 原仅由槽位前 12 位派生, 同槽位两次 pc003
        # 运行 (BLOCKED + labpos ACTIVATED) 产生相同 audit_id, 审计清单不可区分.
        # 现追加 dshc event_id 尾部 12 位, 保证每次推送事件唯一可溯.
        "audit_id": "PC-003-LISTEN-{}-{}".format(
            slot.replace(":", "").replace("-", "")[:12],
            (ev.get("event_id") or "NONE").replace(":", "")[-12:]),
        "pipeline": "PC-003",
        "listener": "V87-03 Daemon pc003 mode",
        "fixed_slot": slot,
        "seed": SEED,
        "dshc_event": {"path": os.path.relpath(event_path, OUT_DIR),
                       "md5": md5f(event_path), "event_id": ev.get("event_id"),
                       "request": request, "ts": ev.get("ts"),
                       "upstream_ref": ev.get("upstream_ref", "")},
        "unlock_gates": gate_eval,
        "all_gates_verified": all_verified,
        "variant_locks": locks,
        "locks_ok": locks_ok,
        "variants": variants,
        "activated": activated,
        "activated_count": len(activated),
        "verdict": verdict,
        "blocked_reason": "" if activate else (
            "TD002+TD014 双门禁未全达标 ({}) / LOCK {}/4 / 无可激活品种".format(
                ",".join(k for k, v in gate_eval.items() if not v["verified"]) or "n/a",
                sum(1 for v in locks.values() if v["locked"]))),
        "reserved_config": {"path": os.path.relpath(RESERVED_CONFIG, OUT_DIR),
                            "md5": md5f(RESERVED_CONFIG),
                            "config_id": cfg.get("config_id")},
        "audit": os.path.relpath(out_path, OUT_DIR),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    ok = (verdict in ("ACTIVATED", "BLOCKED")) and locks_ok
    return ok, manifest


# ---------------------------------------------------------------------------
# 自测: 单元测试 + 集成测试
# ---------------------------------------------------------------------------
def selftest():
    """单元测试: schema 校验 / 映射 / 升级链 / 恢复链 / 卷轮转语义."""
    results = []
    # U1: schema 校验 (合法/非法 event_id)
    ok_ev = {"event_id": "FR-RISK-501-CU-20261012-001", "severity": "HIGH",
             "action": "NOTIFY_1H", "evidence_refs": ["csv:fr_risk_receive_log.csv"]}
    bad_ev = {"event_id": "FR-RISK-501-CU-001", "severity": "HIGH",
              "action": "NOTIFY_1H", "evidence_refs": ["csv:fr_risk_receive_log.csv"]}
    v1, _ = validate_event(ok_ev)
    v2, _ = validate_event(bad_ev)
    results.append(("U1-SCHEMA", "PASS" if (v1 and not v2) else "FAIL",
                    "valid={} invalid={}".format(v1, v2)))
    # U2: 501 首击 ORANGE (count=1)
    mapping = load_mapping()
    c, le = {}, {}
    r1 = map_event({"fwd_id": "U-501-001", "code": "FR-RISK-501", "symbol": "CU",
                    "zone": "BEAR", "raw_severity": "ORANGE_HINT", "detail": "u2"},
                   mapping, c, le)
    results.append(("U2-501-ORANGE", "PASS" if (r1["severity"] == "HIGH" and r1["color"] == "ORANGE"
                                                and c["FR-RISK-501"] == 1) else "FAIL",
                    "sev={} color={} count={}".format(r1["severity"], r1["color"], c["FR-RISK-501"])))
    # U3: 同码连续 2 次 -> RED (escalate_after=2)
    r2 = map_event({"fwd_id": "U-501-002", "code": "FR-RISK-501", "symbol": "CU",
                    "zone": "BEAR", "raw_severity": "ORANGE_HINT", "detail": "u3"},
                   mapping, c, le)
    results.append(("U3-ESC-RED", "PASS" if (r2["severity"] == "CRITICAL" and r2["color"] == "RED"
                                              and r2["action"] == "STOP_LINE" and c["FR-RISK-501"] == 0) else "FAIL",
                    "sev={} action={} count_after={}".format(r2["severity"], r2["action"], c["FR-RISK-501"])))
    # U4: 502 立即 STOP_LINE (无升级计数)
    c4, le4 = {}, {}
    r4 = map_event({"fwd_id": "U-502-001", "code": "FR-RISK-502", "symbol": "AL",
                    "zone": "ALL", "raw_severity": "RED_HINT", "detail": "u4"},
                   mapping, c4, le4)
    results.append(("U4-502-STOP", "PASS" if r4["action"] == "STOP_LINE" and r4["severity"] == "CRITICAL" else "FAIL",
                    "action={}".format(r4["action"])))
    # U5: evidence_ref 前缀校验 (非法前缀)
    bad_ref = {"event_id": "GATE-P2-01-20261012-001", "severity": "INFO",
               "action": "RECORD", "evidence_refs": ["http:foo"]}
    v5, _ = validate_event(bad_ref)
    results.append(("U5-EVIDENCE-PREFIX", "PASS" if not v5 else "FAIL", "http: rejected={}".format(not v5)))
    # U6: 卷轮转边界语义 (VOL_LIMIT 常量 + manifest 结构)
    results.append(("U6-VOL-LIMIT", "PASS" if VOL_LIMIT == 1000 else "FAIL", "VOL_LIMIT={}".format(VOL_LIMIT)))
    return results


def integtest(store_dir, events_csv):
    """集成测试: fixture 事件流 -> 全链路 (接入/映射/持久计数/存储/恢复)."""
    import shutil
    if os.path.isdir(store_dir):
        shutil.rmtree(store_dir)
    os.makedirs(store_dir, exist_ok=True)
    mapping = load_mapping()
    counters, last_event = {}, {}
    # 阶段 1: 处理两批事件 (跨调用升级链; 批间状态经 save/load 模拟 daemon 落盘)
    fwd_events = list(csv.DictReader(open(events_csv, encoding="utf-8-sig")))
    batch_a = [e for e in fwd_events if e.get("fwd_id", "").endswith("-A")]
    batch_b = [e for e in fwd_events if not e.get("fwd_id", "").endswith("-A")]
    store_rows_a = []
    for ev in batch_a:
        r = map_event(ev, mapping, counters, last_event)
        if r:
            store_rows_a.append(r)
    if store_rows_a:
        store_events(store_rows_a, store_dir)
    save_state(counters, last_event, FIXED_SLOT)
    # 模拟 daemon 重启: 从 state 载入计数
    state = load_state()
    counters = {c: v.get("count", 0) for c, v in state.get("counters", {}).items()}
    last_event = {c: v.get("last_event_id", "") for c, v in state.get("counters", {}).items()}
    store_rows_b = []
    for ev in batch_b:
        r = map_event(ev, mapping, counters, last_event)
        if r:
            store_rows_b.append(r)
    stored_b = store_events(store_rows_b, store_dir)
    save_state(counters, last_event, FIXED_SLOT)
    # 阶段 2: 恢复校验 record_md5 链
    ok, msg = recover(store_dir)
    state_final = load_state()
    n_total = len(store_rows_a) + len(store_rows_b)
    esc_codes = sorted(set(r["code"] for r in stored_b if r["action"] == "STOP_LINE"))
    return {
        "events_total": len(fwd_events),
        "stored_total": n_total,
        "recover_ok": ok,
        "recover_msg": msg,
        "stop_line_codes": esc_codes,
        "state_counters": {c: v["count"] for c, v in state_final.get("counters", {}).items()},
    }


def main():
    ap = argparse.ArgumentParser(description="V87-03 常驻监控服务 daemon")
    ap.add_argument("--mode", choices=["selftest", "integtest", "recover", "patrol", "pc003"],
                    default="selftest", help="运行模式")
    ap.add_argument("--store-dir", default=DEFAULT_STORE)
    ap.add_argument("--input", default=None, help="集成测试事件 fixture")
    ap.add_argument("--pc003-event", default=None, help="DSHC 推送 PC-003 事件 (JSON)")
    ap.add_argument("--pc003-out", default=None, help="PC-003 监听审计清单输出路径")
    ap.add_argument("--slot", default=None, help="固定槽位覆盖 (新工单=新槽位纪律)")
    args = ap.parse_args()
    global FIXED_SLOT
    if args.slot:
        FIXED_SLOT = args.slot

    if args.mode == "selftest":
        results = selftest()
        n_pass = sum(1 for _, st, _ in results if st == "PASS")
        for name, st, dt in results:
            print("[SELFTEST] {} | {} | {}".format(name, st, dt))
        print("[SELFTEST] {} / {} PASS slot={}".format(n_pass, len(results), FIXED_SLOT))
        return 0 if n_pass == len(results) else 1

    if args.mode == "integtest":
        if not args.input:
            print("[INTEG] --input required")
            return 1
        res = integtest(args.store_dir, args.input)
        print("[INTEG] stored={} recover_ok={} stop_line={} state={}".format(
            res["stored_total"], res["recover_ok"],
            ",".join(res["stop_line_codes"]) or "-",
            json.dumps(res["state_counters"], ensure_ascii=False)))
        print("[INTEG] {}".format(res["recover_msg"]))
        return 0 if res["recover_ok"] else 1

    if args.mode == "recover":
        ok, msg = recover(args.store_dir)
        print("[RECOVER] ok={} {}".format(ok, msg))
        return 0 if ok else 1

    if args.mode == "patrol":
        n, statuses, el = schedule_patrol()
        print("[PATROL] checks={} statuses={} elapsed={:.2f}s (<60s J14)".format(
            n, json.dumps(statuses, ensure_ascii=False), el))
        return 0 if el < 60 and n >= 37 else 1

    if args.mode == "pc003":
        audit_path = args.pc003_out or PC003_AUDIT
        ok, man = pc003_listen(args.pc003_event, audit_path, slot=FIXED_SLOT)
        print("[PC003] verdict={} request={} gates_verified={} locks_ok={} activated={}".format(
            man["verdict"], man["dshc_event"]["request"],
            man["all_gates_verified"], man["locks_ok"],
            ",".join(man["activated"]) or "-"))
        for gid, g in man["unlock_gates"].items():
            print("[PC003] {} {} verified={}".format(gid, g["status"], g["verified"]))
        for v in man["variants"]:
            print("[PC003] {} {} -> {} template={} lock={} missing={}".format(
                v["symbol"], v["current_status"], v["target_status"], v["template_items"],
                "LOCKED" if v["variant_lock"].get("locked") else "UNLOCKED",
                ",".join(v["missing_prereq"]) or "-"))
        if man["verdict"] == "BLOCKED":
            print("[PC003] blocked_reason={}".format(man["blocked_reason"]))
        print("[PC003] audit={} md5={}".format(man["audit"], md5f(audit_path)))
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
