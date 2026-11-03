# Gaia Discovery AI — Bonus Eligibility Summary

**Status:** planned, not awarded. Based on the [official 2026 contest bonus announcement](https://community.intersystems.com/post/technology-bonuses-intersystems-programming-contest-ai-agents-interoperability-workflows).

| Technology bonus | Points | Included? | Product use / proof |
|---|---:|---|---|
| Java Production EXtension (PEX) | 3 | Yes | Real Java PEX outbound TAP adapter registered as an IRIS component and used by native catalog BOs |
| Custom Adapter | 2 | Yes | The **same** custom Java TAP adapter implements allowlisted ADQL communication with three external catalogs |
| Embedded Python | 3 | Yes | Python-first in-process Fink/catalog data processing, angular separation, evidence/report SQL and embeddings |
| IRIS Vector Search | 2 | Yes | IRIS SQL `VECTOR_COSINE` over prior `DiscoveryReport` conclusions |
| IRIS Workflow Engine | 2 | Yes | Existing BPL native asynchronous `TaskRequest` to `EnsLib.Workflow.Operation` / `AstronomyReviewer` role, native Inbox completion, `TaskResponse.%Action` via BPL `<sync>`, saved review-status update |
| Docker | 2 | Yes | IRIS AI Hub EAP build 154 container; Java gateway in same deployment |
| ZPM | 2 | Yes | Published installable package with Java JAR/proxy setup and clean install verification |
| Implement Community Idea | 4 | Optional | No dependency or requirement in the primary product specification |

**Total potential technology bonus: 16 points (excluding Community Idea).** A single custom Java PEX adapter is intended to satisfy both separately listed PEX and Custom Adapter criteria, but bonus eligibility is decided by contest organizers after runtime inspection.

**Mandatory scientific safeguard:** Similarity of investigation narratives is not evidence that the sky coordinates refer to the same source. Historic AI conclusions may be erroneous and must be labeled as previous application assessments, not as verified research.

## Python-first implementation policy

Follow the canonical [Python First policy](../../SPEC.md): Embedded Python implements application/data behavior; ObjectScript supplies necessary IRIS-native glue; Java is restricted to the one PEX custom TAP adapter. Verify build-154 compatibility.

## Operational evidence to capture

- IRIS Message Trace: distinct AI-selected routes, selected catalog BO call, normalized response and report ID.
- Registered Java PEX component/proxy, Java gateway logs and live TAP request.
- IRIS SQL containing an actual vector plus SELECT top-three `VECTOR_COSINE` results.
- Embedded Python method inside IRIS computing an angular distance.
- Workflow Inbox task created, completed and linked to a changed `ReviewStatus`.
- Docker run of approved EAP build; published ZPM clean install.

The official announcement also lists separately earned non-architecture bonuses (public demo, videos and Community articles). They are not included in the 16-point technology total.
