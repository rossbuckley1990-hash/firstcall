#!/usr/bin/env python3
"""FIRSTCALL Programme A, Population A1: E2 starting links from the PRIMARY ENTRY only.

Operates on an already-parsed OpenAPI 3.x / Swagger 2.0 document (the parser itself is a
registered, pinned tool: role R17). Server URLs here are evidence leads only; they never
affect RDG grouping, the primary entry or inclusion. Deterministic: same document -> same
byte-sorted, de-duplicated lead list plus a record of every dropped candidate and why.
"""
import ipaddress
import re
import urllib.parse

TRACKING = re.compile(r"^(utm_.*|gclid|fbclid)$")
TEMPLATE = re.compile(r"\{([^{}]+)\}")
DEFAULT_PORTS = {"http": 80, "https": 443}


def _norm_url(url):
    """Returns (normalised absolute http(s) URL, None) or (None, reason)."""
    if not isinstance(url, str) or not url.strip():
        return None, "EMPTY_OR_NOT_STRING"
    url = url.strip()
    if TEMPLATE.search(url):
        return None, "UNRESOLVED_TEMPLATE"
    try:
        p = urllib.parse.urlsplit(url)
    except ValueError:
        return None, "MALFORMED"
    if p.scheme.lower() not in ("http", "https"):
        return None, "RELATIVE_OR_NON_HTTP"
    host = (p.hostname or "").rstrip(".")
    if not host:
        return None, "NO_HOST"
    try:
        ipaddress.ip_address(host)
        return None, "IP_LITERAL_HOST"
    except ValueError:
        pass
    if "." not in host:
        return None, "NON_DNS_HOST"
    try:
        port = p.port
    except ValueError:
        return None, "MALFORMED_PORT"
    try:
        host = host.encode("idna").decode("ascii").lower()
    except UnicodeError:
        return None, "INVALID_IDN"
    netloc = host if port in (None, DEFAULT_PORTS[p.scheme.lower()]) else f"{host}:{port}"
    query = urllib.parse.urlencode(sorted((k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True)
                                          if not TRACKING.match(k)))
    path = p.path
    if len(path) > 1:
        path = path.rstrip("/")
    return urllib.parse.urlunsplit((p.scheme.lower(), netloc, path or "/", query, "")), None


def _substitute(url, variables):
    """Fill {var} only from the definition's own server-variable defaults; otherwise leave the template."""
    if not isinstance(variables, dict):
        return url

    def rep(m):
        v = variables.get(m.group(1))
        return str(v["default"]) if isinstance(v, dict) and "default" in v else m.group(0)
    return TEMPLATE.sub(rep, url)


def candidate_links(doc):
    """(field, raw value) pairs from the frozen E2 fields only."""
    out = []
    if not isinstance(doc, dict):
        return out
    info = doc.get("info") if isinstance(doc.get("info"), dict) else {}
    origins = info.get("x-origin")
    for o in (origins if isinstance(origins, list) else [origins] if origins else []):
        if isinstance(o, dict):
            out.append(("info.x-origin.url", o.get("url")))
    ext = doc.get("externalDocs")
    if isinstance(ext, dict):
        out.append(("externalDocs.url", ext.get("url")))
    out.append(("info.termsOfService", info.get("termsOfService")))
    contact = info.get("contact")
    if isinstance(contact, dict):
        out.append(("info.contact.url", contact.get("url")))
    servers = doc.get("servers")
    for s in (servers if isinstance(servers, list) else []):
        if isinstance(s, dict):
            out.append(("servers.url", _substitute(s.get("url", ""), s.get("variables"))))
    if doc.get("swagger") and isinstance(doc.get("host"), str):          # Swagger 2.0
        schemes = doc.get("schemes") if isinstance(doc.get("schemes"), list) else ["https"]
        for sch in schemes:
            out.append(("swagger.host", f"{sch}://{doc['host']}{doc.get('basePath', '')}"))
    return [(f, v) for f, v in out if v is not None]


def e2_leads(doc):
    leads, dropped = set(), []
    for field, value in candidate_links(doc):
        url, why = _norm_url(value)
        if url:
            leads.add(url)
        else:
            dropped.append({"field": field, "value": value if isinstance(value, str) else repr(value), "reason": why})
    return {"leads": sorted(leads, key=lambda u: u.encode("utf-8")), "dropped": dropped}
