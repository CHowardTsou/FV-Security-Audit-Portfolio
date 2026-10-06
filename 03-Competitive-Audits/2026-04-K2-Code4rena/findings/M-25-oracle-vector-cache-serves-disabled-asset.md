# [M-25] Disabled oracle assets remain usable through the batch-price TTL cache

| | |
|:--|:--|
| **Contest** | [Code4rena — K2 (April 2026)](https://code4rena.com/reports/2026-04-k2) |
| **Judged severity** | Medium (submitted as High) |
| **Official finding** | [M-25 — Disabled oracle assets remain usable through the batch-price TTL cache](https://code4rena.com/reports/2026-04-k2#m-25-disabled-oracle-assets-remain-usable-through-the-batch-price-ttl-cache) |
| **My submission** | [S-1781](https://code4rena.com/audits/2026-04-k2/submissions/S-1781) (credited as `cht1206`) |
| **Component** | `contracts/price-oracle/src/contract.rs` — `get_asset_prices_vec` |
| **Found with** | Certora Sunbeam (reduced-model rules) → confirmed with a Soroban host PoC |

## Summary

`get_asset_prices_vec` (the batch price path the router uses for account valuation) returns a fresh entry from `LastPriceData` **before** it loads the asset's live `AssetConfig` and checks `config.enabled`. If an admin disables an asset after its price was cached, the single-asset path (`get_asset_price_data`) correctly rejects it, but the batch path keeps serving the cached price until the cache TTL expires.

## Root cause

[`contract.rs#L438-L475`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/price-oracle/src/contract.rs#L438-L475) (contest snapshot):

```rust
for (idx, asset) in assets.iter().enumerate() {
    // Try cache first
    if cache_ttl > 0 {
        if let Some(cached) = storage::get_last_price_data(&env, &asset) {
            ...
            if cache_age <= cache_ttl && price_age <= oracle_config.price_staleness_threshold {
                results.push_back(Some(price_data));
                continue;                       // <-- returns before any config check
            }
        }
    }

    let config = storage::get_asset_config(&env, &asset)
        .ok_or(OracleError::AssetNotWhitelisted)?;
    if !config.enabled {
        return Err(OracleError::AssetDisabled); // never reached on a cache hit
    }
```

[`set_asset_enabled`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/price-oracle/src/contract.rs#L176-L183) only flips `config.enabled`. It does not clear or epoch-tag `LastPriceData`, so the cached value outlives the admin's decision. `set_price_cache_ttl` has the same problem (GAP-47): changing the TTL doesn't invalidate entries cached under the old setting.

## Impact

Disabling an asset is the admin's emergency lever for delisting broken collateral or debt. During the TTL window, every router path that prices through the batch call still values the disabled asset. That covers health factor, account data, borrow and withdraw validation, and liquidation minimum-output checks. The admin believes the asset is out of the risk engine when it isn't.

## How the Prover found it

The campaign split the K2 workspace into 8 spec families. For the price-oracle storage and cache family I wrote **reduced-model rules**: each one restates the cache-or-config decision in `get_asset_prices_vec` as a pure function, and the Prover checks a safety property over all inputs.

**Property (GAP-39): a cache hit must never be accepted when the live config is missing or disabled.**

```rust
// Model of the contest code
fn price_oracle_gap39_current_cache_accepts_without_live_config(
    cached_price_present: bool, cache_usable: bool,
    asset_config_present: bool, asset_enabled: bool,
) -> bool {
    if cached_price_present && cache_usable {
        return true;                       // cache short-circuits config
    }
    asset_config_present && asset_enabled
}

#[rule]
pub fn price_oracle_gap39_cache_hit_requires_live_asset_config() {
    let accepted =
        price_oracle_gap39_current_cache_accepts_without_live_config(true, true, false, false);
    cvlr_assert!(!accepted);
}
```

**Property (GAP-47): a cache entry written before a TTL change must not be served afterwards.**

| Step | Run | Result |
|:--|:--|:--|
| Expected-red (contest code) | [`gap39_47_cache_config_epoch_expected_red`](https://prover.certora.com/output/6854102/f7fd2fe09c7a4a8b8e571b2f9ec1a5e2?anonymousKey=010f81181f8cef998467df588cb5b3d46a624a4b) | ❌ 2/2 violated. The Prover finds the cached-but-disabled acceptance path. |
| Closure (patched code) | [`sfc02_price_oracle_storage_cache_closure`](https://prover.certora.com/output/6854102/a0a6402285254d97bcbcc3617ad4e912?anonymousKey=b3ba369e7e3c189ca8ce5935d8084ede40bbfc67) | ✅ 4/4 verified |

Full rule source: [`../certora/specs/price_oracle_cache_rules.rs`](../certora/specs/price_oracle_cache_rules.rs). Confs: [`../certora/confs/`](../certora/confs/).

> **Scope note.** These rules check a model of the branch logic, not the deployed `get_asset_prices_vec` entrypoint. The Prover found the bad branch ordering. The host PoC below then confirmed it against the real compiled contracts.

## Proof of Concept (Soroban host test)

1. Set a cache TTL, clear the seeded manual override, and register a custom price source.
2. Call `get_asset_prices_vec([asset])` to seed `LastPriceData`.
3. Admin calls `set_asset_enabled(asset, false)`.
4. `try_get_asset_price_data(asset)` returns an error, which is correct.
5. `get_asset_prices_vec([asset])` still returns the cached $1.00. **This is the bug.**

Test: [`../poc/c4_poc_tests.rs`](../poc/c4_poc_tests.rs) → `test_poc_high_oracle_vector_cache_serves_disabled_asset_price_confirmed`

```sh
bash build.sh
cargo test -p k2-c4 test_poc_high_oracle_vector_cache_serves_disabled_asset_price_confirmed -- --nocapture
```

## Recommended mitigation

Load and validate the live `AssetConfig` (exists, `enabled`, current source metadata) **before** you trust the cache. Gate cache use on a config or cache epoch, and clear or epoch-bump `LastPriceData` on `set_asset_enabled`, on oracle-source changes and on `set_price_cache_ttl`. The patched model (`price_oracle_sfc02_fixed_*`) is what the closure run proves.

## Lessons

- **Watch for early `continue`/`return` on a fast path.** A check placed after one is skipped whenever the fast path hits. A boolean decision model makes that ordering easy to prove wrong.
- **A cache needs an invalidation story for every admin setter that changes what's valid.** Here that's enable/disable, source rotation and TTL changes.
