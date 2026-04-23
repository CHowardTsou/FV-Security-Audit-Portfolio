/**
 * Shared setup for WhitelistOracle verification.
 *
 * - External SimpleOracle calls are routed via DISPATCHER(true) so each
 *   oracle instance retains its own storage.
 * - setup(e): environment-only constraints (used in Sanity, base rules).
 * - setupValidState(e): invoked once V-01..V-03 are proven in Step 9.
 */

using SimpleOracle as _simpleOracle;

methods {
    // WhitelistOracle harness accessors
    function getOraclesLength() external returns (uint256) envfree;
    function getOracleAt(uint256) external returns (address) envfree;
    function getOraclePriceValueAt(uint256) external returns (uint256) envfree;
    function getOracleTimestampAt(uint256) external returns (uint256) envfree;
    function getOracleOwnerAt(uint256) external returns (address) envfree;
    function STALE_DATA_WINDOW() external returns (uint256) envfree;
    function owner() external returns (address) envfree;

    // Wildcard DISPATCHER routes each oracles[i].getPrice() call through
    // SimpleOracle's real bytecode. This is needed because `getPrice()`
    // shares a selector between WhitelistOracle (1 return) and
    // SimpleOracle (2 returns); conf enables optimistic_summary_recursion
    // with limit 1 — the nesting here is exactly 1 level deep.
    function _.getPrice() external => DISPATCHER(true);
    function _.setPrice(uint256) external => DISPATCHER(true);
    function _.price() external => DISPATCHER(true);
    function _.timestamp() external => DISPATCHER(true);
    function _.owner() external => DISPATCHER(true);
}

/**
 * Minimal environment constraints. Used by Sanity and basic rules.
 * - Caller is a concrete EOA (non-zero)
 * - Block timestamp is non-zero and bounded well below max_uint64 so
 *   that `currentTime - time` arithmetic has a predictable regime.
 * - No ETH sent (WhitelistOracle has no payable functions).
 */
function setup(env e) {
    require e.msg.sender != 0;
    require e.msg.value == 0;
    require e.block.timestamp > 0;
    require e.block.timestamp < 2^64;
}

/**
 * setupValidState(e): Step 9 invariants composed as a shared precondition.
 *
 * Any spec that imports setup.spec can call setupValidState(e) to assume
 * all proven invariants. Note: ghosts + hooks are defined in ValidState.spec,
 * so specs consuming setupValidState must also import that file's hooks
 * transitively — either by importing ValidState.spec or by including its
 * ghost declarations. For this campaign the downstream specs declare the
 * ghosts locally when needed.
 *
 * V-02 (uniqueness) is NOT composed here: it cannot be proven with
 * Certora's symbolic CREATE semantics (address collision with existing
 * entries is admissible in the model even though impossible in EVM).
 * Documented in MODELING_DEBT.md.
 */
function setupValidState(env e) {
    setup(e);
    // V-01 and ghostLenMatches must be requireInvariant'd by the caller
    // after locally declaring the ghosts + hooks. Kept here as a hook
    // point; filled in per-spec to avoid ghost-declaration collisions.
}
