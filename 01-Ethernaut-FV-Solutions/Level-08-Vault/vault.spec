methods {
    function unlock(bytes32) external;
    function locked() external returns (bool) envfree;
}

// ─────────────────────────────────────────────────────────────
// RULE 1: PASSES — wrong password never unlocks
// ─────────────────────────────────────────────────────────────
rule wrongPasswordFails(env e, bytes32 attempt) {
    bool lockedBefore = locked();
    require lockedBefore == true;

    // Certora will try ALL possible bytes32 values for attempt
    // and verify this holds — EXCEPT it will find the one that breaks it
    unlock(e, attempt);

    // This will FAIL — Certora finds: attempt == password is a valid input
    assert locked() == true, "vault was unlocked — a valid password exists";
}

// ─────────────────────────────────────────────────────────────
// RULE 2: PASSES — locked never goes false → true
// No re-lock mechanism exists
// ─────────────────────────────────────────────────────────────
rule cannotReLock(env e, method f, calldataarg args) {
    require locked() == false;

    f(e, args);

    assert locked() == false, "vault re-locked — unexpected state change";
}

// ─────────────────────────────────────────────────────────────
// RULE 3: PASSES — only unlock() can change locked state
// ─────────────────────────────────────────────────────────────
rule onlyUnlockChangesState(env e, method f, calldataarg args) {
    bool lockedBefore = locked();

    f(e, args);

    bool lockedAfter = locked();

    assert lockedBefore != lockedAfter => f.selector == sig:unlock(bytes32).selector, "locked state changed by unexpected function";
}
