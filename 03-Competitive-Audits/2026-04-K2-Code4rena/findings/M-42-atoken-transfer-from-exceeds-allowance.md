# [M-42] Approved spender can move more aToken value than its nominal allowance

| | |
|:--|:--|
| **Contest** | [Code4rena — K2 (April 2026)](https://code4rena.com/reports/2026-04-k2) |
| **Judged severity** | Medium |
| **Official finding** | [M-42 — Approved spender exceed nominal allowance by splitting aToken transfers into dust chunks](https://code4rena.com/reports/2026-04-k2#m-42-approved-spender-exceed-nominal-allowance-by-splitting-atoken-transfers-into-dust-chunks) |
| **My submission** | [S-2190](https://code4rena.com/audits/2026-04-k2/submissions/S-2190) (credited as `cht1206`) |
| **Component** | `contracts/a-token/src/contract.rs` — `transfer_from` → `transfer_internal` |
| **Found with** | Certora Sunbeam (bounded symbolic reduced-model rules) → confirmed with a Soroban host PoC |

## Summary

aToken balances are stored as **scaled shares**: `indexed balance = scaled × liquidityIndex / RAY`. `transfer_from` checks and decrements the spender's allowance by the caller-supplied **nominal** `amount`. The balance movement happens afterwards in `transfer_internal`, which converts `amount` to shares with **rounded-up** division (`ray_div_up`). Once the liquidity index is above `RAY` (any reserve that has accrued interest), one rounded-up share is worth more than the allowance it consumed. A spender can therefore move more of the owner's deposit claim than the owner approved.

## Root cause

[`contract.rs#L83-L120`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/a-token/src/contract.rs#L83-L120) and [`#L579-L682`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/a-token/src/contract.rs#L579-L682) (contest snapshot):

```rust
pub fn transfer_from(env, spender, from, to, amount: i128) -> Result<(), TokenError> {
    ...
    if current_allowance < amount { return Err(TokenError::InsufficientAllowance); }
    allowance_data.amount = current_allowance.checked_sub(amount)?;   // spends NOMINAL units
    ...
    Self::transfer_internal(env, from, to, amount)
}

fn transfer_internal(...) {
    let scaled_u128 = ray_div_up(&env, amount_u128, liquidity_index)?;  // debits rounded-UP shares
    ...
}
```

Allowance is accounted in nominal units, while the balance moves in rounded-up scaled shares. The two units drift apart as soon as `liquidity_index > RAY`.

## Impact

With a 2× index, a spender approved for **1** calls `transfer_from(owner, recipient, 1)`. The allowance drops to 0, but the owner loses one scaled share worth **2** indexed units, and the recipient gains the same 2.

The excess per call is `ray_mul(ceil(amount · RAY / index), index) − amount`, which is up to about one share's value in the smallest unit. A single large transfer barely notices it. As the judged title points out, though, a spender can **split the allowance into dust-sized calls**. Each call then carries up to one share of excess, so the leakage grows with the number of calls rather than staying fixed. Integrations such as DEX routers and aggregators that hold aToken allowances can extract more of the user's deposit claim than the user approved.

This is Medium: it needs an existing allowance and an accrued index, the excess per call is small, and the attacker's gain is bounded by the allowance and the index multiplier. It still breaks the core delegated-spend rule: *a spender approved for N cannot move more than N*.

## How the Prover found it

The transfer arithmetic and the `transfer_from` acceptance guard are written as pure `u128` functions. The Prover explores amounts up to 1e9, scaled balances up to 1e9 and liquidity indices from 2× to 10× `RAY`.

```rust
fn atoken_gap96_transfer_from_indexed_debit(amount: u128, liquidity_index: u128) -> u128 {
    let scaled_amount = atoken_reduced_ray_div_up(amount, liquidity_index);   // ceil
    atoken_reduced_ray_mul_half_up(scaled_amount, liquidity_index)            // back to indexed units
}

fn atoken_gap96_current_transfer_from_accepts(allowance, amount, from_scaled_balance, index) -> bool {
    if amount == 0 || allowance < amount || index == 0 { return false; }      // nominal allowance check
    let scaled_amount = atoken_reduced_ray_div_up(amount, index);
    scaled_amount > 0 && from_scaled_balance >= scaled_amount
}
```

Three expected-red rules, each stating the invariant the contest code should satisfy:

| Rule | Invariant | Result |
|:--|:--|:--|
| `atoken_gap96_transfer_from_allowance_must_cover_indexed_debit` | For any amount and index, `indexed_debit <= amount` | ❌ violated |
| `atoken_gap96_exact_allowance_cannot_transfer_more_than_approved` | If `transfer_from` is **accepted** with `allowance == amount`, then `indexed_debit <= allowance` | ❌ violated |
| `atoken_gap96_concrete_one_unit_allowance_moves_two_indexed_units` | Concrete check: allowance 1, index 2×, balance 10 shares | ❌ violated (1 approved → 2 moved) |

| Run | Prover | Result |
|:--|:--|:--|
| [Expected-red, original run](https://prover.certora.com/output/6854102/37903592c1854b81ab881427976d2011?anonymousKey=dd35f61b757933c4de1e6c7618bf740e0ba4e7d0) | 8.6.4 | ❌ 3/3 violated |
| [Expected-red, refreshed run](https://prover.certora.com/output/6854102/f4687e97891c426bb9ef2ca10af2654f?anonymousKey=40f43b7c6f76a18e3303faea31e21ba42868c9e5) | 8.13.1 | ❌ 3/3 violated, 0 unknown |

Full rule source: [`../certora/specs/atoken_transfer_from_allowance_rules.rs`](../certora/specs/atoken_transfer_from_allowance_rules.rs). Conf: [`../certora/confs/gap96_transfer_from_allowance_scaled_rounding_expected_red.conf`](../certora/confs/gap96_transfer_from_allowance_scaled_rounding_expected_red.conf).

> **Scope note.** These rules check a model of the arithmetic and guard, not the deployed entrypoint. The host PoC confirms the behavior on the real compiled aToken. I did not write a closure rule for a patched version of this finding.

## Proof of Concept (Soroban host test)

1. Deploy the production aToken WASM against a mock router that returns liquidity index `2 × RAY`.
2. `mint_scaled` 20 to the owner, which gives 10 scaled shares.
3. Owner approves the spender for exactly **1**.
4. Spender calls `transfer_from(owner, recipient, 1)`.
5. Allowance goes to 0, the recipient receives 1 scaled share, and the owner is debited **2** indexed units. **This is the bug.**

Test: [`../poc/c4_poc_tests.rs`](../poc/c4_poc_tests.rs) → `test_poc_medium_atoken_transfer_from_allowance_can_move_more_than_approved`

```sh
bash build.sh
cargo test -p k2-c4 test_poc_medium_atoken_transfer_from_allowance_can_move_more_than_approved -- --nocapture
```

## Recommended mitigation

Bind allowance consumption to the actual debit. Compute the rounded-up scaled amount and its indexed value **before** touching the allowance, then require and spend at least that indexed debit:

```rust
let scaled = ray_div_up(&env, amount_u128, liquidity_index)?;
let indexed_debit = ray_mul(&env, scaled, liquidity_index)?.max(amount_u128);
if current_allowance < indexed_debit { return Err(TokenError::InsufficientAllowance); }
allowance_data.amount = current_allowance - indexed_debit;
```

Alternatively, define aToken allowances in scaled-share units and document that. Because the public balance and transfer API uses indexed units, spending the indexed debit is less surprising.

## Lessons

- **Check that every limit is in the same unit as the value it limits.** Here allowance is nominal while the debit is in rounded-up shares. The same mismatch also turned up in this contest's transfer HF check (M-19) and liquidation transfers (QA-57).
- **A "can't exceed the approved amount" invariant is one line of CVLR and finds the bug immediately.** Rounding-direction bugs are cheap to search for with bounded symbolic arithmetic.
