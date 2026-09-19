#!/usr/bin/env python3
"""FIRSTCALL Programme A, Population A1 — operative E2 starting links (Freeze 1.2.1, defect D8).

Supersedes ONLY the URL normaliser of the anchored a1_evidence.py (_norm_url). Field selection
(candidate_links) and server-variable substitution (_substitute) are imported from the anchored
module unchanged. The normaliser applies Freeze-1.1 §2 URI normalisation exactly, and keeps a lead
only if its host is a syntactically valid DNS hostname:

  1  non-string / empty after trimming ASCII whitespace          -> EMPTY_OR_NOT_STRING
  2  NFC (Freeze 1.1: Unicode strings use NFC)
  3  balanced {template} left after default substitution        -> UNRESOLVED_TEMPLATE
  4  urlsplit failure                                            -> MALFORMED
  5  scheme not http/https (relative, scheme-relative, other)    -> RELATIVE_OR_NON_HTTP
  6  host: userinfo discarded, trailing dots removed; none       -> NO_HOST
  7  IPv4/IPv6 literal                                           -> IP_LITERAL_HOST
  8  fewer than two labels (e.g. localhost)                      -> NON_DNS_HOST
  9  invalid port                                                -> MALFORMED_PORT
 10  lower-case; IDNA2008 (vendored idna 3.11, Unicode 16.0.0, uts46=False, strict label split);
     LDH A-labels of 1-63 octets; total <= 253; final label not all-numeric (RFC 1123 §2.1)
                                                                  -> INVALID_DNS_HOST
 11  any internal ASCII whitespace or control character; or, after non-ASCII path/query characters are
     UTF-8 percent-encoded (RFC 3987 §3.1), any character outside RFC 3986 path/query syntax or a
     malformed percent-escape                                   -> MALFORMED_URI
 12  percent-escapes: upper-case hex; decode only unreserved characters (Freeze 1.1)
 13  path: RFC 3986 §5.2.4 dot-segment removal after step 12; empty path -> '/'; remove the entire terminal slash run
     except for the root path; path case preserved (Freeze 1.1)
 14  query: pairs split on '&' (empty pairs dropped), key/value split at the first '='; drop utm_*, gclid,
     fbclid; sort by (key, value, has '=') in UTF-8 byte order, duplicates preserved (Freeze 1.1)
 15  fragment removed; scheme lower-case; default port (80/443) removed, other ports kept
Deterministic, offline, no randomness. Output lists are byte-sorted and de-duplicated.
"""
import hashlib
import ipaddress
import json
import re
import sys
import unicodedata
import urllib.parse
from pathlib import Path

from a1_host import canonical_host, HostError, LDH
import a1_evidence

RULE_VERSION = "1.2.1"
TEMPLATE = re.compile(r"\{([^{}]+)\}")
TRACKING = re.compile(r"^(utm_.*|gclid|fbclid)$")
DEFAULT_PORTS = {"http": 80, "https": 443}
LDH = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")
UNRESERVED = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
SUB_DELIMS = frozenset("!$&'()*+,;=")
PATH_OK = UNRESERVED | SUB_DELIMS | frozenset(":@/%")
QUERY_OK = PATH_OK | frozenset("?")
HEX = frozenset("0123456789abcdefABCDEF")
ASCII_WS = " \t\n\r\f\v"


class _Drop(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _iri_to_uri(component):
    """RFC 3987 §3.1: percent-encode the UTF-8 octets of non-ASCII characters."""
    return "".join(c if ord(c) < 128 else "".join(f"%{b:02X}" for b in c.encode("utf-8")) for c in component)


def _check_chars(component, allowed):
    i, n = 0, len(component)
    while i < n:
        c = component[i]
        if c == "%":
            h = component[i + 1:i + 3]
            if len(h) != 2 or not set(h) <= HEX:
                raise _Drop("MALFORMED_URI")
            i += 3
            continue
        if c not in allowed:
            raise _Drop("MALFORMED_URI")
        i += 1


def _percent_normalise(component):
    """Freeze 1.1: upper-case percent-escape hex; decode only unreserved characters."""
    out, i = [], 0
    while i < len(component):
        if component[i] == "%":
            h = component[i + 1:i + 3]
            ch = chr(int(h, 16))
            out.append(ch if ch in UNRESERVED else "%" + h.upper())
            i += 3
        else:
            out.append(component[i])
            i += 1
    return "".join(out)


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


def dns_host(host):
    try:
        return canonical_host(host)
    except HostError as exc:
        raise _Drop(exc.reason) from None


def normalise_lead(url):
    """(normalised URL, None) or (None, reason). Freeze 1.2.1 authoritative E2 rule."""
    try:
        if not isinstance(url, str) or not url.strip(ASCII_WS):
            raise _Drop("EMPTY_OR_NOT_STRING")
        url = unicodedata.normalize("NFC", url.strip(ASCII_WS))
        if any(ord(c) < 0x21 or ord(c) == 0x7F for c in url):      # internal whitespace/control: urlsplit would silently drop some
            raise _Drop("MALFORMED_URI")
        if TEMPLATE.search(url):
            raise _Drop("UNRESOLVED_TEMPLATE")
        try:
            p = urllib.parse.urlsplit(url)
        except ValueError:
            raise _Drop("MALFORMED")
        scheme = p.scheme.lower()
        if scheme not in ("http", "https"):
            raise _Drop("RELATIVE_OR_NON_HTTP")
        host = (p.hostname or "").rstrip(".")
        if not host:
            raise _Drop("NO_HOST")
        try:
            ipaddress.ip_address(host)
            raise _Drop("IP_LITERAL_HOST")
        except ValueError:
            pass
        if len(host.split(".")) < 2:
            raise _Drop("NON_DNS_HOST")
        try:
            port = p.port
        except ValueError:
            raise _Drop("MALFORMED_PORT")
        if p.netloc.count('@') > 1 or ('@' in p.netloc and not p.netloc.split('@', 1)[0]):
            raise _Drop("MALFORMED_URI")
        if p.netloc.endswith(':'):
            raise _Drop("MALFORMED_PORT")
        if '@' in p.netloc:
            _check_chars(_iri_to_uri(p.netloc.rsplit('@', 1)[0]), UNRESERVED | SUB_DELIMS | frozenset(":%"))
        _check_chars(_iri_to_uri(p.fragment), QUERY_OK)
        host = dns_host(host)
        path, query = _iri_to_uri(p.path), _iri_to_uri(p.query)
        _check_chars(path, PATH_OK)
        _check_chars(query, QUERY_OK)
        path = remove_dot_segments(_percent_normalise(path)) or "/"
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/") or "/"
        pairs = []
        for seg in _percent_normalise(query).split("&"):
            if not seg:
                continue
            key, eq, value = seg.partition("=")
            if TRACKING.match(key):
                continue
            pairs.append((key, eq, value))
        pairs.sort(key=lambda t: (t[0].encode("utf-8"), t[2].encode("utf-8"), t[1] == "="))
        q = "&".join(k + e + v for k, e, v in pairs)
        netloc = host if port in (None, DEFAULT_PORTS[scheme]) else f"{host}:{port}"
        return urllib.parse.urlunsplit((scheme, netloc, path, q, "")), None
    except (UnicodeError, ValueError):
        return None, "MALFORMED_URI"
    except _Drop as d:
        return None, d.reason


def e2_leads(doc):
    """Same fields and substitution as anchored a1_evidence.e2_leads; Freeze-1.2.1 normaliser."""
    leads, dropped = set(), []
    for field, value in a1_evidence.candidate_links(doc):
        url, why = normalise_lead(value)
        if url:
            leads.add(url)
        else:
            dropped.append({"field": field, "value": value if isinstance(value, str) else repr(value), "reason": why})
    dropped.sort(key=lambda d: json.dumps(d, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return {"leads": sorted(leads, key=lambda u: u.encode("utf-8")), "dropped": dropped, "rule_version": RULE_VERSION}
