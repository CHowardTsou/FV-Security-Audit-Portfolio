methods {
    function balanceOf(address) external returns (uint256) envfree;
    function transfer(address, uint256) external returns (bool);
    function totalSupply() external returns (uint256) envfree;
}

ghost mathint g_total_sum_of_balance {
    init_state axiom g_total_sum_of_balance == 100000;
}

hook Sstore balances[KEY address account] uint256 newVal (uint256 oldVal) {
    g_total_sum_of_balance = g_total_sum_of_balance + newVal - oldVal;
}

rule balance_integrity_after_transfer(env e) {
    address to;
    uint256 amount;

    // pre-condition
    uint256 userBalance = balanceOf(e.msg.sender);
    require userBalance == 20; // user start at 20 tokens
    require to != e.msg.sender;
    // calls

    transfer(e, to, amount);

    // assert
    assert amount > 0 => balanceOf(e.msg.sender) < 20;
}

rule total_sum_of_balance_is_constant(env e) {
    address to;
    uint256 amount;

    // pre-condition
    mathint sumBefore = g_total_sum_of_balance;

    // calls
    transfer(e, to, amount);

    mathint sumAfter = g_total_sum_of_balance;

    // assert
    assert amount > 0 => sumAfter == sumBefore;
}
