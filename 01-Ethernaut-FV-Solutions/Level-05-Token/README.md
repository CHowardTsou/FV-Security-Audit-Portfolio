# Ethernaut Level 05: Token — Integer Underflow & Ghost Variables

## 📋 Overview
This module analyzes an **Integer Underflow** vulnerability in Solidity `< 0.8.0`. The contract fails to validate sufficient balance before subtraction, leading to infinite token inflation.



## 🛠 Formal Specification (CVL)
I utilized **Ghost Variables** and **SSTORE Hooks** to track the global state, proving that the vulnerability affects the entire protocol's solvency.

### Rule 1: `balance_integrity_after_transfer`
* **Objective**: Ensure a sender's balance decreases correctly after a transfer.
* **Finding**: ❌ **Violated.** The balance wrapped around to $2^{256}-2$ when the transfer amount exceeded the current balance.

### Rule 2: `total_sum_of_balance_is_constant`
* **Mechanism**: A **Ghost Variable** tracks the sum of all mapping values via hooks.
* **Objective**: Prove that tokens cannot be created "out of thin air."
* **Finding**: ❌ **Violated.** The Prover demonstrated massive inflation, as the underflow caused the global sum of tokens to explode.

## 📊 Findings Summary
| Rule                 | Security Property     | Result     |
| :------------------- | :-------------------- | :--------- |
| `balance_integrity`  | User Solvency         | ❌ Violated |
| `total_sum_constant` | Conservation of Value | ❌ Violated |

### Counter-example Trace
* **Action**: `transfer(recipient, 22)` while balance was `20`.
* **Result**: `sender_balance` became a massive 78-digit number, and the **Ghost Sum** reflected this illegal inflation.

> **[View Interactive Certora Report](https://prover.certora.com/output/6854102/dbb36fb40fe04728872569e580acbfea?anonymousKey=ae33997b0ca3725a0c3f44410a94e396457b7e3c)**