import "./setup/setup.spec";

rule inactiveEffectiveStakeIsZero(env e, address node) {
    setup(e);
    require !getNodeActive(node);

    assert getEffectiveStake(e, node) == 0, "inactive node has nonzero effective stake";
}

rule effectiveStakeMatchesMissedBucketFormula(
    env e,
    address node,
    uint256 stake,
    uint256 firstBucket,
    uint256 lastReportedBucket,
    uint256 reportCount
) {
    setup(e);
    require node != 0;
    require stake < MAX_REASONABLE_PRICE();
    require firstBucket > 0;
    require firstBucket < getCurrentBucketNumber(e);
    require lastReportedBucket <= getCurrentBucketNumber(e);
    require reportCount < MAX_REASONABLE_PRICE();

    certoraSeedNode(e, node, stake, firstBucket, lastReportedBucket, reportCount, 0, true);

    mathint expectedReports = getCurrentBucketNumber(e) - firstBucket;
    mathint actualCompleted = reportCount;
    if (lastReportedBucket == getCurrentBucketNumber(e) && reportCount > 0) {
        actualCompleted = reportCount - 1;
    }

    if (actualCompleted >= expectedReports) {
        assert getEffectiveStake(e, node) == stake, "effective stake should equal stake when no buckets are missed";
    } else {
        mathint missedBuckets = expectedReports - actualCompleted;
        mathint penalty = missedBuckets * INACTIVITY_PENALTY();
        if (penalty > stake) {
            assert getEffectiveStake(e, node) == 0, "effective stake should floor at zero";
        } else {
            assert getEffectiveStake(e, node) == require_uint256(stake - penalty), "effective stake formula mismatch";
        }
    }
}

rule effectiveStakeReportsBeyondExpectedReturnsStake(
    env e,
    address node,
    uint256 stake,
    uint256 firstBucket,
    uint256 reportCount
) {
    setup(e);
    require node != 0;
    require stake < MAX_REASONABLE_PRICE();
    require firstBucket > 0;
    require firstBucket < getCurrentBucketNumber(e);
    require reportCount < MAX_REASONABLE_PRICE();

    mathint expectedReports = getCurrentBucketNumber(e) - firstBucket;
    require reportCount > expectedReports;

    certoraSeedNode(e, node, stake, firstBucket, 0, reportCount, 0, true);

    getEffectiveStake@withrevert(e, node);

    assert !lastReverted, "effective stake reverted when completed reports exceed expected reports";
    assert getEffectiveStake(e, node) == stake, "extra completed reports should keep full effective stake";
}

rule currentBucketFormula(env e) {
    setup(e);

    assert getCurrentBucketNumber(e) == e.block.number / BUCKET_WINDOW() + 1, "current bucket formula changed";
}

rule exactTenPercentDeviationIsNotSlashable(uint256 medianPrice) {
    require medianPrice > 0;
    require medianPrice < MAX_REASONABLE_PRICE();

    assert !checkPriceDeviatedHarness(require_uint256(medianPrice + medianPrice / 10), medianPrice),
        "exact positive 10 percent deviation is slashable";
    assert !checkPriceDeviatedHarness(require_uint256(medianPrice - medianPrice / 10), medianPrice),
        "exact negative 10 percent deviation is slashable";
}

rule greaterThanTenPercentDeviationIsSlashable(uint256 medianPrice) {
    require medianPrice > 10;
    require medianPrice < MAX_REASONABLE_PRICE();

    assert checkPriceDeviatedHarness(require_uint256(medianPrice + medianPrice / 5), medianPrice),
        "greater than positive 10 percent deviation is not slashable";
}

rule getPastPriceRevertsWhenMedianMissing(env e, uint256 bucketNumber) {
    setup(e);
    require getBucketMedian(bucketNumber) == 0;

    getPastPrice@withrevert(e, bucketNumber);

    assert lastReverted, "getPastPrice succeeded without recorded median";
}

rule getPastPriceReturnsRecordedMedian(env e, uint256 bucketNumber, uint256 medianPrice) {
    setup(e);
    require medianPrice > 0;
    require medianPrice < MAX_REASONABLE_PRICE();

    certoraSeedBucketReport(e, e.msg.sender, bucketNumber, medianPrice, medianPrice, false);

    assert getPastPrice(e, bucketNumber) == medianPrice, "getPastPrice did not return recorded median";
}

rule getLatestPriceRevertsWhenLatestMedianMissing(env e) {
    setup(e);
    require getCurrentBucketNumber(e) > 0;
    uint256 latestBucket = require_uint256(getCurrentBucketNumber(e) - 1);
    require getBucketMedian(latestBucket) == 0;

    getLatestPrice@withrevert(e);

    assert lastReverted, "getLatestPrice succeeded without latest bucket median";
}

rule getLatestPriceReturnsLatestRecordedMedian(env e, uint256 medianPrice) {
    setup(e);
    require getCurrentBucketNumber(e) > 0;
    require medianPrice > 0;
    require medianPrice < MAX_REASONABLE_PRICE();
    uint256 latestBucket = require_uint256(getCurrentBucketNumber(e) - 1);

    certoraSeedBucketReport(e, e.msg.sender, latestBucket, medianPrice, medianPrice, false);

    assert getLatestPrice(e) == medianPrice, "getLatestPrice did not return latest recorded median";
}

rule getOutlierNodesIncludesUnslashedDeviatedReporter(env e, uint256 bucketNumber, uint256 medianPrice) {
    setup(e);
    require medianPrice > 10;
    require medianPrice < MAX_REASONABLE_PRICE();

    uint256 reportedPrice = require_uint256(medianPrice + medianPrice / 5);
    certoraSeedBucketReport(e, e.msg.sender, bucketNumber, reportedPrice, medianPrice, false);

    assert certoraGetOutlierNodesLength(bucketNumber) == 1, "deviated unslashed reporter was excluded";
    assert certoraGetOutlierNodeAt(bucketNumber, 0) == e.msg.sender, "outlier reporter mismatch";
}

rule getOutlierNodesExcludesNonDeviatedReporter(env e, uint256 bucketNumber, uint256 medianPrice) {
    setup(e);
    require medianPrice > 0;
    require medianPrice < MAX_REASONABLE_PRICE();

    uint256 reportedPrice = require_uint256(medianPrice + medianPrice / 10);
    certoraSeedBucketReport(e, e.msg.sender, bucketNumber, reportedPrice, medianPrice, false);

    assert certoraGetOutlierNodesLength(bucketNumber) == 0, "non-deviated reporter was included";
}

rule getOutlierNodesExcludesAlreadySlashedReporter(env e, uint256 bucketNumber, uint256 medianPrice) {
    setup(e);
    require medianPrice > 10;
    require medianPrice < MAX_REASONABLE_PRICE();

    uint256 reportedPrice = require_uint256(medianPrice + medianPrice / 5);
    certoraSeedBucketReport(e, e.msg.sender, bucketNumber, reportedPrice, medianPrice, true);

    assert certoraGetOutlierNodesLength(bucketNumber) == 0, "already slashed reporter was included";
}

rule getOutlierNodesFiltersMixedThreeReporterBucket(
    env e,
    uint256 bucketNumber,
    uint256 medianPrice,
    address nearReporter,
    address slashedReporter
) {
    setup(e);
    require nearReporter != 0;
    require slashedReporter != 0;
    require nearReporter != currentContract;
    require slashedReporter != currentContract;
    require nearReporter != e.msg.sender;
    require slashedReporter != e.msg.sender;
    require nearReporter != slashedReporter;
    require medianPrice > 10;
    require medianPrice < MAX_REASONABLE_PRICE();

    uint256 nearPrice = require_uint256(medianPrice + medianPrice / 10);
    uint256 outlierPrice = require_uint256(medianPrice + medianPrice / 5);
    certoraSeedBucketReports3(
        e,
        bucketNumber,
        medianPrice,
        nearReporter,
        nearPrice,
        false,
        e.msg.sender,
        outlierPrice,
        false,
        slashedReporter,
        outlierPrice,
        true
    );

    certoraGetOutlierNodesLength@withrevert(e, bucketNumber);
    assert !lastReverted, "mixed outlier query reverted";
    assert certoraGetOutlierNodesLength(bucketNumber) == 1, "mixed outlier bucket returned wrong count";
    assert certoraGetOutlierNodeAt(bucketNumber, 0) == e.msg.sender, "mixed outlier bucket returned wrong node";
}

rule getOutlierNodesRevertsWhenMedianMissing(env e, uint256 bucketNumber) {
    setup(e);
    require getBucketMedian(bucketNumber) == 0;

    certoraGetOutlierNodesLength@withrevert(e, bucketNumber);

    assert lastReverted, "getOutlierNodes succeeded without recorded median";
}
