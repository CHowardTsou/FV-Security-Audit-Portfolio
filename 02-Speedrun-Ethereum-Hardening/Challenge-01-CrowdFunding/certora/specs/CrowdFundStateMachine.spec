methods {
    function contractBalance() external returns(uint256) envfree;
    function recipientBalance() external returns(uint256) envfree;
    function recipientCompleted() external returns(bool) envfree;
    function openToWithdraw() external returns(bool) envfree;
    function deadline() external returns(uint256) envfree;
    function thresholdValue() external returns(uint256) envfree;
    function execute() external;
    function contribute() external;
    function withdraw() external;
}

rule deadlineIsImmutable(env e, method f, calldataarg args) {
    require e.msg.value == 0;

    uint256 before = deadline();
    f(e, args);
    assert deadline() == before,
        "deadline should never change after construction";
}

rule openToWithdrawIsSticky(env e, method f, calldataarg args) {
    require e.msg.value == 0;

    bool before = openToWithdraw();
    f(e, args);
    assert before => openToWithdraw(),
        "openToWithdraw should never flip from true back to false";
}

rule executeBeforeDeadlineReverts(env e) {
    require e.msg.value == 0;
    require e.block.timestamp < deadline();
    require !recipientCompleted();

    execute@withrevert(e);

    assert lastReverted,
        "execute must revert before the deadline";
}

rule executeBelowThresholdOpensWithdraw(env e) {
    require e.msg.value == 0;
    require e.block.timestamp >= deadline();
    require !recipientCompleted();
    require contractBalance() < thresholdValue();

    execute@withrevert(e);

    assert !lastReverted,
        "execute should not revert after the deadline in the failed-funding branch";
    assert openToWithdraw(),
        "failed funding should open withdrawals";
}

rule executeAtOrAboveThresholdCompletesAndDrains(env e) {
    require e.msg.value == 0;
    require e.block.timestamp >= deadline();
    require !recipientCompleted();
    require contractBalance() >= thresholdValue();

    uint256 recipientBalanceBefore = recipientBalance();
    uint256 contractBalanceBefore = contractBalance();
    require recipientBalanceBefore <= max_uint256 - contractBalanceBefore;

    execute@withrevert(e);

    assert !lastReverted,
        "execute should not revert after the deadline in the success branch";
    assert contractBalance() == 0,
        "successful funding should drain the crowdfund balance";
    assert recipientBalance() == recipientBalanceBefore + contractBalanceBefore,
        "successful funding should transfer the full crowdfund balance to the recipient";
}

rule failedExecuteKeepsWithdrawalsOpen(env e) {
    require e.msg.value == 0;
    require e.block.timestamp >= deadline();
    require !recipientCompleted();
    require contractBalance() < thresholdValue();

    execute@withrevert(e);
    require !lastReverted;
    require openToWithdraw();

    execute@withrevert(e);

    assert !lastReverted,
        "repeated execute in the failed branch should not revert";
    assert openToWithdraw(),
        "once failed execution opens withdrawals, they should remain open";
    assert !recipientCompleted(),
        "failed execution should never complete the recipient";
}

rule contributeRevertsAfterCompletion(env e) {
    require e.msg.sender != currentContract;
    require e.block.timestamp >= deadline();
    require !recipientCompleted();
    require contractBalance() >= thresholdValue();

    uint256 recipientBalanceBefore = recipientBalance();
    uint256 contractBalanceBefore = contractBalance();
    require recipientBalanceBefore <= max_uint256 - contractBalanceBefore;

    execute@withrevert(e);
    require !lastReverted;
    require recipientCompleted();

    contribute@withrevert(e);
    assert lastReverted,
        "contribute should revert after funding is completed";
}

rule withdrawRevertsAfterCompletion(env e) {
    require e.msg.value == 0;
    require e.msg.sender != currentContract;
    require e.block.timestamp >= deadline();
    require !recipientCompleted();
    require contractBalance() >= thresholdValue();

    uint256 recipientBalanceBefore = recipientBalance();
    uint256 contractBalanceBefore = contractBalance();
    require recipientBalanceBefore <= max_uint256 - contractBalanceBefore;

    execute@withrevert(e);
    require !lastReverted;
    require recipientCompleted();

    withdraw@withrevert(e);
    assert lastReverted,
        "withdraw should revert after funding is completed";
}

rule executeRevertsAfterCompletion(env e) {
    require e.msg.value == 0;
    require e.block.timestamp >= deadline();
    require !recipientCompleted();
    require contractBalance() >= thresholdValue();

    uint256 recipientBalanceBefore = recipientBalance();
    uint256 contractBalanceBefore = contractBalance();
    require recipientBalanceBefore <= max_uint256 - contractBalanceBefore;

    execute@withrevert(e);
    require !lastReverted;
    require recipientCompleted();

    execute@withrevert(e);
    assert lastReverted,
        "execute should revert after funding is completed";
}
