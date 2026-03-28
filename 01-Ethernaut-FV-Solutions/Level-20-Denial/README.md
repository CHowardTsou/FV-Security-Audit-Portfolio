# Ethernaut Level 20: Denial — Denial of Service via Gas Exhaustion

## 📋 Overview
The **Denial** level demonstrates a vulnerability where a contract's core functionality can be "brickable" by a malicious participant. By exploiting a low-level `.call` that does not cap gas, a recipient can consume the entire transaction's gas limit, preventing subsequent code from executing.

## 🔍 The Vulnerability
The `withdraw()` function performs a raw call to the `partner` address before sending funds to the `owner`:
```solidity
partner.call{value:amountToSend}("");
payable(owner).transfer(amountToSend);
```
If `partner` is a contract with a `receive()` function that enters an infinite loop or consumes 63/64ths of the remaining gas, the `transfer` to the owner will fail due to `Out of Gas (OOG)`.

## 🛠 Formal Specification (CVL)
I used **Liveness Analysis** to prove that the `owner` can be prevented from accessing their funds.

Rule: `owner_cannot_be_blocked`
**Objective**: Prove that the `owner` can always successfully call `withdraw()`.

**Mechanism**: Using the `@withrevert` modifier on a call initiated by the `owner`.

**Result**: ❌ Violation Found. * Counter-example: The Prover generated a malicious `partner` contract.

**Insight**: When the `withdraw` function calls the partner, the partner's code triggers a state that exhausts the transaction gas, causing the owner's logic to never reach completion.

### 🔬 Call Trace Analysis
The Certora Prover identified a path where the `withdraw` function successfully executes the call to the `partner` but reverts on the subsequent `transfer` to the `owner`.

**Key Observations:**
* **Vulnerable Line**: `payable(owner).transfer(amountToSend)`
* **Root Cause**: The preceding `partner.call` is summarized as a `DEFAULT HAVOC`. This allowed the Prover to simulate a state where the gas remaining was insufficient for the `transfer` to succeed.
* **Result**: The transaction enters a `REVERT` state, satisfying the DoS condition where the owner is unable to claim their 1% share.

---

## 💡 Lessons Learned
1. **External Call Risks**: Raw .call instructions without a gas limit are dangerous if the recipient is untrusted.

2. **Checks-Effects-Interactions**: While usually discussed regarding Reentrancy, this level shows that the order of interactions matters for availability as well.

3. **Liveness vs. Safety**: Formal Verification isn't just about preventing "bad" things (Safety); it's about ensuring "good" things can always happen (Liveness).

> **[🔗 View Interactive Certora Report](https://prover.certora.com/output/6854102/c3a32bd8c24247ed9ee890194d369af6?anonymousKey=a8923a019ea050a0d6e1767e54513d9dccbc0300)**