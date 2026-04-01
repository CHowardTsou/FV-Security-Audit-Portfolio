// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import "../../contracts/DEX.sol";

/// @dev Thin harness exposing scalar getters for Certora Prover.
///      No business logic changes — only view helpers added.
contract DEXHarness is DEX {
    constructor(address tokenAddr) DEX(tokenAddr) {}

    function getEthBalance() external view returns (uint256) {
        return address(this).balance;
    }

    function getTokenBalance() external view returns (uint256) {
        return token.balanceOf(address(this));
    }

    function getTokenAddress() external view returns (address) {
        return address(token);
    }

    function getLiquidityOf(address lp) external view returns (uint256) {
        return liquidity[lp];
    }
}
