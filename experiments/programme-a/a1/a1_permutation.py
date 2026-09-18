#!/usr/bin/env python3
"""FIRSTCALL Programme A, Population A1: the single uniform permutation of the sealed RDG frame G.

The permutation is over registrable-domain groups (RDGs), the final sampling units; never over
keys, entries, or platforms identified later. Freeze-1.1 §6/§8.5 tape mechanics:
  tape = os.urandom(32*|G|) in ONE call by the registered entropy custodian, after G is
  sealed; SHA256(tape) is committed before interpretation; G in byte order; RDG j gets
  priority int(tape[32j:32j+32], big-endian); ascending priority = order; any tie aborts.
Blocks of BLOCK_SIZE consecutive RDGs are released one at a time. Presentation order inside
a block is a domain-separated hash order, so screeners never see positions.
Nothing in this module runs automatically, and offline tests never call os.urandom.
"""
import hashlib
import os

BLOCK_SIZE = 6
PRIORITY_BYTES = 32
PRESENTATION_DOMAIN = b"FIRSTCALL-A1-BLOCK-PRESENTATION"


class PermutationHalt(Exception):
    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}")
        self.code = code


def generate_tape(g_size, entropy=os.urandom):
    """Registered generator: exactly one call. Raises on any failure; no fallback source."""
    if g_size < 1:
        raise PermutationHalt("EMPTY_G")
    tape = entropy(PRIORITY_BYTES * g_size)
    if not isinstance(tape, (bytes, bytearray)) or len(tape) != PRIORITY_BYTES * g_size:
        raise PermutationHalt("SHORT_OR_INVALID_TAPE")
    return bytes(tape)


def tape_commitment(tape):
    return hashlib.sha256(tape).hexdigest()


def permutation(G, tape, committed_sha256):
    """Uniform permutation of the sealed RDG frame G from the committed tape."""
    if list(G) != sorted(G, key=str.encode) or len(set(G)) != len(G):
        raise PermutationHalt("G_NOT_SORTED_UNIQUE")
    if len(tape) != PRIORITY_BYTES * len(G):
        raise PermutationHalt("TAPE_LENGTH", f"{len(tape)} != {PRIORITY_BYTES * len(G)}")
    if tape_commitment(tape) != committed_sha256:
        raise PermutationHalt("TAPE_COMMITMENT_MISMATCH")
    prio = {g: int.from_bytes(tape[PRIORITY_BYTES * j:PRIORITY_BYTES * (j + 1)], "big") for j, g in enumerate(G)}
    if len(set(prio.values())) != len(prio):
        raise PermutationHalt("PRIORITY_TIE", "cohort aborts; no reroll")
    return sorted(G, key=lambda g: prio[g])


def blocks(order, size=BLOCK_SIZE):
    return [order[i:i + size] for i in range(0, len(order), size)]


def presentation_order(block, block_index, committed_sha256):
    """Order shown to adjudicators: independent of permutation position, reproducible, unlabelled."""
    def score(k):
        return hashlib.sha256(PRESENTATION_DOMAIN + b"\0" + committed_sha256.encode() + b"\0" +
                              str(block_index).encode() + b"\0" + k.encode("utf-8")).digest()
    return sorted(block, key=score)
