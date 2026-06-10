import "setup/setup.spec";

// Invariant: bond always equals 2x reward for any created assertion
invariant bondEqualsDoubleReward(uint256 id)
    getAsserter(id) != 0 => getBond(id) == getReward(id) * 2
filtered { f -> !f.isView && !f.isPure && f.contract == currentContract }
{
    preserved with (env e) { setup(e); }
}

// Invariant: if proposer is set, asserter must be set
invariant proposerImpliesAsserter(uint256 id)
    getProposer(id) != 0 => getAsserter(id) != 0
filtered { f -> !f.isView && !f.isPure && f.contract == currentContract }
{
    preserved with (env e) { setup(e); }
}

// Invariant: if disputer is set, proposer must be set
invariant disputerImpliesProposer(uint256 id)
    getDisputer(id) != 0 => getProposer(id) != 0
filtered { f -> !f.isView && !f.isPure && f.contract == currentContract }
{
    preserved with (env e) {
        setup(e);
        requireInvariant proposerImpliesAsserter(id);
    }
}

// Invariant: winner must be proposer or disputer (if set)
invariant winnerIsProposerOrDisputer(uint256 id)
    getWinner(id) != 0 => (
        getWinner(id) == getProposer(id) ||
        getWinner(id) == getDisputer(id)
    )
filtered { f -> !f.isView && !f.isPure && f.contract == currentContract }
{
    preserved with (env e) {
        setup(e);
        requireInvariant disputerImpliesProposer(id);
    }
}

// Invariant: once winner is set, asserter must also be set
invariant winnerImpliesAsserter(uint256 id)
    getWinner(id) != 0 => getAsserter(id) != 0
filtered { f -> !f.isView && !f.isPure && f.contract == currentContract }
{
    preserved with (env e) {
        setup(e);
        requireInvariant proposerImpliesAsserter(id);
    }
}

// Invariant: nextAssertionId is always >= 1
invariant nextAssertionIdAtLeastOne()
    nextAssertionId() >= 1
filtered { f -> !f.isView && !f.isPure && f.contract == currentContract }
{
    preserved with (env e) { setup(e); }
}
