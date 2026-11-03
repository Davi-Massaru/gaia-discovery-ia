# Codex — Minimal Implementation Prompt

Use this short prompt in the repository root. The documents below establish requirements; avoid re-reading all of them on every task.

```text
Implement Gaia Discovery AI from SPEC.md (source of truth).
Use docs/implementation/IMPLEMENTATION_GUIDE.md for build order and
CLASS_MAP.md + CLASS_CONTRACTS.md for the exact class/file boundaries.
Read only the related docs/specification/components/*.md and docs/contracts/*.md
before implementing each respective component. Validate external signatures
against the installed IRIS AI Hub EAP runtime; never invent vendor APIs.

Web API is **Flask** (`backend/app.py`, callable `app`) hosted via **native IRIS WSGI**
under `/gaia`; API routes are mount-relative. No native %CSP.REST wrapper, no
external Flask/Gunicorn server. Verify native WSGI on EAP build 154.
Python First: Embedded Python for IRIS domain/science logic; ObjectScript only
for native declarations/BPL/schema/required SDK glue; Java only for one
registered PEX TAP transport adapter shared by Gaia, SIMBAD and IRSA BOs.
One Production, one BPL, one native AI Hub agent and native IRIS Workflow
Operation/Role/Inbox; do not create another BPL, reviewer service/table/UI.
Use real Fink alerts/images and external catalog responses. Preserve statuses,
source provenance, SQL report/vector history and IRIS session trace IDs.
Fetch count is bounded/configurable 1..20 (default 5), processed sequentially;
max three distinct catalog requests per alert. Build UI last (two views).

Never change requirements, add unrelated classes, make fake astronomy data,
or include .env in source control. Run real contract/runtime tests, publish
ZPM only when complete, report what is verified vs unverified.
```

**Use with:** [master SPEC](../../SPEC.md) · [build plan](IMPLEMENTATION_GUIDE.md) · [class contracts](CLASS_CONTRACTS.md).
