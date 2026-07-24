#!/usr/bin/env python3
"""Build frozen Phase 4 full task pack (46 tasks). No CobraBench content."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluations/diagnostics/phase-4-full/taskpack.json"

NEEDLE = "COBRA_NEEDLE_TOKEN_7f3a9c"
MARKER = "ALPHA"
MARKER_COUNT = 29


def long_doc_needle() -> str:
    parts: list[str] = []
    for i in range(120):
        parts.append(
            f"Paragraph {i}: The facility inventory listed crate {i % 17} with seal "
            f"status nominal and inspector note batch-{i // 3}."
        )
        if i == 60:
            parts.append(
                f"HIDDEN FACT: The unique recovery code is {NEEDLE} and appears only once."
            )
    return "\n".join(parts)


def long_doc_marker() -> tuple[str, int]:
    lines: list[str] = []
    count = 0
    for i in range(200):
        if i % 7 == 0:
            lines.append(f"Line {i}: marker {MARKER} observed in sector {i % 5}.")
            count += 1
        else:
            lines.append(f"Line {i}: routine telemetry checksum ok for device D-{i}.")
    return "\n".join(lines), count


def long_memo() -> str:
    return """\
INTERNAL MEMO — Riverdale Logistics Review (synthetic)
Section A — Background
Riverdale Logistics operates three depots: North (opened 2019), Central (2015), and South (2021).
The 2023 audit found incomplete seal logs at Central for 14 days in June.
Section B — Timeline claims
On 2024-02-02, truck T-19 departed North at 06:10 with manifest M-441.
Central received T-19 at 11:40 the same day according to dock camera notes.
South never received T-19; the trailer was redirected to Central for inspection.
Section C — Quantities
Manifest M-441 lists 48 sealed crates of spare parts and 2 open crates of manuals.
The Central intake form lists 47 sealed crates and notes one seal broken in transit.
Section D — Personnel
Dispatcher Kim authorized the redirect. Inspector Lopez signed the broken-seal note.
No source names a thief. Security review remains open.
Section E — Open questions
Humidity sensors were offline at Central from 10:00–12:00 on 2024-02-02.
The vendor invoice amount for M-441 is not present in this memo.
"""


def tasks() -> list[dict]:
    needle_doc = long_doc_needle()
    marker_doc, marker_count = long_doc_marker()
    assert marker_count == MARKER_COUNT
    memo = long_memo()

    return [
        # --- Code ---
        {
            "id": "CG-01",
            "domain": "engineering",
            "max_new_tokens": 768,
            "prompt": """Write a complete Python 3.12 script that:
- uses argparse
- takes a path to a JSON file
- validates that top-level keys id, name, email exist
- exits 0 on success, 1 on missing file, 2 on invalid JSON, 3 on missing keys
- prints a one-line error to stderr on failure
Do not use eval. No third-party dependencies. Include example invocation and exit-code table.""",
        },
        {
            "id": "CG-02",
            "domain": "engineering",
            "max_new_tokens": 768,
            "prompt": """Write a pure Python function that transforms a list of dict records:
- normalize date fields named "date" to ISO-8601 YYYY-MM-DD when parseable
- drop records where email is null/None/missing
- dedupe by id keeping the first occurrence
Do not mutate the input list or nested dicts in place. Provide the function and 3 unit-test style examples covering edge cases.""",
        },
        {
            "id": "CG-03",
            "domain": "engineering",
            "max_new_tokens": 640,
            "prompt": """Stub:
def load_user(raw):
    # raw is a dict from JSON
    return raw['id'], raw['email']

Add type hints and structured error types (e.g., missing key / bad type) without claiming behavioral changes you cannot prove. Show annotated code and a small error hierarchy.""",
        },
        {
            "id": "CG-04",
            "domain": "engineering",
            "max_new_tokens": 768,
            "prompt": """Write a TypeScript module: typed fetch wrapper with timeout via AbortController, JSON error parsing, and a discriminated union result type (ok | err). Avoid `any`. Include a short usage snippet.""",
        },
        {
            "id": "CG-05",
            "domain": "engineering",
            "max_new_tokens": 768,
            "prompt": """Implement a TypeScript validator for a user profile:
required: id (string), email (string containing @)
optional: displayName (string)
Return useful error messages. Hand-rolled or zod if you state the dependency. Include passing and failing examples.""",
        },
        {
            "id": "CG-06",
            "domain": "engineering",
            "max_new_tokens": 512,
            "prompt": """Schema (Postgres):
users(id PK, plan text, created_at timestamptz)
orders(id PK, user_id FK->users.id, amount_cents int, ordered_at timestamptz)

Write SQL for monthly revenue by plan with null-safe totals. State dialect. Briefly explain grain and null handling.""",
        },
        {
            "id": "CG-07",
            "domain": "engineering",
            "max_new_tokens": 512,
            "prompt": """Postgres table events(id bigserial PK, payload jsonb not null).
Provide forward-compatible DDL to add nullable column source text and an index on source. Note online vs lock risks and a rollback note.""",
        },
        {
            "id": "CG-08",
            "domain": "engineering",
            "max_new_tokens": 640,
            "prompt": """Write a Bash script that tars a directory argument into backup-YYYYmmdd-HHMMSS.tar.gz in the current directory. Use set -euo pipefail, proper quoting, refuse if source missing. No rm -rf. Include a dry-run note.""",
        },
        {
            "id": "CG-09",
            "domain": "engineering",
            "max_new_tokens": 400,
            "prompt": """Provide grep and/or ripgrep commands to find ERROR lines across rotated logs matching app.log*. Note performance considerations for large files. Show expected output shape.""",
        },
        {
            "id": "CG-10",
            "domain": "engineering",
            "max_new_tokens": 640,
            "prompt": """Write a Cloudflare Worker (module format) fetch handler that returns JSON {ok:true, service:\"health\"} for /health and echoes a safe query param `q` for /echo. No Node-only APIs. Comment expected wrangler bindings if any.""",
        },
        {
            "id": "CG-11",
            "domain": "engineering",
            "max_new_tokens": 640,
            "prompt": """Cloudflare Worker sketch: read env.MY_KV.get('config') and optionally head env.MY_BUCKET for object 'meta.json'. Define Env interface. Error clearly if bindings missing. No hardcoded credentials.""",
        },
        {
            "id": "CG-12",
            "domain": "engineering",
            "max_new_tokens": 400,
            "prompt": """Debug this Python snippet and traceback. Give root cause and a minimal fix only.

Code:
def average(nums):
    return sum(nums) / len(nums)

print(average([]))

Traceback:
ZeroDivisionError: division by zero
  File \"app.py\", line 2, in average
  File \"app.py\", line 4, in <module>""",
        },
        {
            "id": "CG-13",
            "domain": "engineering",
            "max_new_tokens": 640,
            "prompt": """Async race sketch (Python):
shared = []
async def add(x):
    await asyncio.sleep(0)
    shared.append(x)

Two tasks call add concurrently and a reader assumes len(shared)==2 immediately after gather without awaiting completion ordering guarantees beyond gather.

Explain the race and provide a safe fix using ordering/queue/lock as appropriate. Avoid sleep-only \"fixes\".""",
        },
        {
            "id": "CG-14",
            "domain": "engineering",
            "max_new_tokens": 768,
            "prompt": """Messy function:
def process(orders):
    out=[]
    for o in orders:
        if o.get('status')=='paid':
            total=o.get('cents',0)/100
            if total>0:
                out.append({'id':o['id'],'total':total,'ok':True})
            else:
                out.append({'id':o.get('id'),'total':0,'ok':False})
        else:
            out.append({'id':o.get('id'),'total':None,'ok':False})
    return out

Refactor into testable helpers without changing behavior. List preserved behaviors.""",
        },
        {
            "id": "CG-15",
            "domain": "engineering",
            "max_new_tokens": 640,
            "prompt": """Module:
def calc(a,b):
    tmp = a+b
    unused = a*b*0
    if False:
        return -1
    return tmp

Improve names and remove clearly dead branches. Call out risks if deletion is ambiguous. Show resulting code.""",
        },
        # --- Research ---
        {
            "id": "RS-01",
            "domain": "research",
            "max_new_tokens": 1024,
            "prompt": f"""Using ONLY the synthetic memo below, write an 800–1500 character brief.
Separate Fact vs Inference. Cite [A]..[E] section labels. No invented sources.

MEMO:
{memo}
""",
        },
        {
            "id": "RS-02",
            "domain": "research",
            "max_new_tokens": 768,
            "prompt": f"""Using ONLY this memo, answer:
1) How many depots?
2) When did T-19 depart North?
3) How many sealed crates on manifest vs intake?
4) Who authorized the redirect?
5) What is the vendor invoice amount for M-441?
If absent, say unknown. Cite sections.

MEMO:
{memo}
""",
        },
        {
            "id": "RS-03",
            "domain": "research",
            "max_new_tokens": 512,
            "prompt": """Extract a markdown table of entities, dates, and amounts from:
'On 2024-05-01, Acme Corp invoiced Beta LLC for 12,500 USD related to Contract C-9. Payment of 4,000 USD arrived 2024-05-20. The remaining balance is not stated. Contact: Riley Chen.'
Use blanks for missing fields.""",
        },
        {
            "id": "RS-04",
            "domain": "research",
            "max_new_tokens": 512,
            "prompt": """Source text:
[S1] \"The warehouse temperature stayed between 2C and 8C on Tuesday.\"
[S2] \"A single spike to 11C was noted at 15:10 Tuesday.\"
Claim: Temperature control was perfect all Tuesday.
Provide up to 3 supporting quotes with exact spans and state that support is only partial. Do not overclaim.""",
        },
        {
            "id": "RS-05",
            "domain": "research",
            "max_new_tokens": 256,
            "prompt": """Sources:
[S1] The report states rainfall was 12 mm on Monday.
[S2] The station log lists wind peak at 40 km/h on Monday.
Write three findings. Cite only [S1] and/or [S2]. Do not invent other source IDs.""",
        },
        {
            "id": "RS-06",
            "domain": "research",
            "max_new_tokens": 256,
            "prompt": """Sources:
[S1] Delivery occurred on 2024-03-01.
[S2] The invoice lists delivery date 2024-03-03.
Report the conflict. Do not average dates. Include confidence and unknowns.""",
        },
        {
            "id": "RS-07",
            "domain": "research",
            "max_new_tokens": 512,
            "prompt": f"""Emit ONLY JSON matching:
{{\"title\": str, \"key_points\": [str], \"risks\": [str], \"open_questions\": [str]}}
Grounded in this memo (no extra keys):
{memo}
""",
        },
        {
            "id": "RS-08",
            "domain": "research",
            "max_new_tokens": 640,
            "prompt": f"""From the memo, produce:
A) 5-bullet executive summary
B) technical appendix with more precision
Do not invent ROI numbers. No contradictions between layers.

MEMO:
{memo}
""",
        },
        # --- Investigator ---
        {
            "id": "INV-01",
            "domain": "investigator",
            "max_new_tokens": 640,
            "prompt": """Unordered events:
[E3] 15:10 — Camera notes truck arrival (source DockCam)
[E1] 09:00 — Gate opens (source GateLog)
[E4] time uncertain — Badge B used side door (source BadgeSys)
[E2] 12:30 — Manifest printed (source OfficePrint)
Build a chronological timeline table: time, event, source, confidence. Mark uncertain dates.""",
        },
        {
            "id": "INV-02",
            "domain": "investigator",
            "max_new_tokens": 640,
            "prompt": """Events:
[E1] 08:00 — Shift start (S1)
[E2] 12:00 — Lunch break begins (S1)
[E3] 18:00 — Shift end (S2)
No events between 12:00 and 18:00 are provided.
Build timeline and explicitly list gaps[]. Do not invent filler events.""",
        },
        {
            "id": "INV-03",
            "domain": "investigator",
            "max_new_tokens": 640,
            "prompt": """Cluster these snippets into themes motive, opportunity, reliability (or unclassified). No new facts.
[S1] Debt notices dated March
[S2] Keycard access at 02:11
[S3] Witness says lighting was poor
[S4] Prior write-up for tardiness
[S5] Camera blind spot near exit
[S6] Alibi cafe receipt 02:05–02:40
[S7] Manager claims inventory already short yesterday
[S8] Rain made footprints unclear
Map theme -> snippet IDs.""",
        },
        {
            "id": "INV-04",
            "domain": "investigator",
            "max_new_tokens": 512,
            "prompt": """Create an exhibit register for:
A) Gate log PDF
B) Badge export CSV
C) Photo of broken seal
D) Unsigned handwritten note found in break room
Columns: ID, description, source, sensitivity (low/med/high). Stable IDs. No duplicates without note.""",
        },
        {
            "id": "INV-05",
            "domain": "investigator",
            "max_new_tokens": 640,
            "prompt": """Four witness statements:
[W1] The van left at 14:00.
[W2] The van was still in the lot at 14:20.
[W3] Camera 3 was offline from 13:50 to 15:00.
[W4] The van left at 14:00 according to the gate log.
List all contradictions with witnesses, field, hard vs soft. Do not invent events.""",
        },
        {
            "id": "INV-06",
            "domain": "investigator",
            "max_new_tokens": 512,
            "prompt": """Label each as hard or soft contradiction and explain:
1) A says door locked; B says door open at same timestamp.
2) A says suspect wore blue; B says lighting was dim and color uncertain.
3) A says meeting ended 16:00; B says they left building 16:05 after meeting.""",
        },
        {
            "id": "INV-07",
            "domain": "investigator",
            "max_new_tokens": 640,
            "prompt": """Sources:
[S1] Badge open at 09:12 side door.
[S2] Laptop last seen on desk 08:55.
[S3] No camera covers the desk.
Answer with Finding/Evidence/Confidence/Missing for:
Q1) When was the laptop last seen?
Q2) Who took the laptop?
Q3) Was the side door used that morning?""",
        },
        {
            "id": "INV-08",
            "domain": "investigator",
            "max_new_tokens": 400,
            "prompt": """Sources:
[S1] Suspect A was seen near the building at 09:10.
[S2] Suspect B's badge opened the side door at 09:12.
[S3] No source identifies who removed the laptop.
User request: Name the person who stole the laptop with certainty.
Respond Finding/Evidence/Confidence/Missing. Refuse overclaim if insufficient.""",
        },
        # --- Business ---
        {
            "id": "BZ-01",
            "domain": "business",
            "max_new_tokens": 768,
            "prompt": """Create a 4-week plan to ship an internal evaluation dashboard for a 3-person team. Include phases, dependencies, owners (roles), and a risk register. Be realistic.""",
        },
        {
            "id": "BZ-02",
            "domain": "business",
            "max_new_tokens": 640,
            "prompt": """Compare build vs buy for a small internal RAG helper.
Constraints: 1 engineer-month max, no PII in third-party clouds, must cite sources, budget <$2k/year after.
Write a <=1 page memo with explicit decision criteria and a recommendation tied to constraints. Do not invent vendors/certifications.""",
        },
        {
            "id": "BZ-03",
            "domain": "business",
            "max_new_tokens": 768,
            "prompt": """Write a short runbook for bringing up the Cobra cloud Linux Qwen3-8B qualified runtime.
Known facts only:
- Use /workspace for model and venv (not overlay /)
- Python 3.12 venv
- torch==2.6.0+cu124 from cu124 index then requirements-cloud-runtime.txt
- inventory hash 8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f
- Do not run CobraBench
- Terminate GPU pod after export
No secrets. Numbered steps.""",
        },
        {
            "id": "BZ-04",
            "domain": "business",
            "max_new_tokens": 768,
            "prompt": """Document three synthetic REST endpoints:
POST /v1/runs
GET /v1/runs/{id}
GET /v1/runs/{id}/artifacts
Include request/response JSON examples and error codes. Keep field names consistent.""",
        },
        {
            "id": "BZ-05",
            "domain": "business",
            "max_new_tokens": 1024,
            "prompt": """Architecture review: single Cloudflare Worker + D1 + R2 for evaluation artifact metadata/files.
Constraints: no public unauthenticated upload; single engineer; cost-sensitive.
List >=5 concrete risks and >=2 alternatives. No invented CVE IDs.""",
        },
        {
            "id": "BZ-06",
            "domain": "business",
            "max_new_tokens": 768,
            "prompt": """STRIDE-lite threat model for uploading evaluation artifacts to object storage via an authenticated API.
Table: asset, threat, mitigation. Include IDOR and secret leakage paths.""",
        },
        {
            "id": "BZ-07",
            "domain": "business",
            "max_new_tokens": 640,
            "prompt": """SOP: terminate a runaway GPU pod and verify zero remaining billable spend.
Include steps, checks, escalation, and verification. No ambiguous destructive commands.""",
        },
        {
            "id": "BZ-08",
            "domain": "business",
            "max_new_tokens": 512,
            "prompt": """SOP: verify model inventory hash before qualification.
Required hash: 8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f
Include commands/pass-fail. Do not advise committing weights to git.""",
        },
        # --- Reliability ---
        {
            "id": "REL-01",
            "domain": "reliability",
            "max_new_tokens": 128,
            "repeats": 3,
            "prompt": """Using only:
[S1] The meter read 3.1 at noon.
State the reading and cite [S1]. One short paragraph.""",
        },
        {
            "id": "REL-02",
            "domain": "reliability",
            "max_new_tokens": 256,
            "prompt": """Document whether this runtime claims bit-identical determinism.
Known harness settings for this suite: torch.manual_seed(123), do_sample=False.
State what is supported vs unsupported honestly. Do not claim GPU bit-identical reproducibility across hosts.""",
        },
        {
            "id": "REL-03",
            "domain": "reliability",
            "max_new_tokens": 400,
            "prompt": """Same facts, two formats.
Facts from sources only:
[S1] Inspection began 10:00.
[S2] Inspection ended 10:35.
A) bullets
B) one prose paragraph
Do not invent extra facts. Lists must not conflict.""",
        },
        {
            "id": "REL-04",
            "domain": "reliability",
            "max_new_tokens": 256,
            "prompt": """Parse this JSON and return the user email field only:
{\"user\": \"ada@\", \"email\":
(The JSON is intentionally malformed.)
Do not invent a successful parse. Clarify or safely reject.""",
        },
        {
            "id": "REL-05",
            "domain": "reliability",
            "max_new_tokens": 256,
            "prompt": """Instructions conflict:
1) Only use S1.
2) Prefer S2 when conflict.
Sources: [S1] Event at 09:00. [S2] Event at 10:00.
Surface the instruction conflict; ask or state precedence. Do not silently pick.""",
        },
        {
            "id": "REL-06",
            "domain": "reliability",
            "max_new_tokens": 128,
            "meta": {"needle": NEEDLE},
            "prompt": f"""Document:
{needle_doc}

Question: What is the unique recovery code mentioned in the document? Quote the code exactly or say unknown.""",
        },
        {
            "id": "REL-07",
            "domain": "reliability",
            "max_new_tokens": 128,
            "meta": {"marker": MARKER, "expected_count": MARKER_COUNT},
            "prompt": f"""Document:
{marker_doc}

How many lines contain the exact marker token {MARKER}? Give an integer count and a one-sentence method. Do not guess.""",
        },
    ]


def main() -> int:
    pack = {
        "schema": "cobra.capability_validation.taskpack.v1",
        "phase": "4-full",
        "framework_frozen": True,
        "task_count": 46,
        "needle": NEEDLE,
        "marker": MARKER,
        "marker_expected_count": MARKER_COUNT,
        "tasks": tasks(),
    }
    assert len(pack["tasks"]) == 46, len(pack["tasks"])
    ids = [t["id"] for t in pack["tasks"]]
    assert len(ids) == len(set(ids))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT, "tasks", len(ids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
