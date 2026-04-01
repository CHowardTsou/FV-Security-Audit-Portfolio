# Certora Formal Verification — DEX

Verifies the constant-product AMM (`DEX.sol`) using the Certora Prover.

## Directory layout

```
certora/
  harness/DEXHarness.sol     Inherits DEX; adds getEthBalance(), getTokenBalance(),
                              getTokenAddress(), getLiquidityOf(address) view helpers.
  specs/
    DEXSanity.spec           Reachability + pure-function properties
    DEXStateMachine.spec     Revert conditions and access-control gates
    DEXAccounting.spec       Balance deltas, LP share ghost invariant, isolation rules
  confs/
    dex_sanity.conf
    dex_statemachine.conf
    dex_accounting.conf
```

## Verification commands

### Local typecheck (no cloud submission)

```bash
# From repo root
certoraRun certora/confs/dex_sanity.conf --compilation_steps_only
certoraRun certora/confs/dex_statemachine.conf --compilation_steps_only
certoraRun certora/confs/dex_accounting.conf --compilation_steps_only
```

### Full cloud run

```bash
certoraRun certora/confs/dex_sanity.conf
certoraRun certora/confs/dex_statemachine.conf
certoraRun certora/confs/dex_accounting.conf
```

## Certora cloud results

| Spec | Report |
| ---- | ------ |
| DEXSanity | [View report](https://prover.certora.com/output/6854102/2d01573728f74463985656eb363f67cc?anonymousKey=54979b64f176761bbd12d671e4162b820921f424) |
| DEXStateMachine | [View report](https://prover.certora.com/output/6854102/ebf866928ef54f4ea35bafb68f8f6c82?anonymousKey=e69fe4f334fd5bf02f10d174fcb6d97fc728094c) |
| DEXAccounting | [View report](https://prover.certora.com/output/6854102/432e81534d144669b8393c66da9bc5c3?anonymousKey=b34995466ca24f89c06be8786c0fa455cd36b4be) |

## Expected results

All rules GREEN except `ethToToken_reverts_when_uninitialized` in DEXStateMachine, which is intentionally RED — it documents Finding C (uninitialized pool token drain). See the Findings section below.

### DEXSanity.spec

| Rule                                 | Expected                               |
| ------------------------------------ | -------------------------------------- |
| `price_output_less_than_reserve`     | GREEN — AMM output < reserve always    |
| `price_monotone`                     | GREEN — larger input yields larger output |
| `satisfy_init_succeeds`              | GREEN — reachability of pool bootstrap |
| `satisfy_ethToToken_produces_output` | GREEN — reachability of ETH→token swap |
| `satisfy_deposit_mints_shares`       | GREEN — reachability of LP deposit     |
| `satisfy_withdraw_returns_eth`       | GREEN — reachability of LP withdrawal  |

### DEXStateMachine.spec

| Rule                                           | Expected                                               |
| ---------------------------------------------- | ------------------------------------------------------ |
| `init_reverts_if_already_initialized`          | GREEN                                                  |
| `only_init_bootstraps_pool`                    | GREEN — only init can move totalLiquidity from 0 to >0 |
| `ethToToken_reverts_on_zero_msg_value`         | GREEN                                                  |
| `ethToToken_reverts_when_uninitialized`        | **RED — documents Finding C (see below)**              |
| `tokenToEth_reverts_on_zero_input`             | GREEN                                                  |
| `tokenToEth_reverts_on_insufficient_allowance` | GREEN                                                  |
| `deposit_reverts_on_zero_msg_value`            | GREEN                                                  |
| `deposit_reverts_when_uninitialized`           | GREEN                                                  |
| `withdraw_reverts_on_insufficient_shares`                | GREEN                                                  |
| `withdraw_reverts_on_zero_amount`                        | GREEN                                                  |
| `only_tokenToEth_or_withdraw_decreases_eth`              | GREEN — authorized ETH drain guard                     |
| `only_ethToToken_or_withdraw_decreases_tokens`           | GREEN — authorized token drain guard                   |

### DEXAccounting.spec

| Rule                                              | Expected                        |
| ------------------------------------------------- | ------------------------------- |
| `initialized_pool_has_positive_reserves` (invariant) | GREEN — pool solvency            |
| `totalLiquidity_equals_sum_of_shares` (invariant) | GREEN                           |
| `ethToToken_eth_increases_tokens_decrease`        | GREEN                           |
| `tokenToEth_token_balance_increases_by_input`     | GREEN                           |
| `tokenToEth_eth_output_matches_price`             | GREEN                           |
| `deposit_increases_total_liquidity`               | GREEN                           |
| `deposit_increases_caller_shares`                 | GREEN                           |
| `withdraw_decreases_caller_shares_by_amount`      | GREEN                           |
| `withdraw_decreases_total_liquidity_by_amount`    | GREEN                           |
| `swaps_do_not_affect_any_lp_shares`               | GREEN                           |
| `tokenToEth_does_not_affect_any_lp_shares`        | GREEN                           |
| `deposit_does_not_affect_other_users_shares`      | GREEN                           |
| `ethToToken_nondecreasing_k`                      | GREEN — k' ≥ k after ETH→token |
| `tokenToEth_nondecreasing_k`                      | GREEN — k' ≥ k after token→ETH |
| `withdraw_returns_proportional_eth`               | GREEN — exact formula check     |
| `withdraw_returns_proportional_tokens`            | GREEN — exact formula check     |
| `deposit_preserves_price_ratio`                   | GREEN — ratio non-decrease      |
| `deposit_does_not_decrease_eth_per_share`         | GREEN — LP value non-dilution   |
| `init_sets_totalLiquidity_to_msg_value`           | GREEN — exact post-init liquidity |
| `deposit_pulls_correct_token_amount`              | GREEN — exact token debit formula |

## Modeling constraints

- **`optimistic_fallback: true`** — `tokenToEth` and `withdraw` use low-level `call{value:...}("")` for ETH transfers. Without this, the prover assumes the receiver's fallback may reenter and corrupt state. Assumption: ETH receivers are EOAs or contracts that don't modify DEX state on receipt.

- **`link: DEXHarness:token=Balloons`** — Resolves the `IERC20 public immutable token` field to the concrete `Balloons` implementation so ERC-20 storage (balances, allowances) is tracked across calls.

- **`persistent ghost sumOfLiquidityShares`** — Without `persistent`, the prover havocs this ghost after every external call (e.g. `Balloons.transferFrom`), corrupting the LP share conservation invariant. `persistent` is safe here because only DEXHarness writes to `liquidity[]`, which no external contract can modify.

- **Ghost-storage consistency in init preserved block** — Certora's inductive pre-state for `init` is symbolic: it can place a non-zero value in `liquidity[msg.sender]` even though `sumOfLiquidityShares == 0` and `totalLiquidity == 0`. This makes the hook compute `ghost = 0 + newVal - oldVal` with a non-zero `oldVal`, producing the wrong ghost value. Requiring `getLiquidityOf(e.msg.sender) == 0` restores consistency. This is sound: in any reachable state with `totalLiquidity == 0`, every user's LP share is 0.

- **OZ ERC-20 state bounding** — OpenZeppelin's `_update()` uses `unchecked { _balances[to] += value }`. In a fully symbolic state `totalSupply` can be `MAX_UINT256`, causing silent wraparound. All rules require `token.totalSupply() < 2^128` and bound individual balances to `<= totalSupply` to prevent spurious overflow counterexamples.

- **ETH/liquidity bounding** — `price()` computes `xInput * 997 * yReserves` in `uint256`. Bounding all inputs to `< 2^128` ensures this intermediate multiplication stays within range.

- **Self-call ETH aliasing** — When `msg.sender == address(this)`, a `payable` call is an ETH self-transfer: the contract's balance doesn't change, so `address(this).balance - msg.value` inside the function differs from the pre-call balance captured by `getEthBalance()`. Rules that compute `ethReserve = pre-call balance` require `e.msg.sender != currentContract` to exclude this unreachable but symbolically valid case.

- **Phantom-ETH initial state** — The prover's symbolic initial state can set `address(this).balance > 0` even when `totalLiquidity == 0`, a state unreachable in practice because DEX has no `receive()` or `fallback()`. Rules that prove "reverts when uninitialized" add `require getEthBalance() == 0` to restrict to the true uninitialized state where `ethReserve = balance - msg.value = 0` causes division by zero.

## Findings

### Finding C — ethToToken succeeds on uninitialized pool (token drain)

**Rule:** `ethToToken_reverts_when_uninitialized` — **RED (expected)**

**Severity:** High

**Description:** `ethToToken` has no `totalLiquidity > 0` guard. When the pool is uninitialized (`totalLiquidity == 0`, `address(this).balance == 0`), calling `ethToToken` with any `msg.value > 0` computes:

```
ethReserve = address(this).balance - msg.value = msg.value - msg.value = 0
price(msg.value, 0, tokenBal) = (msg.value * 997 * tokenBal) / (0 + msg.value * 997) = tokenBal
```

The output equals the entire token balance. The guard `tokenOutput > balanceOf(this)` is `tokenBal > tokenBal` — false — so no revert occurs. The caller receives all tokens in exchange for any nonzero ETH amount.

**Attack vector:** An attacker directly transfers tokens to the DEX contract before `init()` is called (e.g. via `Balloons.transfer(dexAddress, amount)`). They then call `ethToToken` with 1 wei to drain all pre-loaded tokens at a price of 1 wei for the full balance. This requires no special permissions.

**Contrast with `deposit`:** `deposit` divides by `ethReserve` directly (line 115–116), so it hits division by zero when uninitialized and correctly reverts. `ethToToken` subtracts `msg.value` first, producing `ethReserve = 0` without a division-by-zero.

**Mitigation:** Add an initialized pool guard at the top of `ethToToken`:

```solidity
if (totalLiquidity == 0) {
    revert DexNotInitialized();
}
```

This mirrors the implicit protection that `deposit` gets from its division-by-zero on `ethReserve`. The same guard should be added to `tokenToEth` for consistency, although `tokenToEth` divides by `address(this).balance` directly and will revert on division by zero when the ETH balance is 0 — making it less urgent but still worth hardening.

## Known limitations

### Integer division truncation in `price()`

`price()` uses Solidity integer division throughout. For sufficiently small inputs relative to reserves, the output truncates to 0:

```
price(2, 8, 4) = (2 * 997 * 4) / (8000 + 2*997) = 7976 / 9994 = 0
```

This means a caller can send a tiny ETH or token amount and receive 0 output — silently burning funds. This is **not** a floating-point precision problem that a math library can solve. Libraries like Uniswap's `FullMath` address intermediate *overflow*, not truncation; `FullMath.mulDiv(2, 997*4, 9994)` still returns 0.

The correct mitigation is a zero-output guard in `ethToToken` and `tokenToEth` (e.g. `require(output > 0)`). This DEX omits that guard, so the truncation behavior is an accepted design limitation of the current implementation. The `price_positive_for_positive_inputs` rule was intentionally excluded from `DEXSanity.spec` for this reason.

### Universal withdrawal liveness

`withdraw` may revert when `payable(msg.sender).call{value: ethAmount}("")` fails. This happens when (a) the LP is a contract with a reverting fallback, or (b) `ethAmount` truncates to 0 via integer division and the 0-value call is non-deterministic. Neither is a DEX bug.

`optimistic_fallback: true` suppresses storage havoc from the receiver's fallback but does not force the call's success bit to `true`. A rule asserting `!lastReverted` for all states where shares exist is therefore unprovable with this tool under these conditions.

The existential `satisfy_withdraw_returns_eth` in `DEXSanity.spec` proves withdrawal *can* succeed. Universal liveness (it *always* succeeds) is a liveness property about external recipients, not internal DEX correctness, and is out of scope for this suite.

## Harness caveats

`DEXHarness` adds four `view` getters and no other logic. It does **not** override `tokenToEth`, `withdraw`, or any function that uses low-level `call` — those are handled by `optimistic_fallback` in the conf.
