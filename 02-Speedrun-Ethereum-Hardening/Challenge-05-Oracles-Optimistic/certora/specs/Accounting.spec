import "setup/setup.spec";
import "ValidState.spec";

// No double claim: claimUndisputedReward reverts if already claimed
rule noDoubleClaimUndisputed(env e, uint256 assertionId) {
    setup(e);
    require getAsserter(assertionId) != 0;
    require getClaimed(assertionId);
    claimUndisputedReward@withrevert(e, assertionId);
    assert lastReverted;
}

// No double claim: claimDisputedReward reverts if already claimed
rule noDoubleClaimDisputed(env e, uint256 assertionId) {
    setup(e);
    require getAsserter(assertionId) != 0;
    require getClaimed(assertionId);
    claimDisputedReward@withrevert(e, assertionId);
    assert lastReverted;
}

// No double claim: claimRefund reverts if already claimed
rule noDoubleClaimRefund(env e, uint256 assertionId) {
    setup(e);
    require getAsserter(assertionId) != 0;
    require getClaimed(assertionId);
    claimRefund@withrevert(e, assertionId);
    assert lastReverted;
}

// claimUndisputedReward sets claimed and winner = proposer
rule undisputedClaimSetsClaimedAndWinner(env e, uint256 assertionId) {
    setup(e);
    requireInvariant bondEqualsDoubleReward(assertionId);
    require getAsserter(assertionId) != 0;
    require !getClaimed(assertionId);
    require getProposer(assertionId) != 0;
    require getDisputer(assertionId) == 0;
    require e.block.timestamp > getEndTime(assertionId);
    address proposerBefore = getProposer(assertionId);
    claimUndisputedReward@withrevert(e, assertionId);
    require !lastReverted;
    assert getClaimed(assertionId);
    assert getWinner(assertionId) == proposerBefore;
}

// claimRefund sets claimed flag
rule refundClaimSetsClaimed(env e, uint256 assertionId) {
    setup(e);
    require getAsserter(assertionId) != 0;
    require !getClaimed(assertionId);
    require getProposer(assertionId) == 0;
    require e.block.timestamp > getEndTime(assertionId);
    claimRefund@withrevert(e, assertionId);
    require !lastReverted;
    assert getClaimed(assertionId);
}

// claimDisputedReward requires winner to be set (decider must have settled)
rule disputedClaimRequiresWinner(env e, uint256 assertionId) {
    setup(e);
    require getAsserter(assertionId) != 0;
    require getProposer(assertionId) != 0;
    require getDisputer(assertionId) != 0;
    require getWinner(assertionId) == 0;
    require !getClaimed(assertionId);
    claimDisputedReward@withrevert(e, assertionId);
    assert lastReverted;
}

// proposeOutcome requires exact bond payment (= 2x reward)
rule proposalRequiresExactBond(env e, uint256 assertionId, bool outcome) {
    setup(e);
    requireInvariant bondEqualsDoubleReward(assertionId);
    require getAsserter(assertionId) != 0;
    require getProposer(assertionId) == 0;
    require e.msg.value != getBond(assertionId);
    proposeOutcome@withrevert(e, assertionId, outcome);
    assert lastReverted;
}

// disputeOutcome requires exact bond payment (= 2x reward)
rule disputeRequiresExactBond(env e, uint256 assertionId) {
    setup(e);
    requireInvariant bondEqualsDoubleReward(assertionId);
    require getAsserter(assertionId) != 0;
    require getProposer(assertionId) != 0;
    require getDisputer(assertionId) == 0;
    require e.msg.value != getBond(assertionId);
    disputeOutcome@withrevert(e, assertionId);
    assert lastReverted;
}

// assertEvent requires non-zero ETH
rule assertEventRequiresValue(env e, calldataarg args) {
    setup(e);
    require e.msg.value == 0;
    assertEvent@withrevert(e, args);
    assert lastReverted;
}
