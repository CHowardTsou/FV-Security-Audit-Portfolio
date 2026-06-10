// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0 <0.9.0;

import "../../contracts/OptimisticOracle.sol";

contract OptimisticOracleHarness is OptimisticOracle {
    constructor(address _decider) OptimisticOracle(_decider) {}

    // Struct field getters for CVL access
    function getAsserter(uint256 assertionId) external view returns (address) {
        return assertions[assertionId].asserter;
    }

    function getProposer(uint256 assertionId) external view returns (address) {
        return assertions[assertionId].proposer;
    }

    function getDisputer(uint256 assertionId) external view returns (address) {
        return assertions[assertionId].disputer;
    }

    function getProposedOutcome(uint256 assertionId) external view returns (bool) {
        return assertions[assertionId].proposedOutcome;
    }

    function getResolvedOutcome(uint256 assertionId) external view returns (bool) {
        return assertions[assertionId].resolvedOutcome;
    }

    function getReward(uint256 assertionId) external view returns (uint256) {
        return assertions[assertionId].reward;
    }

    function getBond(uint256 assertionId) external view returns (uint256) {
        return assertions[assertionId].bond;
    }

    function getStartTime(uint256 assertionId) external view returns (uint256) {
        return assertions[assertionId].startTime;
    }

    function getEndTime(uint256 assertionId) external view returns (uint256) {
        return assertions[assertionId].endTime;
    }

    function getClaimed(uint256 assertionId) external view returns (bool) {
        return assertions[assertionId].claimed;
    }

    function getWinner(uint256 assertionId) external view returns (address) {
        return assertions[assertionId].winner;
    }

    function getDescription(uint256 assertionId) external view returns (string memory) {
        return assertions[assertionId].description;
    }

}
