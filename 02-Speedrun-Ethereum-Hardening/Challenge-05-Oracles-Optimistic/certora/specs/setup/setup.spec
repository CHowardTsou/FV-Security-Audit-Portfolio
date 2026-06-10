import "protocol/methods.spec";
import "protocol/storage_hooks.spec";
import "helper.spec";

function setup(env e) {
    require nextAssertionId_ghost >= 1;
    require e.block.timestamp > 0;
    require e.block.timestamp < max_uint256;
    require e.msg.value < max_uint256;
}

function setupValidState(env e) {
    setup(e);

    // if claimed, winner must be set
    uint256 id;
    require claimed_ghost[id] => winner_ghost[id] != 0;

    // if disputer set, proposer must be set
    require disputer_ghost[id] != 0 => proposer_ghost[id] != 0;

    // if winner set, must be proposer or disputer
    require winner_ghost[id] != 0 => (
        winner_ghost[id] == proposer_ghost[id] ||
        winner_ghost[id] == disputer_ghost[id]
    );

    // bond is 2x reward for created assertions
    require getAsserter(id) != 0 => getBond(id) == getReward(id) * 2;

    // time window sanity
    require getAsserter(id) != 0 => getStartTime(id) <= getEndTime(id);
}
