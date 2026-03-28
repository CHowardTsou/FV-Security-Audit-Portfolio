# Ethernaut Level 15: NaughtCoin — Inheritance & Access Control Verification

## 📋 Overview
NaughtCoin is an ERC20 token where the player's initial supply is supposed to be locked for 10 years. The vulnerability demonstrates a common oversight in Smart Contract development: **Incomplete interface overrides.** While the `transfer` function is restricted, the standard `transferFrom` remains accessible.

## 🛠 Formal Specification (CVL)
I used a **Parametric Method Rule** in Certora to audit the entire contract interface simultaneously.

### Rule: `no_function_can_drain_player_before_timelock`
* **Objective**: Prove that no function in the contract can decrease the player's balance while `block.timestamp < timeLock`.
* **Methodology**: By using the `method f` syntax, the Certora Prover automatically tested every public function in the contract, including inherited functions from OpenZeppelin's ERC20.
* **Result**: ❌ **Violation Found.** The Prover identified that `transferFrom(player, recipient, amount)` could bypass the timelock because the developer failed to apply the `lockTokens` modifier to the inherited `transferFrom` function.

## 📊 Findings Summary
| Rule                   | Security Property  | Result     | Finding                                 |
| :--------------------- | :----------------- | :--------- | :-------------------------------------- |
| `no_drain_before_lock` | Timelock Integrity | ❌ Violated | `transferFrom` bypasses the lock check. |

> **[View Interactive Certora Report](https://prover.certora.com/output/6854102/a8c3f9faec534f7fb1bab54ac90f2958?anonymousKey=53f02c23f673640158f0d2c8cd1e66edee477267)**