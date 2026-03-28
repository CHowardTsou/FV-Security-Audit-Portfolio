methods {
    function contributionOf(address) external returns(uint256) envfree;
    function contractBalance() external returns(uint256) envfree;
    function receiveForwarderAddress() external returns(address) envfree;
    function openToWithdraw() external returns(bool) envfree;
    function recipientCompleted() external returns(bool) envfree;
    function deadline() external returns(uint256) envfree;
    function thresholdValue() external returns(uint256) envfree;
    function timeLeft() external returns(uint256);
    function withdraw() external;
    function contribute() external;
    function execute() external;
    function sendEthToReceive() external returns(bool);
}

rule contributeHasEffect(env e) {
    storage before = lastStorage;
    contribute(e);
    storage after = lastStorage;

    satisfy(before[currentContract] != after[currentContract]);
}

rule withdrawHasEffect(env e) {
    require e.msg.value == 0;
    require openToWithdraw();

    storage before = lastStorage;
    withdraw(e);
    storage after = lastStorage;

    satisfy(before[currentContract] != after[currentContract]);
}

rule executeHasEffect(env e) {
    require e.msg.value == 0;
    require e.block.timestamp >= deadline();
    require !recipientCompleted();

    storage before = lastStorage;
    execute(e);
    storage after = lastStorage;

    satisfy(before[currentContract] != after[currentContract]);
}

rule nonViewFunctionCanSucceed(env e, method f, calldataarg args)
    filtered { f ->
        f.selector == sig:contribute().selector ||
        f.selector == sig:withdraw().selector ||
        f.selector == sig:execute().selector ||
        f.selector == sig:sendEthToReceive().selector
    }
{
    f@withrevert(e, args);
    satisfy(!lastReverted);
}

rule viewFunctionDoesNotChangeStorage(env e, method f, calldataarg args)
    filtered { f ->
        f.selector == sig:contributionOf(address).selector ||
        f.selector == sig:contractBalance().selector ||
        f.selector == sig:receiveForwarderAddress().selector ||
        f.selector == sig:openToWithdraw().selector ||
        f.selector == sig:recipientCompleted().selector ||
        f.selector == sig:deadline().selector ||
        f.selector == sig:thresholdValue().selector ||
        f.selector == sig:timeLeft().selector
    }
{
    storage before = lastStorage;
    f(e, args);

    assert before[currentContract] == lastStorage[currentContract];
}

rule revertRollsBackStorage(env e, method f, calldataarg args)
    filtered { f ->
        f.selector == sig:contribute().selector ||
        f.selector == sig:withdraw().selector ||
        f.selector == sig:execute().selector ||
        f.selector == sig:sendEthToReceive().selector
    }
{
    storage before = lastStorage;
    f@withrevert(e, args);

    assert lastReverted => before[currentContract] == lastStorage[currentContract];
}
