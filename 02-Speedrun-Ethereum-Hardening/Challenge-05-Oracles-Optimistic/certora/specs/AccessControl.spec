import "setup/setup.spec";

// Only owner can update decider
rule onlyOwnerCanSetDecider(env e, address newDecider) {
    setup(e);
    require e.msg.sender != owner();
    setDecider@withrevert(e, newDecider);
    assert lastReverted;
}

// setDecider by owner succeeds and updates decider
rule setDeciderUpdatesState(env e, address newDecider) {
    setup(e);
    require e.msg.sender == owner();
    require newDecider != 0;
    setDecider@withrevert(e, newDecider);
    require !lastReverted;
    assert decider() == newDecider;
}

// Only decider can settle assertions
rule onlyDeciderCanSettle(env e, uint256 assertionId, bool outcome) {
    setup(e);
    require e.msg.sender != decider();
    settleAssertion@withrevert(e, assertionId, outcome);
    assert lastReverted;
}

// settleAssertion by decider requires disputed state
rule settleRequiresDispute(env e, uint256 assertionId, bool outcome) {
    setup(e);
    require e.msg.sender == decider();
    require getDisputer(assertionId) == 0;
    settleAssertion@withrevert(e, assertionId, outcome);
    assert lastReverted;
}

// Proposal requires assertion to exist
rule proposalRequiresExistingAssertion(env e, uint256 assertionId, bool outcome) {
    setup(e);
    require getAsserter(assertionId) == 0;
    proposeOutcome@withrevert(e, assertionId, outcome);
    assert lastReverted;
}

// Dispute requires proposal to exist
rule disputeRequiresProposal(env e, uint256 assertionId) {
    setup(e);
    require getProposer(assertionId) == 0;
    disputeOutcome@withrevert(e, assertionId);
    assert lastReverted;
}
