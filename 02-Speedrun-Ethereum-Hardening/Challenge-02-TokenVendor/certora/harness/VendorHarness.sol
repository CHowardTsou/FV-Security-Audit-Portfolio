// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import "../../contracts/Vendor.sol";

/// @notice Thin harness for Certora verification.
/// Inherits Vendor so all functions are directly available.
/// Adds view helpers that CVL specs need to read state.
contract VendorHarness is Vendor {
    constructor(address tokenAddress) Vendor(tokenAddress) {}

    function getVendorTokenBalance() external view returns (uint256) {
        return yourToken.balanceOf(address(this));
    }

    function getVendorEthBalance() external view returns (uint256) {
        return address(this).balance;
    }

    function getTokenAddress() external view returns (address) {
        return address(yourToken);
    }
}
