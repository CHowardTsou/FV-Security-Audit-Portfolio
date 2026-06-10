import "methods.spec";

// Ghost variables for assertion field tracking
ghost mapping(uint256 => bool) claimed_ghost {
    init_state axiom forall uint256 id. claimed_ghost[id] == false;
}

ghost mapping(uint256 => address) winner_ghost {
    init_state axiom forall uint256 id. winner_ghost[id] == 0;
}

ghost mapping(uint256 => address) proposer_ghost {
    init_state axiom forall uint256 id. proposer_ghost[id] == 0;
}

ghost mapping(uint256 => address) disputer_ghost {
    init_state axiom forall uint256 id. disputer_ghost[id] == 0;
}

ghost mapping(uint256 => uint256) bond_ghost {
    init_state axiom forall uint256 id. bond_ghost[id] == 0;
}

ghost uint256 nextAssertionId_ghost {
    init_state axiom nextAssertionId_ghost == 1;
}

// Storage hooks for claimed field (bool stored as uint8 in packed slot)
hook Sload bool val OptimisticOracleHarness.assertions[KEY uint256 id].claimed {
    require claimed_ghost[id] == val;
}

hook Sstore OptimisticOracleHarness.assertions[KEY uint256 id].claimed bool val {
    claimed_ghost[id] = val;
}

// Storage hooks for winner field
hook Sload address val OptimisticOracleHarness.assertions[KEY uint256 id].winner {
    require winner_ghost[id] == val;
}

hook Sstore OptimisticOracleHarness.assertions[KEY uint256 id].winner address val {
    winner_ghost[id] = val;
}

// Storage hooks for proposer field
hook Sload address val OptimisticOracleHarness.assertions[KEY uint256 id].proposer {
    require proposer_ghost[id] == val;
}

hook Sstore OptimisticOracleHarness.assertions[KEY uint256 id].proposer address val {
    proposer_ghost[id] = val;
}

// Storage hooks for disputer field
hook Sload address val OptimisticOracleHarness.assertions[KEY uint256 id].disputer {
    require disputer_ghost[id] == val;
}

hook Sstore OptimisticOracleHarness.assertions[KEY uint256 id].disputer address val {
    disputer_ghost[id] = val;
}

// Storage hooks for bond field
hook Sload uint256 val OptimisticOracleHarness.assertions[KEY uint256 id].bond {
    require bond_ghost[id] == val;
}

hook Sstore OptimisticOracleHarness.assertions[KEY uint256 id].bond uint256 val {
    bond_ghost[id] = val;
}

// Storage hook for nextAssertionId (top-level state variable)
hook Sload uint256 val OptimisticOracleHarness.nextAssertionId {
    require nextAssertionId_ghost == val;
}

hook Sstore OptimisticOracleHarness.nextAssertionId uint256 val {
    nextAssertionId_ghost = val;
}
