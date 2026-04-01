// DEXAccounting.spec
// Balance delta rules, LP share conservation ghost, and cross-user isolation.
// All rules expected GREEN on the fixed DEX implementation.

using Balloons as token;

methods {
    // Harness getters
    function getEthBalance()              external returns (uint256) envfree;
    function getTokenBalance()            external returns (uint256) envfree;
    function getLiquidityOf(address)      external returns (uint256) envfree;
    function totalLiquidity()             external returns (uint256) envfree;
    function price(uint256, uint256, uint256) external returns (uint256) envfree;

    // Balloons (concrete dispatch via link)
    function Balloons.balanceOf(address)           external returns (uint256) envfree;
    function Balloons.allowance(address, address)  external returns (uint256) envfree;
    function Balloons.totalSupply()                external returns (uint256) envfree;
    function Balloons.transfer(address, uint256)   external returns (bool);
    function Balloons.transferFrom(address, address, uint256) external returns (bool);
}

// ─────────────────────────────────────────────
// Ghost: sum of all LP shares
// ─────────────────────────────────────────────

// persistent: prevents havoc after external calls (e.g. Balloons.transferFrom).
// Safe because this ghost only mirrors DEXHarness.liquidity[], which no external
// contract can write to.
persistent ghost mathint sumOfLiquidityShares {
    init_state axiom sumOfLiquidityShares == 0;
}

hook Sstore liquidity[KEY address user] uint256 newVal (uint256 oldVal) {
    sumOfLiquidityShares = sumOfLiquidityShares + to_mathint(newVal) - to_mathint(oldVal);
}

// ─────────────────────────────────────────────
// Common state bounding helper
// ─────────────────────────────────────────────

// Bound values to avoid spurious OZ ERC-20 unchecked-overflow CEXes.
// OZ _update() uses unchecked arithmetic; symbolic totalSupply at MAX_UINT256 corrupts balances.
definition tokenStateBounded(env e) returns bool =
    token.totalSupply() < 2^128 &&
    token.balanceOf(currentContract)   <= token.totalSupply() &&
    token.balanceOf(e.msg.sender)      <= token.totalSupply() &&
    token.allowance(e.msg.sender, currentContract) <= token.totalSupply();

definition poolStateBounded(env e) returns bool =
    totalLiquidity()  > 0 &&
    totalLiquidity()  < 2^128 &&
    getEthBalance()   < 2^128 &&
    getTokenBalance() < 2^128 &&
    e.msg.value       < 2^128;

// ─────────────────────────────────────────────
// Valid state invariant: pool solvency
// ─────────────────────────────────────────────

/// An initialized pool always has positive ETH and token reserves.
/// Ensures integer division in withdraw/tokenToEth can never drain one side to zero
/// while leaving totalLiquidity > 0.
invariant initialized_pool_has_positive_reserves()
    totalLiquidity() > 0 => getEthBalance() > 0 && getTokenBalance() > 0
    {
        preserved with (env e) {
            require poolStateBounded(e);
            require tokenStateBounded(e);
        }
        preserved init(uint256 tokens) with (env e) {
            require totalLiquidity() == 0;
            require e.msg.value > 0;
            require tokens > 0;
            require getEthBalance() == 0;
            require tokenStateBounded(e);
        }
        preserved Balloons.transfer(address to, uint256 value) with (env e) {
            require e.msg.sender != currentContract;
            require tokenStateBounded(e);
        }
        preserved Balloons.transferFrom(address from, address to, uint256 value) with (env e) {
            require from != currentContract;
            require tokenStateBounded(e);
            require token.balanceOf(from) <= token.totalSupply();
        }
    }

// ─────────────────────────────────────────────
// LP share conservation invariant
// ─────────────────────────────────────────────

/// totalLiquidity always equals the sum of every individual LP share.
/// Proved as a parametric rule (inductive step) over all functions.
invariant totalLiquidity_equals_sum_of_shares()
    to_mathint(totalLiquidity()) == sumOfLiquidityShares
    {
        preserved init(uint256 tokens) with (env e) {
            // Pre-state: both are zero before init
            require sumOfLiquidityShares == 0;
            require totalLiquidity() == 0;
            // Ghost-storage consistency: liquidity[msg.sender] must equal what the ghost
            // thinks it is (0). Without this, the symbolic pre-state can set
            // liquidity[msg.sender] to an arbitrary non-zero value while sumOfLiquidityShares == 0,
            // making the hook update ghost = 0 + newVal - oldVal produce a wrong result.
            // Sound because any reachable state with totalLiquidity == 0 has all LP shares == 0.
            require getLiquidityOf(e.msg.sender) == 0;
        }
        preserved deposit() with (env e) {
            require to_mathint(totalLiquidity()) == sumOfLiquidityShares;
            require poolStateBounded(e);
        }
        preserved withdraw(uint256 amount) with (env e) {
            require to_mathint(totalLiquidity()) == sumOfLiquidityShares;
            require poolStateBounded(e);
        }
    }

// ─────────────────────────────────────────────
// ethToToken balance deltas
// ─────────────────────────────────────────────

/// After ethToToken: DEX ETH balance increases by msg.value and token balance decreases by tokenOutput.
/// Note: getEthBalance() before the call gives the pre-msg.value balance (the ethReserve used in price()).
rule ethToToken_eth_increases_tokens_decrease(env e) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require e.msg.value > 0;
    // Exclude self-call: if msg.sender == address(this), ETH is self-transferred and
    // address(this).balance doesn't change, breaking the pre-call balance formula.
    require e.msg.sender != currentContract;

    // Pre-call state (before msg.value is credited)
    uint256 ethReservePre = getEthBalance();
    uint256 tokenBefore   = getTokenBalance();

    uint256 tokenOut = ethToToken(e);

    // ETH increases by msg.value (no ETH leaves in ethToToken)
    assert to_mathint(getEthBalance()) == to_mathint(ethReservePre) + to_mathint(e.msg.value);
    // Tokens decrease by exactly tokenOut
    assert to_mathint(getTokenBalance()) == to_mathint(tokenBefore) - to_mathint(tokenOut);
    // tokenOut matches the AMM price formula
    assert tokenOut == price(e.msg.value, ethReservePre, tokenBefore);
}

// ─────────────────────────────────────────────
// tokenToEth balance deltas
// ─────────────────────────────────────────────

/// After tokenToEth: DEX token balance increases by tokenInput.
rule tokenToEth_token_balance_increases_by_input(env e, uint256 tokenInput) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require tokenInput > 0 && tokenInput < 2^128;
    require e.msg.value == 0; // tokenToEth is not payable

    uint256 tokenBefore = getTokenBalance();
    tokenToEth(e, tokenInput);
    assert to_mathint(getTokenBalance()) == to_mathint(tokenBefore) + to_mathint(tokenInput);
}

/// After tokenToEth: ETH output equals price(tokenInput, tokenReserve, ethReserve).
/// Verifies Bug B is fixed — implementation now uses address(this).balance, not totalLiquidity.
rule tokenToEth_eth_output_matches_price(env e, uint256 tokenInput) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require tokenInput > 0 && tokenInput < 2^128;
    require e.msg.value == 0;
    require token.allowance(e.msg.sender, currentContract) >= tokenInput;
    require token.balanceOf(e.msg.sender) >= tokenInput;

    uint256 ethBefore   = getEthBalance();
    uint256 tokenBefore = getTokenBalance();

    uint256 ethOut = tokenToEth(e, tokenInput);

    assert ethOut == price(tokenInput, tokenBefore, ethBefore);
}

// ─────────────────────────────────────────────
// deposit balance deltas
// ─────────────────────────────────────────────

/// After deposit: totalLiquidity increases by the correct liquidityMinted amount.
/// getEthBalance() before the call is the pre-deposit ETH reserve (before msg.value is added).
rule deposit_increases_total_liquidity(env e) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require e.msg.value > 0;
    // Exclude self-call: msg.sender == address(this) makes ETH self-transfer leave balance
    // unchanged, so contract ethReserve = balance - msg.value != pre-call balance.
    require e.msg.sender != currentContract;

    uint256 liqBefore     = totalLiquidity();
    uint256 ethReservePre = getEthBalance(); // pre-call: before msg.value arrives

    deposit(e);

    // liqMinted = msg.value * totalLiquidityBefore / ethReserveBefore  (integer division)
    mathint liqMinted = to_mathint(e.msg.value) * to_mathint(liqBefore) / to_mathint(ethReservePre);
    assert to_mathint(totalLiquidity()) == to_mathint(liqBefore) + liqMinted;
}

/// After deposit: caller's LP share increases by liquidityMinted.
rule deposit_increases_caller_shares(env e) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require e.msg.value > 0;
    require e.msg.sender != currentContract;

    uint256 sharesBefore  = getLiquidityOf(e.msg.sender);
    uint256 liqBefore     = totalLiquidity();
    uint256 ethReservePre = getEthBalance();

    deposit(e);

    mathint liqMinted = to_mathint(e.msg.value) * to_mathint(liqBefore) / to_mathint(ethReservePre);
    assert to_mathint(getLiquidityOf(e.msg.sender)) == to_mathint(sharesBefore) + liqMinted;
}

/// After init: totalLiquidity equals msg.value exactly.
/// Requires getEthBalance() == 0: DEX has no receive(), so pre-existing balance > 0 is
/// unreachable, but the prover's symbolic state can produce it. With balance == 0,
/// initialLiquidity = address(this).balance = msg.value, so totalLiquidity == msg.value.
rule init_sets_totalLiquidity_to_msg_value(env e, uint256 tokens) {
    require totalLiquidity() == 0;
    require e.msg.value > 0 && e.msg.value < 2^128;
    require tokens > 0;
    require getEthBalance() == 0;
    init(e, tokens);
    assert totalLiquidity() == e.msg.value;
}

/// After deposit: token balance increases by exactly (msg.value * tokenReserve / ethReserve) + 1.
/// Verifies the full token debit formula, complementing deposit_increases_total_liquidity.
rule deposit_pulls_correct_token_amount(env e) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require e.msg.value > 0;
    require e.msg.sender != currentContract;

    uint256 ethReservePre = getEthBalance();
    uint256 tokenBefore   = getTokenBalance();

    deposit(e);

    mathint tokensDeposited = to_mathint(e.msg.value) * to_mathint(tokenBefore) / to_mathint(ethReservePre) + 1;
    assert to_mathint(getTokenBalance()) == to_mathint(tokenBefore) + tokensDeposited;
}

// ─────────────────────────────────────────────
// withdraw balance deltas
// ─────────────────────────────────────────────

/// After withdraw(amount): caller's LP share decreases by exactly amount.
rule withdraw_decreases_caller_shares_by_amount(env e, uint256 amount) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require amount > 0;
    require getLiquidityOf(e.msg.sender) >= amount;
    require e.msg.value == 0;

    uint256 sharesBefore = getLiquidityOf(e.msg.sender);
    withdraw(e, amount);
    assert to_mathint(getLiquidityOf(e.msg.sender)) == to_mathint(sharesBefore) - to_mathint(amount);
}

/// After withdraw(amount): totalLiquidity decreases by exactly amount.
rule withdraw_decreases_total_liquidity_by_amount(env e, uint256 amount) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require amount > 0;
    require getLiquidityOf(e.msg.sender) >= amount;
    require e.msg.value == 0;

    uint256 liqBefore = totalLiquidity();
    withdraw(e, amount);
    assert to_mathint(totalLiquidity()) == to_mathint(liqBefore) - to_mathint(amount);
}

// ─────────────────────────────────────────────
// Cross-user isolation
// ─────────────────────────────────────────────

/// ethToToken never modifies any user's LP share balance.
rule swaps_do_not_affect_any_lp_shares(env e, address other) {
    require poolStateBounded(e);
    require tokenStateBounded(e);

    uint256 sharesBefore = getLiquidityOf(other);
    ethToToken(e);
    assert getLiquidityOf(other) == sharesBefore;
}

/// tokenToEth never modifies any user's LP share balance.
rule tokenToEth_does_not_affect_any_lp_shares(env e, uint256 tokenInput, address other) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require tokenInput > 0 && tokenInput < 2^128;
    require e.msg.value == 0;

    uint256 sharesBefore = getLiquidityOf(other);
    tokenToEth(e, tokenInput);
    assert getLiquidityOf(other) == sharesBefore;
}

/// deposit does not modify any other user's LP shares.
rule deposit_does_not_affect_other_users_shares(env e, address other) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require other != e.msg.sender;
    require e.msg.value > 0;

    uint256 sharesBefore = getLiquidityOf(other);
    deposit(e);
    assert getLiquidityOf(other) == sharesBefore;
}

// ─────────────────────────────────────────────
// Constant product non-decrease (fee accrual)
//
// The core AMM invariant: after every swap k' = ethReserve' * tokenReserve' >= k.
// Proof sketch: the 997/1000 fee factor means the pool retains more value than
// it pays out. For ethToToken: 1000 * tokenInput >= 997 * tokenInput, which
// is sufficient to prove (ethAfter * tokenAfter >= ethReservePre * tokenBefore).
// ─────────────────────────────────────────────

/// k never decreases after ethToToken.
rule ethToToken_nondecreasing_k(env e) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require e.msg.value > 0;
    require e.msg.sender != currentContract;

    uint256 ethReservePre = getEthBalance();
    uint256 tokenBefore   = getTokenBalance();

    ethToToken(e);

    uint256 ethAfter   = getEthBalance();
    uint256 tokenAfter = getTokenBalance();

    assert to_mathint(ethAfter) * to_mathint(tokenAfter) >=
           to_mathint(ethReservePre) * to_mathint(tokenBefore);
}

/// k never decreases after tokenToEth.
rule tokenToEth_nondecreasing_k(env e, uint256 tokenInput) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require tokenInput > 0 && tokenInput < 2^128;
    require e.msg.value == 0;
    require e.msg.sender != currentContract;
    require token.allowance(e.msg.sender, currentContract) >= tokenInput;
    require token.balanceOf(e.msg.sender) >= tokenInput;

    uint256 ethBefore   = getEthBalance();
    uint256 tokenBefore = getTokenBalance();

    tokenToEth(e, tokenInput);

    uint256 ethAfter   = getEthBalance();
    uint256 tokenAfter = getTokenBalance();

    assert to_mathint(ethAfter) * to_mathint(tokenAfter) >=
           to_mathint(ethBefore) * to_mathint(tokenBefore);
}

// ─────────────────────────────────────────────
// Proportional withdrawal correctness
//
// Verifies the exact formula used by withdraw():
//   ethOut   = amount * ethReserve  / totalLiquidity
//   tokenOut = amount * tokenReserve / totalLiquidity
// ─────────────────────────────────────────────

/// ETH returned by withdraw equals the proportional share of the ETH reserve.
rule withdraw_returns_proportional_eth(env e, uint256 amount) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require amount > 0;
    require getLiquidityOf(e.msg.sender) >= amount;
    require e.msg.value == 0;

    uint256 ethReservePre  = getEthBalance();
    uint256 totalLiqBefore = totalLiquidity();

    uint256 ethOut; uint256 tokenOut;
    ethOut, tokenOut = withdraw(e, amount);

    assert to_mathint(ethOut) ==
           to_mathint(amount) * to_mathint(ethReservePre) / to_mathint(totalLiqBefore);
}

/// Tokens returned by withdraw equal the proportional share of the token reserve.
rule withdraw_returns_proportional_tokens(env e, uint256 amount) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require amount > 0;
    require getLiquidityOf(e.msg.sender) >= amount;
    require e.msg.value == 0;

    uint256 tokenBefore    = getTokenBalance();
    uint256 totalLiqBefore = totalLiquidity();

    uint256 ethOut; uint256 tokenOut;
    ethOut, tokenOut = withdraw(e, amount);

    assert to_mathint(tokenOut) ==
           to_mathint(amount) * to_mathint(tokenBefore) / to_mathint(totalLiqBefore);
}

// ─────────────────────────────────────────────
// Deposit economic correctness
// ─────────────────────────────────────────────

/// After deposit the token/ETH ratio does not decrease.
/// The +1 in tokensDeposited makes it slightly more token-heavy, giving:
///   tokenAfter * ethReservePre >= tokenBefore * ethAfter
rule deposit_preserves_price_ratio(env e) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require e.msg.value > 0;
    require e.msg.sender != currentContract;
    require getEthBalance() > 0;
    require getTokenBalance() > 0;

    uint256 ethReservePre = getEthBalance();
    uint256 tokenBefore   = getTokenBalance();

    deposit(e);

    uint256 ethAfter   = getEthBalance();
    uint256 tokenAfter = getTokenBalance();

    assert to_mathint(tokenAfter) * to_mathint(ethReservePre) >=
           to_mathint(tokenBefore) * to_mathint(ethAfter);
}

/// Existing LP shares are worth at least as much ETH after a deposit.
/// Floor division in liqMinted makes totalLiqAfter slightly smaller than exact,
/// so existing shares earn a rounding bonus: existing ETH-per-share can only increase.
///   ethAfter * totalLiqBefore >= ethReservePre * totalLiqAfter
rule deposit_does_not_decrease_eth_per_share(env e) {
    require poolStateBounded(e);
    require tokenStateBounded(e);
    require e.msg.value > 0;
    require e.msg.sender != currentContract;
    require getEthBalance() > 0;

    uint256 ethReservePre  = getEthBalance();
    uint256 totalLiqBefore = totalLiquidity();

    deposit(e);

    uint256 ethAfter      = getEthBalance();
    uint256 totalLiqAfter = totalLiquidity();

    assert to_mathint(ethAfter) * to_mathint(totalLiqBefore) >=
           to_mathint(ethReservePre) * to_mathint(totalLiqAfter);
}
