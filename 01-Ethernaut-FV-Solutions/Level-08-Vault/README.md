# Ethernaut Level 08: Vault — Storage Privacy & State Machine Verification

## 📋 Overview
The **Vault** level highlights a common misconception in Web3: the idea that `private` state variables are hidden from the public. While the password is not accessible via a getter function, it is easily retrieved by inspecting the contract's storage slots.

Instead of just "cracking" the password, I used **Formal Verification (FV)** to verify the **State Machine Integrity** of the contract.

---

## 🔍 The Vulnerability: Private Storage Access
Solidity's `private` visibility only prevents other contracts from reading the variable. However, the data remains visible on the blockchain.
* **Password Location**: Slot 1.
* **Exploit Method**: `cast storage contractAddress 1`.



---

## 🛠 Formal Specification (CVL)

I implemented three rules to verify the transition logic of the vault.

### 1. Rule: `wrongPasswordFails` (Exploit Discovery)
* **Objective**: Prove that a valid input exists that can change the `locked` state.
* **Property**: `assert locked() == true` after an `unlock` attempt.
* **Result**: ❌ **Violation Found (Expected).** * **Insight**: The Certora Prover found a counter-example (a specific `bytes32` value) that satisfies the requirement to unlock the vault. This confirms the `unlock` function is functional and reachable.

### 2. Rule: `onlyUnlockChangesState`
* **Objective**: Prove that no function other than `unlock(bytes32)` can transition the vault from locked to unlocked.
* **Methodology**: Parametric method testing (`method f`).
* **Result**: ✅ **Passed.** This confirms there are no hidden backdoors or inheritance flaws (unlike the NaughtCoin exploit).

### 3. Rule: `cannotRelock`
* **Objective**: Verify the "One-Way" nature of the vault. Once open, it should stay open.
* **Result**: ✅ **Passed.** Proved that the contract lacks any logic to set `locked = true` after initialization.

---

## 📊 Findings Summary

| Rule                     | Security Property | Result     | Finding                                      |
| :----------------------- | :---------------- | :--------- | :------------------------------------------- |
| `wrongPasswordFails`     | Functionality     | ❌ Violated | Prover found a valid password to unlock.     |
| `onlyUnlockChangesState` | Access Control    | ✅ Passed   | Only the intended function can change state. |
| `cannotRelock`           | State Consistency | ✅ Passed   | No "Re-locking" mechanism detected.          |



---

## 💡 Lessons Learned
1. **Privacy != Security**: `private` variables only restrict internal contract access, not off-chain visibility.
2. **Logic Verification**: Even when a secret is compromised, FV proves the **transition logic** is correct. If this contract had an inherited function that accidentally reset `locked`, Rule 2 would have caught it.
3. **Symbolic Execution**: This level demonstrates how Certora treats data as symbols. It doesn't "know" the password, but it proves that *if* the input matches the stored symbol, the state changes.

> **[🔗 View Interactive Certora Report](https://prover.certora.com/output/6854102/d7f1907ffb4b4581ad1db6482aad150f?anonymousKey=5be29e088cce2d4e9587eb0bdd664cbc6d3719c1)**