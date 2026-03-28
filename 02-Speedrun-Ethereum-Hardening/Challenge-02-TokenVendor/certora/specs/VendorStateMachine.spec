/*
 * VendorStateMachine.spec — Revert conditions and access control
 *
 * PURPOSE: Prove that the Vendor's "gates" work correctly:
 * - Functions revert when they should (0 ETH, 0 tokens)
 * - Access control is enforced (only owner can withdraw)
 * - No unintended access restrictions (anyone can buy/sell)
 *
 * KEY CONCEPTS INTRODUCED:
 * - `@withrevert`: lets a function revert without failing the rule
 * - `lastReverted`: true if the previous @withrevert call reverted
 * - `require e.msg.value == 0`: constrain non-payable function calls
 * - `nativeBalances[addr]`: CVL built-in to read ETH balances
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
//  REVERT CONDITIONS
// ═══════════════════════════════════════════════════

/*
 * RULE: buyTokens_reverts_on_zero_eth
 *
 * The contract checks `if (msg.value == 0) revert InvalidEthAmount()`.
 * We prove this is GUARANTEED — for ALL possible states and senders,
 * if msg.value == 0, buyTokens reverts. This is exhaustive, not sampled.
 *
 * `@withrevert` tells the Prover: "don't treat a revert as a counterexample.
 * Let the function revert and set `lastReverted = true`."
 * Then we `assert lastReverted` to prove the revert always happens.
 */
rule buyTokens_reverts_on_zero_eth {
    env e;
    require e.msg.value == 0;

    buyTokens@withrevert(e);

    assert lastReverted, "buyTokens must revert when msg.value == 0";
}

/*
 * RULE: sellTokens_reverts_on_zero_amount
 *
 * Same pattern — prove that sellTokens(0) always reverts.
 */
rule sellTokens_reverts_on_zero_amount {
    env e;
    require e.msg.value == 0; // sellTokens is not payable

    sellTokens@withrevert(e, 0);

    assert lastReverted, "sellTokens must revert when amount == 0";
}

// ═══════════════════════════════════════════════════
//  ACCESS CONTROL
// ═══════════════════════════════════════════════════

/*
 * RULE: withdraw_onlyOwner
 *
 * This is the power of formal verification vs fuzzing:
 * The Prover tries EVERY possible msg.sender that is NOT the owner.
 * If ANY of them can call withdraw() without reverting, you get a
 * concrete counterexample. This is a mathematical proof of access control.
 */
rule withdraw_onlyOwner {
    env e;
    require e.msg.sender != owner();
    require e.msg.value == 0; // withdraw is not payable

    withdraw@withrevert(e);

    assert lastReverted, "withdraw must revert for non-owner";
}

/*
 * RULE: withdraw_drains_all_eth
 *
 * When the owner calls withdraw, the vendor's ETH balance goes to 0.
 * This proves the function sends ALL ETH, not just some.
 *
 * Note: We require vendor has some ETH so the test is meaningful.
 * We also require the owner is not the vendor itself (self-transfer
 * would make balance assertions tricky).
 */
rule withdraw_drains_all_eth {
    env e;
    require e.msg.sender == owner();
    require e.msg.value == 0;
    require getVendorEthBalance() > 0;
    // Owner must not be the vendor itself (avoids self-transfer confusion)
    require owner() != currentContract;

    withdraw(e);

    assert getVendorEthBalance() == 0,
        "After withdraw, vendor ETH balance must be 0";
}

// ═══════════════════════════════════════════════════
//  OPEN ACCESS (anyone can buy/sell)
// ═══════════════════════════════════════════════════

/*
 * RULE: anyone_can_buy
 *
 * `satisfy` proves EXISTENCE: there is at least one non-owner address
 * that can successfully buy tokens. Combined with the absence of any
 * onlyOwner modifier on buyTokens, this confirms open access.
 */
rule anyone_can_buy {
    env e;
    require e.msg.value > 0;
    require e.msg.sender != owner();
    require e.msg.sender != currentContract;
    // Vendor must have enough tokens
    require getVendorTokenBalance() >= e.msg.value * tokensPerEth();

    buyTokens(e);

    satisfy true;
}

/*
 * RULE: anyone_can_sell
 *
 * Same open-access proof for sellTokens.
 * Requires the user has approved tokens and vendor has enough ETH.
 */
rule anyone_can_sell {
    env e;
    uint256 amount;
    require amount > 0;
    require e.msg.sender != owner();
    require e.msg.sender != currentContract;
    require e.msg.value == 0;
    // User must have tokens and approval
    require token.balanceOf(e.msg.sender) >= amount;
    require token.allowance(e.msg.sender, currentContract) >= amount;
    // Vendor must have enough ETH
    require getVendorEthBalance() >= amount / tokensPerEth();

    sellTokens(e, amount);

    satisfy true;
}
