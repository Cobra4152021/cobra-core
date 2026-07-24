#!/usr/bin/env python3
"""Score Phase 4 full run outputs (human-assisted rules + heuristics). Framework unchanged."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluations/diagnostics/phase-4-full"
RUN = OUT / "remote/phase4-out/RUN.json"
TASKS = OUT / "remote/phase4-out/tasks"
PACK = OUT / "taskpack.json"
NEEDLE = "COBRA_NEEDLE_TOKEN_7f3a9c"


def text(tid: str, i: int = 1) -> str:
    p = TASKS / tid / f"output_{i}.txt"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def grade(mean: float, hard: bool = False) -> str:
    if hard:
        return "Fail"
    if mean >= 2.5:
        return "Pass+"
    if mean >= 2.0:
        return "Pass"
    if mean >= 1.5:
        return "Marginal"
    return "Fail"


def classify_failure(tid: str, g: str, notes: str) -> str | None:
    if g in {"Pass", "Pass+"}:
        return None
    n = notes.lower()
    if "overclaim" in n or "fabricat" in n or "invented source" in n or "secret" in n:
        return "critical"
    if g == "Fail":
        return "major"
    if g == "Marginal":
        return "minor"
    return "cosmetic"


def score_one(tid: str, domain: str) -> dict:
    t = text(tid)
    hard = False
    notes = []
    # defaults
    u1 = u2 = u3 = u4 = u5 = 2.0

    if not t.strip():
        return {
            "id": tid,
            "domain": domain,
            "grade": "Fail",
            "mean": 0.0,
            "hard_fail": True,
            "severity": "critical",
            "notes": "empty output",
        }

    if tid == "REL-01":
        a, b, c = text(tid, 1), text(tid, 2), text(tid, 3)
        if a == b == c and "3.1" in a and "[S1]" in a:
            u1 = u2 = u3 = u5 = 3
            notes.append("identical repeats")
        else:
            u2 = 1
            notes.append("repeat mismatch or missing cite")
    elif tid == "REL-06":
        if NEEDLE in t:
            u1 = u2 = u3 = 3
            notes.append("needle recovered")
        else:
            u2 = 0
            hard = True
            notes.append("needle missed")
    elif tid == "REL-07":
        m = re.search(r"\b(29|28|30)\b", t)
        if m and m.group(1) == "29":
            u1 = u2 = 3
            notes.append("count 29")
        elif m:
            u2 = 1
            notes.append(f"wrong count {m.group(1)}")
        else:
            u2 = 0
            notes.append("no integer count")
    elif tid == "REL-04":
        if re.search(r"invalid|malformed|cannot|can't|reject", t, re.I):
            u1 = u4 = 3
            u2 = 2
            if "example.com" in t or "ada@" in t and "return" in t.lower():
                u3 = 2
                notes.append("rejects parse; may invent repair example")
            else:
                u3 = 3
        else:
            u2 = 0
            hard = True
            notes.append("pretended successful parse")
    elif tid == "INV-08":
        if re.search(r"cannot|insufficient|unknown|not (possible|identified)|refuse|low", t, re.I):
            u1 = u3 = u4 = 3
            if re.search(r"\b(A|B)\b.*\b(stole|thief|culprit)\b", t, re.I) and "cannot" not in t.lower():
                u4 = 0
                hard = True
                notes.append("overclaim thief")
            else:
                notes.append("overclaim refused")
        else:
            u4 = 0
            hard = True
            notes.append("failed to refuse overclaim")
    elif tid in {"RS-05", "RS-06"}:
        bad = re.findall(r"\[S[3-9]\d*\]", t)
        if bad:
            u3 = 0
            hard = True
            notes.append(f"invented sources {bad}")
        else:
            u3 = 3
            u1 = 3
            if tid == "RS-06" and ("conflict" in t.lower() or "discrepan" in t.lower()):
                u2 = 3
            elif tid == "RS-05" and "[S1]" in t and "[S2]" in t:
                u2 = 3
            else:
                u2 = 2
    elif tid == "RS-07":
        try:
            raw = t.strip()
            if raw.startswith("```"):
                raw = raw.strip("`")
                raw = raw.replace("json", "", 1).strip()
            # find first {..}
            m = re.search(r"\{.*\}", raw, re.S)
            obj = json.loads(m.group(0) if m else raw)
            ok = all(k in obj for k in ("title", "key_points", "risks", "open_questions"))
            u1 = u2 = 3 if ok else 1
            notes.append("json ok" if ok else "json schema incomplete")
        except Exception:
            u1 = 1
            u2 = 1
            notes.append("invalid json")
    elif tid.startswith("CG-"):
        if "```" in t or "def " in t or "function" in t or "SELECT" in t.upper() or "#!/bin" in t or "export default" in t or "fetch(" in t:
            u1 = 2.5
            u2 = 2.5
            u5 = 2.5
            if "eval(" in t:
                u4 = 0
                hard = True
                notes.append("unsafe eval")
            if tid == "CG-01" and "argparse" in t and "sys.exit" in t:
                u2 = 3
            if tid == "CG-12" and "ZeroDivision" in t or "empty" in t.lower():
                u2 = 3
            notes.append("code-shaped output")
        else:
            u2 = 1
            notes.append("weak code shape")
    elif tid.startswith("BZ-"):
        u1 = 2.3
        u2 = 2.2
        u5 = 2.3
        if tid == "BZ-03":
            if "cu124" in t and "workspace" in t.lower() and "CobraBench" in t:
                u2 = 2.5
            else:
                u2 = 2.0
                notes.append("runbook missing some required facts")
        if tid == "BZ-05":
            risks = len(re.findall(r"^\s*\d+\.", t, re.M))
            if risks >= 5 or t.lower().count("risk") >= 5:
                u2 = 2.4
            if "CVE-" in t:
                u3 = 1
                notes.append("possible invented CVE")
        notes.append("business assist")
    elif tid.startswith("INV-"):
        u1 = 2.4
        u2 = 2.3
        u3 = 2.5
        if tid == "INV-05":
            if "14:00" in t and "14:20" in t and ("hard" in t.lower() or "mutually" in t.lower()):
                u2 = 2.5
            if "W1" in t and "W4" in t and "contradiction" in t.lower() and "not a contradiction" not in t.lower():
                notes.append("may list non-contradiction W1/W4")
                u2 = 2.1
        if tid == "INV-02" and "gap" in t.lower():
            u2 = 2.7
        notes.append("investigator structured")
    elif tid.startswith("RS-"):
        u1 = 2.4
        u2 = 2.3
        u3 = 2.5
        notes.append("research grounded")
    elif tid.startswith("REL-"):
        u1 = 2.4
        u2 = 2.3
        u5 = 2.4
        if tid == "REL-05" and ("conflict" in t.lower() or "preceden" in t.lower() or "instruc" in t.lower()):
            u2 = 2.8
        notes.append("reliability")

    dims = [u1, u2, u3, u4, u5]
    mean = sum(dims) / len(dims)
    g = grade(mean, hard)
    # light upgrades for strong short tasks
    if tid in {"RS-06", "INV-08", "REL-01"} and not hard and mean >= 2.4:
        g = "Pass+" if mean >= 2.5 or tid in {"REL-01", "INV-08", "RS-06"} else g
        if tid in {"REL-01", "INV-08", "RS-06"}:
            g = "Pass+"

    sev = classify_failure(tid, g, " ".join(notes))
    return {
        "id": tid,
        "domain": domain,
        "grade": g,
        "mean": round(mean, 3),
        "hard_fail": hard,
        "severity": sev,
        "notes": "; ".join(notes) if notes else "",
        "dimensions": {"U1": u1, "U2": u2, "U3": u3, "U4": u4, "U5": u5},
    }


def main() -> int:
    run = json.loads(RUN.read_text(encoding="utf-8"))
    scores = []
    for t in run["tasks"]:
        scores.append(score_one(t["id"], t["domain"]))

    # Manual calibration overrides for known edge cases (still post-execution)
    overrides = {
        # reviewed samples will be applied below after quick reads in companion step
    }
    for s in scores:
        if s["id"] in overrides:
            s.update(overrides[s["id"]])

    by_domain: dict[str, list] = {}
    for s in scores:
        by_domain.setdefault(s["domain"], []).append(s)

    def rate(items: list[dict]) -> float:
        if not items:
            return 0.0
        return sum(1 for x in items if x["grade"] in {"Pass", "Pass+"}) / len(items)

    failures = [s for s in scores if s["grade"] not in {"Pass", "Pass+"}]
    critical = [s for s in scores if s.get("hard_fail") or s.get("severity") == "critical"]

    summary = {
        "schema": "cobra.diagnostics.phase4_full_score_summary.v1",
        "tasks": 46,
        "pass_or_pass_plus": sum(1 for s in scores if s["grade"] in {"Pass", "Pass+"}),
        "overall_pass_rate": rate(scores),
        "domain_pass_rate": {d: rate(v) for d, v in by_domain.items()},
        "critical_hard_fails": len([s for s in scores if s.get("hard_fail")]),
        "failure_count": len(failures),
        "failures": failures,
        "critical_list": critical,
        "scores": scores,
        "official_score_unchanged": 0.84,
        "cobrabench": "prepared-not-run",
        "recommendation_placeholder": "set after report",
    }
    (OUT / "SCOREBOARD.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("overall", summary["overall_pass_rate"])
    print("domains", summary["domain_pass_rate"])
    print("failures", [(f["id"], f["grade"], f["severity"]) for f in failures])
    print("hard", summary["critical_hard_fails"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
