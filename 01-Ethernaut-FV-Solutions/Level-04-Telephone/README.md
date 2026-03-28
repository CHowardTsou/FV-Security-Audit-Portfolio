# Ethernaut Level 04: Telephone — Access Control Verification

## 📋 Overview
The **Telephone** level demonstrates the danger of using `tx.origin` for authorization. This contract allows any caller to claim ownership if they use a "Proxy" contract as an intermediary.



## 🔍 The Vulnerability
The vulnerability lies in the conditional check: `if (tx.origin != msg.sender)`. An attacker can use a malicious contract to call `changeOwner()`, making `msg.sender` the attack contract while `tx.origin` remains the attacker's wallet, bypassing the check.

## 🛠 Formal Specification (CVL)
I defined the **Ownership Integrity** property to prove this flaw.

### Rule: `integrityOfOwnership`
* **Property**: If a caller is not the current owner, the owner state should not change.
* **Logic**: `(e.msg.sender != oldOwner) => (newOwner == oldOwner)`
* **Result**: **Violation Found.** The Prover identified a counter-example where a proxy-style call successfully reassigned the `owner`.

## 📊 Findings Summary
| Rule                   | Result     | Finding                                                  |
| :--------------------- | :--------- | :------------------------------------------------------- |
| `integrityOfOwnership` | ❌ Violated | Detected unauthorized ownership change via Proxy bypass. |

> **[View Interactive Certora Report](https://prover.certora.com/output/6854102/bed191d064eb418b9f9e5895833b9620?anonymousKey=6b3cde495e3867ff61e30354dd20e932637918a4)**