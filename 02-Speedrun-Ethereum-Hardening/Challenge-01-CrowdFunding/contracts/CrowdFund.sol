// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import "./FundingRecipient.sol";

contract CrowdFund {
    /////////////////
    /// Errors //////
    /////////////////

    error NotOpenToWithdraw();
    error WithdrawTransferFailed(address to, uint256 amount);
    error TooEarly(uint256 deadline, uint256 currentTimestamp);
    error CrowdFundIsFinished();

    //////////////////////
    /// State Variables //
    //////////////////////

    FundingRecipient public fundingRecipient;
    mapping(address => uint256) public balances;
    bool public openToWithdraw;
    uint256 public deadline = block.timestamp + 1 hours;
    uint256 public constant threshold = 1 ether;

    ////////////////
    /// Events /////
    ////////////////

    event Contribution(address, uint256);

    ///////////////////
    /// Modifiers /////
    ///////////////////

    modifier notCompleted() {
        if (fundingRecipient.completed()) {
            revert CrowdFundIsFinished();
        }
        _;
    }

    ///////////////////
    /// Constructor ///
    ///////////////////

    constructor(address fundingRecipientAddress) {
        fundingRecipient = FundingRecipient(fundingRecipientAddress);
    }

    ///////////////////
    /// Functions /////
    ///////////////////

    function contribute() public payable notCompleted {
        if (timeLeft() == 0) {
            revert CrowdFundIsFinished();
        }
        balances[msg.sender] += msg.value;
        emit Contribution(msg.sender, msg.value);
    }

    function withdraw() public notCompleted {
        if (!openToWithdraw) {
            revert NotOpenToWithdraw();
        }
        uint256 amountToWithdraw = balances[msg.sender];
        balances[msg.sender] -= amountToWithdraw;
        (bool success,) = payable(msg.sender).call{value: amountToWithdraw}("");
        if (!success) {
            revert WithdrawTransferFailed(msg.sender, amountToWithdraw);
        }
    }

    function execute() public notCompleted {
        if (block.timestamp < deadline) {
            revert TooEarly(deadline, block.timestamp);
        }
        if (address(this).balance >= threshold) {
            fundingRecipient.complete{value: address(this).balance}();
        } else {
            openToWithdraw = true;
        }
    }

    receive() external payable {
        contribute();
    }

    ////////////////////////
    /// View Functions /////
    ////////////////////////

    function timeLeft() public view returns (uint256) {
        if (deadline > block.timestamp) {
            return deadline - block.timestamp;
        } else {
            return 0;
        }
    }
}
