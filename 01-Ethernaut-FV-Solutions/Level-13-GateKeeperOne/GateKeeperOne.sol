// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @notice This contract is modified for use with the Certora Prover.
 * * METHODOLOGY:
 * 1. Gate One (tx.origin) and Gate Two (gasleft) are removed as they rely on
 * environment/gas variables that are not suitable for static SMT solvers.
 * 2. Gate Three is converted from a modifier into a public function to allow
 * the Certora Prover to treat it as a constraint-solving problem.
 */
contract GateKeeperOne {
    /**
     * @dev Ported from modifier gateThree.
     * We use this function to solve for the 'bytes8 _gateKey' that satisfies
     * the complex bitwise constraints.
     */
    function gateThree(bytes8 _gateKey) external view returns (bool) {
        require(uint32(uint64(_gateKey)) == uint16(uint64(_gateKey)), "invalid gateThree part one");
        require(uint32(uint64(_gateKey)) != uint64(_gateKey), "invalid gateThree part two");
        require(uint32(uint64(_gateKey)) == uint16(uint160(msg.sender)), "invalid gateThree part three");
        return true;
    }

    /* // GATE ONE: Standard tx.origin != msg.sender check (Solved via Proxy)
    modifier gateOne() {
        require(msg.sender != tx.origin);
        _;
    }

    // GATE TWO: Exact Gas check (Solved via brute force/debugging)
    // Removed: gasleft() is a runtime environment variable not modeled by SMT.
    modifier gateTwo() {
        require(gasleft() % 8191 == 0);
        _;
    }
    */
}
