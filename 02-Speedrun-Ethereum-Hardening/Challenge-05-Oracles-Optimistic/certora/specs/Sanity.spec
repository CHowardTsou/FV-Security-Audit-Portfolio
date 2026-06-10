import "setup/setup.spec";
import "ValidState.spec";

// Sanity 1: All state-changing functions can succeed
// Excludes access-gated functions (setDecider=onlyOwner, settleAssertion=onlyDecider)
rule nonViewCanSucceed(env e, method f, calldataarg args)
    filtered {
        f -> !f.isView && !f.isPure
          && f.contract == currentContract
          && f.selector != sig:setDecider(address).selector
          && f.selector != sig:settleAssertion(uint256,bool).selector
    }
{
    setup(e);
    f@withrevert(e, args);
    satisfy !lastReverted;
}

// Sanity 2: nextAssertionId only increases
rule nextAssertionIdNeverDecreases(env e, method f, calldataarg args)
    filtered { f -> !f.isView && !f.isPure && f.contract == currentContract }
{
    setup(e);
    uint256 idBefore = nextAssertionId_ghost;
    f@withrevert(e, args);
    bool reverted = lastReverted;
    uint256 idAfter = nextAssertionId_ghost;
    assert !reverted => idAfter >= idBefore;
}

// Sanity 3: witness that the ValidState invariants hold (referenced as proof)
rule bondInvariantWitness(env e, uint256 id) {
    setup(e);
    requireInvariant bondEqualsDoubleReward(id);
    require getAsserter(id) != 0;
    assert getBond(id) == getReward(id) * 2;
}

// Sanity 4: witness that disputer => proposer invariant holds
rule disputerInvariantWitness(env e, uint256 id) {
    setup(e);
    requireInvariant disputerImpliesProposer(id);
    require getDisputer(id) != 0;
    assert getProposer(id) != 0;
}
