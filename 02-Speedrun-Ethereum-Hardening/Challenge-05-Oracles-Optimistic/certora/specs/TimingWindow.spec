import "setup/setup.spec";

// Proposal blocked if before assertion startTime
rule proposalBeforeStartReverts(env e, uint256 assertionId, bool outcome) {
    setup(e);
    require getAsserter(assertionId) != 0;
    require getProposer(assertionId) == 0;
    require e.block.timestamp < getStartTime(assertionId);
    proposeOutcome@withrevert(e, assertionId, outcome);
    assert lastReverted;
}

// Proposal blocked if after assertion endTime
rule proposalAfterEndReverts(env e, uint256 assertionId, bool outcome) {
    setup(e);
    require getAsserter(assertionId) != 0;
    require getProposer(assertionId) == 0;
    require e.block.timestamp > getEndTime(assertionId);
    proposeOutcome@withrevert(e, assertionId, outcome);
    assert lastReverted;
}

// Dispute blocked after dispute window
rule disputeAfterWindowReverts(env e, uint256 assertionId) {
    setup(e);
    require getProposer(assertionId) != 0;
    require getDisputer(assertionId) == 0;
    require e.block.timestamp > getEndTime(assertionId);
    disputeOutcome@withrevert(e, assertionId);
    assert lastReverted;
}

// Undisputed claim blocked before dispute window expires
rule undisputedClaimBeforeWindowReverts(env e, uint256 assertionId) {
    setup(e);
    require getProposer(assertionId) != 0;
    require getDisputer(assertionId) == 0;
    require !getClaimed(assertionId);
    require e.block.timestamp <= getEndTime(assertionId);
    claimUndisputedReward@withrevert(e, assertionId);
    assert lastReverted;
}

// Refund blocked before assertion expires
rule refundBeforeExpiryReverts(env e, uint256 assertionId) {
    setup(e);
    require getAsserter(assertionId) != 0;
    require getProposer(assertionId) == 0;
    require !getClaimed(assertionId);
    require e.block.timestamp <= getEndTime(assertionId);
    claimRefund@withrevert(e, assertionId);
    assert lastReverted;
}

// Proposal inside window sets endTime to timestamp + DISPUTE_WINDOW
rule proposalSetsDisputeDeadline(env e, uint256 assertionId, bool outcome) {
    setup(e);
    require getAsserter(assertionId) != 0;
    require getProposer(assertionId) == 0;
    require getDisputer(assertionId) == 0;
    require e.block.timestamp >= getStartTime(assertionId);
    require e.block.timestamp <= getEndTime(assertionId);
    require e.msg.value == getBond(assertionId);

    proposeOutcome@withrevert(e, assertionId, outcome);
    require !lastReverted;

    assert getEndTime(assertionId) == e.block.timestamp + 180;
}
