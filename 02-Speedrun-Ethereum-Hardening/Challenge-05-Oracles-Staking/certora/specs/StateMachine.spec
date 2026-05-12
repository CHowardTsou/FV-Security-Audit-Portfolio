import "./setup/setup.spec";

rule inactiveNodeCannotReport(env e, uint256 price) {
    setup(e);
    require !getNodeActive(e.msg.sender);

    reportPrice@withrevert(e, price);

    assert lastReverted, "inactive node reported a price";
}

rule inactiveNodeCannotAddStake(env e, uint256 amount) {
    setup(e);
    require !getNodeActive(e.msg.sender);

    addStake@withrevert(e, amount);

    assert lastReverted, "inactive node added stake";
}

rule registeredNodeReportsAtMostOncePerBucket(env e, uint256 amount, uint256 price) {
    setupFundedNode(e, amount);
    require price > 0;
    require price < MAX_REASONABLE_PRICE();

    registerNode@withrevert(e, amount);
    require !lastReverted;
    reportPrice@withrevert(e, price);
    require !lastReverted;

    reportPrice@withrevert(e, price);

    assert lastReverted, "node reported twice in one bucket";
}

rule successfulReportUpdatesBucketAndCount(env e, uint256 amount, uint256 price) {
    setupFundedNode(e, amount);
    require price > 0;
    require price < MAX_REASONABLE_PRICE();

    registerNode@withrevert(e, amount);
    require !lastReverted;

    uint256 bucketBefore = getCurrentBucketNumber(e);
    uint256 reportCountBefore = getNodeReportCount(e.msg.sender);
    reportPrice@withrevert(e, price);
    assert !lastReverted, "funded active node should be able to report once";

    assert getNodeLastReportedBucket(e.msg.sender) == bucketBefore, "last reported bucket not updated";
    assert getNodeReportCount(e.msg.sender) == reportCountBefore + 1, "report count not incremented";
}

rule reportingInLaterBucketRequiresPriorMedian(env e1, env e2, uint256 amount, uint256 price) {
    setupFundedNode(e1, amount);
    require e2.msg.sender == e1.msg.sender;
    require price > 0;
    require price < MAX_REASONABLE_PRICE();
    require amount >= MINIMUM_STAKE() + 4 * INACTIVITY_PENALTY();

    registerNode@withrevert(e1, amount);
    require !lastReverted;
    reportPrice@withrevert(e1, price);
    require !lastReverted;

    require e2.block.number >= e1.block.number + BUCKET_WINDOW();
    require getBucketMedian(getNodeLastReportedBucket(e1.msg.sender)) == 0;

    reportPrice@withrevert(e2, price);

    assert lastReverted, "later report succeeded before previous bucket median was recorded";
}

rule recordBucketMedianRecordsSortedMedian(
    env e,
    uint256 bucketNumber,
    uint256 medianPrice,
    address reporter0,
    address reporter1
) {
    setup(e);
    require reporter0 != 0;
    require reporter1 != 0;
    require reporter0 != currentContract;
    require reporter1 != currentContract;
    require reporter0 != reporter1;
    require reporter0 != e.msg.sender;
    require reporter1 != e.msg.sender;
    require medianPrice > 1;
    require medianPrice < MAX_REASONABLE_PRICE();
    require bucketNumber < getCurrentBucketNumber(e);

    uint256 lowPrice = require_uint256(medianPrice - 1);
    uint256 highPrice = require_uint256(medianPrice + 1);
    certoraSeedUnrecordedBucketReports3(
        e, bucketNumber, reporter0, highPrice, reporter1, lowPrice, e.msg.sender, medianPrice
    );

    recordBucketMedian@withrevert(e, bucketNumber);

    assert !lastReverted, "past bucket median recording reverted";
    assert getBucketMedian(bucketNumber) == medianPrice, "recorded bucket median is not the sorted median";
}

rule recordBucketMedianRejectsCurrentAndFutureBuckets(env e, uint256 bucketNumber) {
    setup(e);
    require bucketNumber >= getCurrentBucketNumber(e);

    recordBucketMedian@withrevert(e, bucketNumber);

    assert lastReverted, "current or future bucket median was recorded";
}

rule slashMarksOffenseAndReducesStake(
    env e,
    address nodeToSlash,
    uint256 stake,
    uint256 bucketNumber,
    uint256 medianPrice
) {
    setup(e);
    require nodeToSlash != 0;
    require nodeToSlash != currentContract;
    require nodeToSlash != e.msg.sender;
    require bucketNumber < getCurrentBucketNumber(e);
    require medianPrice > 10;
    require medianPrice < MAX_REASONABLE_PRICE();
    require stake > MISREPORT_PENALTY();
    require stake < MAX_REASONABLE_PRICE();

    uint256 outlierPrice = require_uint256(medianPrice + medianPrice / 5);
    certoraSeedSlashScenario(e, nodeToSlash, stake, bucketNumber, outlierPrice, medianPrice);
    certoraSetTokenBalance(e, e.msg.sender, 0);

    slashNode@withrevert(e, nodeToSlash, bucketNumber, 0, 0);

    assert !lastReverted, "valid slash reverted";
    assert getBucketSlashed(bucketNumber, nodeToSlash), "slash did not mark the offense";
    assert getNodeStakedAmount(nodeToSlash) == stake - MISREPORT_PENALTY(), "slash did not reduce stake";
    assert getNodeActive(nodeToSlash), "partial slash deactivated node";
}

rule exitDeactivatesNode(env e1, env e2, uint256 amount) {
    setupFundedNode(e1, amount);
    require e2.msg.sender == e1.msg.sender;
    require amount >= MINIMUM_STAKE() + 4 * INACTIVITY_PENALTY();

    registerNode@withrevert(e1, amount);
    require !lastReverted;

    require e2.block.number >= e1.block.number + WAITING_PERIOD() * BUCKET_WINDOW();
    exitNode@withrevert(e2, 0);
    require !lastReverted;

    assert !getNodeActive(e1.msg.sender), "exited node remained active";
}
