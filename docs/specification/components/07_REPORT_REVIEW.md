# Component 07 — DiscoveryReport + Minimal Native IRIS Workflow

**Source of truth:** [`SPEC.md`](../../../SPEC.md). This document contains the **single canonical implementation contract** for human review. The scientific report exists before a reviewer acts. Reviewer `ACCEPT` means *send for further scientific investigation*, never confirm an astronomical discovery.

## One existing report, one native task type

`Gaia.Data.DiscoveryReport extends %Persistent` stores one report per investigated Fink object/run, including Fink source IDs, RA/Dec/time, real Science/Template/Difference binary streams, AI hypotheses, evidence/provenance JSON, `InteropSessionId`, vector fields, `Assessment`, and `ReviewStatus`. Compose and update report data in **in-process Embedded Python** where supported; native `%Persistent` is declarative.

**Review statuses:** `NOT_REQUIRED`, `PENDING`, `ACCEPTED_FOR_REVIEW`, `REJECTED`, `TASK_ERROR`. No separate task table or reviewer domain entity is required.

## Production configuration (native only)

| Element | Exact minimal configuration |
|---|---|
| Existing BPL | `Gaia.Interop.DiscoveryWorkflow`; reuse it for scientific investigation and review |
| Existing BO class | `EnsLib.Workflow.Operation` (**native**, no subclass) |
| BO configuration name | `AstronomyReviewer` (same exact name as BPL `<call>` target) |
| Workflow role | `AstronomyReviewer` (native **Workflow Role**, not a new IRIS security-role class); enable `AutoCreateRole = 1` or create this same role with native administration |
| Reviewer | Assign at least one authorized IRIS workflow user to this role through standard IRIS configuration |
| Task request class | `EnsLib.Workflow.TaskRequest` (**native**, no subclass) |
| Task response class | `EnsLib.Workflow.TaskResponse` (**native**, no subclass) |
| Inbox | Built-in IRIS Workflow Inbox / User Portal; no custom page or API |
| Actions | `%Actions = "ACCEPT,REJECT"`; only the returned `%Action` determines the outcome |

The operation represents the workflow role. `AutoCreateRole` can create a role named after that operation; **it does not automatically assign a reviewer**. See [official Developing a Workflow](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=EGWF_dev) and [Workflow Overview](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=EGWF_overview).

## Required BPL sequence — no second process, no callback service

1. Complete the autonomous investigation for each alert. Save the report and real scientific data; never await human review before the save.
2. If `Assessment != REVIEW_CANDIDATE`, persist `ReviewStatus = NOT_REQUIRED` and finish that alert.
3. If `Assessment = REVIEW_CANDIDATE`, persist `ReviewStatus = PENDING` and prepare **one** `EnsLib.Workflow.TaskRequest`. Set `%Subject` to a clear summary including report ID, `%Message` to a short human-readable evidence summary plus the report ID, and `%Actions = "ACCEPT,REJECT"`. The BPL context keeps the original `reportId` for updating the right row.
4. Use an **asynchronous BPL `<call>`** to target `AstronomyReviewer`. This is a native Workflow Operation call, not an ordinary AI Hub decision or a simulated database approval. An enqueue/dispatch failure results in `ReviewStatus = TASK_ERROR`, not a false pending/accepted result.
5. When scientific work for the run is saved and tasks have been dispatched, mark **run scientific status** `COMPLETED` (or the applicable failure/no-alert state). The REST `POST /api/discoveries/run` already returned `202 {runId}`; it **does not wait** for a human.
6. The **same BPL instance** uses native `<sync>` to wait for its outstanding asynchronous Workflow call(s). The instance may remain suspended until a reviewer acts; this is **not** an open HTTP connection. For batches, dispatch/save all candidate reports before the synchronization and correlate each reply to its original report ID.
7. The native Inbox returns `EnsLib.Workflow.TaskResponse` after completion. Read **`%Action`**, not a guessed field. Map `ACCEPT → ACCEPTED_FOR_REVIEW`, `REJECT → REJECTED`. Persist in the **same** `DiscoveryReport`, optionally recording reviewer/timestamp in existing evidence JSON. A missing/invalid action is an error, not an approval.
8. The UI only reads the report's saved review state from IRIS. No approval buttons, new REST endpoint, reviewer dashboard, separate workflow service, new class, or polling of the Workflow Engine are part of the MVP.

> **BPL construction note:** `<call>` with asynchronous flag plus `<sync>` is the documented native pattern; the exact generated BPL XML and message property syntax must be checked in the installed EAP build before compilation. Do **not** improvise a custom `TaskResponse` callback handler to bypass native `<sync>`.

```mermaid
sequenceDiagram
    participant UI as REST / Discovery Feed
    participant BP as Existing DiscoveryWorkflow BPL
    participant DB as DiscoveryReport
    participant OP as AstronomyReviewer (native Workflow BO)
    participant WF as Workflow Inbox
    UI->>BP: Submit investigation (request accepted with runId)
    BP->>DB: Save scientific report
    alt REVIEW_CANDIDATE
        BP->>DB: ReviewStatus = PENDING
        BP-)OP: async TaskRequest (%Actions=ACCEPT,REJECT)
        OP->>WF: Native IRIS Workflow Engine task
        Note over BP,WF: UI request already returned; BPL later syncs for reply
        WF-->>OP: Reviewer completes task
        OP-->>BP: TaskResponse (%Action)
        BP->>DB: Update same report review status
    else Normal result
        BP->>DB: ReviewStatus = NOT_REQUIRED
    end
```

## Demo and tests required for the +2-point opportunity

- Production screenshot shows `DiscoveryWorkflow` BPL and native `AstronomyReviewer` operation of class `EnsLib.Workflow.Operation`.
- Native Workflow Role has at least one assigned user; review task appears in that user's **native Inbox**.
- A real `REVIEW_CANDIDATE` report is readable with `PENDING` while its reviewer task is incomplete.
- Complete one task as `ACCEPT` and one as `REJECT`; their **actual** `TaskResponse.%Action` values return through BPL `<sync>` and update the same saved reports.
- Show one noncandidate report with `NOT_REQUIRED`, one submission/assignment error with `TASK_ERROR`, and verify the run's REST request was not blocked by the human wait.
- Capture BPL Visual Trace and task completion evidence. These are acceptance targets, **not evidence of execution** in this ZIP.

**Scope guard:** This implementation uses the existing BPL, one native operation, one Workflow Role, native TaskRequest/TaskResponse, and native Inbox. No custom Workflow Engine class, approval microservice, new database table, or third UI view.
