methods {
    function goTo(uint256) external;
    function top() external returns (bool) envfree;
    function floor() external returns (uint256) envfree;
    function _.isLastFloor(uint256) external => flip_logic() expect(bool);
}

ghost bool g_secondcall {
    init_state axiom g_secondcall == false;
}

/**
 * This helper logic defines the behavior of our summary:
 * 1. If it's the first call: return false, set ghost to true.
 * 2. If it's the second call: return true.
 */
function flip_logic() returns bool {
    if (!g_secondcall) {
        g_secondcall = true;
        return false;
    } else {
        return true;
    }
}

rule can_not_reach_the_top(env e) {
    uint256 floor;
    bool beforeGoTo = top();
    require beforeGoTo == false;

    goTo(e, floor);

    bool afterGoto = top();

    assert afterGoto == beforeGoTo;
}
