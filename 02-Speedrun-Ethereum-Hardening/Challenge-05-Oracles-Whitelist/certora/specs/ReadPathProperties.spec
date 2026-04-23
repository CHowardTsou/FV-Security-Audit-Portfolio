/**
 * ReadPathProperties.spec — Step 8 / Step 10.
 *
 * Behavioral properties of the read path: getPrice() and
 * getActiveOracleNodes().
 *
 * External SimpleOracle.getPrice() returns (price, timestamp) are
 * resolved via DISPATCHER(true) — each call site receives an
 * independently chosen symbolic return (the DISPATCHER routes through
 * SimpleOracle's view code, but each instance's storage is arbitrary
 * under the abstract model). This gives coverage of the staleness-
 * filter logic without pinning down specific oracle state.
 *
 * Covers H-04 (staleness boundary), H-05 (underflow via time > now),
 * H-06 (NoOraclesAvailable propagation), H-07 (empty-set revert, also
 * covered in StateTransitions), H-10 (view-only reentrancy witness),
 * H-13 (active-set membership).
 */

import "setup/setup.spec";

/* ----------------------------------------------------------------------
   H-05: If any oracle has timestamp > block.timestamp, getPrice() would
   underflow `currentTime - time`. Solidity 0.8 reverts on underflow.

   Witness: getPrice() can revert when some oracle's timestamp exceeds
   block.timestamp. (Does not assert which path — just that a revert
   is reachable under that precondition.)
   ---------------------------------------------------------------------- */
rule getPriceRevertsOnFutureTimestamp(env e) {
    setup(e);
    uint256 len = getOraclesLength();
    require len > 0 && len <= 3;

    // At least one oracle has a future timestamp.
    require getOracleTimestampAt(0) > e.block.timestamp;

    getPrice@withrevert(e);
    satisfy lastReverted;
}

/* ----------------------------------------------------------------------
   H-06 / H-07: getPrice() reverts when no oracle is fresh.
   We use the harness's per-index timestamp getter to force all oracles
   stale (delta >= STALE_DATA_WINDOW).
   ---------------------------------------------------------------------- */
rule getPriceRevertsWhenAllStale(env e) {
    setup(e);
    uint256 len = getOraclesLength();
    require len == 1;  // single-oracle regime, sufficient witness

    uint256 staleWindow = STALE_DATA_WINDOW();
    uint256 t0 = getOracleTimestampAt(0);

    // Strictly stale: delta >= STALE_DATA_WINDOW
    require e.block.timestamp >= t0;
    require e.block.timestamp - t0 >= staleWindow;

    getPrice@withrevert(e);
    assert lastReverted,
        "getPrice() with single stale oracle must revert";
}

/* ----------------------------------------------------------------------
   H-04 staleness boundary witness:
   At delta == STALE_DATA_WINDOW exactly, the oracle is treated as STALE
   (the filter uses `<`, not `<=`). Prove by exhibiting a stale-revert
   at delta == window.
   ---------------------------------------------------------------------- */
rule staleBoundaryIsStale(env e) {
    setup(e);
    uint256 len = getOraclesLength();
    require len == 1;

    uint256 staleWindow = STALE_DATA_WINDOW();
    uint256 t0 = getOracleTimestampAt(0);

    require e.block.timestamp >= t0;
    require e.block.timestamp - t0 == staleWindow;

    getPrice@withrevert(e);
    assert lastReverted,
        "delta == STALE_DATA_WINDOW must be classified as stale (filter uses <)";
}

/* ----------------------------------------------------------------------
   Complementary: at delta < STALE_DATA_WINDOW the oracle is FRESH, and
   getPrice can succeed (if the oracle returns a well-formed price).
   Witness only — we don't bind the exact median value.
   ---------------------------------------------------------------------- */
rule strictlyFreshCanSucceed(env e) {
    setup(e);
    uint256 len = getOraclesLength();
    require len == 1;

    uint256 staleWindow = STALE_DATA_WINDOW();
    uint256 t0 = getOracleTimestampAt(0);

    require e.block.timestamp >= t0;
    require e.block.timestamp - t0 < staleWindow;

    getPrice@withrevert(e);
    satisfy !lastReverted;
}

/* ----------------------------------------------------------------------
   H-13 / H-10: getActiveOracleNodes is view and can be called on any state.
   Witness: the function succeeds even with a mix of fresh and stale oracles.
   ---------------------------------------------------------------------- */
rule getActiveOracleNodesAlwaysSucceeds(env e) {
    setup(e);
    uint256 len = getOraclesLength();
    require len <= 3;  // bounded regime matching loop_iter

    getActiveOracleNodes@withrevert(e);
    satisfy !lastReverted;
}

/* ----------------------------------------------------------------------
   Assert-style strengthening of the above.

   The satisfy-only form above lets a mutant survive when the trivial
   `len == 0` case still produces a non-reverting witness. Mutation
   testing (run 2) exposed this: `--i` on uint256, `/`-for-`-`,
   `**`-for-`-`, and `swap` mutants in the staleness check all survived
   because the oraclesLength==0 path doesn't execute the loop body.

   Here we force `len >= 1` and bound the symbolic SimpleOracle
   timestamp to be <= block.timestamp (matching real SimpleOracle
   semantics: `setPrice` always stamps with the current block.timestamp,
   so no oracle can legitimately carry a future timestamp). Under those
   preconditions the healthy contract never reverts, and any mutation
   that turns the staleness expression into an underflow / divide-by-zero
   is killed by the assert.

   Covers mutants:
   - `++i` -> `--i` (underflow on first iteration)
   - `a - b` -> `a / b` (division by zero when `time == 0`)
   - `a - b` -> `b - a` (underflow when `time < currentTime`)
   - `a - b` -> `a ** b` (exponent overflow on large values)
   ---------------------------------------------------------------------- */
rule getActiveOracleNodesNeverRevertsOnValidTimestamps(env e) {
    setup(e);
    uint256 len = getOraclesLength();
    require len >= 1 && len <= 3;

    // Match real SimpleOracle: every oracle's timestamp is <= now.
    require getOracleTimestampAt(0) <= e.block.timestamp;
    require len < 2 || getOracleTimestampAt(1) <= e.block.timestamp;
    require len < 3 || getOracleTimestampAt(2) <= e.block.timestamp;

    getActiveOracleNodes@withrevert(e);
    assert !lastReverted,
        "getActiveOracleNodes must not revert when all timestamps <= now";
}

/* ----------------------------------------------------------------------
   H-10 view-purity: getPrice and getActiveOracleNodes must not mutate
   oracles.length. Under the wildcard DISPATCHER(true) summary, reading
   state before and after a call that reaches back into currentContract
   triggers Certora's contract-recursion tracking; enable
   `optimistic_contract_recursion=true, contract_recursion_limit=1` in
   the conf to keep the chain bounded.
   ---------------------------------------------------------------------- */
rule getPriceDoesNotChangeOraclesLength(env e) {
    setup(e);
    uint256 lenBefore = getOraclesLength();

    getPrice@withrevert(e);

    uint256 lenAfter = getOraclesLength();
    assert lenBefore == lenAfter,
        "getPrice() is view — oracles.length must not change";
}

rule getActiveOracleNodesDoesNotChangeState(env e) {
    setup(e);
    uint256 lenBefore = getOraclesLength();

    getActiveOracleNodes@withrevert(e);

    uint256 lenAfter = getOraclesLength();
    assert lenBefore == lenAfter,
        "getActiveOracleNodes() is view — oracles.length must not change";
}
