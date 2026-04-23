// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0 <0.9.0;

import { WhitelistOracle } from "../../packages/hardhat/contracts/00_Whitelist/WhitelistOracle.sol";
import { SimpleOracle } from "../../packages/hardhat/contracts/00_Whitelist/SimpleOracle.sol";

/**
 * Harness exposing scalar + array-element getters over WhitelistOracle's
 * internal state. Inherits WhitelistOracle without touching source.
 */
contract WhitelistOracleHarness is WhitelistOracle {
    function getOraclesLength() external view returns (uint256) {
        return oracles.length;
    }

    function getOracleAt(uint256 i) external view returns (address) {
        return address(oracles[i]);
    }

    function getOraclePriceValueAt(uint256 i) external view returns (uint256) {
        return SimpleOracle(address(oracles[i])).price();
    }

    function getOracleTimestampAt(uint256 i) external view returns (uint256) {
        return SimpleOracle(address(oracles[i])).timestamp();
    }

    function getOracleOwnerAt(uint256 i) external view returns (address) {
        return SimpleOracle(address(oracles[i])).owner();
    }

    /**
     * Wrapper enforcing the EVM CREATE guarantee that Certora's symbolic
     * CREATE does not model: a newly-deployed contract address cannot collide
     * with any previously-deployed contract address. The post-call `require`
     * loop filters out the collision universe, making V-02 provable.
     *
     * See MODELING_DEBT.md V-02 entry and certora/FINDINGS.md F-002.
     */
    function addOracleUnique(address _owner) external {
        uint256 oldLen = oracles.length;
        addOracle(_owner);
        address tail = address(oracles[oldLen]);
        for (uint256 i = 0; i < oldLen; ++i) {
            require(address(oracles[i]) != tail, "CREATE cannot collide (EVM guarantee)");
        }
    }
}
