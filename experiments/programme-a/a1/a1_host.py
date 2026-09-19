#!/usr/bin/env python3
"""Freeze 1.2.1 shared DNS host canonicalisation. Strict IDNA2008, never UTS46.
No network, DNS lookup, entropy, confusable folding or vendor identity inference.
"""
from a1_integrity_121 import VERIFIED
import hashlib
import ipaddress
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENDOR_IDNA = HERE / "vendor" / "idna-3.11"
IDNA_SHA256 = {
    "LICENSE.md": "b7a336abf3b04e180ec065cdd16e705d079e1cc7a14f910aa6e9187f36b9cd87",
    "idna/__init__.py": "30fa8d0cb65b5ea19a35d5f1005862a853ca1105e3bb68cd42109ecbafb97893",
    "idna/codec.py": "33648658dedcb3fe81df6426293c9337ac50199798420436c225f7fc347a9681",
    "idna/compat.py": "4732f2e90402765f7bf3868585bd845fd10a1822638343f73e294675e5d7731f",
    "idna/core.py": "3f6ebf5d5c9cb8c4d9d51da634ad594445733399af4f375a6c15dfc99554d4b7",
    "idna/idnadata.py": "486f2385a184e778a20fa078f69b76a704effd4bc295c89613e379e28476a785",
    "idna/intranges.py": "6a652d91d8587101bc66bf82a0c33f91545a731922bc2d568313756fadca29d5",
    "idna/package_data.py": "fc251abcec686e76f2346d852f21e837c4073f740cf56d6d2aec3b7aaf50c019",
    "idna/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "idna/uts46data.py": "1fd277e55903d05f4bf6628eaa378d19dd80f956ba1653e8cfa273e0aee1fa9b",
}


class DependencyIntegrityError(RuntimeError):
    pass


def _verify_idna():
    for rel, digest in IDNA_SHA256.items():
        p = VENDOR_IDNA / rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            raise DependencyIntegrityError(f"vendored idna differs: {rel}")
    present = {str(p.relative_to(VENDOR_IDNA)) for p in VENDOR_IDNA.rglob("*") if p.is_file()}
    if present != set(IDNA_SHA256):
        raise DependencyIntegrityError("unexpected vendored idna files")


_verify_idna()
sys.dont_write_bytecode = True
sys.path.insert(0, str(VENDOR_IDNA))
sys.path.insert(0, str(HERE))
import idna  # noqa: E402  (vendored 3.11)

if Path(idna.__file__).resolve().parent != (VENDOR_IDNA / "idna").resolve() or idna.__version__ != "3.11" \
        or idna.idnadata.__version__ != unicodedata.unidata_version:
    raise DependencyIntegrityError("idna must be the vendored 3.11 with tables matching the runtime Unicode version")


LDH = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")

class HostError(ValueError):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason

def canonical_host(host, *, psl_label=False):
    """Return one ASCII DNS host; PSL label mode uses the identical IDNA conversion.
    Hosts need >=2 labels, are not IPs, and have a nonnumeric final label.
    Trailing ASCII dots are removed; whitespace and URI syntax are never repaired.
    """
    if not isinstance(host, str) or not host:
        raise HostError("NO_HOST")
    host = unicodedata.normalize("NFC", host).lower().rstrip(".")
    try:
        ipaddress.ip_address(host.strip('[]'))
    except ValueError:
        pass
    else:
        if not psl_label:
            raise HostError("IP_LITERAL_HOST")
    if not psl_label and len(host.split('.')) < 2:
        raise HostError("NON_DNS_HOST")
    try:
        result = idna.encode(host, strict=True, uts46=False).decode('ascii')
    except (idna.IDNAError, UnicodeError, ValueError):
        raise HostError("INVALID_DNS_HOST") from None
    labels = result.split('.')
    if len(result) > 253 or any(not LDH.fullmatch(x) for x in labels) or (not psl_label and labels[-1].isdigit()):
        raise HostError("INVALID_DNS_HOST")
    if psl_label and len(labels) != 1:
        raise HostError("INVALID_DNS_HOST")
    return result
