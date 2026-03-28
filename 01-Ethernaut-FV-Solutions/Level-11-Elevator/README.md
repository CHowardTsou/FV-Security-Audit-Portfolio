# Ethernaut Level 11: Elevator — Modeling Stateful External Contracts

## 📋 Overview
The **Elevator** contract depends on an external `Building` contract to determine if a specific floor is the "top" floor. The vulnerability is a logic error: the contract trusts an external call to return a consistent result within a single execution block.

## 🛠 Formal Specification (CVL)
This level requires **Method Summarization** and **Ghost Variables** to model a "lying" external contract.

### The "Stateful Ghost" Technique
Standard FV models usually assume external calls are stateless or "pure." To prove this exploit, I implemented:
1. **Ghost Variable (`g_secondcall`)**: A tracking variable that persists across the duration of the transaction.
2. **Hooked Summary**: I replaced the external `isLastFloor` call with a custom logic block that returns `false` on the first call and `true` on every subsequent call.

### Rule: `can_not_reach_the_top`
* **Objective**: Prove that the elevator can be tricked into setting `top = false`.
* **Result**: ❌ **Violation Found.** * **Discovery**: The Prover confirmed that if the `Building` contract changes its return value between calls, the `Elevator` will set `top = true` even if it initially thought it wasn't at the top.

### 📊 Verification Analysis
The Certora Prover successfully identified the logic flaw using the "Stateful Ghost" method. 

**Call Trace Breakdown:**
* **First Call**: `isLastFloor` returns `false`, satisfying the `if` condition in `Elevator.sol`.
* **State Change**: The ghost variable `g_secondcall` transitions from `false` to `true`.
* **Second Call**: Inside the same transaction, the Elevator calls `isLastFloor` again to set the `top` variable.
* **The Exploit**: Our summary returns `true` on this second call, resulting in `Elevator.top` being set to `true`.

**Result**: `assert !top` violated ❌ (Proof of Vulnerability).

---

## 💡 Lessons Learned
1. **Never trust external state**: If your contract logic depends on a boolean check from an external contract, that contract can manipulate its internal state to change the answer.
2. **Summarization Power**: This audit demonstrates how Certora can model complex, malicious behaviors in dependencies without needing the actual source code of those dependencies.
3. **View vs. Logic**: Even if a function is theoretically "view" or "pure" in an interface, you must treat the return values as untrusted if the source is external.

> **[🔗 View Interactive Certora Report](https://prover.certora.com/output/6854102/b01c6e893cea48e0810f570f19aca04d?anonymousKey=a8af0ea4b3fab814430f6c01738a94f363966e4c)**