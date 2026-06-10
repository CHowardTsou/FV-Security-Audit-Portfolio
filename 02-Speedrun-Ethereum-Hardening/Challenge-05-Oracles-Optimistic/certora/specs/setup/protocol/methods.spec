methods {
    function nextAssertionId() external returns (uint256) envfree;
    function decider() external returns (address) envfree;
    function owner() external returns (address) envfree;

    function getAsserter(uint256) external returns (address) envfree;
    function getProposer(uint256) external returns (address) envfree;
    function getDisputer(uint256) external returns (address) envfree;
    function getProposedOutcome(uint256) external returns (bool) envfree;
    function getResolvedOutcome(uint256) external returns (bool) envfree;
    function getReward(uint256) external returns (uint256) envfree;
    function getBond(uint256) external returns (uint256) envfree;
    function getStartTime(uint256) external returns (uint256) envfree;
    function getEndTime(uint256) external returns (uint256) envfree;
    function getClaimed(uint256) external returns (bool) envfree;
    function getWinner(uint256) external returns (address) envfree;

    function setDecider(address) external;
    function assertEvent(string, uint256, uint256) external returns (uint256);
    function proposeOutcome(uint256, bool) external;
    function disputeOutcome(uint256) external;
    function claimUndisputedReward(uint256) external;
    function claimDisputedReward(uint256) external;
    function claimRefund(uint256) external;
    function settleAssertion(uint256, bool) external;

    function getState(uint256) external returns (uint8);
    function getResolution(uint256) external returns (bool);
}
