methods {
    function transfer(address, uint256) external returns (bool);
    function INITIAL_SUPPLY() external returns (uint256) envfree;
    function player() external returns (address) envfree;
    function balanceOf(address) external returns (uint256) envfree;
    function timeLock() external returns (uint256) envfree;
}

rule no_function_can_drain_player_before_timelock(env e, method f, calldataarg args) {
    // pre condition
    require player() == e.msg.sender;
    require INITIAL_SUPPLY() == balanceOf(player());
    uint256 balanceBefore = balanceOf(player());

    // call
    f(e, args);
    uint256 balanceAfter = balanceOf(player());

    // assert
    assert e.block.timestamp < timeLock() => balanceBefore == balanceAfter;
}
