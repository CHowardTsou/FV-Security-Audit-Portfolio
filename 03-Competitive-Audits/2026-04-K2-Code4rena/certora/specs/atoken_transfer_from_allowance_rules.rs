// Excerpt from contracts/a-token/src/certora_specs.rs (K2 Certora Sunbeam campaign).
// Finding: Code4rena 2026-04-K2 M-42 — an approved spender can move more indexed aToken
// value than the nominal allowance it spends.
//
// Reduced-model rules: the helpers restate the aToken arithmetic (ray_div_up scaled
// debit, half-up ray_mul re-indexing) and the transfer_from acceptance guard
// (nominal allowance check + scaled balance check) as pure u128 functions.
// Inputs are symbolic and bounded (amounts up to 1e9, liquidity index 2x..10x RAY).
// All three rules are expected RED on the contest code: every violation is a
// concrete transfer_from that moves more value than the owner approved.

#![allow(dead_code)]

use cvlr_asserts::{cvlr_assert, cvlr_assume};
use cvlr_soroban_derive::rule;

const ATOKEN_CERTORA_RAY: u128 = 1_000_000_000_000_000_000_000_000_000;

// ---------------------------------------------------------------------------
// Arithmetic + guard model of the contest code
// ---------------------------------------------------------------------------

fn atoken_reduced_ray_div_up(amount: u128, index: u128) -> u128 {
    (amount * ATOKEN_CERTORA_RAY + index - 1) / index
}

fn atoken_reduced_ray_mul_half_up(scaled_amount: u128, index: u128) -> u128 {
    (scaled_amount * index + (ATOKEN_CERTORA_RAY / 2)) / ATOKEN_CERTORA_RAY
}

fn atoken_gap96_transfer_from_indexed_debit(amount: u128, liquidity_index: u128) -> u128 {
    let scaled_amount = atoken_reduced_ray_div_up(amount, liquidity_index);
    atoken_reduced_ray_mul_half_up(scaled_amount, liquidity_index)
}

fn atoken_gap96_current_transfer_from_accepts(
    allowance: u128,
    amount: u128,
    from_scaled_balance: u128,
    liquidity_index: u128,
) -> bool {
    if amount == 0 || allowance < amount || liquidity_index == 0 {
        return false;
    }

    let scaled_amount = atoken_reduced_ray_div_up(amount, liquidity_index);
    scaled_amount > 0 && from_scaled_balance >= scaled_amount
}

// ---------------------------------------------------------------------------
// Expected-red rules (violated 3/3 on the contest code)
// ---------------------------------------------------------------------------

#[rule]
pub fn atoken_gap96_transfer_from_allowance_must_cover_indexed_debit(
    amount: u64,
    index_multiplier: u64,
) {
    cvlr_assume!(amount > 0);
    cvlr_assume!(amount <= 1_000_000_000);
    cvlr_assume!(index_multiplier >= 2);
    cvlr_assume!(index_multiplier <= 10);

    let amount = amount as u128;
    let liquidity_index = ATOKEN_CERTORA_RAY * (index_multiplier as u128);
    let indexed_debit = atoken_gap96_transfer_from_indexed_debit(amount, liquidity_index);

    cvlr_assert!(indexed_debit <= amount);
}

#[rule]
pub fn atoken_gap96_exact_allowance_cannot_transfer_more_than_approved(
    amount: u64,
    from_scaled_balance: u64,
    index_multiplier: u64,
) {
    cvlr_assume!(amount > 0);
    cvlr_assume!(amount <= 1_000_000_000);
    cvlr_assume!(from_scaled_balance > 0);
    cvlr_assume!(from_scaled_balance <= 1_000_000_000);
    cvlr_assume!(index_multiplier >= 2);
    cvlr_assume!(index_multiplier <= 10);

    let amount = amount as u128;
    let allowance = amount;
    let from_scaled_balance = from_scaled_balance as u128;
    let liquidity_index = ATOKEN_CERTORA_RAY * (index_multiplier as u128);
    let accepted = atoken_gap96_current_transfer_from_accepts(
        allowance,
        amount,
        from_scaled_balance,
        liquidity_index,
    );
    let indexed_debit = atoken_gap96_transfer_from_indexed_debit(amount, liquidity_index);

    cvlr_assume!(accepted);
    cvlr_assert!(indexed_debit <= allowance);
}

#[rule]
pub fn atoken_gap96_concrete_one_unit_allowance_moves_two_indexed_units() {
    let amount = 1u128;
    let allowance = 1u128;
    let from_scaled_balance = 10u128;
    let liquidity_index = ATOKEN_CERTORA_RAY * 2;
    let accepted = atoken_gap96_current_transfer_from_accepts(
        allowance,
        amount,
        from_scaled_balance,
        liquidity_index,
    );
    let indexed_debit = atoken_gap96_transfer_from_indexed_debit(amount, liquidity_index);

    cvlr_assert!(!accepted || indexed_debit <= allowance);
}
