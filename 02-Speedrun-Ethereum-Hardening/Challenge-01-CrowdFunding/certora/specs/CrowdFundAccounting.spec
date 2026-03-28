methods {
    function contributionOf(address) external returns(uint256) envfree;
    function contractBalance() external returns(uint256) envfree;
    function receiveForwarderAddress() external returns(address) envfree;
    function openToWithdraw() external returns(bool) envfree;
    function recipientCompleted() external returns(bool) envfree;
    function deadline() external returns(uint256) envfree;
    function withdraw() external;
    function contribute() external;
    function sendEthToReceive() external returns(bool);
}

ghost mapping(address => mathint) shadowContribution {
    init_state axiom forall address a. shadowContribution[a] == 0;
}

ghost mathint trackedTotalContribution {
    init_state axiom trackedTotalContribution == 0;
}

hook Sstore balances[KEY address user] uint256 newValue (uint256 oldValue) {
    shadowContribution[user] = newValue;
    trackedTotalContribution = trackedTotalContribution + newValue - oldValue;
}

rule contributeIncreasesCallerBalanceByMsgValue(env e) {
    require e.block.timestamp < deadline();
    require !recipientCompleted();
    require e.msg.sender != currentContract;

    uint256 balanceBefore = contributionOf(e.msg.sender);
    uint256 contractBalanceBefore = contractBalance();
    mathint trackedTotalBefore = trackedTotalContribution;

    contribute(e);

    assert contributionOf(e.msg.sender) == balanceBefore + e.msg.value,
        "caller contribution should increase exactly by msg.value";
    assert contractBalance() == contractBalanceBefore + e.msg.value,
        "contract ETH balance should increase exactly by msg.value";
    assert shadowContribution[e.msg.sender] == to_mathint(contributionOf(e.msg.sender)),
        "ghost shadow should match the caller's recorded contribution after contribute";
    assert trackedTotalContribution == trackedTotalBefore + e.msg.value,
        "tracked total contribution should increase by msg.value on contribute";
}

rule receiveIncreasesCallerBalanceByMsgValue(env e) {
    require e.block.timestamp < deadline();
    require !recipientCompleted();

    address forwarder = receiveForwarderAddress();
    uint256 balanceBefore = contributionOf(forwarder);
    mathint trackedTotalBefore = trackedTotalContribution;
    require balanceBefore <= max_uint256 - e.msg.value;

    bool ok = sendEthToReceive(e);

    assert ok,
        "receive-path low-level call should succeed";
    assert contributionOf(forwarder) == balanceBefore + e.msg.value,
        "receive should credit the direct ETH sender exactly like contribute";
    assert shadowContribution[forwarder] == to_mathint(contributionOf(forwarder)),
        "ghost shadow should match the receive sender's recorded contribution";
    assert trackedTotalContribution == trackedTotalBefore + e.msg.value,
        "tracked total contribution should increase by msg.value on receive";
}

rule successfulWithdrawZerosRecordedBalance(env e) {
    require e.msg.value == 0;
    require openToWithdraw();
    require !recipientCompleted();
    require e.msg.sender != currentContract;

    uint256 balanceBefore = contributionOf(e.msg.sender);
    require balanceBefore > 0;

    withdraw@withrevert(e);
    bool withdrawSucceeded = !lastReverted;

    assert withdrawSucceeded => contributionOf(e.msg.sender) == 0,
        "successful withdraw must zero the user's recorded contribution";
}

rule withdrawCannotIncreaseRecordedBalance(env e) {
    require e.msg.value == 0;
    require openToWithdraw();
    require !recipientCompleted();
    require e.msg.sender != currentContract;

    uint256 balanceBefore = contributionOf(e.msg.sender);

    withdraw@withrevert(e);

    assert contributionOf(e.msg.sender) <= balanceBefore,
        "withdraw should never increase a recorded contribution";
}

rule contributeDoesNotChangeOtherUserBalance(env e, address otherUser) {
    require e.block.timestamp < deadline();
    require !recipientCompleted();
    require e.msg.sender != currentContract;
    require otherUser != e.msg.sender;

    uint256 otherBalanceBefore = contributionOf(otherUser);

    contribute(e);

    assert contributionOf(otherUser) == otherBalanceBefore,
        "contribute should not change another user's recorded contribution";
}

rule withdrawDoesNotChangeOtherUserBalance(env e, address otherUser) {
    require e.msg.value == 0;
    require openToWithdraw();
    require !recipientCompleted();
    require e.msg.sender != currentContract;
    require otherUser != e.msg.sender;

    uint256 otherBalanceBefore = contributionOf(otherUser);

    withdraw@withrevert(e);

    assert contributionOf(otherUser) == otherBalanceBefore,
        "withdraw should not change another user's recorded contribution";
}
