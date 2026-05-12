methods {
    function MINIMUM_STAKE() external returns (uint256) envfree;
    function BUCKET_WINDOW() external returns (uint256) envfree;
    function SLASHER_REWARD_PERCENTAGE() external returns (uint256) envfree;
    function REWARD_PER_REPORT() external returns (uint256) envfree;
    function INACTIVITY_PENALTY() external returns (uint256) envfree;
    function MISREPORT_PENALTY() external returns (uint256) envfree;
    function MAX_DEVIATION_BPS() external returns (uint256) envfree;
    function WAITING_PERIOD() external returns (uint256) envfree;

    function getCurrentBucketNumber() external returns (uint256);
    function getEffectiveStake(address) external returns (uint256);
    function getLatestPrice() external returns (uint256);
    function getPastPrice(uint256) external returns (uint256) envfree;
    function getNodeAddressesLength() external returns (uint256) envfree;
    function getNodeAddressAt(uint256) external returns (address) envfree;
    function getNodeStakedAmount(address) external returns (uint256) envfree;
    function getNodeLastReportedBucket(address) external returns (uint256) envfree;
    function getNodeReportCount(address) external returns (uint256) envfree;
    function getNodeClaimedReportCount(address) external returns (uint256) envfree;
    function getNodeFirstBucket(address) external returns (uint256) envfree;
    function getNodeActive(address) external returns (bool) envfree;
    function getBucketReportersLength(uint256) external returns (uint256) envfree;
    function getBucketPricesLength(uint256) external returns (uint256) envfree;
    function getBucketReporterAt(uint256,uint256) external returns (address) envfree;
    function getBucketPriceAt(uint256,uint256) external returns (uint256) envfree;
    function getBucketMedian(uint256) external returns (uint256) envfree;
    function getBucketSlashed(uint256,address) external returns (bool) envfree;
    function certoraGetOutlierNodesLength(uint256) external returns (uint256) envfree;
    function certoraGetOutlierNodeAt(uint256,uint256) external returns (address) envfree;
    function certoraGetOutlierNodesLengthAndFirst(uint256) external returns (uint256,address) envfree;
    function checkPriceDeviatedHarness(uint256,uint256) external returns (bool) envfree;
    function certoraTokenBalance(address) external returns (uint256) envfree;
    function certoraOracleTokenBalance() external returns (uint256) envfree;
}
