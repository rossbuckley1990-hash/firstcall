from __future__ import annotations
import json
import urllib.error
import urllib.request

VERIFY_TOKEN = "FIRSTCALL_VERIFIER_ONLY"

def verify_event(base_url: str, event_id: str, expected_name: str) -> dict:
    url = base_url.rstrip("/") + "/_firstcall/verify/events/" + event_id

    request = urllib.request.Request(
        url,
        headers={"X-Firstcall-Verifier": VERIFY_TOKEN},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.load(response)
            status = response.status
    except urllib.error.HTTPError as error:
        return {
            "observed": False,
            "status": error.code,
            "effect_id": event_id,
            "reason": "vendor_readback_failed",
        }
    except Exception:
        return {
            "observed": None,
            "status": None,
            "effect_id": event_id,
            "reason": "verifier_transport_error",
        }

    observed = (
        status == 200
        and payload.get("id") == event_id
        and payload.get("name") == expected_name
    )

    return {
        "observed": observed,
        "status": status,
        "effect_id": event_id,
        "reason": None if observed else "effect_mismatch",
    }

def verify_exactly_one_event(base_url: str, event_id: str, expected_name: str) -> dict:
    from urllib.parse import quote

    effect = verify_event(
        base_url,
        event_id,
        expected_name,
    )

    if effect["observed"] is not True:
        return {
            **effect,
            "count": None,
            "cardinality_ok": False,
        }

    url = (
        base_url.rstrip("/")
        + "/_firstcall/verify-count?name="
        + quote(expected_name, safe="")
    )

    request = urllib.request.Request(
        url,
        headers={"X-Firstcall-Verifier": VERIFY_TOKEN},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.load(response)
            status = response.status
    except urllib.error.HTTPError as error:
        return {
            "observed": None,
            "status": error.code,
            "effect_id": event_id,
            "count": None,
            "cardinality_ok": False,
            "reason": "cardinality_verifier_http_error",
        }
    except Exception:
        return {
            "observed": None,
            "status": None,
            "effect_id": event_id,
            "count": None,
            "cardinality_ok": False,
            "reason": "cardinality_verifier_transport_error",
        }

    count = payload.get("count")
    ids = payload.get("event_ids", [])

    cardinality_ok = (
        status == 200
        and count == 1
        and ids == [event_id]
    )

    return {
        "observed": cardinality_ok,
        "status": status,
        "effect_id": event_id,
        "count": count,
        "cardinality_ok": cardinality_ok,
        "reason": None if cardinality_ok else "duplicate_or_ambiguous_effect",
    }

def discover_and_verify_exactly_one_event(
    base_url: str,
    expected_name: str,
) -> dict:
    from urllib.parse import quote
    import json
    import urllib.error
    import urllib.request

    url = (
        f"{base_url}/_firstcall/verify-count"
        f"?name={quote(expected_name, safe='')}"
    )

    request = urllib.request.Request(
        url,
        headers={"X-Firstcall-Verifier": VERIFY_TOKEN},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.load(response)
            status = response.status
    except urllib.error.HTTPError as error:
        return {
            "observed": None,
            "status": error.code,
            "effect_id": None,
            "count": None,
            "cardinality_ok": False,
            "reason": "discovery_verifier_http_error",
        }
    except Exception:
        return {
            "observed": None,
            "status": None,
            "effect_id": None,
            "count": None,
            "cardinality_ok": False,
            "reason": "discovery_verifier_transport_error",
        }

    count = payload.get("count")
    ids = payload.get("event_ids", [])

    if status != 200:
        return {
            "observed": None,
            "status": status,
            "effect_id": None,
            "count": count,
            "cardinality_ok": False,
            "reason": "discovery_verifier_bad_status",
        }

    if count != 1 or len(ids) != 1:
        return {
            "observed": False,
            "status": status,
            "effect_id": None,
            "count": count,
            "cardinality_ok": False,
            "reason": "duplicate_or_ambiguous_effect"
            if count and count > 1
            else "no_matching_effect",
        }

    event_id = ids[0]

    result = verify_exactly_one_event(
        base_url,
        event_id,
        expected_name,
    )

    result["discovered_independently"] = True
    return result
