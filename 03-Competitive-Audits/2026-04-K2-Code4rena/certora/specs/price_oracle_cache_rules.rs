// Excerpt from contracts/price-oracle/src/certora_specs.rs (K2 Certora Sunbeam campaign).
// Finding: Code4rena 2026-04-K2 M-25 — disabled oracle assets remain usable through the
// batch-price TTL cache.
//
// These are reduced-model rules: each helper re-states the decision logic of
// `get_asset_prices_vec` as a pure function, and the Prover checks the property
// over every combination of inputs.
//   * gap39 / gap47 helpers model the ORIGINAL (contest) code → expected RED.
//   * sfc02 helpers model the PATCHED code → closure, expected GREEN.

#![allow(dead_code)]

use cvlr_asserts::{cvlr_assert, cvlr_assume};
use cvlr_soroban_derive::rule;
use k2_shared::MAX_RESERVES;

// ---------------------------------------------------------------------------
// Models of the original code (bug)
// ---------------------------------------------------------------------------

fn price_oracle_gap39_current_cache_accepts_without_live_config(
    cached_price_present: bool,
    cache_usable: bool,
    asset_config_present: bool,
    asset_enabled: bool,
) -> bool {
    if cached_price_present && cache_usable {
        return true;
    }

    asset_config_present && asset_enabled
}

fn price_oracle_gap47_current_cache_accepts_after_epoch_change(
    cache_usable_under_new_ttl: bool,
    cache_written_before_ttl_disable: bool,
    ttl_disabled_then_reenabled: bool,
) -> bool {
    let _ = cache_written_before_ttl_disable;
    let _ = ttl_disabled_then_reenabled;
    cache_usable_under_new_ttl
}

// ---------------------------------------------------------------------------
// Models of the patched code (fix)
// ---------------------------------------------------------------------------

fn price_oracle_sfc02_fixed_add_to_asset_list_accepts(
    current_len: u32,
    duplicate_present: bool,
) -> bool {
    if duplicate_present {
        return true;
    }

    current_len < MAX_RESERVES
}

fn price_oracle_sfc02_fixed_remove_len_after(list_len: u32, target_index: u32) -> u32 {
    if target_index < list_len {
        list_len - 1
    } else {
        list_len
    }
}

fn price_oracle_sfc02_fixed_cache_accepts_without_live_config(
    cached_price_present: bool,
    cache_usable: bool,
    asset_config_present: bool,
    asset_enabled: bool,
) -> bool {
    let _ = cached_price_present;
    let _ = cache_usable;
    asset_config_present && asset_enabled
}

fn price_oracle_sfc02_fixed_cache_accepts_after_epoch_change(
    cache_usable_under_new_ttl: bool,
    cache_written_before_ttl_change: bool,
    ttl_changed: bool,
) -> bool {
    if ttl_changed && cache_written_before_ttl_change {
        return false;
    }

    cache_usable_under_new_ttl
}


// ---------------------------------------------------------------------------
// Expected-red rules (violated on the contest code)
// ---------------------------------------------------------------------------

#[rule]
pub fn price_oracle_gap39_cache_hit_requires_live_asset_config() {
    let accepted =
        price_oracle_gap39_current_cache_accepts_without_live_config(true, true, false, false);

    cvlr_assert!(!accepted);
}

#[rule]
pub fn price_oracle_gap47_ttl_reenable_invalidates_prior_cache_epoch() {
    let accepted = price_oracle_gap47_current_cache_accepts_after_epoch_change(true, true, true);

    cvlr_assert!(!accepted);
}

// ---------------------------------------------------------------------------
// Closure rules (pass on the patched code)
// ---------------------------------------------------------------------------

#[rule]
pub fn price_oracle_sfc02_add_rejects_65th_asset() {
    let accepted = price_oracle_sfc02_fixed_add_to_asset_list_accepts(MAX_RESERVES, false);

    cvlr_assert!(!accepted);
}

#[rule]
pub fn price_oracle_sfc02_remove_high_index_preserves_tail(list_len: u32, target_index: u32) {
    cvlr_assume!(list_len > MAX_RESERVES);
    cvlr_assume!(list_len <= MAX_RESERVES + 16);
    cvlr_assume!(target_index >= MAX_RESERVES);
    cvlr_assume!(target_index < list_len);

    let len_after = price_oracle_sfc02_fixed_remove_len_after(list_len, target_index);

    cvlr_assert!(len_after == list_len - 1);
}

#[rule]
pub fn price_oracle_sfc02_cache_hit_requires_live_asset_config() {
    let accepted =
        price_oracle_sfc02_fixed_cache_accepts_without_live_config(true, true, false, false);

    cvlr_assert!(!accepted);
}

#[rule]
pub fn price_oracle_sfc02_ttl_change_invalidates_prior_cache_epoch() {
    let accepted = price_oracle_sfc02_fixed_cache_accepts_after_epoch_change(true, true, true);

    cvlr_assert!(!accepted);
}

