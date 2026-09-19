#!/usr/bin/env python3
"""FIRSTCALL Programme A, Population A1 — registered spec parser (role R17).

Turns the bytes of ONE definition file (an RDG's primary entry) into a canonical structural
record. It is offline and deterministic:

  bytes --(strict UTF-8; stdlib json | vendored PyYAML 6.0.3 SafeLoader, pure Python)--> document
        --(Freeze-1.2.1 a1_e2_leads.e2_leads, digest-verified)--> E2 leads
  path  --(Freeze-1.2.1 a1_frame_121.normalise_key / key_host / pinned PSL, digest-verified)--> key, host, RDG

The frozen field-selection and sampling code is preserved; the additive Freeze-1.2.1
host/E2 implementations are operative. Parsing is fail-closed. Same input bytes + same
pinned PSL + same registered parser => byte-identical output.

It never touches the network, never reads A1 membership by itself and is used only after G4 on
released primary entries. Offline tests feed it synthetic documents.
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys
import urllib.parse
from pathlib import Path

sys.dont_write_bytecode = True

PARSER_ID = "firstcall-a1-spec-parser"
PARSER_VERSION = "1.2.1"
HERE = Path(__file__).resolve().parent
A1_DIR = HERE.parent
ROOT = HERE.parents[3]
AMENDMENT_JSON = ROOT / "experiments/programme-a/amendments/freeze-1.2-a1.json"
VENDOR = HERE / "vendor" / "pyyaml-6.0.3"
PYYAML_VERSION = "6.0.3"
PYYAML_SDIST_SHA256 = "d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f"
VENDOR_SHA256 = {
    "LICENSE": "8d3928f9dc4490fd635707cb88eb26bd764102a7282954307d3e5167a577e8a4",
    "yaml/__init__.py": "b19dfcc333d6a75dfd73073901164507252f271b41d3b5f7d85510033a0547a7",
    "yaml/composer.py": "fcaa37d16afa783594794a5ab94193dcb720f503c19ce3d59539c8311189f453",
    "yaml/constructor.py": "90d8247da78b524c10618fd0e857f54f3d97570fe91b5c5513d024ef3faf88b0",
    "yaml/cyaml.py": "e99ac01bd7c062f7557b614aff0d21997a06ed962ca185306a91bc0a20bbd87d",
    "yaml/dumper.py": "3cb72d66563064ba7b5e679477046ebf89d8399d940670c8532f3e94a7cb17ea",
    "yaml/emitter.py": "8e086d694ede170837d5b1b407b45979aff6f40762f422a65eafd08e04290a44",
    "yaml/error.py": "021f73fada072546c4f63f8cf18a7181244ce4280b09cc15cc980b2d1176171a",
    "yaml/events.py": "e74fd392c810884e2ea7e94aa3f57e9c1cbeb402319083d0c58e6a0e1282787c",
    "yaml/loader.py": "5156becc8aa6905482218abf3e04869b835226db4763645fff3438fdbd5f1cdd",
    "yaml/nodes.py": "80f28d8fca4a09d87677882bde021820d9cf39a3b11a12405226211919cf13ce",
    "yaml/parser.py": "8a55a9e6fbe0a07146cef3990c8b45a068c3e83e369e1959ad9ca30306b4a09a",
    "yaml/reader.py": "d1d9b38ab3a20c6e17a38d519ee412ecaf6b918df18c78956ac7c330d4ea08dc",
    "yaml/representer.py": "22e58ff9c016f6c1ca1274b4802a926bcf78935060e1c813c5a0f021c6d143e6",
    "yaml/resolver.py": "f4bf9561f9b89961f1503d558385fbae30d12bfed565de9bf76c33abb63620a6",
    "yaml/scanner.py": "60433788b652690c17710460da5d91e0c753d3318fd85f5e1e42862a71f25906",
    "yaml/serializer.py": "0a1b85826854d35863e31808f0668abfabdf33606e8f06bd8bb7761401e3edc0",
    "yaml/tokens.py": "953408cd2570f0c83dc2fe39f7e4e388e41eeb05738aa69196a5f6ffcf6ba79e",
}
FROZEN_DEPENDENCIES = ("experiments/programme-a/a1/a1_evidence.py", "experiments/programme-a/a1/a1_frame.py")
MAX_INPUT_BYTES = 64 * 1024 * 1024
MAX_ALIASES = 10000
MAX_DEPTH = 1000
SPEC_SUFFIXES = {".json": "JSON", ".yaml": "YAML"}


class ParserIntegrityError(RuntimeError):
    """Registered artefacts differ from their registration: nothing may be parsed."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


# ------------------------------------------------------------------ integrity and imports

def verify_integrity(vendor_digests=VENDOR_SHA256, vendor_dir=VENDOR):
    for rel, digest in vendor_digests.items():
        p = vendor_dir / rel
        if not p.is_file() or sha256(p.read_bytes()) != digest:
            raise ParserIntegrityError(f"vendored PyYAML file differs: {rel}")
    present = {str(p.relative_to(vendor_dir)) for p in vendor_dir.rglob("*") if p.is_file()
               and "__pycache__" not in p.parts}
    if present != set(vendor_digests):
        raise ParserIntegrityError(f"unexpected vendored files: {sorted(present ^ set(vendor_digests))}")
    anchored = json.loads(AMENDMENT_JSON.read_bytes())["registered_file_sha256"]
    for rel in FROZEN_DEPENDENCIES:
        if sha256((ROOT / rel).read_bytes()) != anchored[rel]:
            raise ParserIntegrityError(f"anchored dependency differs from freeze-1.2-a1.json: {rel}")
    sys.path.insert(0, str(A1_DIR))
    from a1_integrity_121 import verify_package
    verify_package()
    return True


verify_integrity()
sys.path.insert(0, str(VENDOR))
sys.path.insert(0, str(A1_DIR))
import yaml  # noqa: E402  (vendored, pure Python)
import a1_evidence  # noqa: E402  (anchored)
import a1_frame_121 as a1_frame  # noqa: E402
import a1_e2_leads

if Path(yaml.__file__).resolve().parent != (VENDOR / "yaml").resolve() or yaml.__version__ != PYYAML_VERSION:
    raise ParserIntegrityError("imported yaml is not the vendored PyYAML 6.0.3")
if yaml.__with_libyaml__:
    raise ParserIntegrityError("libyaml C extension must not be used")


class StrictSafeLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate explicit mapping keys (ambiguous documents fail closed).
    YAML merge keys ('<<') keep their standard semantics; the type is part of the identity and Python-equal keys such as 1 and true are rejected before either can overwrite the other."""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self.construct_object(key_node, deep=deep)
            try:
                marker = key
                hash(marker)
            except TypeError:
                raise yaml.constructor.ConstructorError(None, None, "UNHASHABLE_KEY", key_node.start_mark)
            if marker in seen:
                raise yaml.constructor.ConstructorError(None, None, "DUPLICATE_KEY", key_node.start_mark)
            seen.add(marker)
        return super().construct_mapping(node, deep=deep)


class ParseFailure(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _no_dupes(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ParseFailure("DUPLICATE_KEY")
        out[k] = v
    return out


def _no_constants(name):
    raise ParseFailure("NON_FINITE_NUMBER")


def parse_document(data, filename):
    """Strict, fail-closed parse. Returns the document (a dict) or raises ParseFailure(reason)."""
    fmt = SPEC_SUFFIXES.get(Path(filename).suffix.lower())
    if fmt is None:
        raise ParseFailure("UNSUPPORTED_FILE_TYPE")
    if len(data) > MAX_INPUT_BYTES:
        raise ParseFailure("INPUT_TOO_LARGE")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise ParseFailure("INVALID_UTF8")
    try:
        if fmt == "JSON":
            doc = json.loads(text, object_pairs_hook=_no_dupes, parse_constant=_no_constants)
        else:
            aliases = documents = 0
            for event in yaml.parse(text, Loader=StrictSafeLoader):
                if isinstance(event, yaml.AliasEvent):
                    aliases += 1
                    if aliases > MAX_ALIASES:
                        raise ParseFailure("ALIAS_LIMIT")
                elif isinstance(event, yaml.DocumentStartEvent):
                    documents += 1
            if documents != 1:
                raise ParseFailure("NOT_EXACTLY_ONE_DOCUMENT")
            doc = yaml.load(text, Loader=StrictSafeLoader)
    except ParseFailure:
        raise
    except RecursionError:
        raise ParseFailure("TOO_DEEP")
    except yaml.constructor.ConstructorError as exc:
        raise ParseFailure("DUPLICATE_KEY" if "DUPLICATE_KEY" in str(exc) else "YAML_CONSTRUCTOR_ERROR")
    except yaml.YAMLError:
        raise ParseFailure("YAML_INVALID")
    except json.JSONDecodeError:
        raise ParseFailure("JSON_INVALID")
    except (ValueError, TypeError):
        raise ParseFailure("DOCUMENT_INVALID")
    if not isinstance(doc, dict):
        raise ParseFailure("ROOT_NOT_MAPPING")
    if depth_exceeds(doc, MAX_DEPTH):
        raise ParseFailure("TOO_DEEP")
    return doc


def depth_exceeds(doc, limit):
    """Memoised DAG height; cycles and nonfinite numbers fail closed."""
    heights, active, stack = {}, set(), [(doc, False)]
    while stack:
        node, exiting = stack.pop()
        if isinstance(node, float) and not math.isfinite(node):
            raise ParseFailure("NON_FINITE_NUMBER")
        if not isinstance(node, (dict, list)):
            continue
        ident = id(node)
        if ident in heights:
            continue
        if isinstance(node, dict) and any(isinstance(k, float) and not math.isfinite(k) for k in node):
            raise ParseFailure("NON_FINITE_NUMBER")
        values = list(node.values()) if isinstance(node, dict) else node
        if exiting:
            active.remove(ident)
            heights[ident] = 1 + max((heights.get(id(v), 1) for v in values), default=0)
            if heights[ident] > limit:
                return True
        else:
            if ident in active:
                raise ParseFailure("DOCUMENT_INVALID")
            active.add(ident)
            stack.append((node, True))
            stack.extend((v, False) for v in values)
    return heights.get(id(doc), 1) > limit


def family(doc):
    o = doc.get("openapi")
    s = doc.get("swagger")
    oas3 = isinstance(o, str) and o.startswith("3.")
    oas2 = s is not None and str(s) in ("2.0", "2")
    if oas3 and oas2:
        return "AMBIGUOUS_OPENAPI_AND_SWAGGER"
    return "OAS3" if oas3 else "OAS2" if oas2 else "UNRECOGNISED_VERSION"


def ignored_nonroot_servers(doc):
    """OAS3 path- and operation-level servers are NOT E2 fields (root servers only); count them."""
    n = 0
    paths = doc.get("paths")
    if isinstance(paths, dict):
        for item in paths.values():
            if isinstance(item, dict):
                if isinstance(item.get("servers"), list):
                    n += len(item["servers"])
                for op in item.values():
                    if isinstance(op, dict) and isinstance(op.get("servers"), list):
                        n += len(op["servers"])
    return n


# ------------------------------------------------------------------ D8 conformance annotation

UNRESERVED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")


def remove_dot_segments(path):
    """RFC 3986 §5.2.4."""
    out, i = [], path
    while i:
        if i.startswith("../"):
            i = i[3:]
        elif i.startswith("./"):
            i = i[2:]
        elif i.startswith("/./"):
            i = "/" + i[3:]
        elif i == "/.":
            i = "/"
        elif i.startswith("/../"):
            i = "/" + i[4:]
            if out:
                out.pop()
        elif i == "/..":
            i = "/"
            if out:
                out.pop()
        elif i in (".", ".."):
            i = ""
        else:
            j = i.find("/", 1)
            seg, i = (i, "") if j == -1 else (i[:j], i[j:])
            out.append(seg)
    return "".join(out)


def freeze11_percent(path):
    """Freeze-1.1 §2: upper-case percent-escape hex; decode only unreserved characters."""
    out, k = [], 0
    while k < len(path):
        c = path[k]
        if c == "%" and k + 2 < len(path) + 0 and all(x in "0123456789abcdefABCDEF" for x in path[k + 1:k + 3]) \
                and len(path[k + 1:k + 3]) == 2:
            ch = chr(int(path[k + 1:k + 3], 16))
            out.append(ch if ch in UNRESERVED else "%" + path[k + 1:k + 3].upper())
            k += 3
        else:
            out.append(c)
            k += 1
    return "".join(out)


def text_rule_flags(url):
    """Where the anchored code's lead departs from the anchored TEXT rule (defect D8).
    Diagnostic only: repaired leads come from a1_e2_leads; the historical
    function remains available only for regression demonstrations."""
    flags = []
    p = urllib.parse.urlsplit(url)
    host, why = a1_frame.key_host(p.hostname or "")
    if host is None:
        flags.append(f"TEXT_RULE_NON_DNS_HOST:{why}")
    if remove_dot_segments(p.path) != p.path:
        flags.append("TEXT_RULE_DOT_SEGMENTS_UNRESOLVED")
    if freeze11_percent(p.path) != p.path:
        flags.append("TEXT_RULE_PERCENT_ENCODING_UNNORMALISED")
    return flags


# ------------------------------------------------------------------ structural record

def structural_record(path, data, psl_bytes=None):
    psl_bytes = a1_frame.load_pinned_psl() if psl_bytes is None else psl_bytes
    if sha256(psl_bytes) != a1_frame.PSL_SHA256:
        raise ParserIntegrityError("PSL differs from the pinned PSL")
    parts = path.split("/")
    if len(parts) < 3 or parts[0] != a1_frame.ROOT_DIR or parts[-1] not in a1_frame.SPEC_FILENAMES:
        raise ParseFailure("NOT_AN_A1_RAW_ENTRY_PATH")
    key = a1_frame.normalise_key(parts[1])
    host, why = a1_frame.key_host(key)
    rd = a1_frame.PublicSuffixList(psl_bytes.decode("utf-8")).registrable_domain(host) if host else None
    if host and rd is None:
        why = "HOST_IS_PUBLIC_SUFFIX"
    record = {
        "schema": "firstcall.programmeA.a1_spec_record.v1",
        "parser": {"id": PARSER_ID, "version": PARSER_VERSION, "pyyaml": PYYAML_VERSION, "libyaml": False},
        "input": {"path": path, "sha256": sha256(data), "bytes": len(data)},
        "structure": {"key": key, "host": host, "host_reason": why,
                      "rdg": rd if rd else "singleton:" + key, "psl_sha256": a1_frame.PSL_SHA256},
        "e2_fields_scope": "ROOT_ONLY: info.x-origin, externalDocs, info.termsOfService, info.contact, root servers, Swagger-2.0 host",
    }
    try:
        doc = parse_document(data, path)
    except ParseFailure as exc:
        record.update(status="PARSE_FAILED", reason=exc.reason, family=None,
                      e2={"leads": [], "dropped": []}, d8_flags={}, ignored_nonroot_servers=None,
                      consequence="no E2 leads: predicates needing them are UNRESOLVED (evidence insufficient)")
        return canonical(record)
    e2 = a1_e2_leads.e2_leads(doc)
    e2["dropped"] = sorted(e2["dropped"], key=canonical)
    record.update(status="PARSED", reason=None, family=family(doc), e2=e2,
                  d8_flags={u: f for u in e2["leads"] if (f := text_rule_flags(u))},
                  ignored_nonroot_servers=ignored_nonroot_servers(doc), consequence=None)
    return canonical(record)


def read_entry(repo, commit, path):
    """Primary-entry bytes from a local git repository (the custody bundle clone). No network."""
    return subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"], check=True,
                          capture_output=True).stdout


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--describe", action="store_true")
    ap.add_argument("--repo")
    ap.add_argument("--commit", default=a1_frame.SNAPSHOT_COMMIT)
    ap.add_argument("--path")
    args = ap.parse_args(argv)
    if args.describe or not args.path:
        print(json.dumps({"id": PARSER_ID, "version": PARSER_VERSION, "pyyaml": PYYAML_VERSION,
                          "pyyaml_sdist_sha256": PYYAML_SDIST_SHA256, "integrity": verify_integrity()}, indent=2))
        return 0
    sys.stdout.buffer.write(structural_record(args.path, read_entry(args.repo, args.commit, args.path)) + b"\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
