# FV Security Audit Portfolio

A hands-on portfolio of smart contract security work using **Formal Verification (FV)** with the [Certora Prover](https://www.certora.com/). Each entry contains the target contract, CVL specification, and a write-up of the findings.

## Structure

```
01-Ethernaut-FV-Solutions/       # Vulnerability discovery on intentionally broken contracts
02-Speedrun-Ethereum-Hardening/  # Protocol hardening on production-style Speedrun Ethereum contracts
```

---

## 01 — Ethernaut FV Solutions

Applying Certora to the [Ethernaut](https://ethernaut.openzeppelin.com/) wargame challenges. Each level contains a known vulnerability; the goal is to specify and prove (or disprove) safety properties, using the Prover as a bug-finding engine.

| Level | Title | Vulnerability Class | CVL Technique | Result |
|:------|:------|:--------------------|:--------------|:-------|
| [04](01-Ethernaut-FV-Solutions/Level-04-Telephone/) | Telephone | Access Control (`tx.origin`) | Ownership integrity rule | ❌ Violated |
| [05](01-Ethernaut-FV-Solutions/Level-05-Token/) | Token | Integer Underflow | Ghost variables + Sstore hooks | ❌ Violated |
| [08](01-Ethernaut-FV-Solutions/Level-08-Vault/) | Vault | Private Storage Misconception | State machine rules | ✅ / ❌ Mixed |
| [11](01-Ethernaut-FV-Solutions/Level-11-Elevator/) | Elevator | Untrusted External Call | Stateful ghost + method summary | ❌ Violated |
| [13](01-Ethernaut-FV-Solutions/Level-13-GateKeeperOne/) | Gatekeeper One | Bitwise Constraint Bypass | FV as constraint solver | ❌ Violated |
| [15](01-Ethernaut-FV-Solutions/Level-15-NaughtCoin/) | NaughtCoin | Incomplete Interface Override | Parametric method rule | ❌ Violated |
| [20](01-Ethernaut-FV-Solutions/Level-20-Denial/) | Denial | Denial of Service (gas) | Liveness analysis | ❌ Violated |
| [21](01-Ethernaut-FV-Solutions/Level-21-Shop/) | Shop | Deceptive View Function | Wildcard summary + stateful ghost | ❌ Violated |

---

## 02 — Speedrun Ethereum Hardening

Applying Certora to [Speedrun Ethereum](https://speedrunethereum.com/) challenges. Unlike the Ethernaut work, these contracts are correct implementations — the goal is to build a comprehensive proof suite that hardens the protocol and documents its invariants.

Each challenge follows the 4-tier methodology: valid state → variable transitions → state transitions → high-level expectations.

### Challenge 01 — CrowdFunding

**Contracts**: `CrowdFund.sol`, `FundingRecipient.sol`

A crowdfunding protocol where contributors pool ETH before a deadline. On success, funds are forwarded to a recipient; on failure, contributors can withdraw.

| Spec | Rules | What it proves |
|:-----|:------|:---------------|
| [CrowdFundStateMachine](02-Speedrun-Ethereum-Hardening/Challenge-01-CrowdFunding/certora/specs/CrowdFundStateMachine.spec) | 9 | Deadline immutability, sticky failure state, pre/post-deadline behavior, post-completion blocking |
| [CrowdFundAccounting](02-Speedrun-Ethereum-Hardening/Challenge-01-CrowdFunding/certora/specs/CrowdFundAccounting.spec) | 6 + 2 ghosts | Exact contribution accounting, receive-path equivalence, withdraw zeroing, per-user balance isolation |
| [CrowdFundMeta](02-Speedrun-Ethereum-Hardening/Challenge-01-CrowdFunding/certora/specs/CrowdFundMeta.spec) | 6 | Function reachability, storage effect, view safety, revert rollback |

### Challenge 04 — DEX

**Contracts**: `DEX.sol`, `Balloons.sol` (ERC-20)

A constant-product AMM (`x * y = k`) supporting ETH ↔ ERC-20 swaps with a 0.3% fee, plus proportional liquidity deposit and withdrawal.

| Spec | Rules / Invariants | What it proves |
|:-----|:-------------------|:---------------|
| [DEXAccounting](02-Speedrun-Ethereum-Hardening/Challenge-04-DEX/certora/specs/DEXAccounting.spec) | 12 rules + 2 invariants + ghost | Pool solvency invariant, LP share conservation, exact balance deltas for all functions, constant-product non-decrease (fee accrual), proportional withdraw correctness, deposit price-ratio and ETH-per-share non-decrease |
| [DEXStateMachine](02-Speedrun-Ethereum-Hardening/Challenge-04-DEX/certora/specs/DEXStateMachine.spec) | 10 rules | Revert gates for all functions, only `init` bootstraps pool, authorized reserve drain (ETH / token) |
| [DEXSanity](02-Speedrun-Ethereum-Hardening/Challenge-04-DEX/certora/specs/DEXSanity.spec) | 6 rules | `price()` output bound and monotonicity, reachability for all state-changing functions |

**Finding documented**: `ethToToken_reverts_when_uninitialized` is intentionally red — the spec documents Finding C: an uninitialized pool with pre-deposited tokens can be drained by calling `ethToToken` with 1 wei before `init()`.

---

### Challenge 02 — Token Vendor

**Contracts**: `Vendor.sol`, `YourToken.sol` (ERC-20)

A fixed-rate token vending machine that sells and buys back ERC-20 tokens. Demonstrates AMM fundamentals, the ERC-20 approve/transferFrom pattern, and Ownable access control.

| Spec | Rules | What it proves |
|:-----|:------|:---------------|
| [VendorAccounting](02-Speedrun-Ethereum-Hardening/Challenge-02-TokenVendor/certora/specs/VendorAccounting.spec) | 5 + ghost | Exact buy/sell exchange rate, token conservation, no unauthorized token drain, dust-loss witness |
| [VendorStateMachine](02-Speedrun-Ethereum-Hardening/Challenge-02-TokenVendor/certora/specs/VendorStateMachine.spec) | 5 | Revert on zero inputs, onlyOwner withdraw, full ETH drain on withdraw, open buy/sell access |
| [VendorSanity](02-Speedrun-Ethereum-Hardening/Challenge-02-TokenVendor/certora/specs/VendorSanity.spec) | 4 | Function reachability, no-op detection |

---

## CVL Techniques Covered

| Technique | Where used |
|:----------|:-----------|
| Parametric rules (`method f`) | Token, NaughtCoin, Vault, Vendor |
| Ghost variables + Sstore hooks | Token, Elevator, Shop, CrowdFunding, Vendor |
| `@withrevert` + `lastReverted` | CrowdFunding, Vendor, multiple Ethernaut levels |
| Method summaries (wildcard `_`) | Elevator, Shop |
| `invariant` | Vendor (exchange rate) |
| `satisfy` (witness / existence proof) | GatekeeperOne, Vendor, CrowdFunding |
| `nativeBalances` built-in | Vendor |
| Linked contracts + harness | CrowdFunding, Vendor |
| Liveness analysis | Denial |

---

## Tools

- **Certora Prover** — `certoraRun`
- **Solidity** `0.8.20`
- **OpenZeppelin Contracts** v5
- **Hardhat** (challenge development)
