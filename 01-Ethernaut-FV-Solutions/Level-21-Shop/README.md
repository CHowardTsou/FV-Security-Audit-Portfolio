# Ethernaut Level 21: Shop — Deceptive View Functions

## 📋 Overview
The **Shop** level is a sister challenge to the **Elevator**. It demonstrates that relying on an external contract's `view` function for critical logic is a major security risk. While `view` functions are theoretically non-state-changing, they can still return inconsistent values by reading the state of the calling contract, leading to Price Manipulation.

## 🔍 The Vulnerability
The `buy()` function in the Shop contract performs a check and an assignment based on two separate calls to an external `Buyer` contract:

Check: if `(_buyer.price() >= price && !isSold)`

Assignment: `price = _buyer.price();`

Because the contract sets `isSold = true` between these two calls, a malicious buyer can implement logic that returns `100` first (to pass the check) and `1` second (to pay almost nothing).

## 🛠 Formal Specification (CVL)
I utilized a **Ghost Variable** and a **Wildcard Method Summary** to prove this exploit. This demonstrates the ability to model untrusted external contracts whose addresses are only known at runtime.

### The "Stateful Ghost" Technique
1. **Ghost Variable (`g_count`)**: Acts as a call counter to track how many times the buyer's price has been queried.

2. **Wildcard Summary (`_.price()`)**: Since the `_buyer` address is dynamic (`msg.sender`), I used a wildcard summary to intercept any call to a `price()` function and redirect it to my custom logic.


### 📊 Verification Analysis
The Certora Prover successfully generated a counter-example. In the call trace, we can observe the "Heist" in action:

**Call Trace Breakdown:**
* **First togglePrice() Call**: Returns 100. This satisfies the `if (_buyer.price() >= price && !isSold)` check in the Solidity code.

* **State Update**: `Store at Shop.isSold ↪ true`. The shop now thinks the item is sold.

* **Second togglePrice() Call**: Returns 1. Because your ghost count is no longer 0, it hits the else branch.

**The Result**: `Store at Shop.price ↪ 1`. The final price is set to 1 Wei.

**The Violation**: assert `Shop.isSold() => Shop.price() >= 100` evaluates to true => 1 >= 100, which is False. ❌

---

## 💡 Lessons Learned
1. **view is not a Security Boundary**: A view modifier only prevents the function from modifying its own state. It does not prevent it from reading your state to change its behavior.

2. **Internal Source of Truth**: Critical values like price should be immutable or stored internally. Never rely on an untrusted external contract to provide the "correct" price during an active transaction.

3. **Dynamic Summaries**: Mastered the use of _ wildcard summaries to handle interactions with arbitrary user-provided contracts.

> **[🔗 View Interactive Certora Report](https://prover.certora.com/output/6854102/5a75e18b721442ba811eb66dddb8aa7b/?anonymousKey=58b9979e748e532622415f6413777d854978c927)**