// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0 <0.9.0;

import {StakingOracle} from "../../packages/hardhat/contracts/01_Staking/StakingOracle.sol";
import {ORA} from "../../packages/hardhat/contracts/01_Staking/OracleToken.sol";
import {CertoraORA} from "./CertoraORA.sol";

contract StakingOracleHarness is StakingOracle {
    constructor() StakingOracle(address(0)) {}

    function certoraSetOracleToken(address token) external {
        oracleToken = ORA(payable(token));
    }

    function certoraSetTokenBalance(address account, uint256 amount) external {
        CertoraORA(address(oracleToken)).setBalance(account, amount);
    }

    function certoraSetTokenBalanceAndAllowance(address owner, uint256 amount) external {
        CertoraORA(address(oracleToken)).setBalance(owner, amount);
        CertoraORA(address(oracleToken)).setAllowance(owner, address(this), amount);
    }

    function certoraPrepareStake(address owner, uint256 amount) external {
        CertoraORA(address(oracleToken)).setBalance(address(this), 0);
        CertoraORA(address(oracleToken)).setBalance(owner, amount);
        CertoraORA(address(oracleToken)).setAllowance(owner, address(this), amount);
    }

    function certoraSeedSlashScenario(
        address node,
        uint256 stake,
        uint256 bucketNumber,
        uint256 reportedPrice,
        uint256 medianPrice
    ) external {
        delete nodeAddresses;
        delete blockBuckets[bucketNumber].reporters;
        delete blockBuckets[bucketNumber].prices;

        nodes[node] = OracleNode({
            stakedAmount: stake,
            lastReportedBucket: bucketNumber,
            reportCount: 1,
            claimedReportCount: 0,
            firstBucket: bucketNumber,
            active: true
        });
        nodeAddresses.push(node);

        BlockBucket storage bucket = blockBuckets[bucketNumber];
        bucket.reporters.push(node);
        bucket.prices.push(reportedPrice);
        bucket.medianPrice = medianPrice;
        bucket.slashedOffenses[node] = false;

        CertoraORA(address(oracleToken)).setBalance(address(this), stake);
    }

    function certoraSeedBucketReport(
        address node,
        uint256 bucketNumber,
        uint256 reportedPrice,
        uint256 medianPrice,
        bool slashed
    ) external {
        delete blockBuckets[bucketNumber].reporters;
        delete blockBuckets[bucketNumber].prices;

        BlockBucket storage bucket = blockBuckets[bucketNumber];
        bucket.reporters.push(node);
        bucket.prices.push(reportedPrice);
        bucket.medianPrice = medianPrice;
        bucket.slashedOffenses[node] = slashed;
    }

    function certoraSeedBucketReports3(
        uint256 bucketNumber,
        uint256 medianPrice,
        address reporter0,
        uint256 price0,
        bool slashed0,
        address reporter1,
        uint256 price1,
        bool slashed1,
        address reporter2,
        uint256 price2,
        bool slashed2
    ) external {
        delete blockBuckets[bucketNumber].reporters;
        delete blockBuckets[bucketNumber].prices;

        BlockBucket storage bucket = blockBuckets[bucketNumber];
        bucket.reporters.push(reporter0);
        bucket.prices.push(price0);
        bucket.slashedOffenses[reporter0] = slashed0;
        bucket.reporters.push(reporter1);
        bucket.prices.push(price1);
        bucket.slashedOffenses[reporter1] = slashed1;
        bucket.reporters.push(reporter2);
        bucket.prices.push(price2);
        bucket.slashedOffenses[reporter2] = slashed2;
        bucket.medianPrice = medianPrice;
    }

    function certoraSeedUnrecordedBucketReports3(
        uint256 bucketNumber,
        address reporter0,
        uint256 price0,
        address reporter1,
        uint256 price1,
        address reporter2,
        uint256 price2
    ) external {
        delete blockBuckets[bucketNumber].reporters;
        delete blockBuckets[bucketNumber].prices;

        BlockBucket storage bucket = blockBuckets[bucketNumber];
        bucket.reporters.push(reporter0);
        bucket.prices.push(price0);
        bucket.reporters.push(reporter1);
        bucket.prices.push(price1);
        bucket.reporters.push(reporter2);
        bucket.prices.push(price2);
        bucket.medianPrice = 0;
    }

    function certoraSeedNode(
        address node,
        uint256 stakedAmount,
        uint256 firstBucket,
        uint256 lastReportedBucket,
        uint256 reportCount,
        uint256 claimedReportCount,
        bool active
    ) external {
        nodes[node] = OracleNode({
            stakedAmount: stakedAmount,
            lastReportedBucket: lastReportedBucket,
            reportCount: reportCount,
            claimedReportCount: claimedReportCount,
            firstBucket: firstBucket,
            active: active
        });
    }

    function certoraTokenBalance(address account) external view returns (uint256) {
        return CertoraORA(address(oracleToken)).balanceOf(account);
    }

    function certoraOracleTokenBalance() external view returns (uint256) {
        return CertoraORA(address(oracleToken)).balanceOf(address(this));
    }

    function getNodeAddressesLength() external view returns (uint256) {
        return nodeAddresses.length;
    }

    function getNodeAddressAt(uint256 index) external view returns (address) {
        return nodeAddresses[index];
    }

    function getNodeStakedAmount(address node) external view returns (uint256) {
        return nodes[node].stakedAmount;
    }

    function getNodeLastReportedBucket(address node) external view returns (uint256) {
        return nodes[node].lastReportedBucket;
    }

    function getNodeReportCount(address node) external view returns (uint256) {
        return nodes[node].reportCount;
    }

    function getNodeClaimedReportCount(address node) external view returns (uint256) {
        return nodes[node].claimedReportCount;
    }

    function getNodeFirstBucket(address node) external view returns (uint256) {
        return nodes[node].firstBucket;
    }

    function getNodeActive(address node) external view returns (bool) {
        return nodes[node].active;
    }

    function getBucketReportersLength(uint256 bucketNumber) external view returns (uint256) {
        return blockBuckets[bucketNumber].reporters.length;
    }

    function getBucketPricesLength(uint256 bucketNumber) external view returns (uint256) {
        return blockBuckets[bucketNumber].prices.length;
    }

    function getBucketReporterAt(uint256 bucketNumber, uint256 index) external view returns (address) {
        return blockBuckets[bucketNumber].reporters[index];
    }

    function getBucketPriceAt(uint256 bucketNumber, uint256 index) external view returns (uint256) {
        return blockBuckets[bucketNumber].prices[index];
    }

    function getBucketMedian(uint256 bucketNumber) external view returns (uint256) {
        return blockBuckets[bucketNumber].medianPrice;
    }

    function getBucketSlashed(uint256 bucketNumber, address node) external view returns (bool) {
        return blockBuckets[bucketNumber].slashedOffenses[node];
    }

    function certoraGetOutlierNodesLength(uint256 bucketNumber) external view returns (uint256) {
        return getOutlierNodes(bucketNumber).length;
    }

    function certoraGetOutlierNodeAt(uint256 bucketNumber, uint256 index) external view returns (address) {
        return getOutlierNodes(bucketNumber)[index];
    }

    function certoraGetOutlierNodesLengthAndFirst(uint256 bucketNumber)
        external
        view
        returns (uint256 length, address first)
    {
        address[] memory outliers = getOutlierNodes(bucketNumber);
        if (outliers.length == 0) {
            return (0, address(0));
        }
        return (outliers.length, outliers[0]);
    }

    function checkPriceDeviatedHarness(uint256 reportedPrice, uint256 medianPrice) external pure returns (bool) {
        return _checkPriceDeviated(reportedPrice, medianPrice);
    }
}
