// DEXStateMachine.spec
// Revert conditions and access control gate rules.
// All rules expected GREEN on the fixed DEX implementation.

using Balloons as token;

methods {
    // Harness getters
    function getEthBalance()              external returns (uint256) envfree;
    function getTokenBalance()            external returns (uint256) envfree;
    function getLiquidityOf(address)      external returns (uint256) envfree;
    function totalLiquidity()             external returns (uint256) envfree;

    // Balloons (concrete dispatch via link)
    function Balloons.balanceOf(address)           external returns (uint256) envfree;
    function Balloons.allowance(address, address)  external returns (uint256) envfree;
    function Balloons.totalSupply()                external returns (uint256) envfree;
    function Balloons.transfer(address, uint256)   external returns (bool);
    function Balloons.transferFrom(address, address, uint256) external returns (bool);
}

// ─────────────────────────────────────────────
// Common state bounds (avoid spurious arithmetic overflow CEXes)
// ─────────────────────────────────────────────

definition stateBounded(env e) returns bool =
    totalLiquidity()   < 2^128 &&
    getEthBalance()    < 2^128 &&
    getTokenBalance()  < 2^128 &&
    e.msg.value        < 2^128 &&
    token.totalSupply() < 2^128;

// ─────────────────────────────────────────────
// init() gate
// ─────────────────────────────────────────────

/// init() always reverts when the pool is already initialized.
rule init_reverts_if_already_initialized(env e, uint256 tokens) {
    require totalLiquidity() > 0;
    init@withrevert(e, tokens);
    assert lastReverted;
}

/// Only init() can bootstrap the pool — i.e. move totalLiquidity from 0 to >0.
/// Filtered to currentContract to avoid loop-unwinding issues in Balloons.name()/symbol().
/// withdraw() is excluded because it can never increase totalLiquidity (vacuous for this rule)
/// and is already fully covered by withdraw_decreases_total_liquidity_by_amount in DEXAccounting.spec.
rule only_init_bootstraps_pool(env e, method f, calldataarg args)
    filtered { f -> f.contract == currentContract &&
                    f.selector != sig:withdraw(uint256).selector }
{
    require totalLiquidity() == 0;
    f(e, args);
    assert totalLiquidity() > 0 => f.selector == sig:init(uint256).selector;
}

// ─────────────────────────────────────────────
// ethToToken() gate
// ─────────────────────────────────────────────

/// ethToToken() reverts when msg.value is zero.
rule ethToToken_reverts_on_zero_msg_value(env e) {
    require e.msg.value == 0;
    ethToToken@withrevert(e);
    assert lastReverted;
}

/// EXPECTED RED — documents Finding C: ethToToken has no totalLiquidity > 0 guard.
///
/// With getEthBalance() == 0 and msg.value > 0, inside ethToToken:
///   ethReserve = address(this).balance - msg.value = msg.value - msg.value = 0
///   price(msg.value, 0, tokenBal) = tokenBal   (denominator = msg.value*997, no division by zero)
///
/// tokenOutput == tokenBal, so the guard "tokenOutput > balanceOf" is false and the function
/// succeeds, draining ALL tokens. An attacker can pre-fund the contract with tokens before
/// init() and then call ethToToken with 1 wei to extract them.
///
/// Mitigation: add `if (totalLiquidity == 0) revert DexNotInitialized();` at the top of ethToToken.
rule ethToToken_reverts_when_uninitialized(env e) {
    require totalLiquidity() == 0;
    require getEthBalance() == 0;
    require e.msg.value > 0;
    ethToToken@withrevert(e);
    assert lastReverted;
}

// ─────────────────────────────────────────────
// tokenToEth() gate
// ─────────────────────────────────────────────

/// tokenToEth() reverts when tokenInput is zero.
rule tokenToEth_reverts_on_zero_input(env e) {
    require stateBounded(e);
    tokenToEth@withrevert(e, 0);
    assert lastReverted;
}

/// tokenToEth() reverts when the caller's allowance is insufficient (Bug A fixed).
rule tokenToEth_reverts_on_insufficient_allowance(env e, uint256 tokenInput) {
    require stateBounded(e);
    require tokenInput > 0 && tokenInput < 2^128;
    require token.allowance(e.msg.sender, currentContract) < tokenInput;

    tokenToEth@withrevert(e, tokenInput);
    assert lastReverted;
}

// ─────────────────────────────────────────────
// deposit() gate
// ─────────────────────────────────────────────

/// deposit() reverts when msg.value is zero.
rule deposit_reverts_on_zero_msg_value(env e) {
    require e.msg.value == 0;
    deposit@withrevert(e);
    assert lastReverted;
}

/// deposit() reverts when pool is uninitialized (division by zero computing ethReserve ratio).
/// Requires getEthBalance() == 0 to model the true uninitialized state: DEX has no receive()
/// so balance > 0 with totalLiquidity == 0 is not reachable through normal operation, but the
/// prover's symbolic initial state can produce it. With both == 0, ethReserve = balance - msg.value
/// = 0, triggering division by zero.
rule deposit_reverts_when_uninitialized(env e) {
    require totalLiquidity() == 0;
    require getEthBalance() == 0;
    require e.msg.value > 0;
    deposit@withrevert(e);
    assert lastReverted;
}

// ─────────────────────────────────────────────
// withdraw() gate
// ─────────────────────────────────────────────

/// withdraw() reverts when caller requests more shares than they own.
rule withdraw_reverts_on_insufficient_shares(env e, uint256 amount) {
    require stateBounded(e);
    require amount > getLiquidityOf(e.msg.sender);

    withdraw@withrevert(e, amount);
    assert lastReverted;
}

/// withdraw() reverts when amount is zero.
rule withdraw_reverts_on_zero_amount(env e) {
    require stateBounded(e);
    withdraw@withrevert(e, 0);
    assert lastReverted;
}

// ─────────────────────────────────────────────
// Authorized reserve drain
// ─────────────────────────────────────────────

/// Only tokenToEth or withdraw can decrease the DEX ETH reserve.
/// Guards against any future function accidentally sending ETH out of the pool.
rule only_tokenToEth_or_withdraw_decreases_eth(env e, method f, calldataarg args)
    filtered { f -> f.contract == currentContract }
{
    require stateBounded(e);
    require token.balanceOf(currentContract)   <= token.totalSupply();
    require token.balanceOf(e.msg.sender)      <= token.totalSupply();
    require token.allowance(e.msg.sender, currentContract) <= token.totalSupply();
    require e.msg.sender != currentContract;

    uint256 ethBefore = getEthBalance();
    f(e, args);

    assert getEthBalance() < ethBefore =>
        f.selector == sig:tokenToEth(uint256).selector ||
        f.selector == sig:withdraw(uint256).selector;
}

/// Only ethToToken or withdraw can decrease the DEX token reserve.
/// Guards against any future function accidentally pulling tokens out of the pool.
rule only_ethToToken_or_withdraw_decreases_tokens(env e, method f, calldataarg args)
    filtered { f -> f.contract == currentContract }
{
    require stateBounded(e);
    require token.balanceOf(currentContract)   <= token.totalSupply();
    require token.balanceOf(e.msg.sender)      <= token.totalSupply();
    require token.allowance(e.msg.sender, currentContract) <= token.totalSupply();
    require e.msg.sender != currentContract;

    uint256 tokenBefore = getTokenBalance();
    f(e, args);

    assert getTokenBalance() < tokenBefore =>
        f.selector == sig:ethToToken().selector ||
        f.selector == sig:withdraw(uint256).selector;
}
