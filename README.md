# FIRSTCALL

**Synthetic customer monitoring for autonomous agents.**

FIRSTCALL asks a fresh coding agent to integrate a product,
executes what it builds, and independently verifies whether the
required real-world effect occurred.

The agent does not grade itself.

## Core outcomes

- `PROVEN_SUCCESS`
- `FALSE_SUCCESS`
- `EXECUTION_FAILED`
- `EFFECT_FAILED`
- `UNSAFE_SUCCESS`
- `UNKNOWN`

## Core experiment

1. Snapshot the onboarding surface.
2. Give a fresh agent a customer task.
3. Execute its integration.
4. Verify the effect independently.
5. Localise failures.
6. Patch the onboarding surface.
7. Replay fresh agents.
8. Measure the causal improvement.

This is **Counterfactual Replay**.

## North-star metric

**Agent First-Call Rate (AFCR)**

The proportion of fresh agent runs that reach an independently
verified successful first product outcome.

## Principle

> Agent says success != proof of success.
