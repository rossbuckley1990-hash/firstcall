# Programme A — Freeze 1.2 registration and source-mechanism repair (prospective, revision 2)

Status: **PROPOSED. Binding only once committed, tagged `programme-a-freeze-1.2-registration`
and pushed to `origin` before 2026-09-22T09:00:00Z.**
Design date: 2026-09-18. Parents: Freeze 1 `13ff44c37a96882553ffb9103a5596787555e0f3`
(`programme-a-freeze-1-protocol`) and Freeze 1.1 `4eaa6493924256dbeb888ff992a769a6b9c6d56d`
(`programme-a-freeze-1.1-protocol`, sealed 2026-09-18T18:00:20Z).

Programme A counters when this was written:

| Counter | Value |
| --- | --- |
| Source (discovery) requests | 0 |
| Source observations | 0 |
| Candidate observations | 0 |
| Selected vendors | 0 |
| Random draw | none |
| Entropy | none |
| Outcome observations | 0 |
| Real vendor runs | 0 |

## 1. Why Freeze 1.2 exists

Two defects were found while trying to carry out the frozen protocol. Both were found
before any discovery request or source observation.

1. **Missing registrations** (found 2026-09-18, about 20:00Z, during the Freeze-2
   attempt). Freeze 1.1 §8.2 says the Freeze-1.1 sealing certificate names the capture
   custodian and runner, and §4, §5, §8.3–8.5 require further "registered" adjudicators and
   tools. No certificate was issued and no registration mechanism exists. The Freeze-2
   attempt stopped before any source request.
2. **Discovery mechanism** (found 2026-09-18 during review of the uncommitted revision 1 of
   this amendment). Freeze 1.1 §3 and §8.2 make the discovery input the public Bing
   web-search result HTML. External review found material uncertainty over whether
   automated retrieval, parsing and archival of Bing result HTML is permitted under
   Microsoft's public terms. Technical accessibility is not permission. The Bing mechanism
   is therefore withdrawn. **No Bing request was ever made**: the revision-1 runner was
   never invoked against any network.

The certificate is not treated as having existed, and nothing is backdated. **All unrelated
provisions of Freeze 1 and Freeze 1.1 remain unchanged and operative.**

## 2. Clauses repaired (crosswalk)

| Id | Freeze-1.1 location | Defect | Replacement |
| --- | --- | --- | --- |
| F12-R1 | §8.2 para 2; `rules.source_universe.capture.authority` | Sealing certificate never issued | The Freeze-1.2 registration certificate (this package, remotely anchored) names the custodian and runner (§3–§4). |
| F12-R2 | §4 para 4, §5, §8.3, §8.4, §8.5 | "Registered" roles have no mechanism | Slot records, schema-valid and validated fail-closed, committed under a remotely anchored `programme-a-registration-<slot>-<n>` tag before each slot's gate. Append-only; frozen after first use (§6). |
| F12-R3 | §8.2 network-egress identity | A residential address cannot be known in advance | Method frozen; the IPv4 echo is bound into the hashed preflight record before the first request. |
| F12-R4 | §8.2 start time / five-second lateness | Clock undefined | SNTP-corrected UTC; lateness judged under both pre- and post-capture offsets. |
| F12-R5 | §3 para 1, §8.2 (Bing web-search HTML, logged-out GB/English interface, organic positions) | Unclear legal basis for automated retrieval and archival | **GitHub REST API repository search** (unauthenticated) using the same four query strings (§5). |
| F12-R6 | §3 para 1 "one registered session starting on the first UTC day after sealing"; §8.2 09:00Z start | Tied to the withdrawn Bing session | Capture at **2026-09-23T09:00:00Z**, anchor deadline 2026-09-22T09:00:00Z. **T0 = 2026-09-17T00:00:00Z is unchanged.** |
| F12-R7 | §3 source eligibility | No criterion on reuse or access rights | Two new source criteria: S-LIC (explicit reuse licence) and S-ACCESS (a permitted automated retrieval path), under the existing Freeze-1.1 precedence (§5). |
| F12-R8 | §3 / §8.2 "archive raw responses ... publish" | Raw API responses contain user objects (personal information) | Raw bytes are kept in custody, unpublished, with their hash published. A deterministic, non-personal projection is published (§5). |
| F12-R9 | §8.4 projector (a Freeze-1.2 revision-1 artefact) | Policy-flag false positive | Structural value-type rule, fenced code ignored, and example paths block (§8). |

Everything else stays unchanged, including:
- the four query strings;
- the 0/60/120/180 s offsets;
- the 5 s lateness limit;
- the single attempt with no alternate session;
- all other source criteria;
- the ≥2 independently controlled maintainers requirement;
- the "no substitute catalog" rule;
- identity, strata, eligibility, budgets, allocation, entropy and analysis.

## 3. Capture custodian (registered)

Freeze 1.1 imposes independence only on the *entropy* custodian (§8.5). It calls capture
registration "administrative registration, not permission to choose catalogs" (§8.2).
**Ross Buckley may therefore serve as capture custodian, and is registered.** The
registration is binding when he commits, tags and pushes this package.

The custodian:
- launches the registered runner once;
- keeps the host awake and online;
- keeps the custody directory intact and unpublished;
- publishes the capture directory before any screening;
- ensures every resulting Programme A publication is open access, which is the condition
  of GitHub's research clause.

The custodian controls no query, parameter, timing, parsing or halt decision. They may not
issue or view the registered queries on any search surface before the manifest is
published, and may never hold an entropy role.

## 4. Capture runner (registered)

`registration/source_capture_runner.py` is registered, with its digest in
`source-capture-runner-manifest.json`. It keeps the generic properties of revision 1:
- a single authoritative attempt with an exclusive capture directory; reruns are refused
  and logged;
- a self-timed start;
- the clock and egress checks;
- the registration-bytes check against the remote tag;
- no hidden retries;
- capture before parse;
- canonical JSON, SHA256 hashes and a complete audit manifest.

All Bing-specific behaviour is removed.

**Request:** `GET https://api.github.com/search/repositories?q=<query> in:name,description,topics,readme&per_page=20&page=1`.
- No sort parameter, so the API default best match applies.
- No credentials.
- Fixed honest User-Agent, `Accept: application/vnd.github+json`,
  `X-GitHub-Api-Version: 2026-03-10`.
- IPv4 only; 30 s deadline.
- No redirects, retries, pagination or cache.

**Before any search request, the preflight:**
1. fetches the GitHub Acceptable Use Policies page, archives it in custody, and requires
   the registered research and API sentences (otherwise `TERMS_CHANGED` or
   `TERMS_UNVERIFIED`);
2. checks `https://api.github.com/robots.txt` under RFC 9309 (otherwise `ROBOTS_DISALLOW`
   or `ROBOTS_UNVERIFIED`).

The two preflight fetches go to terms and policy documents, never to the discovery
endpoint.

**Timing:** interactive starting cannot meet the 5 s tolerance, so the pre-launched
self-timed runner remains the only compliant mechanism. The source guard arms the
discovery endpoint only per scheduled request, and offline tests prove it is never
contacted early.

## 5. Replacement source-universe rule

Full specification: `registration/source-mechanism.json`.

**Access basis.** GitHub Acceptable Use Policies §7, read on 2026-09-18, says:
- "regardless of whether the information was scraped, collected through our API, or
  obtained otherwise";
- "Researchers may use public, non-personal information from the Service for research
  purposes, only if any publications resulting from that research are open access";
- "Scraping does not refer to the collection of information through our API."

GitHub Terms of Service §H prohibits API abuse and spam or sale of personal information.
The search API allows 10 unauthenticated requests per minute; this protocol makes 4, 60 s
apart. `api.github.com/robots.txt` returned HTTP 404.

**Terms review only.** Choosing this index involved reading terms and API documentation
only. No search request was made, and no catalog, repository or vendor listing was opened.

**Rejected alternatives:**

| Alternative | Reason |
| --- | --- |
| Search-engine HTML | Terms uncertainty |
| Commercial search APIs | Need accounts and credentials |
| Zenodo search | `robots.txt` disallows `/api` and `/search` |
| Zenodo OAI-PMH | Permitted, but a full harvest with untested local semantics; recorded, not adopted |
| Wikidata | Single maintainer, discretionary class choice |
| Package registries | Enumerate packages, not platforms |
| Named catalogs chosen from memory | Reintroduces discretionary source choice |

**Procedure:**
- The four Freeze-1.1 query strings are used verbatim. Positions 1..min(20, `total_count`)
  of each response form the discovered set.
- Results are unioned by repository id, with every occurrence recorded. Forks and mirrors
  are resolved to their upstream at screening.
- The Freeze-1.1 checklist applies, plus two new criteria:
  - **S-LIC:** an explicit reuse licence or public-domain dedication at the T0 version.
    Absence is FALSE; non-standard, NC, ND or contradictory terms are UNRESOLVED.
  - **S-ACCESS:** the complete version ≤T0 is retrievable through a permitted automated
    path. A GitHub repository data file qualifies. An off-GitHub distribution needs an
    explicit grant, is FALSE if robots or terms prohibit access, and is UNRESOLVED
    otherwise.

**Evidence representation.**
- Raw responses contain user objects, so they go O_EXCL to a custody directory outside the
  repository and are never published.
- A deterministic projection is published: `total_count`, `incomplete_results` and
  per-item id, full_name, html_url, owner type, fork, archived, dates, default branch and
  licence SPDX id. Its SHA256 and the raw SHA256 are published with it.
- Anyone given the raw bytes can reproduce both hashes using the digested projection
  function. Repository ids and commit SHAs ≤T0 make the source universe itself publicly
  reconstructible.

**Failure behaviour** (all final for this cohort, with no substitute and no alternate
session):

| Event | Result |
| --- | --- |
| Terms changed or unreachable | Halt |
| `robots.txt` disallows, or is unverifiable | Halt |
| Network error, non-200 or redirect | Halt |
| 403/429 (rate limit) | Halt |
| Malformed response, or partial (`item count ≠ min(20, total_count)`) | Halt after custody write |
| `incomplete_results` true | Halt |
| Duplicate across queries | Recorded once with all occurrences |
| Repository deleted, renamed or rewritten before lock | SOURCE_UNRESOLVED, which blocks lock |

**Coverage and estimand.** The estimand text (Freeze 1.1 §8.6) is unchanged, and it was
already relative to the frame.

This is a **declared support change in the discovery layer**. Discoverable sources are now
public GitHub repositories matching the four queries, with explicit licences and permitted
retrieval. Qualifying catalogs hosted only elsewhere can no longer be discovered.
Vendor-level rules and the UK-customer context are unchanged.

Neither index was ever observed, so nothing was traded on outcome grounds. The overlap
between the two indexes is unknown. Reports must state the GitHub-hosted,
licensed-catalog support. The custodian must accept this change explicitly at anchoring;
anyone who judges it a material change to the target population should not anchor.

**Disclosed biases:**
- GitHub hosting;
- English query terms;
- undocumented best-match ranking with top-20 truncation (`total_count` is published);
- the licence requirement;
- catalog-maintainer editorial choices.

## 6. Registration records, adjudicators, translation, scheduler

The registration-record mechanism and the adjudicator independence standard are unchanged
from revision 1.
- Adjudicators must be two distinct natural persons.
- Freeze 1.1 contemplates human adjudication and authorizes no model instances. Two model
  processes, one person in two slots, or duplicated prompts are rejected.
- Neither adjudicator may hold an entropy role.
- No replacement is allowed once any packet has been opened.

**Both adjudicator slots are unfilled.** Registering them before capture is recommended.

**Translation tool:** unfilled; its requirements are frozen.

**Scheduler/fetcher:** unfilled, and now also **blocked on its access basis**.
- Freeze 1.1's identity and eligibility stages retrieve and retain vendor documentation
  pages automatically. That raises the same class of terms question that withdrew Bing.
- Freeze 1.2 requires RFC 9309 compliance: disallowed pages are evidence gaps and are never
  circumvented.
- A prospective rule on the terms basis for retaining vendor pages must be registered
  before gate G3. This is recorded, not resolved.

## 7. Schedule

| Event | Time (UTC) |
| --- | --- |
| Anchor deadline | 2026-09-22T09:00:00Z |
| Preflight | 2026-09-23T08:50:00Z |
| Preflight deadline | 2026-09-23T08:58:00Z |
| Queries | 2026-09-23T09:00:00Z, 09:01, 09:02, 09:03 |
| T0 (unchanged) | 2026-09-17T00:00:00Z |

The 2026-09-19 Bing schedule is invalid. Keeping it for appearance would be wrong, and it
would compress review into hours. The new date was chosen before any observation and is
independent of source content.

## 8. Prior-FIRSTCALL projector (revision 2)

The revision-1 trigger flagged any experiment-object key containing
`vendor|target|provider`. It blocked on the policy flag
`experiments/resend-001/policy.json` `independent_vendor_verification_required`.

Revision 2 uses purely repository-structural rules, with no reading of outcomes:
- a vendor-, target- or provider-named key blocks only if its JSON **value type** can carry
  an identity (string, number, array or object);
- boolean or null policy flags are recorded as incidental;
- fenced Markdown code is ignored as example material;
- a designation-shaped record under an example, sample, fixture, template or demo path is
  neither admitted nor ignored: it blocks.

Hostile tests cover:
- an incidental mention;
- a documentation example (fenced and example-path);
- a policy field;
- an actual target;
- a renamed experiment;
- a nested experiment, which blocks;
- a historical artefact;
- a receipt;
- a prose-only mention.

The dry run on the provenance cutoff now gives `DRAFT_REQUIRES_TWO_ADJUDICATOR_APPROVAL`,
with no unrecognized designations and no positive grammar designations. The four named
mandatory exclusions remain. Adjudicators must still confirm every in-scope path.
`experiments/multi-001/candidates.json` is flagged by path name as a plausible
target-list file; Freeze 1.1 forbids ignoring such a file merely because nothing in it
parses.

## 9. Non-operative artefacts

`experiments/programme-a/quarantine/NON_OPERATIVE_BING_CAPTURE_DRAFT/` preserves the
revision-1 files byte-for-byte and read-only, with hashes and provenance:
- `capture_runner.py` → `.txt`, SHA256 `a2374399…`;
- `capture-runner-manifest.json`;
- `capture-schedule.json`.

## 10. Registrations remaining unfilled

| Role | Gate |
| --- | --- |
| R06/R07 adjudicators | Source screening |
| R08 checklist | Source screening |
| R09 translation tool | First packet |
| R10/R11 scheduler/fetcher and parsers | G3; also blocked on the access basis |
| R14 registry approval | Candidate extraction |
| R15 entropy custodian, R16 entropy witness | Freeze 2B |
| R12, R17 | Future stages, by design |

Filled roles are R01–R05, which are all the capture-gate roles, and R13 (projector
software).

**Decision: SEALABLE_BUT_REGISTRATIONS_INCOMPLETE.** Capture registration is complete,
pending remote anchoring and the custodian's explicit acceptance of the declared
support change.
