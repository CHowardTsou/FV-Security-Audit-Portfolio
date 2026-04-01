// DEXSanity.spec
// Reachability proofs and pure-function smoke tests.
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
// Pure function properties (price)
// ─────────────────────────────────────────────

/// price() output is strictly less than yReserves — the pool can never output more than it holds.
rule price_output_less_than_reserve(uint256 xInput, uint256 xReserves, uint256 yReserves) {
    require xInput    > 0 && xInput    < 2^128;
    require xReserves > 0 && xReserves < 2^128;
    require yReserves > 0 && yReserves < 2^128;

    uint256 out = price(xInput, xReserves, yReserves);
    assert out < yReserves;
}

// NOTE: price() can return 0 due to integer division truncation when xInput is tiny
// relative to xReserves (e.g. price(2, 8, 4) = 7976/9994 = 0). This is correct
// Solidity behavior, not a bug. No positivity rule is written here.

/// price() is non-decreasing in xInput: a larger input yields a larger or equal output.
/// Monotonicity is the formal basis for "more ETH in -> more tokens out".
rule price_monotone(uint256 x1, uint256 x2, uint256 r, uint256 y) {
    require x1 > 0 && x1 < 2^128;
    require x2 > 0 && x2 < 2^128;
    require r  > 0 && r  < 2^128;
    require y  > 0 && y  < 2^128;
    require x1 >= x2;
    assert price(x1, r, y) >= price(x2, r, y);
}

// ─────────────────────────────────────────────
// Reachability: each function can complete
// ─────────────────────────────────────────────

/// init() can succeed and bootstrap the pool.
rule satisfy_init_succeeds(env e, uint256 tokens) {
    require totalLiquidity() == 0;
    require e.msg.value > 0 && e.msg.value < 2^128;
    require tokens > 0;

    init(e, tokens);

    satisfy totalLiquidity() > 0;
}

/// ethToToken() can produce token output.
rule satisfy_ethToToken_produces_output(env e) {
    require e.msg.value > 0 && e.msg.value < 2^128;
    require totalLiquidity() > 0;
    require getTokenBalance() > 0;
    require getEthBalance() >= e.msg.value;
    require getEthBalance() < 2^128;

    uint256 out = ethToToken(e);
    satisfy out > 0;
}

/// deposit() can mint LP shares.
rule satisfy_deposit_mints_shares(env e) {
    uint256 liquidityBefore = totalLiquidity();
    require e.msg.value > 0 && e.msg.value < 2^128;
    require liquidityBefore > 0 && liquidityBefore < 2^128;
    require getEthBalance() > e.msg.value;
    require getEthBalance() < 2^128;
    require getTokenBalance() < 2^128;

    deposit(e);

    satisfy totalLiquidity() > liquidityBefore;
}

/// withdraw() can return ETH to the caller.
rule satisfy_withdraw_returns_eth(env e, uint256 amount) {
    require amount > 0 && amount < 2^128;
    require getLiquidityOf(e.msg.sender) >= amount;
    require totalLiquidity() > 0 && totalLiquidity() < 2^128;
    require getEthBalance() > 0 && getEthBalance() < 2^128;
    require getTokenBalance() > 0 && getTokenBalance() < 2^128;

    uint256 ethOut; uint256 tokenOut;
    ethOut, tokenOut = withdraw(e, amount);

    satisfy ethOut > 0;
}
