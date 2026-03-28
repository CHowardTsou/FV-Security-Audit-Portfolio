/*
 * VendorSanity.spec — Smoke tests for the Token Vendor
 *
 * PURPOSE: Verify that each function is reachable (can succeed) and that
 * non-view functions actually change state. These are "sanity" checks —
 * if any fail, something is fundamentally wrong with our Certora setup.
 *
 * KEY CONCEPTS INTRODUCED:
 * - `methods` block: declares function signatures Certora should know about
 * - `envfree`: marks functions that don't depend on msg.sender/msg.value/block.*
 * - `satisfy`: asks Certora to FIND an input that makes the body true (opposite of assert)
 * - `method f` + `filtered`: parametric rules that run once per function
 * - `lastStorage`: captures EVM storage snapshots for comparison
 */

// Tell Certora which contracts we're reasoning about
using VendorHarness as vendor;
using YourToken as token;

/*
 * Methods block: every external function the specs reference must be declared here.
 * - `envfree` means the function doesn't use msg.sender, msg.value, or block.* —
 *   you can call it without an `env` variable.
 * - Functions on linked contracts use the `ContractName.functionName` syntax.
 */
methods {
    // Vendor functions
    function buyTokens() external;
    function withdraw() external;
    function sellTokens(uint256) external;
    function tokensPerEth() external returns (uint256) envfree;
    function owner() external returns (address) envfree;

    // Harness helpers
    function getVendorTokenBalance() external returns (uint256) envfree;
    function getVendorEthBalance() external returns (uint256) envfree;

    // YourToken (linked contract)
    function YourToken.balanceOf(address) external returns (uint256) envfree;
    function YourToken.totalSupply() external returns (uint256) envfree;
}

/*
 * RULE: sanity_buyTokens_can_succeed
 *
 * `satisfy true` asks the Prover: "Find me ANY input where buyTokens()
 * completes without reverting." If this fails, it means buyTokens can
 * NEVER succeed — a sign that our linking or method declarations are wrong.
 *
 * Think of `satisfy` as an existence proof: ∃ inputs such that f succeeds.
 */
rule sanity_buyTokens_can_succeed {
    env e;
    buyTokens(e);
    satisfy true;
}

/*
 * RULE: sanity_sellTokens_can_succeed
 *
 * Same pattern — prove sellTokens is reachable.
 * Certora will find an env where the user has approved tokens,
 * the vendor has ETH, etc.
 */
rule sanity_sellTokens_can_succeed {
    env e;
    uint256 amount;
    sellTokens(e, amount);
    satisfy true;
}

/*
 * RULE: sanity_withdraw_can_succeed
 *
 * Prove the owner can withdraw. Certora will automatically
 * figure out that e.msg.sender must equal owner().
 */
rule sanity_withdraw_can_succeed {
    env e;
    withdraw(e);
    satisfy true;
}

/*
 * RULE: noop_detection
 *
 * A PARAMETRIC rule — it runs once for EACH non-view, non-pure function.
 * `method f` iterates over all public/external functions.
 * `filtered { f -> !f.isView && !f.isPure }` skips read-only functions.
 *
 * `satisfy` here asks: "For this function, does there exist an input
 * that actually changes the contract's storage?" If a function is a no-op
 * (changes nothing), this rule fails for it — catching dead code or
 * memory-vs-storage bugs.
 *
 * `lastStorage` is a CVL built-in that captures a snapshot of all EVM storage.
 */
rule noop_detection(method f) filtered { f -> !f.isView && !f.isPure } {
    env e;
    calldataarg args;

    storage before = lastStorage;
    f(e, args);
    storage after = lastStorage;

    satisfy before[currentContract] != after[currentContract];
}
