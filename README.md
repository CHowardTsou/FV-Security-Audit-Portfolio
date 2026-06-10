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

### Challenge 05 — Oracles (Whitelist, Staking, Optimistic)

A three-part series building progressively more sophisticated oracle designs — each with a full Certora suite and a published write-up.

#### Whitelist Oracle

**Contracts**: `WhitelistOracle.sol`, `SimpleOracle.sol`, `StatisticsUtils.sol`

An aggregator oracle managing a whitelist of `SimpleOracle` contracts, filtering stale data, and returning the median price.

| Spec | Rules / Invariants | What it proves |
|:-----|:-------------------|:---------------|
| [Sanity](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Whitelist/certora/specs/Sanity.spec) | 3 | Function reachability, event emission, owner-only revert |
| [ValidState](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Whitelist/certora/specs/ValidState.spec) | 3 invariants | Array length consistency, index bounds, ghost-storage synchronization |
| [StateTransitions](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Whitelist/certora/specs/StateTransitions.spec) | 6 | Add/remove oracle transitions, swap-and-pop correctness, owner enforcement |
| [ReadPathProperties](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Whitelist/certora/specs/ReadPathProperties.spec) | 5 | Staleness filtering, median correctness, `NoOraclesAvailable` revert |
| [ActiveSetMembership](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Whitelist/certora/specs/ActiveSetMembership.spec) | 4 | Active node set tracks fresh oracles only, membership consistency |

📝 [Blog post](https://medium.com/@chinhaotsou_54090/formal-verification-of-a-whitelist-oracle-proving-correctness-with-certora-a0a3fca0da71)

---

#### Staking Oracle

**Contracts**: `StakingOracle.sol`, `OracleToken.sol` (ERC-20), `StatisticsUtils.sol`

An economic-incentive oracle with staking, slashing, bucket-based median reporting, and reward claiming.

| Spec | Rules / Invariants | What it proves |
|:-----|:-------------------|:---------------|
| [Sanity](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Staking/certora/specs/Sanity.spec) | 4 | Function reachability, node registration liveness |
| [ValidState](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Staking/certora/specs/ValidState.spec) | 5 invariants | Node struct consistency, stake floor, active flag semantics |
| [StateMachine](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Staking/certora/specs/StateMachine.spec) | 8 | Registration/exit transitions, waiting period enforcement, bucket sequencing |
| [Accounting](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Staking/certora/specs/Accounting.spec) | 9 | Stake conservation, slash arithmetic, reward minting, effective stake calculation |
| [Views](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Staking/certora/specs/Views.spec) | 5 | `getLatestPrice`, `getEffectiveStake`, `getOutlierNodes` correctness |

📝 [Blog post](https://medium.com/@chinhaotsou_54090/formal-verification-of-a-staking-oracle-certora-prover-continued-59e564ab2ff6)

---

#### Optimistic Oracle

**Contracts**: `OptimisticOracle.sol`, `Decider.sol`

A dispute-based oracle inspired by UMA Protocol. Asserters post ETH rewards; proposers bond `2×reward`; disputers challenge; a trusted decider resolves contested outcomes.

| Spec | Rules / Invariants | What it proves |
|:-----|:-------------------|:---------------|
| [Sanity](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Optimistic/certora/specs/Sanity.spec) | 4 | Liveness for all claim/refund paths, `nextAssertionId` monotonicity, invariant witnesses |
| [ValidState](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Optimistic/certora/specs/ValidState.spec) | 5 invariants | `bond = 2×reward`, proposer/disputer/winner ordering pyramid, ID counter floor |
| [StateMachine](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Optimistic/certora/specs/StateMachine.spec) | 9 | Terminal field immutability (`claimed`, `winner`, `proposer`, `disputer`), correct initialization, winner determination, `getState` semantics |
| [Accounting](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Optimistic/certora/specs/Accounting.spec) | 8 | No double-claim across three payout paths, exact bond enforcement, payout state correctness |
| [AccessControl](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Optimistic/certora/specs/AccessControl.spec) | 6 | Only owner changes decider, only decider settles, prerequisite gating for each transition |
| [TimingWindow](02-Speedrun-Ethereum-Hardening/Challenge-05-Oracles-Optimistic/certora/specs/TimingWindow.spec) | 7 | Proposal/dispute/claim/refund window enforcement, dispute deadline reset on proposal |

📝 [Blog post](https://medium.com/@chinhaotsou_54090/formal-verification-of-an-optimistic-oracle-certora-prover-the-final-oracle-ed1671f9d3f1)

---

## CVL Techniques Covered

| Technique | Where used |
|:----------|:-----------|
| Parametric rules (`method f`) | Token, NaughtCoin, Vault, Vendor, Oracles |
| Ghost variables + `hook Sstore`/`Sload` | Token, Elevator, Shop, CrowdFunding, Vendor, Staking Oracle, Optimistic Oracle |
| `@withrevert` + `lastReverted` | CrowdFunding, Vendor, all Oracle suites, multiple Ethernaut levels |
| Method summaries (wildcard `_`) | Elevator, Shop |
| `invariant` + `preserved` blocks | Vendor, all Oracle suites |
| `requireInvariant` in preserved blocks (invariant pyramid) | Optimistic Oracle |
| `satisfy` (witness / existence proof) | GatekeeperOne, Vendor, CrowdFunding, Oracle Sanity suites |
| `nativeBalances` built-in | Vendor |
| Linked contracts + harness | CrowdFunding, Vendor, Staking Oracle, Optimistic Oracle |
| `calldataarg` for opaque arguments | Optimistic Oracle (`string description`) |
| `optimistic_fallback` for ETH transfer modeling | Optimistic Oracle |
| Mutation testing (Gambit) | All Oracle suites |
| Liveness analysis | Denial |

---

## Tools

- **Certora Prover** — `certoraRun`
- **Solidity** `0.8.20`
- **OpenZeppelin Contracts** v5
- **Hardhat** (challenge development)
