# Certora Verification Suite — Token Vendor

Formal verification specs for the Token Vendor protocol (YourToken ERC-20 + Vendor).

## How to Run

Run each spec separately from the project root:

```bash
# 1. Sanity checks (smoke tests)
certoraRun certora/conf/VendorSanity.conf
https://prover.certora.com/output/6854102/e2143e7b8b0b4d059b01581748cf1873?anonymousKey=4e31b33b11ce861354b02c3afb6f5189c17a438c
# 2. State machine (reverts + access control)
certoraRun certora/conf/VendorStateMachine.conf
https://prover.certora.com/output/6854102/3b92141ab0104474bffb61197c89b44f?anonymousKey=8b547644e314294b009fc26e601449bf5e7b87ff
# 3. Accounting (exchange rate, conservation, dust loss)
certoraRun certora/conf/VendorAccounting.conf
https://prover.certora.com/output/6854102/54676fff653741d796cece22abfb800c?anonymousKey=20c6c8d8305e2e0f23c52c8d85d66235c23cdc60
```

Each command submits to the Certora cloud. Check the dashboard URL in the output.

## Spec Overview

### VendorSanity.spec
Smoke tests — verify the Certora setup works before writing real properties.

| Rule                            | Type    | Expected                                                                                                                        |
| ------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `sanity_buyTokens_can_succeed`  | satisfy | **Green**                                                                                                                       |
| `sanity_sellTokens_can_succeed` | satisfy | **Green**                                                                                                                       |
| `sanity_withdraw_can_succeed`   | satisfy | **Green**                                                                                                                       |
| `noop_detection` (parametric)   | satisfy | **Green** for buyTokens/sellTokens. **Red (`rule_not_vacuous`)** for withdraw and all YourToken functions — expected, see below |

**Why noop_detection is red for some functions:**
- `withdraw()`: only sends ETH via `call` — ETH is account state (`nativeBalances`), not contract storage (`lastStorage`). The rule checks storage changes, so it's unsatisfiable.
- YourToken functions (`transfer`, `approve`, etc.): they modify YourToken's storage, not VendorHarness's storage. The rule checks `currentContract` (VendorHarness) storage, so also unsatisfiable.

### VendorStateMachine.spec
Revert conditions and access control — mathematical proofs, not sampling.

| Rule                                | Type    | Expected                                   |
| ----------------------------------- | ------- | ------------------------------------------ |
| `buyTokens_reverts_on_zero_eth`     | assert  | **Green** — 0 ETH always reverts           |
| `sellTokens_reverts_on_zero_amount` | assert  | **Green** — 0 tokens always reverts        |
| `withdraw_onlyOwner`                | assert  | **Green** — ALL non-owner addresses revert |
| `withdraw_drains_all_eth`           | assert  | **Green** — owner withdraw empties balance |
| `anyone_can_buy`                    | satisfy | **Green** — non-owner can buy              |
| `anyone_can_sell`                   | satisfy | **Green** — non-owner can sell             |

### VendorAccounting.spec
The core verification — proves the math is correct.

| Rule                           | Type    | Expected                                                 |
| ------------------------------ | ------- | -------------------------------------------------------- |
| `buyTokens_exact_accounting`   | assert  | **Green** — exact token deltas                           |
| `sellTokens_exact_accounting`  | assert  | **Green** — exact token + ETH deltas                     |
| `token_conservation_on_buy`    | assert  | **Green** — no tokens created/destroyed                  |
| `token_conservation_on_sell`   | assert  | **Green** — no tokens created/destroyed                  |
| `sellTokens_dust_loss_witness` | satisfy | **Green** — proves the dust-loss scenario IS reachable   |
| `no_unauthorized_token_drain`  | assert  | **Green** — cross-user isolation (Vendor functions only) |

Note: `exchange_rate_is_100` invariant was removed — `tokensPerEth` is `constant`, so Certora's trivial invariant sanity check correctly flags it as unnecessary.

## Confirmed Issue: Dust Loss in sellTokens

Selling fewer than 100 tokens (e.g., `sellTokens(50)`) transfers the tokens to the vendor but returns 0 ETH due to Solidity integer division (`50 / 100 == 0`). The user loses tokens with no compensation. The `sellTokens_dust_loss_witness` rule produces a concrete witness of this.

**Severity:** Low/Informational — the amounts are tiny, but the economic loss is real.

**Fix options:**
1. Require `amount >= tokensPerEth` (reject sub-minimum sells)
2. Require `amount % tokensPerEth == 0` (only accept exact multiples)
3. Check `ethAmount > 0` before transferring tokens

## Harness Design

`VendorHarness.sol` inherits `Vendor` and adds three view helpers:
- `getVendorTokenBalance()` — reads `yourToken.balanceOf(address(this))`
- `getVendorEthBalance()` — reads `address(this).balance`
- `getTokenAddress()` — reads `address(yourToken)`

The `link` directive in each `.conf` file tells Certora that the `yourToken` immutable in the harness points to the real `YourToken` contract. Without this, all ERC-20 calls would be "havoced" (assumed to return any value), destroying every property.

## Ghost Variable: sumOfBalances

Tracks the mathematical sum of all token balances by hooking into `SSTORE` on `YourToken._balances`. Used to prove token conservation (no mint/burn during buy/sell).

The `Sload` hook ensures the ghost stays consistent when Certora starts from a symbolic (non-constructor) state.

## Modeling Constraints

### 1. Symbolic state overflow prevention

OZ ERC20 uses `unchecked { _balances[to] += value }` in `_update()`. In Certora's symbolic state, both `totalSupply()` and individual balances can be `MAX_UINT256`, causing silent wraparound. All accounting and conservation rules require:
```cvl
require token.totalSupply() < max_uint256 / 2;
require token.balanceOf(addr) <= token.totalSupply();
```
This is safe because in reality no balance exceeds totalSupply (1000e18).

### 2. Optimistic fallback

`withdraw()` and `sellTokens()` use low-level `call` to send ETH. Without `optimistic_fallback: true` in the conf, Certora applies DEFAULT HAVOC — assuming the receiver's `receive()`/`fallback()` could do anything (including sending ETH back). The optimistic setting assumes fallbacks don't modify state, which is correct for EOA owners but should be noted.

### 3. Self-transfer exclusion

Rules that check balance deltas require `e.msg.sender != currentContract` because a self-transfer (vendor buying from itself) produces zero delta, which is correct behavior but would fail the delta assertion.

### 4. Parametric rule scoping

`no_unauthorized_token_drain` is filtered to `f.contract == currentContract` (Vendor only). Without this, it also runs for `YourToken.transferFrom`, which is *designed* to decrease a third party's balance (with approval). The security property "no function decreases third-party balances" only makes sense for Vendor functions.

### 5. The `_balances` hook

Hooks into OZ's `private mapping(address => uint256) _balances`. If OZ changes the storage layout in a future version, the hook path would need updating.

## Lessons Learned (iterative debugging)

These are the issues we hit and fixed during development — useful context for anyone learning Certora:

1. **DEFAULT HAVOC on `call`**: Low-level ETH transfers trigger havoc. Fix: `optimistic_fallback: true`.
2. **Trivial invariant**: Constants don't need invariants — Certora's sanity check catches this.
3. **Symbolic totalSupply**: Everything is symbolic unless constrained. Bounding balances by `totalSupply()` is useless if `totalSupply` itself is MAX_UINT256. Always bound the denominator first.
4. **Unchecked arithmetic + symbolic state**: OZ's `unchecked` blocks are safe in production but break Certora's symbolic exploration. Realistic bounds are required.
5. **Parametric rule scope**: Rules running across all contracts can be too broad. `transferFrom` is supposed to decrease balances — filter to the contract you're actually verifying.
6. **Storage vs account state**: `lastStorage` tracks SSTORE/SLOAD. ETH balances are account state (`nativeBalances`), not storage. The noop detector correctly flags `withdraw` as a no-op in storage terms.
