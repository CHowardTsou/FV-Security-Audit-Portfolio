import "./setup/setup.spec";

rule registerEscrowsExactStake(env e, uint256 amount) {
    setupFundedNode(e, amount);

    uint256 contractBalanceBefore = certoraOracleTokenBalance();
    registerNode@withrevert(e, amount);
    assert !lastReverted, "funded registration reverted";

    assert getNodeStakedAmount(e.msg.sender) == amount, "registered stake mismatch";
    assert certoraOracleTokenBalance() == contractBalanceBefore + amount, "stake was not escrowed";
}

rule addStakeIncreasesStoredStakeAndEscrow(env e, uint256 amount, uint256 addAmount) {
    setupFundedNode(e, amount);
    require amount >= MINIMUM_STAKE();
    require addAmount > 0;
    require addAmount < MAX_REASONABLE_PRICE();

    registerNode@withrevert(e, amount);
    require !lastReverted;
    certoraSetTokenBalanceAndAllowance(e, e.msg.sender, addAmount);

    uint256 stakeBefore = getNodeStakedAmount(e.msg.sender);
    uint256 contractBalanceBefore = certoraOracleTokenBalance();
    addStake@withrevert(e, addAmount);
    assert !lastReverted, "funded addStake reverted";

    assert getNodeStakedAmount(e.msg.sender) == stakeBefore + addAmount, "stake did not increase by amount";
    assert certoraOracleTokenBalance() == contractBalanceBefore + addAmount, "added stake was not escrowed";
}

rule claimRewardMintsUnclaimedReports(env e, uint256 amount, uint256 price) {
    setupFundedNode(e, amount);
    require price > 0;
    require price < MAX_REASONABLE_PRICE();

    registerNode@withrevert(e, amount);
    require !lastReverted;
    reportPrice@withrevert(e, price);
    require !lastReverted;

    uint256 balanceBefore = certoraTokenBalance(e.msg.sender);
    uint256 claimedBefore = getNodeClaimedReportCount(e.msg.sender);
    uint256 reportCountBefore = getNodeReportCount(e.msg.sender);
    claimReward@withrevert(e);
    assert !lastReverted, "claimReward reverted despite unclaimed report";

    assert certoraTokenBalance(e.msg.sender) == balanceBefore + REWARD_PER_REPORT(), "incorrect reward minted";
    assert getNodeClaimedReportCount(e.msg.sender) == reportCountBefore, "claimed count not updated";
    assert claimedBefore + 1 == reportCountBefore, "test setup expected one unclaimed report";
}

rule exitPaysAtMostEffectiveStake(env e1, env e2, uint256 amount) {
    setupFundedNode(e1, amount);
    require e2.msg.sender == e1.msg.sender;
    require amount >= MINIMUM_STAKE() + 4 * INACTIVITY_PENALTY();

    registerNode@withrevert(e1, amount);
    require !lastReverted;

    require e2.block.number >= e1.block.number + WAITING_PERIOD() * BUCKET_WINDOW();
    uint256 effectiveStakeBefore = getEffectiveStake(e2, e1.msg.sender);
    uint256 balanceBefore = certoraTokenBalance(e1.msg.sender);
    exitNode@withrevert(e2, 0);
    require !lastReverted;

    assert certoraTokenBalance(e1.msg.sender) <= balanceBefore + effectiveStakeBefore, "exit overpaid effective stake";
    assert getNodeStakedAmount(e1.msg.sender) == 0, "exited node retained stored stake";
}

rule exitBeforeWaitingPeriodReverts(env e1, env e2, uint256 amount, uint256 price) {
    setupFundedNode(e1, amount);
    require e2.msg.sender == e1.msg.sender;
    require amount >= MINIMUM_STAKE() + 4 * INACTIVITY_PENALTY();
    require price > 0;
    require price < MAX_REASONABLE_PRICE();

    registerNode@withrevert(e1, amount);
    require !lastReverted;
    reportPrice@withrevert(e1, price);
    require !lastReverted;

    uint256 reportedBucket = getNodeLastReportedBucket(e1.msg.sender);
    require e2.block.number >= e1.block.number;
    require getCurrentBucketNumber(e2) < reportedBucket + WAITING_PERIOD();

    exitNode@withrevert(e2, 0);

    assert lastReverted, "node exited before waiting period elapsed";
}

rule slashNodeReducesStakeAndPaysReward(env e, address nodeToSlash, uint256 stake, uint256 bucketNumber, uint256 medianPrice) {
    setup(e);
    require nodeToSlash != 0;
    require nodeToSlash != currentContract;
    require nodeToSlash != e.msg.sender;
    require medianPrice > 10;
    require medianPrice < MAX_REASONABLE_PRICE();
    require stake > MISREPORT_PENALTY();
    require stake < MAX_REASONABLE_PRICE();
    require bucketNumber > 0;
    require bucketNumber < getCurrentBucketNumber(e);

    uint256 reportedPrice = require_uint256(medianPrice + medianPrice / 5);

    certoraSeedSlashScenario(e, nodeToSlash, stake, bucketNumber, reportedPrice, medianPrice);
    certoraSetTokenBalance(e, e.msg.sender, 0);
    uint256 slasherBalanceBefore = certoraTokenBalance(e.msg.sender);
    slashNode@withrevert(e, nodeToSlash, bucketNumber, 0, 0);
    assert !lastReverted, "deviated node was not slashable";

    uint256 expectedReward = require_uint256(MISREPORT_PENALTY() * SLASHER_REWARD_PERCENTAGE() / 100);
    assert getNodeStakedAmount(nodeToSlash) == stake - MISREPORT_PENALTY(), "slash did not deduct penalty";
    assert certoraTokenBalance(e.msg.sender) == slasherBalanceBefore + expectedReward, "slasher reward mismatch";
    assert getBucketSlashed(bucketNumber, nodeToSlash), "slash flag not set";
}
