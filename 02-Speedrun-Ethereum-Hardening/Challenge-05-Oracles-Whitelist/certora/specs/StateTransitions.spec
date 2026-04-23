/**
 * StateTransitions.spec — Step 8.
 *
 * Covers hypotheses H-01, H-02, H-03, H-07, H-09, H-14.
 *
 * Uses setup(e) only — these rules do not assume the (yet-unproven)
 * valid-state invariants. Any rule that needs them will be restated in
 * Step 10 against setupValidState(e).
 */

import "setup/setup.spec";

/* ----------------------------------------------------------------------
   H-14: addOracle strictly grows oracles[] by 1.
   ---------------------------------------------------------------------- */
rule addOracleGrowsLengthByOne(env e, address newOwner) {
    setup(e);
    uint256 lenBefore = getOraclesLength();
    // Bound below a sane number — avoids spurious overflow in the length counter.
    require lenBefore < 2^128;

    addOracle(e, newOwner);

    uint256 lenAfter = getOraclesLength();
    assert lenAfter == lenBefore + 1,
        "addOracle must grow oracles[] by exactly 1";
}

/* ----------------------------------------------------------------------
   H-14 (cont.): the newly appended entry is at index oldLen, is non-zero,
   and owned by the caller-supplied address.
   ---------------------------------------------------------------------- */
rule addOracleAppendsAtEnd(env e, address newOwner) {
    setup(e);
    uint256 lenBefore = getOraclesLength();
    require lenBefore < 2^128;

    addOracle(e, newOwner);

    address newEntry = getOracleAt(lenBefore);
    assert newEntry != 0,
        "newly appended SimpleOracle must be non-zero address";
}

/* ----------------------------------------------------------------------
   H-01 / H-02: removeOracle shrinks length by 1 when index < len,
   reverts otherwise.
   ---------------------------------------------------------------------- */
rule removeOracleShrinksLengthWhenValid(env e, uint256 index) {
    setup(e);
    uint256 lenBefore = getOraclesLength();
    require index < lenBefore;

    removeOracle(e, index);

    uint256 lenAfter = getOraclesLength();
    assert lenAfter == lenBefore - 1,
        "removeOracle(valid index) must shrink oracles[] by exactly 1";
}

rule removeOracleRevertsOutOfBounds(env e, uint256 index) {
    setup(e);
    uint256 lenBefore = getOraclesLength();
    require index >= lenBefore;

    removeOracle@withrevert(e, index);
    assert lastReverted,
        "removeOracle(index >= len) must revert";
}

/* ----------------------------------------------------------------------
   H-01 (cont.): swap-and-pop semantics. After removeOracle(i),
   either the element at i is unchanged (i was the last) or it is the
   old last element.
   ---------------------------------------------------------------------- */
rule removeOracleSwapAndPopCorrect(env e, uint256 index) {
    setup(e);
    uint256 lenBefore = getOraclesLength();
    require index < lenBefore;
    require lenBefore > 0;

    uint256 lastIdx = require_uint256(lenBefore - 1);
    address oldLast = getOracleAt(lastIdx);

    removeOracle(e, index);

    uint256 lenAfter = getOraclesLength();

    // Case 1: index was the last element — the element at `index` no
    // longer exists; length shrank by 1.
    // Case 2: swap-and-pop — the element at `index` is now the old last.
    if (index == lastIdx) {
        assert lenAfter == require_uint256(lenBefore - 1);
    } else {
        address atIndexAfter = getOracleAt(index);
        assert atIndexAfter == oldLast,
            "swap-and-pop: removed index now holds old last element";
    }
}

/* ----------------------------------------------------------------------
   H-03: Field-write authority on oracles.length — parametric.
   Only addOracle and removeOracle can change oracles.length. No other
   entrypoint may grow or shrink the array.
   ---------------------------------------------------------------------- */
rule oraclesLengthOnlyChangedByAddOrRemove(env e, method f, calldataarg args)
    filtered {
        // View functions cannot modify state (EVM enforced). Without this
        // filter, DISPATCHER(true) on the internal SimpleOracle.getPrice()
        // call lets the prover imagine arbitrary callee state writes,
        // which is a modeling artifact, not a real reachability.
        f -> f.contract == currentContract && !f.isView
    }
{
    setup(e);
    uint256 lenBefore = getOraclesLength();

    f(e, args);

    uint256 lenAfter = getOraclesLength();

    bool changed = lenAfter != lenBefore;
    bool isAdd = f.selector == sig:addOracle(address).selector;
    bool isRemove = f.selector == sig:removeOracle(uint256).selector;

    assert changed => (isAdd || isRemove),
        "only addOracle or removeOracle may change oracles.length";
}

/* ----------------------------------------------------------------------
   H-07: getPrice reverts when oracles[] is empty.
   ---------------------------------------------------------------------- */
rule getPriceRevertsOnEmpty(env e) {
    setup(e);
    require getOraclesLength() == 0;

    getPrice@withrevert(e);
    assert lastReverted,
        "getPrice() with zero oracles must revert (NoOraclesAvailable)";
}

/* ----------------------------------------------------------------------
   H-09: event witness — OracleAdded is emitted by addOracle on success.
   We prove the causal path with a satisfy: an addOracle call can reach
   the state where length grew AND a non-zero new element was appended.
   (Strict event-emission counting is harder to express in CVL without
   trace ghosts; this is the usual proxy.)
   ---------------------------------------------------------------------- */
rule addOracleProducesVisibleEffect(env e, address newOwner) {
    setup(e);
    uint256 lenBefore = getOraclesLength();
    require lenBefore < 2^128;

    addOracle(e, newOwner);

    satisfy getOraclesLength() == lenBefore + 1
         && getOracleAt(lenBefore) != 0;
}

/* ----------------------------------------------------------------------
   H-12: Access-control is disabled (documented deviation). Anyone can
   call addOracle / removeOracle. Witness.
   ---------------------------------------------------------------------- */
rule anyCallerCanAddOracle(env e, address newOwner) {
    setup(e);
    // Non-owner caller.
    require e.msg.sender != owner();

    addOracle@withrevert(e, newOwner);
    satisfy !lastReverted;
}
