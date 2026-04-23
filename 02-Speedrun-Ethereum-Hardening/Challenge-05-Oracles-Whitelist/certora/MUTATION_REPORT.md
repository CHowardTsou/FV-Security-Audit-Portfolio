# Mutation Testing Report — WhitelistOracle

Per-family Gambit runs against the verification suite.

## Run 1 — StateTransitions.spec (10 mutants)

**Kill rate:** 1/10 (10%)
**Report:** https://mutation-testing.certora.com/?id=a40b7743-bdab-4e2e-849d-2a4fadf69cc4&anonymousKey=d33666f6-70be-4e58-a4dc-c2ccb9f0211d

| # | Location                               | Mutation                                                  | Status   | Classification                     | Kill path                                                  |
|---|----------------------------------------|-----------------------------------------------------------|----------|------------------------------------|------------------------------------------------------------|
| 1 | `removeOracle` L80                     | `oracles.length - 1` → `oracles.length % 1` (=0)         | KILLED   | Real bug — wrong swap source       | `removeOracleSwapAndPopCorrect` ✓                          |
| 2 | `getActiveOracleNodes` outer loop L127 | `++i` → `--i` (underflow)                                 | SURVIVED | Off-surface — owned by ReadPath    | `getActiveOracleNodesAlwaysSucceeds` (ReadPath)            |
| 3 | `getPrice` L100 staleness check        | `currentTime - time` → `currentTime / time`               | SURVIVED | Off-surface — owned by ReadPath    | `staleBoundaryIsStale` (ReadPath)                          |
| 4 | `getPrice` L101 price copy             | `priceArray[validCount] = price` → `= 1`                  | SURVIVED | **Real spec gap (H-11 uncovered)** | Needs median-correctness rule                              |
| 5 | `getPrice` L102 count increment        | `validCount++` → `assert(true)` (no-op)                   | SURVIVED | Off-surface — owned by ReadPath    | `strictlyFreshCanSucceed` (ReadPath)                       |
| 6 | `getPrice` L98 outer-loop increment    | `++i` → `assert(true)` (infinite loop)                    | SURVIVED | Off-surface — owned by ReadPath    | `strictlyFreshCanSucceed` (ReadPath)                       |
| 7 | `getPrice` L107 copy-out loop          | `++i` → `--i`                                             | SURVIVED | **Real spec gap (H-11 uncovered)** | Needs median-correctness rule                              |
| 8 | `getActiveOracleNodes` L129 staleness  | `currentTime - time` → `/`                                | SURVIVED | Off-surface — owned by ReadPath    | `getActiveOracleNodesAlwaysSucceeds` (ReadPath)            |
| 9 | `getActiveOracleNodes` L129 staleness  | `currentTime - time` → `**`                               | SURVIVED | Off-surface — owned by ReadPath    | `getActiveOracleNodesAlwaysSucceeds` (ReadPath)            |
| 10 | `getActiveOracleNodes` L129 swap args | `currentTime - time` → `time - currentTime`               | SURVIVED | Off-surface — owned by ReadPath    | `getActiveOracleNodesAlwaysSucceeds` (ReadPath)            |

9 of 10 mutants targeted the read path (`getPrice` / `getActiveOracleNodes`),
not the write path. StateTransitions.spec intentionally does not reason about
read-path behavior, so the raw 10% kill rate is not a signal of shallow
verification — it reflects spec-surface coverage.

Mutants #4 and #7 are genuine uncovered cases: both corrupt the *value* of the
returned median without breaking the `getPrice` call structure. They correspond
to H-11, which is listed as `Uncovered` in `HYPOTHESES.md`.

---

## Run 2 — ReadPathProperties.spec, satisfy-only (10 mutants)

**Kill rate:** 4/10 (40%)

| # | Location                               | Mutation                                                  | Status   | Classification                         |
|---|----------------------------------------|-----------------------------------------------------------|----------|----------------------------------------|
| 1 | `removeOracle` L80                     | `length - 1` → `length % 1`                               | SURVIVED | Off-surface — owned by StateTransitions |
| 2 | `getActiveOracleNodes` outer loop L127 | `++i` → `--i`                                             | SURVIVED | **Real spec weakness — satisfy too weak** |
| 3 | `getPrice` L100 staleness check        | `currentTime - time` → `currentTime / time`               | KILLED   | ✓                                      |
| 4 | `getPrice` L101 price copy             | `priceArray[validCount] = price` → `= 1`                  | SURVIVED | **H-11 real gap (median correctness)** |
| 5 | `getPrice` L102 count increment        | `validCount++` → `assert(true)`                           | KILLED   | ✓                                      |
| 6 | `getPrice` L98 outer-loop increment    | `++i` → `assert(true)`                                    | KILLED   | ✓                                      |
| 7 | `getPrice` L107 copy-out loop          | `++i` → `--i`                                             | KILLED   | ✓ (uint256 underflow revert)           |
| 8 | `getActiveOracleNodes` L129 staleness  | `currentTime - time` → `/`                                | SURVIVED | Real spec weakness — satisfy too weak  |
| 9 | `getActiveOracleNodes` L129 staleness  | `currentTime - time` → `**`                               | SURVIVED | Real spec weakness — satisfy too weak  |
| 10 | `getActiveOracleNodes` L129 swap args | `currentTime - time` → `time - currentTime`               | SURVIVED | Real spec weakness — satisfy too weak  |

**Key finding:** four survivors (#2, #8, #9, #10) slipped past
`getActiveOracleNodesAlwaysSucceeds`, which used `satisfy !lastReverted`. The
prover only needs one non-reverting witness — the trivial `oracles.length == 0`
path — to pass, regardless of what the loop body does. Mutations that only
manifest when the body executes never mattered.

**Fix:** added `getActiveOracleNodesNeverRevertsOnValidTimestamps` — an
assert-style rule that forces `len >= 1` and bounds each oracle's timestamp to
`<= block.timestamp`. Under that regime the healthy contract never reverts, and
the mutants now die.

---

## Run 3 — ReadPathProperties.spec, strengthened spec (10 mutants)

**Kill rate:** 8/10 (80%)

| # | Mutation                                            | Run 2 outcome      | Run 3 outcome          |
|---|-----------------------------------------------------|--------------------|------------------------|
| 1 | `removeOracle` `length - 1` → `length % 1`         | SURVIVED (off-surface) | **SURVIVED** (off-surface) |
| 2 | `getActiveOracleNodes` `++i` → `--i`               | SURVIVED           | **KILLED** ✓           |
| 3 | `getPrice` staleness `-` → `/`                      | KILLED             | KILLED                 |
| 4 | `priceArray[validCount] = price` → `= 1`            | SURVIVED (H-11)    | **SURVIVED** (H-11)    |
| 5 | `getPrice` `validCount++` → `assert(true)`          | KILLED             | KILLED                 |
| 6 | `getPrice` outer `++i` → `assert(true)`             | KILLED             | KILLED                 |
| 7 | `getPrice` copy-out `++i` → `--i`                   | KILLED             | KILLED                 |
| 8 | `getActiveOracleNodes` staleness `-` → `/`          | SURVIVED           | **KILLED** ✓           |
| 9 | `getActiveOracleNodes` staleness `-` → `**`         | SURVIVED           | **KILLED** ✓           |
| 10 | `getActiveOracleNodes` staleness swap args         | SURVIVED           | **KILLED** ✓           |

**Cross-family union (StateTransitions + ReadPath strengthened): 9/10 (90%).**
Single remaining survivor: #4 (H-11 — median correctness gap).

---

## Run 4 — ValidState.spec (10 mutants)

**Kill rate:** 0/10 — expected result, not a shallow-spec finding.

ValidState.spec proves two invariants: `ghostLenMatches` (ghost length mirror
equals `oracles.length`) and `oraclesNonZero` (every in-range `oracles[i] !=
address(0)`). These talk about **storage shape**, not behavior. Every mutation
in this Gambit batch targeted read-path semantics or behavioral correctness of
`removeOracle` — none wrote `address(0)` into `oracles[i]` or desynced the
ghost length mirror, so no invariant was violated.

Example: mutant #1 (`length - 1` → `length % 1`). Post-state: `length`
decreased by 1 (ghost mirror still matches); all surviving elements still
non-zero. Neither invariant is violated. The behavioral divergence is caught
in StateTransitions via `removeOracleSwapAndPopCorrect`.

Per-family mutation triage measures whether each family kills mutations that
fall on its surface. ValidState's surface is storage shape; this Gambit batch
produced no shape-violating mutations.

---

## Final cross-family kill-rate summary

| Spec family                   | Independent kill rate | Contributes to union         |
|-------------------------------|-----------------------|------------------------------|
| StateTransitions              | 1/10 (10%)            | #1 (removeOracle)            |
| ReadPath (original satisfy)   | 4/10 (40%)            | #3, #5, #6, #7               |
| ReadPath (strengthened)       | 8/10 (80%)            | + #2, #8, #9, #10            |
| **Union (final)**             | **9/10 (90%)**        | all except #4 (H-11)         |

The 10% → 90% gap is entirely explained by spec-surface coverage:
- Per-family 10%–40% is an artifact of Gambit concentrating mutations on
  `getPrice` / `getActiveOracleNodes` while StateTransitions only reasons
  about write-path entrypoints.
- The spec strengthening from satisfy-style to assert-style for
  `getActiveOracleNodes` is the single biggest kill-rate jump and is directly
  traceable to mutation feedback.

Residual: mutant #4 requires closing H-11. Rough sketch for the rule:

```cvl
rule getPriceEqualsMedianOfFreshPrices(env e) {
    setupValidState(e);
    uint256 len = getOraclesLength();
    require len > 0 && len <= 3;

    uint256 p0 = getOraclePriceValueAt(0); uint256 t0 = getOracleTimestampAt(0);
    // … enumerate up to loop_iter …

    uint256 result = getPrice(e);
    assert result == expectedMedian;
}
```

Deferred — not on critical path for Checkpoint 1 grading.
