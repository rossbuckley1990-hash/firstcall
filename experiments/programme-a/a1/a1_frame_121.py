#!/usr/bin/env python3
"""FIRSTCALL Programme A, Population A1: snapshot retrieval and the sealed RDG frame G.

Freeze 1.2.1 operative copy of anchored Freeze-1.2 frame machinery.
Only to_alabel/key_host and their import are superseded; all other code unchanged. Everything here is structural:
  pinned snapshot tree -> raw entries (spec files) -> structural keys (provider directories)
  -> host of each key -> registrable domain under the pinned, vendored Public Suffix List
  -> registrable-domain groups (RDGs) -> one mechanically chosen primary key and primary
  entry per RDG -> sealed frame G (byte-sorted RDG ids).

No definition file is parsed, no server URL is used for grouping, no documentation is read,
no identity is adjudicated, no entropy is generated and nothing is ordered. The PSL is read
only from the vendored, hash-checked file; it is never fetched live.
"""
import argparse
from a1_host import canonical_host, HostError
import hashlib
import ipaddress
import json
import os
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

A1_ID = "FIRSTCALL-A1"
SOURCE_REPO = "https://github.com/APIs-guru/openapi-directory.git"
SNAPSHOT_COMMIT = "f04b8d0bcd39c52e1cf3ad7a5fe744709832ae49"
T0_UTC = "2026-09-17T00:00:00Z"
ROOT_DIR = "APIs"
SPEC_FILENAMES = ("openapi.json", "openapi.yaml", "swagger.json", "swagger.yaml")
PSL_SOURCE = "https://github.com/publicsuffix/list.git"
PSL_COMMIT = "3955e3ec29b94c3cca7bd4509c5f14a7c0959e26"
PSL_COMMIT_UTC = "2026-09-08T12:18:25Z"
PSL_SHA256 = "a26f7d7e334778ed69216cedb5451ef82031feba6615c12039783cdd94e1fcae"
PSL_LOCAL = Path(__file__).resolve().parent / "psl" / "public_suffix_list.dat"
OUTPUT_DIR = "experiments/programme-a/a1/snapshot"
LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")


class FrameHalt(Exception):
    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}")
        self.code = code


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout


def parse_utc(text):
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def bkey(s):
    return s.encode("utf-8")


# ------------------------------------------------------------------ pinned PSL

def load_pinned_psl(path=PSL_LOCAL, expected_sha256=PSL_SHA256):
    data = Path(path).read_bytes()
    if sha256(data) != expected_sha256:
        raise FrameHalt("PSL_MISMATCH", f"{sha256(data)} != {expected_sha256}")
    return data


def to_alabel(label):
    """PSL labels use the shared, pinned IDNA2008 conversion."""
    return canonical_host(label, psl_label=True)


class PublicSuffixList:
    """Full PSL (ICANN and PRIVATE sections). Rules and hosts compared as A-labels."""

    def __init__(self, text):
        self.rules, self.exceptions, self.wildcards = set(), set(), set()
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            rule = line.split()[0]
            exc, wild = rule.startswith("!"), rule.startswith("*.")
            body = rule[1:] if exc else rule[2:] if wild else rule
            try:
                body = ".".join(to_alabel(x) for x in body.split("."))
            except UnicodeError:
                raise FrameHalt("PSL_UNPARSEABLE_RULE", rule)
            (self.exceptions if exc else self.wildcards if wild else self.rules).add(body)

    def registrable_domain(self, host):
        """eTLD+1 by the PSL algorithm with the implicit '*' rule; None if host is itself a suffix."""
        labels = host.split(".")
        suffix_len = 1
        for i in range(len(labels)):
            cand = ".".join(labels[i:])
            if cand in self.exceptions:
                suffix_len = len(labels) - i - 1
                break
            parent = ".".join(labels[i + 1:])
            if cand in self.rules or (parent and parent in self.wildcards):
                suffix_len = len(labels) - i
                break
        if len(labels) <= suffix_len:
            return None
        return ".".join(labels[-(suffix_len + 1):])


# ------------------------------------------------------------------ structural keys and hosts

def normalise_key(name):
    """Structural key: NFC, lower-case, trailing dots removed. No other merge."""
    return unicodedata.normalize("NFC", name).lower().rstrip(".")


def key_host(key):
    """Frozen key grammar; only host canonicalisation superseded by Freeze 1.2.1."""
    if key.startswith('['):
        return None, 'IP_LITERAL'
    host = key.split(':', 1)[0].rstrip('.')
    try:
        return canonical_host(host), None
    except HostError as exc:
        return None, {'IP_LITERAL_HOST': 'IP_LITERAL', 'NO_HOST': 'EMPTY_HOST',
                      'NON_DNS_HOST': 'NON_DNS_HOST', 'INVALID_DNS_HOST': 'INVALID_DNS_LABEL'}[exc.reason]


def has_suffix(key):
    return ":" in key


# ------------------------------------------------------------------ extraction and RDG frame

def extract(repo, commit=SNAPSHOT_COMMIT):
    listing = git(repo, "ls-tree", "-r", "-z", "--full-tree", commit, "--", ROOT_DIR + "/").decode("utf-8")
    raw, top_files, providers = [], [], {}
    for entry in filter(None, listing.split("\0")):
        meta, path = entry.split("\t", 1)
        parts = path.split("/")
        if len(parts) == 2:
            top_files.append(path)
            continue
        provider = parts[1]
        providers.setdefault(provider, 0)
        if parts[-1] in SPEC_FILENAMES:
            providers[provider] += 1
            raw.append({"source_record_id": canonical([A1_ID, commit, None, path]).decode(), "path": path,
                        "provider_dir": provider, "blob": meta.split()[2]})
    raw.sort(key=lambda r: bkey(r["path"]))
    return raw, sorted(top_files, key=bkey), providers


def primary_key_of(rdg_id, members, hosts):
    """Frozen rule: the key that IS the bare registrable domain (host equals the RDG id and no ':'
    suffix); if several such keys (e.g. U-label and A-label spellings), the byte-smallest; if none,
    the byte-smallest key of the group. Singletons: the key itself."""
    if rdg_id.startswith("singleton:"):
        return members[0], "SINGLETON"
    bare = sorted((k for k in members if not has_suffix(k) and hosts[k] == rdg_id), key=bkey)
    if bare:
        return bare[0], "BARE_REGISTRABLE_DOMAIN"
    return sorted(members, key=bkey)[0], "BYTE_SMALLEST_KEY"


def build_frame(repo, psl_bytes, commit=SNAPSHOT_COMMIT, psl_sha256=PSL_SHA256):
    if sha256(psl_bytes) != psl_sha256:
        raise FrameHalt("PSL_MISMATCH")
    psl = PublicSuffixList(psl_bytes.decode("utf-8"))
    raw, top_files, providers = extract(repo, commit)
    exclusions = [{"entry": p, "rule": "XS1_NOT_A_PROVIDER_DIRECTORY"} for p in top_files]
    exclusions += [{"entry": f"{ROOT_DIR}/{d}", "rule": "XS2_NO_SPEC_FILE"}
                   for d in sorted(providers, key=bkey) if providers[d] == 0]
    entries_by_key = {}
    for r in raw:
        entries_by_key.setdefault(normalise_key(r["provider_dir"]), []).append(r["path"])
    hosts, basis = {}, {}
    groups = {}
    for k in sorted(entries_by_key, key=bkey):
        host, why = key_host(k)
        hosts[k] = host
        rd = psl.registrable_domain(host) if host else None
        if host and rd is None:
            why = "HOST_IS_PUBLIC_SUFFIX"
        gid = rd if rd else "singleton:" + k
        basis[gid] = "REGISTRABLE_DOMAIN" if rd else f"SINGLETON_{why}"
        groups.setdefault(gid, []).append(k)
    G = sorted(groups, key=bkey)
    out_groups = []
    for gid in G:
        members = sorted(groups[gid], key=bkey)
        pk, rule = primary_key_of(gid, members, hosts)
        entry = sorted(entries_by_key[pk], key=bkey)[0]
        out_groups.append({"rdg": gid, "basis": basis[gid], "keys": members, "hosts": {k: hosts[k] for k in members},
                           "primary_key": pk, "primary_key_rule": rule, "primary_entry": entry,
                           "raw_entries": sum(len(entries_by_key[k]) for k in members)})
    frame = {"schema": "firstcall.programmeA.a1_rdg_frame.v1", "population": A1_ID,
             "inputs": {"snapshot_commit": commit, "psl_commit": PSL_COMMIT, "psl_sha256": psl_sha256},
             "raw_entry_count": len(raw), "structural_exclusions": exclusions,
             "G": G, "G_size": len(G), "groups": out_groups,
             "raw_entries_sha256": sha256(canonical(raw))}
    validate_frame(frame, raw)
    frame["G_sha256"] = sha256(canonical(G))
    return frame, raw


def validate_frame(frame, raw):
    """RDG conservation and primary-entry integrity."""
    G = frame["G"]
    if len(set(G)) != len(G) or G != sorted(G, key=bkey) or [g["rdg"] for g in frame["groups"]] != G:
        raise FrameHalt("G_NOT_UNIQUE_SORTED")
    keys = [k for g in frame["groups"] for k in g["keys"]]
    if len(keys) != len(set(keys)):
        raise FrameHalt("KEY_IN_TWO_GROUPS")
    paths = {r["path"] for r in raw}
    key_of = {r["path"]: normalise_key(r["provider_dir"]) for r in raw}
    if sum(g["raw_entries"] for g in frame["groups"]) != len(raw) or frame["raw_entry_count"] != len(raw):
        raise FrameHalt("RAW_CONSERVATION")
    if set(key_of.values()) != set(keys):
        raise FrameHalt("KEY_CONSERVATION")
    for g in frame["groups"]:
        if g["primary_key"] not in g["keys"]:
            raise FrameHalt("PRIMARY_KEY_OUTSIDE_GROUP", g["rdg"])
        if g["primary_entry"] not in paths or key_of[g["primary_entry"]] != g["primary_key"]:
            raise FrameHalt("PRIMARY_ENTRY_INVALID", g["rdg"])
        own = sorted((p for p, k in key_of.items() if k == g["primary_key"]), key=bkey)
        if g["primary_entry"] != own[0]:
            raise FrameHalt("PRIMARY_ENTRY_NOT_RULE", g["rdg"])
    ids = [r["source_record_id"] for r in raw]
    if len(set(ids)) != len(ids):
        raise FrameHalt("DUPLICATE_SOURCE_RECORD_ID")
    return True


def verify_frame(frame, repo, psl_bytes, commit=SNAPSHOT_COMMIT):
    """A published frame is valid only if it names the pinned inputs and is reproduced exactly."""
    if frame.get("inputs") != {"snapshot_commit": commit, "psl_commit": PSL_COMMIT, "psl_sha256": PSL_SHA256}:
        raise FrameHalt("FRAME_INPUTS_MISMATCH")
    rebuilt, _ = build_frame(repo, psl_bytes, commit)
    if canonical(rebuilt) != canonical(frame):
        raise FrameHalt("FRAME_NOT_REPRODUCED")
    return True


# ------------------------------------------------------------------ snapshot checks and one-time retrieval

def verify_snapshot(repo, commit=SNAPSHOT_COMMIT, t0=T0_UTC):
    try:
        kind = git(repo, "cat-file", "-t", commit).decode().strip()
    except subprocess.CalledProcessError:
        raise FrameHalt("SNAPSHOT_MISSING", commit)
    if kind != "commit":
        raise FrameHalt("SNAPSHOT_NOT_COMMIT", kind)
    when = datetime.fromisoformat(git(repo, "show", "-s", "--format=%cI", commit).decode().strip())
    if when > parse_utc(t0):
        raise FrameHalt("SNAPSHOT_AFTER_T0", when.isoformat())
    return {"commit": commit, "tree": git(repo, "rev-parse", f"{commit}^{{tree}}").decode().strip(),
            "committer_date": when.isoformat()}


def retrieve(workdir, out_dir, source_repo=SOURCE_REPO, psl_path=PSL_LOCAL):
    """Exactly-once retrieval by the snapshot custodian after anchoring. PSL from the vendored file only."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=False)
    psl_bytes = load_pinned_psl(psl_path)
    src = Path(workdir) / "src"
    subprocess.run(["git", "init", "-q", str(src)], check=True)
    subprocess.run(["git", "-C", str(src), "fetch", "-q", "--no-tags", source_repo, SNAPSHOT_COMMIT], check=True)
    snap = verify_snapshot(src)
    frame, raw = build_frame(src, psl_bytes)
    subprocess.run(["git", "-C", str(src), "branch", "-f", "a1-snapshot", SNAPSHOT_COMMIT], check=True)
    bundle = Path(workdir) / "a1.bundle"
    subprocess.run(["git", "-C", str(src), "bundle", "create", "-q", str(bundle), "a1-snapshot"], check=True)
    record = {"snapshot": snap, "psl": {"commit": PSL_COMMIT, "sha256": PSL_SHA256},
              "custody_bundle_sha256": sha256(bundle.read_bytes()), "frame_sha256": sha256(canonical(frame)),
              "G_sha256": frame["G_sha256"], "G_size": frame["G_size"], "raw_entry_count": frame["raw_entry_count"],
              "retrieved_utc": datetime.now(timezone.utc).isoformat()}
    for name, data in (("frame.json", canonical(frame)), ("raw-entries.json", canonical(raw)),
                       ("retrieval.json", canonical(record))):
        fd = os.open(out / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
        os.write(fd, data)
        os.close(fd)
    return record


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--describe", action="store_true", help="print frozen constants; no network")
    ap.add_argument("--retrieve", metavar="WORKDIR", help="snapshot custodian only, after anchoring")
    args = ap.parse_args(argv)
    if args.retrieve:
        root = Path(__file__).resolve().parents[3]
        print(json.dumps(retrieve(args.retrieve, root / OUTPUT_DIR), indent=2))
        return 0
    load_pinned_psl()
    print(json.dumps({"population": A1_ID, "source": SOURCE_REPO, "snapshot_commit": SNAPSHOT_COMMIT,
                      "t0_utc": T0_UTC, "psl": {"commit": PSL_COMMIT, "sha256": PSL_SHA256, "verified": True},
                      "unit": "registrable-domain group (RDG)"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
