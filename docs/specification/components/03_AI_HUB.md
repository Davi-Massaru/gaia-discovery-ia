# Component 03 — Native AI Hub Scientific Investigator

**Purpose:** form hypotheses from available evidence, ask one testable scientific question, select a permitted next investigation, revise hypotheses after each result, and end with a qualified conclusion. It does **not** execute HTTP requests, inspect undocumented images directly, or confirm a discovery.

**Technology:** native `%AI.Provider` (OpenAI), `Gaia.AI.DiscoveryAgent Extends %AI.Agent` (prompt identity `GaiaDiscoveryAgent`), an isolated `%AI.Agent.Session` per decision, one `AIHubOperation` invoked by BPL. The agent owns the existing provider/model/instruction configuration; the Operation owns messages, session creation, invocation and failure mapping. Python builds/validates context. The extraction preserves the installed build-154 programmatic initialization; see [migration model](../../implementation/DISCOVERY_AGENT_MIGRATION.md).

## Input (bounded evidence)

```json
{
  "runId":"r-001",
  "observation":{"diaObjectId":"313761043604045880","raDeg":61.9648,"decDeg":-48.713,"tag":"in_tns","photometry":{"psfFlux":125.5,"psfFluxErr":8.2}},
  "historicalAnalogies":[],
  "completedActions":["CHECK_SIMBAD"],
  "catalogs":{"SIMBAD":{"status":"OK","matches":[{"id":"EXAMPLE","separationArcsec":2.1,"type":"Galaxy"}]}},
  "remainingCatalogCalls":2
}
```

*This is application sample data, not a Fink query result.* Do not put raw images, binary base64, secrets, full stack traces, or unbounded catalog rows in the context. Optional image features may be computed deterministically; no assumption that build 154 has multimodal input.

## Output schema

Use **exactly** [`AI_HUB_DECISION.schema.json`](../../contracts/AI_HUB_DECISION.schema.json): `hypothesis`, `alternative`, `next_action`, `question`, `reason`, `assessment`. `next_action` is one of `CHECK_GAIA`, `CHECK_SIMBAD`, `CHECK_IRSA`, `FINISH`. A catalog action requires an actual open question and `assessment=null`; `FINISH` requires assessment and an empty question.

```json
{
  "hypothesis":"Possible extragalactic transient",
  "alternative":"Stellar variability",
  "next_action":"CHECK_GAIA",
  "question":"Is there a plausible stellar counterpart?",
  "reason":"SIMBAD reports a nearby galaxy; stellar origin remains unresolved.",
  "assessment":null
}
```

For `FINISH`, use assessment `CATALOG_CONTEXT_FOUND`, `REVIEW_CANDIDATE`, or `INCONCLUSIVE`; `CATALOG_CONTEXT_FOUND` means there is contextual catalog evidence, **not a confirmed source identity**. A report's supporting/opposing evidence and uncertainty summary can be assembled from the decision history, saved catalog facts, and final agent conclusion. Never expose chain-of-thought or hallucinated citations.

## Agent policy

1. Prefer `FINISH` when further queries are not likely to change the outcome. Do not always exhaust the three catalogs.
2. Choose a catalog that addresses a *specific unanswered question*: Gaia for plausible stellar astrometry, SIMBAD for known type/context, IRSA for IR evidence.
3. After a returned result, state whether it supports, weakens, or leaves the hypothesis undecided; no invented probabilities.
4. Distinguish `EMPTY` from `ERROR`; treat vector histories as analogies, not independent scientific proof.
5. Do not repeat completed actions, invent an endpoint, issue SQL, or produce a discovery confirmation.

## Deterministic validation

Embedded Python validates the JSON Schema and ensures `next_action` not already completed; remaining budget; references only supplied evidence; no missing reason/question; valid final assessment. Invalid schema/model timeout -> `INCONCLUSIVE` with a traceable error. Provider key stays in ignored `.env` / supported IRIS secret configuration.

## Observability

Log `runId`, native interoperability session ID, AI Hub Session ID (when available), action, reason and referenced evidence IDs. Track latency and token use when SDK exposes it. Do not claim AI Hub internal tool invocations appear in Interoperability Visual Trace.

**References:** user-provided `IA_HUB.agent(9).md` (source discipline and native SDK responsibility model); official EAP documentation https://github.com/intersystems-community/ai-hub-eap/blob/master/ObjectScript_SDK_Guide.md .
