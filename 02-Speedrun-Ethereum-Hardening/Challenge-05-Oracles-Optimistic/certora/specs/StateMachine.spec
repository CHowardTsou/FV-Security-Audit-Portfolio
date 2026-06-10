import "setup/setup.spec";
import "ValidState.spec";

// Rule: claimed flag is terminal - once set, cannot be reset
rule claimedIsTerminal(env e, uint256 assertionId, method f, calldataarg args)
    filtered { f -> !f.isView && !f.isPure && f.contract == currentContract }
{
    setup(e);
    require getAsserter(assertionId) != 0;
    // Overflow guard: tracked assertion was created before current nextAssertionId
    require assertionId < nextAssertionId();
    bool claimedBefore = getClaimed(assertionId);
    require claimedBefore;

    f@withrevert(e, args);

    bool claimedAfter = getClaimed(assertionId);
    assert claimedAfter;
}

// Rule: winner field is terminal - once set, cannot change
rule winnerIsTerminal(env e, uint256 assertionId, method f, calldataarg args)
    filtered { f -> !f.isView && !f.isPure && f.contract == currentContract }
{
    setup(e);
    require getAsserter(assertionId) != 0;
    require assertionId < nextAssertionId();
    requireInvariant winnerIsProposerOrDisputer(assertionId);
    address winnerBefore = getWinner(assertionId);
    require winnerBefore != 0;

    f@withrevert(e, args);

    address winnerAfter = getWinner(assertionId);
    assert winnerAfter == winnerBefore;
}

// Rule: proposer can only be set once (never overwritten)
rule proposerNeverOverwritten(env e, uint256 assertionId, method f, calldataarg args)
    filtered { f -> !f.isView && !f.isPure && f.contract == currentContract }
{
    setup(e);
    require getAsserter(assertionId) != 0;
    require assertionId < nextAssertionId();
    address proposerBefore = getProposer(assertionId);
    require proposerBefore != 0;

    f@withrevert(e, args);

    address proposerAfter = getProposer(assertionId);
    assert proposerAfter == proposerBefore;
}

// Rule: disputer can only be set once (never overwritten)
rule disputerNeverOverwritten(env e, uint256 assertionId, method f, calldataarg args)
    filtered { f -> !f.isView && !f.isPure && f.contract == currentContract }
{
    setup(e);
    require getAsserter(assertionId) != 0;
    require assertionId < nextAssertionId();
    requireInvariant disputerImpliesProposer(assertionId);
    address disputerBefore = getDisputer(assertionId);
    require disputerBefore != 0;

    f@withrevert(e, args);

    address disputerAfter = getDisputer(assertionId);
    assert disputerAfter == disputerBefore;
}

// Rule: proposeOutcome only succeeds when no prior proposer
rule proposeRequiresNoPriorProposer(env e, uint256 assertionId, bool outcome) {
    setup(e);
    require getProposer(assertionId) != 0;
    proposeOutcome@withrevert(e, assertionId, outcome);
    assert lastReverted;
}

// Rule: disputeOutcome only succeeds when no prior disputer
rule disputeRequiresNoPriorDisputer(env e, uint256 assertionId) {
    setup(e);
    require getDisputer(assertionId) != 0;
    disputeOutcome@withrevert(e, assertionId);
    assert lastReverted;
}

// Rule: settleAssertion only succeeds when not already settled
rule settleRequiresNotSettled(env e, uint256 assertionId, bool outcome) {
    setup(e);
    require getWinner(assertionId) != 0;
    settleAssertion@withrevert(e, assertionId, outcome);
    assert lastReverted;
}

// Rule: assertEvent creates assertion with correct initial state
rule assertEventInitializesCorrectly(env e, calldataarg args) {
    setup(e);
    require e.msg.value > 0;
    uint256 expectedId = nextAssertionId_ghost;
    assertEvent@withrevert(e, args);
    require !lastReverted;
    assert getAsserter(expectedId) == e.msg.sender;
    assert getProposer(expectedId) == 0;
    assert getDisputer(expectedId) == 0;
    assert getWinner(expectedId) == 0;
    assert !getClaimed(expectedId);
    assert getReward(expectedId) == e.msg.value;
    assert getBond(expectedId) == e.msg.value * 2;
}

// Rule: settleAssertion determines winner correctly (assert !lastReverted kills M4)
rule settleDeterminesCorrectWinner(env e, uint256 assertionId, bool resolvedOutcome) {
    setup(e);
    require e.msg.value == 0;
    require e.msg.sender == decider();
    require getAsserter(assertionId) != 0;
    require getProposer(assertionId) != 0;
    require getDisputer(assertionId) != 0;
    require getWinner(assertionId) == 0;
    settleAssertion@withrevert(e, assertionId, resolvedOutcome);
    assert !lastReverted;
    bool proposedOutcome = getProposedOutcome(assertionId);
    address expectedWinner = (resolvedOutcome == proposedOutcome) ?
        getProposer(assertionId) : getDisputer(assertionId);
    assert getWinner(assertionId) == expectedWinner;
    assert getResolvedOutcome(assertionId) == resolvedOutcome;
}

// Rule: getState never returns Invalid (0) when asserter exists (kills M5)
rule getStateInvalidIffNoAsserter(env e, uint256 assertionId) {
    setup(e);
    require getAsserter(assertionId) != 0;
    assert assert_uint8(getState(e, assertionId)) != 0;
}
