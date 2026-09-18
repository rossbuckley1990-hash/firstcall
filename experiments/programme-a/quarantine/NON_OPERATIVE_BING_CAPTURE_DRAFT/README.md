# NON-OPERATIVE — withdrawn Bing capture draft (Freeze 1.2, revision 1)

These files are preserved byte-for-byte as historical draft evidence. They are **not**
Programme A apparatus. Do not run, import or restore them.

- `capture_runner.py.txt` — the revision-1 Freeze-1.2 runner that would have captured Bing
  search-result HTML. It was renamed to `.txt` and made read-only.
- `capture-runner-manifest.json`, `capture-schedule.json` — its registration and its
  2026-09-19T09:00:00Z schedule.

Withdrawn on 2026-09-18, before anchoring. External review found material uncertainty over
whether automated retrieval, parsing and archival of Bing result HTML is permitted under
Microsoft's public terms. **No Bing request was ever made**: the runner was never invoked
in `--authoritative` or `--preflight-check` mode. Its offline tests used synthetic HTML
under a socket ban. The package was never committed, tagged or pushed. See
`provenance.json` and `docs/programme-a-freeze-1.2-registration-amendment.md` §2.
