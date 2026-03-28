pragma solidity 0.8.20;
// SPDX-License-Identifier: MIT

import "@openzeppelin/contracts/access/Ownable.sol";
import "./YourToken.sol";

contract Vendor is Ownable {
    /////////////////
    /// Errors //////
    /////////////////

    error InvalidEthAmount();
    error InsufficientVendorTokenBalance(uint256 available, uint256 required);
    error EthTransferFailed(address to, uint256 amount);
    error InvalidTokenAmount();
    error InsufficientVendorEthBalance(uint256 available, uint256 required);

    //////////////////////
    /// State Variables //
    //////////////////////

    YourToken public immutable yourToken;
    uint256 public constant tokensPerEth = 100;

    ////////////////
    /// Events /////
    ////////////////

    event BuyTokens(address indexed buyer, uint256 amountOfETH, uint256 amountOfTokens);
    event SellTokens(address indexed seller, uint256 amountOfTokens, uint256 amountOfETH);

    ///////////////////
    /// Constructor ///
    ///////////////////

    constructor(address tokenAddress) Ownable(msg.sender) {
        yourToken = YourToken(tokenAddress);
    }

    ///////////////////
    /// Functions /////
    ///////////////////

    function buyTokens() external payable {
        if (msg.value == 0) {
            revert InvalidEthAmount();
        }
        uint256 amountOfToken = msg.value * tokensPerEth;
        if (yourToken.balanceOf(address(this)) < amountOfToken) {
            revert InsufficientVendorTokenBalance(yourToken.balanceOf(address(this)), amountOfToken);
        }
        yourToken.transfer(msg.sender, amountOfToken);
        emit BuyTokens(msg.sender, msg.value, amountOfToken);
    }

    function withdraw() public onlyOwner {
        (bool success,) = payable(owner()).call{value: address(this).balance}("");
        if (!success) {
            revert EthTransferFailed(owner(), address(this).balance);
        }
    }

    function sellTokens(uint256 amount) public {
        if (amount == 0) {
            revert InvalidTokenAmount();
        }
        yourToken.transferFrom(msg.sender, address(this), amount);
        uint256 ethAmount = amount / tokensPerEth;
        if (address(this).balance < ethAmount) {
            revert InsufficientVendorEthBalance(address(this).balance, ethAmount);
        }
        (bool success,) = payable(msg.sender).call{value: ethAmount}("");
        if (!success) {
            revert EthTransferFailed(owner(), address(this).balance);
        }
        emit SellTokens(msg.sender, amount, ethAmount);
    }
}
