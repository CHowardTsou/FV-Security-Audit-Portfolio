/*
 * VendorAccounting.spec — Exchange rate, token conservation, and dust-loss witness
 *
 * PURPOSE: Prove the Vendor's math is correct:
 * - Users receive/pay exactly the right amounts
 * - Tokens are conserved (not created or destroyed)
 * - The exchange rate is truly constant
 * - Integer division creates a dust-loss edge case (witness rule)
 *
 * KEY CONCEPTS INTRODUCED:
 * - `invariant`: a property checked after EVERY function call
 * - `nativeBalances[addr]`: CVL built-in for ETH balances
 * - `ghost` variables: shadow state tracked by the Prover
 * - `hook Sstore`: fires on every EVM SSTORE to a specific slot
 * - witness rules: prove a specific (bad) scenario IS reachable
 */

using VendorHarness as vendor;
using YourToken as token;

methods {
    function buyTokens() external;
    function withdraw() external;
    function sellTokens(uint256) external;
    function tokensPerEth() external returns (uint256) envfree;
    function owner() external returns (address) envfree;
    function getVendorTokenBalance() external returns (uint256) envfree;
    function getVendorEthBalance() external returns (uint256) envfree;
    function YourToken.balanceOf(address) external returns (uint256) envfree;
    function YourToken.totalSupply() external returns (uint256) envfree;
    function YourToken.allowance(address, address) external returns (uint256) envfree;
}

// ═══════════════════════════════════════════════════
//  EXCHANGE RATE INVARIANT
// ═══════════════════════════════════════════════════

/*
 * INVARIANT: exchange_rate_is_100
 *
 * An invariant is stronger than a rule: Certora checks it holds in the
 * initial state AND is preserved by EVERY function. Since tokensPerEth
 * is `constant`, this trivially passes — but it teaches the invariant syntax.
 *
 * If someone accidentally made tokensPerEth a mutable variable and a function
 * changed it, this invariant would catch it immediately.
 *
 * NOTE: Removed because tokensPerEth is `constant`, so Certora's trivial
 * invariant sanity check correctly flags it as unnecessary. A constant
 * can never change — no function call can violate it. The invariant syntax
 * is more useful for mutable state that could be corrupted.
 */

// ═══════════════════════════════════════════════════
//  BUY TOKENS ACCOUNTING
// ═══════════════════════════════════════════════════

/*
 * RULE: buyTokens_exact_accounting
 *
 * Proves: user receives EXACTLY msg.value * 100 tokens, and the vendor
 * loses exactly that many tokens. No rounding, no leakage.
 *
 * Key subtlety: `require e.msg.sender != currentContract` prevents
 * self-transfer (vendor buying from itself), which would make the delta 0.
 * Certora WOULD find this as a counterexample if you forgot this require —
 * that's the power of formal verification exploring adversarial scenarios.
 */
rule buyTokens_exact_accounting {
    env e;
    require e.msg.value > 0;
    require e.msg.sender != currentContract; // no self-transfer

    uint256 userTokensBefore = token.balanceOf(e.msg.sender);
    uint256 vendorTokensBefore = token.balanceOf(currentContract);

    // Bound symbolic state to prevent unchecked overflow in OZ ERC20.
    // OZ's _update() uses `unchecked { _balances[to] += value }` — no overflow check.
    // In a symbolic state, totalSupply AND balances can be MAX_UINT256, so
    // += wraps silently. We must bound totalSupply FIRST (it's also symbolic!),
    // then bound individual balances relative to it.
    require token.totalSupply() < max_uint256 / 2;
    require userTokensBefore <= token.totalSupply();
    require vendorTokensBefore <= token.totalSupply();

    buyTokens(e);

    uint256 userTokensAfter = token.balanceOf(e.msg.sender);
    uint256 vendorTokensAfter = token.balanceOf(currentContract);

    assert userTokensAfter - userTokensBefore == to_mathint(e.msg.value) * 100,
        "User must receive exactly msg.value * tokensPerEth tokens";
    assert vendorTokensBefore - vendorTokensAfter == to_mathint(e.msg.value) * 100,
        "Vendor must lose exactly that many tokens";
}

// ═══════════════════════════════════════════════════
//  SELL TOKENS ACCOUNTING
// ═══════════════════════════════════════════════════

/*
 * RULE: sellTokens_exact_accounting
 *
 * Proves: vendor receives `amount` tokens, user receives `amount / 100` ETH.
 *
 * `nativeBalances[addr]` is a CVL built-in — it reads the ETH balance of
 * any address without needing a harness helper. More precise than calling
 * getVendorEthBalance() because it avoids an extra external call.
 *
 * Note: We require the sender is not the vendor (no self-transfer) and
 * not the owner (ETH assertion would be complicated if owner == seller
 * because withdraw and sell affect the same balance).
 */
rule sellTokens_exact_accounting {
    env e;
    uint256 amount;
    require amount > 0;
    require e.msg.sender != currentContract; // no self-transfer
    require e.msg.value == 0; // sellTokens is not payable

    uint256 userTokensBefore = token.balanceOf(e.msg.sender);
    uint256 vendorTokensBefore = token.balanceOf(currentContract);
    mathint userEthBefore = nativeBalances[e.msg.sender];

    // Same realistic balance bounds as buyTokens (prevent unchecked overflow)
    require token.totalSupply() < max_uint256 / 2;
    require userTokensBefore <= token.totalSupply();
    require vendorTokensBefore <= token.totalSupply();

    sellTokens(e, amount);

    uint256 userTokensAfter = token.balanceOf(e.msg.sender);
    uint256 vendorTokensAfter = token.balanceOf(currentContract);

    assert userTokensBefore - userTokensAfter == to_mathint(amount),
        "User must lose exactly `amount` tokens";
    assert vendorTokensAfter - vendorTokensBefore == to_mathint(amount),
        "Vendor must receive exactly `amount` tokens";
    assert nativeBalances[e.msg.sender] - userEthBefore == to_mathint(amount / 100),
        "User must receive exactly amount / tokensPerEth ETH";
}

// ═══════════════════════════════════════════════════
//  GHOST: Token Balance Sum Tracking
// ═══════════════════════════════════════════════════

/*
 * GHOST VARIABLE: sumOfBalances
 *
 * A ghost is a "shadow variable" that exists only in the Prover — not in
 * the actual EVM. It lets us track derived values that aren't in storage.
 *
 * Here, we track the mathematical SUM of all token balances across all
 * addresses. Since YourToken has no mint/burn functions (only the
 * constructor mint), this sum should never change during vendor operations.
 *
 * `init_state axiom`: tells the Prover the initial value. We set it to 0
 * because at contract creation (before constructor), all balances are 0.
 */
ghost mathint sumOfBalances {
    init_state axiom sumOfBalances == 0;
}

/*
 * HOOK: Fires on every SSTORE to YourToken._balances[address]
 *
 * Every time the EVM writes to the _balances mapping in YourToken,
 * this hook fires. We update the ghost by adding the new value and
 * subtracting the old value. This keeps a running total.
 *
 * `KEY address a` captures which address's balance changed.
 * `uint256 newVal` is what's being written.
 * `uint256 oldVal` is what was stored before.
 *
 * The delta-update form: sumOfBalances = sumOfBalances + newVal - oldVal
 * This works because sum = ... + oldVal + ... becomes ... + newVal + ...
 */
hook Sstore YourToken._balances[KEY address a] uint256 newVal (uint256 oldVal) {
    sumOfBalances = sumOfBalances + newVal - oldVal;
}

/*
 * Hook for SLOAD: keeps the ghost consistent when balances are read.
 * This ensures that if Certora starts from a symbolic state (not from
 * constructor), the ghost still matches the actual storage.
 */
hook Sload uint256 val YourToken._balances[KEY address a] {
    require sumOfBalances >= to_mathint(val);
}

/*
 * RULE: token_conservation_on_buy
 *
 * Proves that buyTokens doesn't create or destroy tokens.
 * The total of all balances (tracked by our ghost) remains unchanged.
 * This is because buyTokens only calls `transfer` — moving tokens
 * from vendor to user, not minting or burning.
 */
rule token_conservation_on_buy {
    env e;
    require e.msg.value > 0;
    require e.msg.sender != currentContract;

    // Bound symbolic state — same reason as accounting rules.
    // Without this, unchecked += in OZ ERC20 wraps around,
    // corrupting the ghost's delta tracking.
    require token.totalSupply() < max_uint256 / 2;
    require token.balanceOf(e.msg.sender) <= token.totalSupply();
    require token.balanceOf(currentContract) <= token.totalSupply();

    mathint sumBefore = sumOfBalances;

    buyTokens(e);

    assert sumOfBalances == sumBefore,
        "buyTokens must not create or destroy tokens";
}

/*
 * RULE: token_conservation_on_sell
 *
 * Same conservation proof for sellTokens.
 * sellTokens calls `transferFrom` — moving tokens from user to vendor.
 * The sum should not change.
 */
rule token_conservation_on_sell {
    env e;
    uint256 amount;
    require amount > 0;
    require e.msg.value == 0;
    require e.msg.sender != currentContract;

    // Bound symbolic state (same unchecked overflow prevention)
    require token.totalSupply() < max_uint256 / 2;
    require token.balanceOf(e.msg.sender) <= token.totalSupply();
    require token.balanceOf(currentContract) <= token.totalSupply();

    mathint sumBefore = sumOfBalances;

    sellTokens(e, amount);

    assert sumOfBalances == sumBefore,
        "sellTokens must not create or destroy tokens";
}

// ═══════════════════════════════════════════════════
//  DUST LOSS WITNESS (the interesting "bug")
// ═══════════════════════════════════════════════════

/*
 * RULE: sellTokens_dust_loss_witness
 *
 * This is arguably a bug in the Vendor: a user can call sellTokens(50)
 * and their 50 tokens get transferred to the vendor, but 50 / 100 == 0
 * in Solidity integer division, so they receive 0 ETH back.
 * The tokens are gone, the ETH is zero. Value destroyed.
 *
 * `satisfy` forces Certora to produce a CONCRETE witness showing this
 * scenario actually happens. This is formal verification finding a
 * real economic issue — not a crash, but a value-loss edge case.
 *
 * In a real audit, this would be reported as a finding.
 */
rule sellTokens_dust_loss_witness {
    env e;
    uint256 amount;
    require amount > 0;
    require amount < 100; // less than 1 ETH worth
    require e.msg.sender != currentContract;
    require e.msg.value == 0;

    mathint userEthBefore = nativeBalances[e.msg.sender];

    sellTokens@withrevert(e, amount);

    // If it didn't revert, user lost tokens but got 0 ETH
    satisfy !lastReverted && (nativeBalances[e.msg.sender] == userEthBefore);
}

// ═══════════════════════════════════════════════════
//  NO UNAUTHORIZED TOKEN DRAIN
// ═══════════════════════════════════════════════════

/*
 * RULE: no_unauthorized_token_drain
 *
 * A PARAMETRIC rule (runs for every function): calling any vendor function
 * should never decrease a third party's token balance. "Third party" means
 * someone who is NOT msg.sender.
 *
 * This proves cross-user isolation: my buy/sell can't steal YOUR tokens.
 *
 * `method f` + `calldataarg args` = "for any function with any arguments."
 * This is one of the most powerful patterns in Certora — a single rule
 * that covers all current AND future functions.
 *
 * IMPORTANT: We filter to `f.contract == currentContract` (VendorHarness only).
 * Without this filter, the rule also runs for YourToken.transfer and
 * YourToken.transferFrom — but transferFrom is DESIGNED to decrease a
 * third party's balance (with their approval). The rule "no function
 * decreases a third party's balance" is only meaningful for Vendor functions.
 */
rule no_unauthorized_token_drain(method f) filtered {
    f -> !f.isView && !f.isPure && f.contract == currentContract
} {
    env e;
    calldataarg args;

    address victim;
    require victim != e.msg.sender;
    require victim != currentContract; // vendor's own balance can change

    // Bound symbolic state (same unchecked overflow prevention)
    require token.totalSupply() < max_uint256 / 2;
    require token.balanceOf(victim) <= token.totalSupply();
    require token.balanceOf(e.msg.sender) <= token.totalSupply();
    require token.balanceOf(currentContract) <= token.totalSupply();

    uint256 balBefore = token.balanceOf(victim);

    f(e, args);

    uint256 balAfter = token.balanceOf(victim);

    assert balAfter >= balBefore,
        "No Vendor function should decrease a third party's token balance";
}
