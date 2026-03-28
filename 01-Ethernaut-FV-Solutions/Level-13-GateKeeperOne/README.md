# Ethernaut Level 13: Gatekeeper One — Automated Exploit Generation

## 📋 Overview
Gatekeeper One is a multi-stage access control challenge. While Gate 1 (`msg.sender` vs `tx.origin`) and Gate 2 (`gasleft()`) are traditional EVM puzzles, **Gate 3** involves complex bitwise constraints that must be satisfied simultaneously to unlock the contract.

## 🛠 Methodology: Constraint Solving via Certora
Instead of manually calculating the bit-masks for the `gateKey`, I utilized the **Certora Prover** to solve the mathematical constraints.

### 1. Logic Isolation
I ported the `gateThree` modifier logic into a standalone function. This allows the Prover to focus exclusively on the bitwise requirements of the `bytes8` key.

### 2. The Specification (CVL)
I defined a "Negative Rule." By asserting that the function **always reverts**, I forced the Prover to search for any input that could successfully pass the requirements.

* **Rule**: `gatethreereturn`
* **Objective**: Find a `bytes8 gatekey` such that the function does NOT revert for a specific `msg.sender`.
* **Result**: ❌ **Violation Found (Exploit Discovered).**
    * The Prover identified a specific counter-example for the `gatekey`.
    * This value satisfies all three conditions:
        1. `uint32(key) == uint16(key)`
        2. `uint32(key) != uint64(key)`
        3. `uint32(key) == uint16(uint160(tx.origin))`

---

## 📊 Findings Summary

| Gate       | Logic Type      | Discovery Method       | Result                      |
| :--------- | :-------------- | :--------------------- | :-------------------------- |
| **Gate 1** | Authorization   | Manual Review          | `tx.origin` bypass          |
| **Gate 2** | Gas Targeting   | Brute Force / Debugger | 8191 Gas modulo             |
| **Gate 3** | Bitwise Masking | **Certora (FV)**       | **Automated Key Discovery** |



---

## 💡 Lessons Learned
1. **FV as a Solver**: Formal Verification tools are not just for defense; they are powerful engines for solving complex logical constraints that would be tedious to calculate manually.
2. **Bit-masking Risks**: This level demonstrates how bitwise logic can be used to create complex identity checks, but also how those checks can be systematically solved if the constraints are public.

> **[🔗 View Interactive Certora Report](https://prover.certora.com/output/6854102/3b60adcf1a9a4a7284b89abd7f22fadd?anonymousKey=b0ad538c653f39a1609d1267b103c23051d9b53a)**
> *In the report, look at the "Counter-example" section to see the solved `gatekey` for the tested address.*