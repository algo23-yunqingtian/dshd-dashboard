#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V87 告警事件导出接口 (VIS Alert Export API).

用途: 为 DSHA 可视化工作台时序图风险标记提供结构化告警事件.
- 从三处数据源聚合 FR-RISK 告警与门禁事件:
  1) fr_risk_receive_log.csv            (接收日志, 持久升级链)
  2) gate_periodic_check_log.csv        (周期门禁巡检)
  3) gate_prep_lab/v87_03_event_store/  (V87-03 daemon 事件卷, record_md5 链)
- 输出结构化告警事件 (JSON/JSONL/CSV), 字段与 event_schema.json REV1 对齐.
- 时序图风险标记: 按固定槽位小时桶聚合, 生成 markers[] 供可视化面板时间轴.

三端字段对齐 (risk_id / severity / action):
- DSHD 侧: FR-RISK-5xx 接收事件 + GATE-P2-xx 门禁事件 (本接口主体)
- DSHA 侧: EVM / FR-RISK 因子风险标签 (经 risk_id 反向引用)
- DSHC 侧: BLK / PC-003 流水线解锁事件 (经 risk_id 前缀 + upstream_ref 反向引用)
- 对齐锚点: risk_id (统一编码) + severity (三色语义) + action (处置动作)

用法:
  python vis_alert_export_api.py --mode export   [--format json|jsonl|csv] [--out PATH]
  python vis_alert_export_api.py --mode timeline
  python vis_alert_export_api.py --mode validate
  python vis_alert_export_api.py --mode all

纪律: 固定槽位 + SEED=42; 只读上游 (3 数据源均不修改); 确定性可重放.
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

WORKSPACE = r"D:\DSH_WORK"
OUT_DIR = os.path.join(WORKSPACE, "factor_exp_workspace", "acd_joint_shadow_verify",
                       "dshd_sub", "dshd_arch_gate_prep")
LAB = os.path.join(OUT_DIR, "gate_prep_lab")
EVENT_STORE = os.path.join(LAB, "v87_03_event_store")

FIXED_SLOT = "2026-10-23T16:30:00+08:00"
SEED = 42
SCHEMA_VERSION = "event_schema.json REV1"
EXPORT_API_VERSION = "V87-VIS-EXPORT-1"

RECEIVE_LOG = os.path.join(OUT_DIR, "fr_risk_receive_log.csv")
GATE_LOG = os.path.join(OUT_DIR, "gate_periodic_check_log.csv")
SCHEMA_JSON = os.path.join(OUT_DIR, "event_schema.json")
MAPPING_JSON = os.path.join(OUT_DIR, "fr_risk_501_508_mapping.json")
DAEMON_PY = os.path.join(OUT_DIR, "v87_03_monitor_service.py")

ACTIVE_SYMS = ("AL", "CU", "PB")
FROZEN_SYMS = ("ZN", "NI", "SN", "SI")
ALL_SYMS = ACTIVE_SYMS + FROZEN_SYMS

# 三色语义 -> 处置动作 (P1-1: severity/action 对齐)
COLOR_ACTION = {"RED": "STOP_LINE", "ORANGE": "NOTIFY_1H", "YELLOW": "RECORD_4H"}
# 三色语义 -> 时序图风险等级 (可视化面板)
COLOR_LEVEL = {"RED": 3, "ORANGE": 2, "YELLOW": 1}
# 原始 action -> 规范 action (action 字段三端对齐域)
ACTION_CANON_DOMAIN = ("STOP_LINE", "NOTIFY_1H", "NOTIFY_2H", "RECORD_4H", "RECORD",
                       "PASS", "HOLD", "BLOCK")


def load_mapping():
    """FR-RISK-501~508 映射表 (只读上游)."""
    try:
        with open(MAPPING_JSON, "r", encoding="utf-8") as f:
            m = json.load(f)
        out = {}
        for e in m.get("mapping", []):
            out[e.get("code")] = e
        return out
    except OSError:
        return {}


def canon_action(raw, color, sla_h=None):
    """规范 action 域: 颜色语义为一等依据 (三色 -> 三动作), 原始 action 仅同语义归一化.

    颜色由 d_severity 派生, 是分级语义的地面真值; 颜色 -> 动作映射为硬约束
    (RED->STOP_LINE / ORANGE->NOTIFY_1H / YELLOW->RECORD_4H). 原始 action 若与颜色
    语义冲突 (如 FR-RISK-508 RED/CRITICAL 被写为 RECORD, 见 DEFECT-P9-001),
    以颜色语义为准 — 导出层防御性修正, 不改动上游只读事件卷字节.
    sla_h 仅作 SLA 承诺时窗随告警输出, 不覆盖颜色语义
    (例: FR-RISK-508 = RED/CRITICAL + sla_h=2 -> 仍 STOP_LINE, 2h 为响应承诺).
    """
    base = COLOR_ACTION.get(color)
    if base:
        return base
    a = (raw or "").strip()
    if a:
        u = a.upper()
        if u.startswith("STOP_LINE"):
            return "STOP_LINE"
        if u.startswith("ESCALATE"):
            return "NOTIFY_1H"
        if u in ACTION_CANON_DOMAIN:
            return u
        return "RECORD"
    return "RECORD"


def map_meta(code, color):
    """从映射表取 SLA / 升级规则 (可视化面板溯源用)."""
    m = load_mapping().get(code) or {}
    return {
        "sla_h": m.get("sla_h", ""),
        "d_severity": m.get("d_severity", ""),
        "color_map": m.get("color", ""),
        "escalate_after": m.get("escalate_after", ""),
        "escalate_to": m.get("escalate_to", ""),
    }


def md5_bytes(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def md5f(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except OSError:
        return None


def _hour_bucket(slot):
    """固定槽位 -> 时序桶键 (YYYYMMDD-HH)."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):\d{2}:\d{2}", slot or "")
    return "-".join([m.group(1), m.group(2), m.group(3), m.group(4)]) if m else "UNKNOWN"


# ---------------------------------------------------------------------------
# 数据源加载 (只读)
# ---------------------------------------------------------------------------
def load_csv_rows(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def source_manifest():
    """3 数据源完整性指纹 (供可视化面板溯源)."""
    vol = os.path.join(EVENT_STORE, "vol_0001.csv")
    man = os.path.join(EVENT_STORE, "manifest.json")
    man_obj = None
    if os.path.exists(man):
        with open(man, "r", encoding="utf-8") as f:
            man_obj = json.load(f)
    return {
        "receive_log": {"path": os.path.relpath(RECEIVE_LOG, OUT_DIR),
                        "rows": len(load_csv_rows(RECEIVE_LOG)), "md5": md5f(RECEIVE_LOG)},
        "gate_log": {"path": os.path.relpath(GATE_LOG, OUT_DIR),
                     "rows": len(load_csv_rows(GATE_LOG)), "md5": md5f(GATE_LOG)},
        "event_store_vol": {"path": os.path.relpath(vol, OUT_DIR),
                            "rows": len(load_csv_rows(vol)), "md5": md5f(vol),
                            "manifest_md5": md5f(man), "tail_md5": (man_obj or {}).get("tail_md5"),
                            "anchor": (man_obj or {}).get("anchor")},
    }


# ---------------------------------------------------------------------------
# FR-RISK 告警事件 (接收日志 -> 结构化告警)
# ---------------------------------------------------------------------------
def build_alerts_from_receive(slot):
    alerts = []
    for r in load_csv_rows(RECEIVE_LOG):
        code = r.get("risk_code") or r.get("code") or r.get("fr_risk_code") or ""
        color = (r.get("color") or "").upper()
        if not code and "fwd_id" in r:
            m = re.match(r"(?:FWD|E2E|P[234]|U)-(\d{3})", r.get("fwd_id", ""))
            code = "FR-RISK-{}".format(m.group(1)) if m else "FR-RISK-UNKNOWN"
        rec_md5 = r.get("record_md5") or md5_bytes(r.get("fwd_id", ""))
        meta = map_meta(code, color)
        sla = meta["sla_h"] if meta["sla_h"] != "" else (int(r["sla_h"]) if str(r.get("sla_h", "")).strip().isdigit() else "")
        action = canon_action(r.get("action"), color, sla)
        esc = "ESCALATED" if (color == "RED" and action == "STOP_LINE") else "ACTIVE"
        alerts.append({
            "alert_id": "VIS-ALERT-{}-{}".format(_hour_bucket(slot).replace("-", ""), r.get("fwd_id", "")),
            "risk_id": code,
            "risk_code": code,
            "risk_family": "FR-RISK" if code.startswith("FR-RISK-") else "OTHER",
            "symbol": r.get("symbol") or "MULTI",
            "zone": r.get("zone") or "",
            "severity": r.get("d_severity") or meta.get("d_severity") or "INFO",
            "color": color or "GRAY",
            "action": action,
            "action_raw": r.get("action") or "",
            "sla_h": meta.get("sla_h", ""),
            "escalate_after": meta.get("escalate_after", ""),
            "escalate_to": meta.get("escalate_to", ""),
            "color_level": COLOR_LEVEL.get(color, 0),
            "status": esc,
            "fwd_id": r.get("fwd_id", ""),
            "fixed_slot": slot,
            "bucket": _hour_bucket(slot),
            "source": "DSHD",
            "upstream_ref": "DSHC:FORWARD;DSHA:EVM",
            "escalation_state": {"persisted": True, "escalated": color == "RED",
                                 "consecutive": r.get("escalation", ""), "action": action},
            "evidence": {"path": os.path.relpath(RECEIVE_LOG, OUT_DIR), "record_md5": rec_md5},
        })
    return alerts


# ---------------------------------------------------------------------------
# 门禁事件 (巡检日志 -> 结构化告警)
# ---------------------------------------------------------------------------
def build_alerts_from_gates(slot):
    alerts = []
    for r in load_csv_rows(GATE_LOG):
        gid = r.get("gate_id") or ""
        status = (r.get("status") or "").upper()
        if not gid:
            continue
        sev = {"FAIL": "CRITICAL", "PENDING": "WARN", "PASS": "INFO"}.get(status, "INFO")
        color = {"FAIL": "RED", "PENDING": "ORANGE", "PASS": "GRAY"}.get(status, "GRAY")
        gate_slot = r.get("fixed_slot") or slot
        alerts.append({
            "alert_id": "VIS-GATE-{}-{}".format(_hour_bucket(gate_slot).replace("-", ""), gid),
            "risk_id": gid,
            "risk_code": gid,
            "risk_family": "GATE-P2",
            "symbol": "SYSTEM",
            "zone": "GATE",
            "severity": sev,
            "color": color,
            "action": {"FAIL": "BLOCK", "PENDING": "HOLD", "PASS": "PASS"}.get(status, "RECORD"),
            "action_raw": r.get("status", ""),
            "sla_h": "",
            "escalate_after": "",
            "escalate_to": "",
            "color_level": COLOR_LEVEL.get(color, 0),
            "status": status,
            "round_no": r.get("round_no", ""),
            "prev_status": r.get("prev_status", ""),
            "status_change": r.get("status_change", ""),
            "title": r.get("title", ""),
            "fixed_slot": gate_slot,
            "bucket": _hour_bucket(gate_slot),
            "source": "DSHD",
            "upstream_ref": "DSHC:PC-003;DSHA:FACTOR-APPROVE" if status == "PENDING" else "",
            "escalation_state": {"persisted": True, "escalated": status == "FAIL",
                                 "action": {"FAIL": "BLOCK", "PENDING": "HOLD", "PASS": "PASS"}.get(status, "RECORD")},
            "evidence": {"path": os.path.relpath(GATE_LOG, OUT_DIR),
                         "record_md5": r.get("record_md5") or md5_bytes(gid + status)},
        })
    return alerts


# ---------------------------------------------------------------------------
# daemon 事件卷 (V87-03 持久化事件 -> 结构化告警)
# ---------------------------------------------------------------------------
def build_alerts_from_vols(slot):
    alerts = []
    for volname in sorted(os.listdir(EVENT_STORE)):
        if not (volname.startswith("vol_") and volname.endswith(".csv")):
            continue
        for r in load_csv_rows(os.path.join(EVENT_STORE, volname)):
            color = (r.get("color") or "").upper()
            code = r.get("code") or r.get("risk_code") or r.get("risk_id") or r.get("event_id", "")
            meta = map_meta(code, color)
            action = canon_action(r.get("action"), color, meta.get("sla_h") or None)
            alerts.append({
                "alert_id": "VIS-VOL-{}-{}".format(_hour_bucket(slot).replace("-", ""), r.get("event_id", "")),
                "risk_id": code,
                "risk_code": code,
                "risk_family": "FR-RISK",
                "symbol": r.get("symbol") or "MULTI",
                "zone": r.get("zone") or "",
                "severity": r.get("severity") or meta.get("d_severity") or "INFO",
                "color": color or "GRAY",
                "action": action,
                "action_raw": r.get("action") or "",
                "sla_h": meta.get("sla_h", ""),
                "escalate_after": meta.get("escalate_after", ""),
                "escalate_to": meta.get("escalate_to", ""),
                "color_level": COLOR_LEVEL.get(color, 0),
                "status": "ESCALATED" if color == "RED" else "ACTIVE",
                "event_id": r.get("event_id", ""),
                "fixed_slot": slot,
                "bucket": _hour_bucket(slot),
                "source": "DSHD",
                "upstream_ref": "V87-03-Daemon",
                "escalation_state": {"persisted": True, "escalated": color == "RED", "action": action},
                "evidence": {"path": os.path.relpath(os.path.join(EVENT_STORE, volname), OUT_DIR),
                             "record_md5": r.get("record_md5", "")},
            })
    return alerts


# ---------------------------------------------------------------------------
# 聚合 + 时序风险标记
# ---------------------------------------------------------------------------
def aggregate(alerts, slot):
    by_color = Counter(a["color"] for a in alerts)
    by_action = Counter(a["action"] for a in alerts)
    by_risk = Counter(a["risk_id"] for a in alerts)
    by_symbol = Counter(a["symbol"] for a in alerts)
    escalation = [a for a in alerts if a.get("escalation_state", {}).get("escalated")]
    buckets = defaultdict(list)
    for a in alerts:
        buckets[a["bucket"]].append(a)
    markers = []
    for b in sorted(buckets):
        items = buckets[b]
        colors = Counter(i["color"] for i in items)
        markers.append({
            "bucket": b,
            "ts": items[0]["fixed_slot"],
            "count": len(items),
            "count_by_color": dict(sorted(colors.items())),
            "max_level": max((COLOR_LEVEL.get(i["color"], 0) for i in items), default=0),
            "risk_ids": sorted({i["risk_id"] for i in items}),
            "symbols": sorted({i["symbol"] for i in items}),
            "escalated": sum(1 for i in items if i.get("escalation_state", {}).get("escalated")),
            "pending_gates": sorted({i["risk_id"] for i in items if i.get("status") == "PENDING"}),
            "stop_line": sum(1 for i in items if i.get("action") == "STOP_LINE"),
        })
    return {
        "total": len(alerts),
        "by_color": dict(sorted(by_color.items())),
        "by_action": dict(sorted(by_action.items())),
        "by_risk_id": dict(sorted(by_risk.items())),
        "by_symbol": dict(sorted(by_symbol.items())),
        "escalation_chains": sorted({e["risk_id"] for e in escalation}),
        "escalation_count": len(escalation),
        "stop_line_count": sum(1 for a in alerts if a.get("action") == "STOP_LINE"),
        "pending_gates": sorted({a["risk_id"] for a in alerts if a.get("status") == "PENDING"}),
        "markers": markers,
    }


def build_export(slot):
    alerts = (build_alerts_from_receive(slot)
              + build_alerts_from_gates(slot)
              + build_alerts_from_vols(slot))
    stats = aggregate(alerts, slot)
    return {
        "export_id": "V87-VIS-EXPORT-{}".format(slot.replace(":", "").replace("-", "").replace("+", "")[:15]),
        "api_version": EXPORT_API_VERSION,
        "schema_ref": SCHEMA_VERSION,
        "generated_at": slot,
        "seed": SEED,
        "source": source_manifest(),
        "alignment": {
            "risk_id": {"anchor": "统一编码 (FR-RISK-5xx / GATE-P2-xx)", "domains": ["FR-RISK-501..508", "GATE-P2-01..11"]},
            "severity": {"anchor": "三色语义 (RED/ORANGE/YELLOW -> CRITICAL/HIGH/MEDIUM)",
                         "domain": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "WARN"]},
            "action": {"anchor": "处置动作 (与 sla_h / 颜色一致)", "domain": list(ACTION_CANON_DOMAIN)},
            "three_way": {"DSHD": "FR-RISK-5xx 接收 + GATE-P2-xx 门禁",
                          "DSHA": "EVM / FR-RISK 因子风险标签 (risk_id 反引)",
                          "DSHC": "BLK / PC-003 流水线解锁 (upstream_ref 反引)"},
        },
        "validation": schema_check(slot),
        "alerts": alerts,
        "timeline": {"bucket": "hour", "markers": stats["markers"]},
        "stats": stats,
    }


# ---------------------------------------------------------------------------
# 序列化 (json / jsonl / csv)
# ---------------------------------------------------------------------------
ALERT_FIELDS = ["alert_id", "risk_id", "risk_code", "risk_family", "symbol", "zone",
                "severity", "color", "color_level", "action", "action_raw",
                "sla_h", "escalate_after", "escalate_to", "status",
                "round_no", "event_id", "fwd_id", "bucket", "fixed_slot",
                "source", "upstream_ref", "title", "prev_status", "status_change",
                "escalation_state", "evidence"]


def to_jsonl(alerts):
    out = []
    for a in alerts:
        row = dict(a)
        row["escalation_state"] = json.dumps(row.get("escalation_state", {}), ensure_ascii=False)
        row["evidence"] = json.dumps(row.get("evidence", {}), ensure_ascii=False)
        for k in ALERT_FIELDS:
            if k not in row:
                row[k] = ""
        out.append(json.dumps({k: row[k] for k in ALERT_FIELDS}, ensure_ascii=False))
    return "\n".join(out) + "\n"


def to_csv(alerts):
    import io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(ALERT_FIELDS)
    for a in alerts:
        w.writerow([json.dumps(a.get(k, ""), ensure_ascii=False) if isinstance(a.get(k, ""), (dict, list))
                    else a.get(k, "") for k in ALERT_FIELDS])
    return buf.getvalue()


# ---------------------------------------------------------------------------
# schema REV1 对齐校验
# ---------------------------------------------------------------------------
def schema_check(slot):
    """导出结构 vs event_schema.json REV1 关键字段稳定性校验 (risk_id/severity/action 三端对齐)."""
    with open(SCHEMA_JSON, "r", encoding="utf-8") as f:
        schema = json.load(f)
    required = ["alert_id", "risk_id", "severity", "color", "action", "fixed_slot",
                "bucket", "source", "evidence"]
    all_alerts = (build_alerts_from_receive(slot) + build_alerts_from_gates(slot)
                  + build_alerts_from_vols(slot))
    sample = build_alerts_from_receive(slot)[:1]
    missing = [k for k in required if sample and k not in sample[0]]
    sev_ok = {a["severity"] for a in all_alerts}
    allowed_sev = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "WARN"}
    sev_bad = sorted(sev_ok - allowed_sev)
    act_ok = {a["action"] for a in all_alerts}
    act_bad = sorted(act_ok - set(ACTION_CANON_DOMAIN))
    id_ok = all(re.match(r"^VIS-(ALERT|GATE|VOL)-", a["alert_id"]) for a in all_alerts)
    rid_ok = all(re.match(r"^(FR-RISK-\d{3}|GATE-P2-\d{2}|SYSTEM)$", a["risk_id"]) for a in all_alerts)
    ev_ok = all(isinstance(a.get("evidence"), dict) and a["evidence"].get("path") for a in all_alerts)
    md5_ok = all(re.match(r"^[0-9a-f]{32}$", a["evidence"].get("record_md5", "")) for a in all_alerts)
    align_total = align_ok = 0
    for a in all_alerts:
        # 仅校验 FR-RISK 家族 (门禁事件颜色表示状态, 不参与颜色->动作对齐)
        if a["color"] in COLOR_ACTION and a.get("risk_family") == "FR-RISK":
            align_total += 1
            sla = a.get("sla_h")
            sla = sla if sla not in ("", None) else None
            if a["action"] == canon_action(a.get("action_raw", ""), a["color"], sla):
                align_ok += 1
    res = {
        "schema_file": os.path.basename(SCHEMA_JSON),
        "schema_version": SCHEMA_VERSION,
        "schema_md5": md5f(SCHEMA_JSON),
        "schema_doc_id": schema.get("schema_id") or schema.get("doc_id") or "",
        "required_fields": required,
        "missing_fields": missing,
        "field_count": len(ALERT_FIELDS),
        "field_stable": len(ALERT_FIELDS) == 27,
        "alert_count": len(all_alerts),
        "alert_id_pattern_ok": id_ok,
        "risk_id_domain_ok": rid_ok,
        "risk_id_seen": sorted({a["risk_id"] for a in all_alerts}),
        "severity_domain_ok": not sev_bad,
        "severity_seen": sorted(sev_ok),
        "severity_out_of_domain": sev_bad,
        "action_domain_ok": not act_bad,
        "action_domain": list(ACTION_CANON_DOMAIN),
        "action_seen": sorted(act_ok),
        "action_out_of_domain": act_bad,
        "evidence_path_ok": ev_ok,
        "evidence_md5_ok": md5_ok,
        "color_action_align_ok": align_total > 0 and align_ok == align_total,
        "color_action_align": "{}/{}".format(align_ok, align_total),
        "verdict": "PASS" if (not missing and not sev_bad and not act_bad and id_ok and rid_ok
                              and ev_ok and md5_ok and len(ALERT_FIELDS) == 27
                              and align_total > 0 and align_ok == align_total) else "FAIL",
    }
    return res


def write_body(out_path, body):
    """字节精确写出 (避免 Windows CRLF 翻译导致 md5 与内容不符)."""
    data = body.encode("utf-8")
    with open(out_path, "wb") as f:
        f.write(data)
    return len(data), hashlib.md5(data).hexdigest()


def cmd_export(slot, fmt, out_path, pretty=True):
    exp = build_export(slot)
    if fmt == "jsonl":
        body = to_jsonl(exp["alerts"])
    elif fmt == "csv":
        body = to_csv(exp["alerts"])
    else:
        body = json.dumps(exp, ensure_ascii=False, indent=2 if pretty else None) + "\n"
    size, digest = write_body(out_path, body)
    print("[EXPORT] mode=export fmt={} alerts={} markers={} out={} size={} md5={}".format(
        fmt, len(exp["alerts"]), len(exp["timeline"]["markers"]), out_path, size, digest))
    print("[EXPORT] by_color={} by_action={}".format(exp["stats"]["by_color"], exp["stats"]["by_action"]))
    print("[EXPORT] escalation_chains={} stop_line={} pending_gates={}".format(
        exp["stats"]["escalation_chains"], exp["stats"]["stop_line_count"],
        exp["stats"]["pending_gates"]))
    print("[EXPORT] source={} md5{}".format(
        {k: v.get("rows") for k, v in exp["source"].items()},
        {k: (v.get("md5") or "")[:8] for k, v in exp["source"].items()}))
    return exp


def cmd_timeline(slot, out_path, pretty=True):
    exp = build_export(slot)
    body = json.dumps(exp["timeline"], ensure_ascii=False, indent=2 if pretty else None) + "\n"
    size, digest = write_body(out_path, body)
    print("[TIMELINE] markers={} buckets={} total_alerts={}".format(
        len(exp["timeline"]["markers"]), len(exp["timeline"]["markers"]), exp["stats"]["total"]))
    for m in exp["timeline"]["markers"]:
        print("[TIMELINE] {} cnt={} colors={} level={} esc={} stop_line={} pending={}".format(
            m["bucket"], m["count"], m["count_by_color"], m["max_level"],
            m["escalated"], m["stop_line"], len(m["pending_gates"])))
    print("[TIMELINE] out={} size={} md5={}".format(out_path, size, digest))
    return exp["timeline"]


def cmd_validate(slot, out_path, pretty=True):
    res = schema_check(slot)
    body = json.dumps({"validation": res, "fixed_slot": slot, "seed": SEED,
                       "schema_ref": SCHEMA_VERSION}, ensure_ascii=False, indent=2 if pretty else None) + "\n"
    size, digest = write_body(out_path, body)
    for k, v in res.items():
        print("[VALIDATE] {} = {}".format(k, v))
    print("[VALIDATE] verdict={} out={} size={} md5={}".format(res["verdict"], out_path, size, digest))
    return res


def _daemon_has_red_branch():
    """DEFECT-P9-001 源头修复存在性校验 (daemon map_event 显式 RED 分支)."""
    try:
        src = open(DAEMON_PY, "r", encoding="utf-8").read()
        return ('elif color == "RED"' in src) and ('action = "STOP_LINE"' in src)
    except OSError:
        return False


# ---------------------------------------------------------------------------
# P0-2 FAIL 门禁 -> 立即告警推送链路# ---------------------------------------------------------------------------
FAIL_PUSH_TARGETS = ["DSHA:VIS-001", "DSHC:DUTY", "GATE-P2-BLOCKED"]


def gate_fail_alerts(slot):
    """任何 FAIL 门禁事件立刻生成告警推送链路 (P0-2 硬要求).

    PASS/PENDING/NO_CHANGE/FAIL 四态区分: 仅 FAIL 触发 P0 级推送;
    PENDING 为数据依赖未就位的已知状态 (已知状态非缺陷, 走 HOLD 不进推送链).
    """
    out = []
    for a in build_alerts_from_gates(slot):
        if (a.get("status") or "").upper() == "FAIL":
            out.append({
                "push_id": "PUSH-FAIL-{}".format(a["alert_id"]),
                "alert_id": a["alert_id"],
                "risk_id": a["risk_id"],
                "round_no": a.get("round_no", ""),
                "fixed_slot": a.get("fixed_slot", ""),
                "prev_status": a.get("prev_status", ""),
                "status_change": a.get("status_change", ""),
                "severity": "CRITICAL",
                "color": "RED",
                "action": "BLOCK",
                "priority": "P0",
                "pushed_to": list(FAIL_PUSH_TARGETS),
                "evidence": a.get("evidence", {}),
            })
    return out


# ---------------------------------------------------------------------------
# P1-4 边界异常回归 (CRLF / risk_family / SLA_ACTION 三处历史修复持续回归)
# ---------------------------------------------------------------------------
def run_regression(slot):
    """三处历史边界修复的持续回归验证 (不引入新缺陷).

    R1-CRLF:       write_body 字节精确写出, 禁止 Windows CRLF 翻译致 md5 与内容不符
    R2-RISKFAMILY: risk_family 必须为 "FR-RISK" (非 code.split('-')[1]='RISK' 的切片错位)
    R3-SLA_ACTION: 颜色语义为一等依据, sla_h 不覆盖颜色 -> 动作映射 (508=RED/sla2 -> STOP_LINE)
    """
    cases = []

    # R1: CRLF 换行字节回归
    probe = os.path.join(LAB, "_regress_crlf_probe.json")
    body = json.dumps({"probe": slot, "seed": SEED, "crlf": False, "nl": "\n"},
                      ensure_ascii=False, indent=2) + "\n"
    size, digest = write_body(probe, body)
    raw = open(probe, "rb").read()
    r1 = {
        "cr_byte_absent": b"\r" not in raw,
        "crlf_absent": b"\r\n" not in raw,
        "lf_count_match": raw.count(b"\n") == body.count("\n"),
        "size_match": len(raw) == size,
        "md5_match": hashlib.md5(raw).hexdigest() == digest,
    }
    cases.append({
        "case_id": "R1-CRLF",
        "history": "Windows 文本模式写出触发 CRLF 翻译, 打印 md5 与落盘 md5 不一致",
        "checks": r1,
        "verdict": "PASS" if all(r1.values()) else "FAIL",
        "evidence": {"path": os.path.relpath(probe, OUT_DIR), "md5": digest, "bytes": len(raw)},
    })
    try:
        os.unlink(probe)
    except OSError:
        pass

    # R2: risk_family 切片回归
    recv = build_alerts_from_receive(slot)
    fam = defaultdict(list)
    for a in recv:
        fam[a.get("risk_family", "")].append(a["risk_id"])
    fr = [a for a in recv if a["risk_id"].startswith("FR-RISK-")]
    r2 = {
        "fr_risk_family_all_FR_RISK": sorted({a["risk_family"] for a in fr}) == ["FR-RISK"],
        "no_RISK_slicing": "RISK" not in fam,
        "no_empty_family": "" not in fam,
        "fr_risk_count": len(fr),
        "family_dist": {k: len(v) for k, v in sorted(fam.items())},
    }
    cases.append({
        "case_id": "R2-RISKFAMILY",
        "history": "risk_family 曾用 code.split('-')[1] 切片, FR-RISK-501 -> 'RISK' 而非 'FR-RISK'",
        "checks": r2,
        "verdict": "PASS" if (r2["fr_risk_family_all_FR_RISK"] and r2["no_RISK_slicing"]
                              and r2["no_empty_family"] and r2["fr_risk_count"] > 0) else "FAIL",
        "evidence": {"path": os.path.relpath(RECEIVE_LOG, OUT_DIR), "md5": md5f(RECEIVE_LOG)},
    })

    # R3: SLA_ACTION 分支回归 (颜色为一等依据, sla_h 不覆盖; DEFECT-P9-001 修复后语义)
    frv = build_alerts_from_vols(slot)
    red_fr = [a for a in (recv + frv)
              if a["color"] == "RED" and a.get("risk_family") == "FR-RISK"]
    r3 = {
        "RED->STOP_LINE": canon_action("", "RED", 2) == "STOP_LINE",
        "ORANGE->NOTIFY_1H": canon_action("", "ORANGE", 1) == "NOTIFY_1H",
        "YELLOW->RECORD_4H": canon_action("", "YELLOW", 4) == "RECORD_4H",
        "sla_h_never_overrides_RED": canon_action("", "RED", 8) == "STOP_LINE",
        "sla_h_never_overrides_YELLOW": canon_action("", "YELLOW", 0) == "RECORD_4H",
        "color_overrides_conflicting_raw_RED": canon_action("RECORD", "RED", 2) == "STOP_LINE",
        "color_overrides_conflicting_raw_YELLOW": canon_action("STOP_LINE", "YELLOW", 4) == "RECORD_4H",
        "color_overrides_conflicting_raw_ORANGE": canon_action("BLOCK", "ORANGE", 1) == "NOTIFY_1H",
        "fr_risk_508_RED_sla2": canon_action("RECORD", "RED", 2) == "STOP_LINE",
        "raw_STOP_LINE_prefix_on_GRAY": canon_action("STOP_LINE:CU", "GRAY", None) == "STOP_LINE",
        "raw_ESCALATE_prefix_on_GRAY": canon_action("ESCALATE x2", "GRAY", None) == "NOTIFY_1H",
        "raw_unknown_on_GRAY->RECORD": canon_action("WEIRD_ACTION", "GRAY", None) == "RECORD",
        "empty_raw_GRAY->RECORD": canon_action("", "GRAY", None) == "RECORD",
        "red_fr_alerts_all_STOP_LINE": all(a["action"] == "STOP_LINE" for a in red_fr),
        "red_fr_alert_count": len(red_fr),
        "daemon_RED_branch_present": _daemon_has_red_branch(),
    }
    cases.append({
        "case_id": "R3-SLA_ACTION",
        "history": "SLA_ACTION 死代码分支曾用 sla_h 覆盖颜色语义; DEFECT-P9-001 曾用原始 action 覆盖 "
                   "RED/CRITICAL 语义 (FR-RISK-508 被写为 RECORD). 现颜色语义为一等依据.",
        "checks": r3,
        "verdict": "PASS" if all(v for k, v in r3.items() if isinstance(v, bool))
                   and r3["red_fr_alert_count"] > 0 else "FAIL",
        "evidence": {"path": os.path.relpath(MAPPING_JSON, OUT_DIR), "md5": md5f(MAPPING_JSON)},
    })

    n_pass = sum(1 for c in cases if c["verdict"] == "PASS")
    return {
        "regression_id": "V87-VIS-REGRESS-{}".format(
            slot.replace(":", "").replace("-", "").replace("+", "")[:15]),
        "fixed_slot": slot,
        "seed": SEED,
        "cases_total": len(cases),
        "cases_pass": n_pass,
        "cases_fail": len(cases) - n_pass,
        "cases": cases,
        "verdict": "PASS" if n_pass == len(cases) else "FAIL",
    }


def cmd_regression(slot, out_path):
    res = run_regression(slot)
    body = json.dumps({"regression": res, "fixed_slot": slot, "seed": SEED,
                       "api_version": EXPORT_API_VERSION},
                      ensure_ascii=False, indent=2) + "\n"
    size, digest = write_body(out_path, body)
    print("[REGRESSION] cases={} pass={} fail={} verdict={}".format(
        res["cases_total"], res["cases_pass"], res["cases_fail"], res["verdict"]))
    for c in res["cases"]:
        print("[REGRESSION] {} | {} | {}".format(c["case_id"], c["verdict"], c["history"]))
        for k, v in c["checks"].items():
            print("           {:38s} {}".format(k, v))
    print("[REGRESSION] out={} size={} md5={}".format(out_path, size, digest))
    return res


# ---------------------------------------------------------------------------
# P1-2 DSHA VIS-001 可视化工作台联调 (时序模块 + 悬浮弹窗事件溯源)
# ---------------------------------------------------------------------------
def build_vis001(slot):
    """VIS-001 时序模块联调载荷: series (图表渲染) + tooltips (悬浮弹窗溯源) + render 校验."""
    alerts = (build_alerts_from_receive(slot) + build_alerts_from_gates(slot)
              + build_alerts_from_vols(slot))
    stats = aggregate(alerts, slot)
    markers = stats["markers"]

    # 图表时序序列
    series = [{
        "bucket": m["bucket"], "ts": m["ts"], "value": m["max_level"], "count": m["count"],
        "stop_line": m["stop_line"], "escalated": m["escalated"],
        "count_by_color": m["count_by_color"], "pending_gates": m["pending_gates"],
        "risk_ids": m["risk_ids"], "symbols": m["symbols"],
    } for m in markers]

    # 悬浮弹窗: 每桶可溯源条目
    by_bucket = defaultdict(list)
    for a in alerts:
        by_bucket[a["bucket"]].append(a)
    tooltips = []
    for b in sorted(by_bucket):
        items = by_bucket[b]
        tooltips.append({
            "bucket": b,
            "popup_title": "VIS-001 ALERTS @ {}".format(b),
            "level": max((COLOR_LEVEL.get(i["color"], 0) for i in items), default=0),
            "stop_line": sum(1 for i in items if i.get("action") == "STOP_LINE"),
            "escalated": sum(1 for i in items if i.get("escalation_state", {}).get("escalated")),
            "items": [{
                "alert_id": i["alert_id"], "risk_id": i["risk_id"],
                "risk_family": i["risk_family"], "symbol": i["symbol"],
                "severity": i["severity"], "color": i["color"], "action": i["action"],
                "status": i["status"], "fixed_slot": i.get("fixed_slot", ""),
                "round_no": i.get("round_no", ""), "event_id": i.get("event_id", ""),
                "fwd_id": i.get("fwd_id", ""), "upstream_ref": i.get("upstream_ref", ""),
                "evidence_path": i["evidence"]["path"],
                "evidence_md5": i["evidence"].get("record_md5", ""),
            } for i in items],
        })

    all_items = [i for t in tooltips for i in t["items"]]
    buckets_sorted = [s["bucket"] for s in series]
    render = {
        "axis_monotonic": buckets_sorted == sorted(buckets_sorted),
        "bucket_count": len(series),
        "series_point_total": len(alerts),
        "series_marker_aligned": len(series) == len(markers),
        "tooltip_bucket_aligned": sorted(t["bucket"] for t in tooltips) == buckets_sorted,
        "every_point_has_backing_event": all(len(t["items"]) > 0 for t in tooltips),
        "level_domain_ok": all(0 <= s["value"] <= 3 for s in series),
        "color_domain_ok": all(i["color"] in COLOR_ACTION or i["color"] == "GRAY"
                               for i in all_items),
        "severity_domain_ok": all(i["severity"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW",
                                                    "INFO", "WARN"} for i in all_items),
        "action_domain_ok": all(i["action"] in ACTION_CANON_DOMAIN for i in all_items),
        "evidence_md5_all_32hex": all(re.match(r"^[0-9a-f]{32}$", i["evidence_md5"])
                                      for i in all_items),
        "hover_traceability_ok": all(i["alert_id"] and i["risk_id"] and i["evidence_path"]
                                     and i["evidence_md5"] for i in all_items),
        "popup_level_consistent": all(t["level"] == max((COLOR_LEVEL.get(i["color"], 0)
                                                          for i in t["items"]), default=0)
                                      for t in tooltips),
    }
    render["stop_line_total"] = stats["stop_line_count"]
    render["escalation_chains"] = stats["escalation_chains"]
    render["pending_gates"] = stats["pending_gates"]
    render["verdict"] = "PASS" if all(v for k, v in render.items()
                                      if isinstance(v, bool)) else "FAIL"

    return {
        "workbench_id": "VIS-001",
        "integration_id": "DSHD-P9-VIS001-{}".format(
            slot.replace(":", "").replace("-", "").replace("+", "")[:15]),
        "api_version": EXPORT_API_VERSION,
        "schema_ref": SCHEMA_VERSION,
        "generated_at": slot,
        "seed": SEED,
        "source": source_manifest(),
        "chart": {
            "module": "时序模块 (timeseries risk markers)",
            "x_axis": "bucket (YYYYMMDD-HH)",
            "y_axis": "max_level (0=NONE 1=YELLOW 2=ORANGE 3=RED)",
            "series": series,
            "legend": {"RED": "STOP_LINE", "ORANGE": "NOTIFY_1H",
                       "YELLOW": "RECORD_4H", "GRAY": "INFO/PASS"},
        },
        "tooltip": {"module": "悬浮弹窗 (hover event traceability)", "entries": tooltips},
        "push": {"fail_alerts": gate_fail_alerts(slot),
                 "fail_alert_count": len(gate_fail_alerts(slot)),
                 "push_targets": FAIL_PUSH_TARGETS},
        "render_check": render,
        "stats": stats,
    }


def cmd_vis001(slot, out_path):
    exp = build_vis001(slot)
    body = json.dumps(exp, ensure_ascii=False, indent=2) + "\n"
    size, digest = write_body(out_path, body)
    r = exp["render_check"]
    print("[VIS001] workbench={} series={} tooltips={} points={} verdict={}".format(
        exp["workbench_id"], len(exp["chart"]["series"]), len(exp["tooltip"]["entries"]),
        exp["chart"]["series"][0]["count"] if exp["chart"]["series"] else 0, r["verdict"]))
    for s in exp["chart"]["series"]:
        print("[VIS001] {} level={} cnt={} stop_line={} esc={} colors={}".format(
            s["bucket"], s["value"], s["count"], s["stop_line"], s["escalated"],
            s["count_by_color"]))
    for k, v in r.items():
        if isinstance(v, bool):
            print("[VIS001-RENDER] {:30s} {}".format(k, v))
    print("[VIS001] fail_alerts={} push_targets={}".format(
        exp["push"]["fail_alert_count"], exp["push"]["push_targets"]))
    print("[VIS001] out={} size={} md5={}".format(out_path, size, digest))
    return exp


def main(argv=None):
    ap = argparse.ArgumentParser(description="V87 VIS Alert Export API")
    ap.add_argument("--mode", default="export", choices=["export", "timeline", "validate", "all",
                                                         "regression", "vis001", "full"])
    ap.add_argument("--format", default="json", choices=["json", "jsonl", "csv"], dest="fmt")
    ap.add_argument("--out", default=os.path.join(LAB, "vis_alert_export.json"))
    ap.add_argument("--slot", default=FIXED_SLOT)
    ap.add_argument("--pretty", action="store_true", default=True)
    args = ap.parse_args(argv)

    slot = args.slot or FIXED_SLOT
    export_path = args.out if args.out else os.path.join(LAB, "vis_alert_export.json")
    ok = True

    if args.mode in ("export", "all"):
        cmd_export(slot, args.fmt, export_path)
        print("[EXPORT] DONE mode={}".format(args.mode))
    if args.mode == "timeline":
        tl_path = os.path.join(LAB, "vis_alert_timeline.json")
        cmd_timeline(slot, tl_path)
        print("[TIMELINE] DONE")
    if args.mode == "validate":
        va_path = os.path.join(LAB, "vis_alert_validate.json")
        r = cmd_validate(slot, va_path)
        ok = r["verdict"] == "PASS"
        print("[VALIDATE] DONE")
    if args.mode == "all":
        cmd_timeline(slot, os.path.join(LAB, "vis_alert_timeline.json"))
        r = cmd_validate(slot, os.path.join(LAB, "vis_alert_validate.json"))
        ok = r["verdict"] == "PASS"
        print("[ALL] export + timeline + validate DONE verdict={}".format("PASS" if ok else "FAIL"))
    if args.mode == "regression":
        rg = cmd_regression(slot, os.path.join(LAB, "vis_alert_regression.json"))
        ok = rg["verdict"] == "PASS"
        print("[REGRESSION] DONE")
    if args.mode == "vis001":
        v = cmd_vis001(slot, os.path.join(LAB, "vis_001_integration.json"))
        ok = v["render_check"]["verdict"] == "PASS"
        print("[VIS001] DONE")
    if args.mode == "full":
        cmd_export(slot, args.fmt, export_path)
        cmd_timeline(slot, os.path.join(LAB, "vis_alert_timeline.json"))
        r = cmd_validate(slot, os.path.join(LAB, "vis_alert_validate.json"))
        rg = cmd_regression(slot, os.path.join(LAB, "vis_alert_regression.json"))
        v = cmd_vis001(slot, os.path.join(LAB, "vis_001_integration.json"))
        ok = (r["verdict"] == "PASS" and rg["verdict"] == "PASS"
              and v["render_check"]["verdict"] == "PASS")
        print("[FULL] export + timeline + validate + regression + vis001 "
              "verdict={}".format("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
