# Freeze 1.2 hostile review (revision 2: source-mechanism correction)

Verdict key: **HELD** = control effective (tested or structural). **RESIDUAL** = partial
control, residual risk stated. **OPEN** = unresolved; blocks a later gate.

| # | Attack | Control | Verdict |
| --- | --- | --- | --- |
| 1 | Source cherry-picking | No catalog is named. The index was chosen only on terms, credentials and robots grounds, with every evaluated class recorded. Catalogs come only from the four unchanged Freeze-1.1 query strings. All qualifying results are used, with ≥2 independent maintainers and no substitute. | HELD. RESIDUAL: the choice of index is a researcher decision, made blind to content. |
| 2 | Terms/licence ambiguity | Access relies on GitHub AUP §7's explicit API-collection and research clause, with the verbatim sentences re-verified at preflight (`TERMS_CHANGED` halts). S-LIC and S-ACCESS gate each catalog's own licence and path. Zenodo and commercial APIs were rejected on robots or credential grounds. | RESIDUAL: the research clause is conditional (open-access publications, non-personal information only), so the custodian must attest. The terms basis for vendor documentation pages at later stages is **OPEN** (scheduler blocked). |
| 3 | Hidden search-engine dependence | No web engine is used. GitHub search is an explicit, named ranking engine, disclosed. Tests assert the runner has no Bing, Google or DuckDuckGo code and no HTML path. | HELD, and disclosed. |
| 4 | Source coverage bias | The narrowing to GitHub-hosted, licensed catalogs is declared in `source-mechanism.json` and the amendment §5. Reporting of that support is mandatory. There is no global-coverage claim. | RESIDUAL, by design: the overlap with web-discoverable catalogs is unknown and not estimated from memory. |
| 5 | Popularity bias | Best match plus top-20 truncation, as under Freeze 1.1. `total_count` is published so the extent of truncation is visible. No sort by stars. | RESIDUAL: GitHub's ranking signals are undocumented. |
| 6 | Geography bias | Worldwide listings and the UK-customer context are unchanged. The GB/English interface parameters are gone because GitHub has no locale; the English query terms remain. | RESIDUAL, disclosed. |
| 7 | Content preview before source selection | Only terms, policy and API-documentation pages were read. Zero search requests; no repository or catalog opened. `--preflight-check` cannot reach the discovery endpoint (tested). | HELD |
| 8 | Mutable source selection | Queries, parameters, positions and screening order are constants in digested code. Preflight enforces the runner bytes equal the remote-tag bytes. | HELD |
| 9 | Post-observation substitution | Any halt is final. No alternate session, date, index or catalog is allowed. A deficient frame halts. | HELD |
| 10 | Source disappearance | Deleted, renamed or rewritten → SOURCE_UNRESOLVED, which blocks lock. Only a byte-identical copy verified against the commit/tree hash is accepted. | HELD, fail-closed. RESIDUAL: a disappearance can kill the cohort. |
| 11 | Incomplete enumeration | `incomplete_results` → halt. `items ≠ min(20, total_count)` → halt. Truncation > 5 MiB → halt. Tests cover each. | HELD |
| 12 | Candidate omission | Every item in positions 1..min(20, total) is projected. Every occurrence is recorded. The Freeze-1.1 all-rows extraction rule is unchanged. | HELD |
| 13 | Duplicate enumeration | Union by repository id with occurrences retained. Forks and mirrors are resolved to their upstream. Duplicates never add weight. | HELD |
| 14 | Raw-evidence retention restrictions | Raw bytes are kept in custody outside the repository and never published, because they contain personal user objects. The published projection excludes owner login objects and avatars (tested). Both hashes are published, and the projection function is digested. | RESIDUAL: `full_name` embeds the owner login for user-owned repositories; auditing raw bytes needs custodian cooperation. |
| 15 | Capture timing gaming | Date fixed now, 2026-09-23T09:00:00Z, before any observation. Self-timed start with a 5 s limit under pre and post offsets; a late invocation halts. | HELD |
| 16 | Rerun ability | Capture and custody directories are created exclusively. `REFUSED_RERUN` is logged. Git history and the remote push anchor the attempt. | RESIDUAL: local deletion plus a rerun cannot be prevented by software. Push `attempts.jsonl` right after launch. |
| 17 | Source-specific parser manipulation | Discovery parsing is one generic, digested projection. Per-source row parsers remain FUTURE_STAGE, locked from each catalog's documented schema before rows are parsed (Freeze 1.1). | HELD at this stage. |
| 18 | Prior-FIRSTCALL leakage | Projector revision 2 is structural: value type, fences and example paths. Result, receipt and evidence contexts are never parsed. Tests show nine leak strings never appear. The dry run printed only statuses and paths. | HELD. RESIDUAL: `candidates.json` needs adjudicator confirmation. |
| 19 | Role conflicts | Unchanged validator rules. The capture custodian can hold no entropy role. ADJ-1 ≠ ADJ-2. Model adjudicators are rejected. | HELD |
| 20 | Estimand drift | The estimand text is unchanged and frame-relative by Freeze-1.1 construction. The support change is declared, never hidden. The custodian must accept it at anchoring or not anchor. | RESIDUAL; this is the key judgement. If a reviewer holds that GitHub-only discovery changes the target population materially, the decision becomes NOT_SEALABLE. |

## Additional findings

- **OPEN:** the terms basis for automated retrieval and retention of vendor documentation
  pages in the Freeze-1.1 identity/eligibility stages is unresolved. It is the same concern
  class that withdrew Bing. The scheduler (R10) cannot be registered until a prospective
  rule exists.
- **Untested feasibility:** whether the four AND-style queries return enough repositories,
  and whether ≥2 independently maintained qualifying catalogs exist among them. Testing
  either would be a preview, and a deficient frame halts.
- **Clean-clone Freeze-1.1 check:** the Freeze-1.1 applicator is closed-world, so integrity
  is verified in a clean clone at the tag (reproduces `13f9e400…`).

Verdict: **SEALABLE_BUT_REGISTRATIONS_INCOMPLETE**. It is conditional on the custodian's
explicit acceptance of the declared discovery-layer support change.
