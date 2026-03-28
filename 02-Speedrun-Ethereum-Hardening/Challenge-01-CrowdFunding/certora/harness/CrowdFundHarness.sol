// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import "../../contracts/CrowdFund.sol";
import "../../contracts/FundingRecipient.sol";

contract ReceiveForwarder {
    receive() external payable {}

    function send(address target) external payable returns (bool success) {
        (success,) = target.call{value: msg.value}("");
    }
}

contract CrowdFundHarness is CrowdFund {
    ReceiveForwarder public receiveForwarder;

    constructor() CrowdFund(address(new FundingRecipient())) {
        receiveForwarder = new ReceiveForwarder();
    }

    function contributionOf(address user) external view returns (uint256) {
        return balances[user];
    }

    function contractBalance() external view returns (uint256) {
        return address(this).balance;
    }

    function recipientBalance() external view returns (uint256) {
        return address(fundingRecipient).balance;
    }

    function recipientCompleted() external view returns (bool) {
        return fundingRecipient.completed();
    }

    function thresholdValue() external pure returns (uint256) {
        return threshold;
    }

    function receiveForwarderAddress() external view returns (address) {
        return address(receiveForwarder);
    }

    function sendEthToReceive() external payable returns (bool success) {
        success = receiveForwarder.send{value: msg.value}(address(this));
    }
}
