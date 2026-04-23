/**
 * Sanity.spec — Step 7.
 *
 * Before any real property work, prove the setup is alive:
 *   (a) every non-view function can reach its end (no unreachable code),
 *   (b) parametric noop detector (catches memory-vs-storage bugs).
 *
 * If any rule here fails, fix linking / methods block / harness before
 * proceeding.
 */

import "setup/setup.spec";

/**
 * Every non-view, non-pure contract function must have a reachable
 * successful execution path.
 */
rule nonViewCanSucceed(env e, method f, calldataarg args)
    filtered { f -> !f.isView && !f.isPure && f.contract == currentContract }
{
    setup(e);
    f@withrevert(e, args);
    satisfy !lastReverted;
}

/**
 * getPrice() can revert in some environment (empty or stale oracles).
 * The satisfy here proves the revert path is reachable.
 */
rule getPriceCanRevert(env e) {
    setup(e);
    getPrice@withrevert(e);
    satisfy lastReverted;
}

/**
 * getPrice() can succeed in some environment (at least one fresh oracle).
 */
rule getPriceCanSucceed(env e) {
    setup(e);
    getPrice@withrevert(e);
    satisfy !lastReverted;
}

/**
 * removeOracle can revert (out-of-bounds).
 */
rule removeOracleCanRevert(env e, uint256 index) {
    setup(e);
    removeOracle@withrevert(e, index);
    satisfy lastReverted;
}

/**
 * addOracle strictly increases oracles.length by 1 (existence of a success path).
 */
rule addOracleSucceedsAndGrows(env e, address newOwner) {
    setup(e);
    uint256 lenBefore = getOraclesLength();
    addOracle(e, newOwner);
    uint256 lenAfter = getOraclesLength();
    satisfy lenAfter == lenBefore + 1;
}
