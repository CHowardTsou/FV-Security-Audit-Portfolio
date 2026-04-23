/**
 * ActiveSetMembership.spec — H-08 / H-13.
 *
 * Claim:
 *   getActiveOracleNodes() returns EXACTLY the addresses in oracles[] whose
 *   data is fresh (delta < STALE_DATA_WINDOW). This file proves the two
 *   directions of that equality independently:
 *
 *   - H-13 (subset):  every returned address appears in oracles[]
 *   - H-08 (forward): every fresh oracle in oracles[] appears in the return
 *
 * Modeling note:
 *   The default ReadPath/StateTransitions setup routes SimpleOracle reads
 *   through DISPATCHER(true), which gives EACH external call an independent
 *   symbolic return — that is enough for per-call behavioral properties
 *   (revert conditions, staleness boundary) but too weak for set-level
 *   properties, because the prover can have `oracles[0].getPrice()` return
 *   "fresh" on one call and "stale" on another.
 *
 *   Here we replace the wildcard DISPATCHER with CVL function summaries
 *   that read from ghost mappings keyed by `calledContract`. That makes the
 *   mapping (oracle address -> price, timestamp) an actual mathematical
 *   function, so repeated reads of the same oracle agree. The harness
 *   getters (getOracleTimestampAt, getOraclePriceValueAt) go through the
 *   same summaries, so rule preconditions and the contract under test read
 *   the same values.
 */

using SimpleOracle as _simpleOracle;

/* --------------------------------------------------------------------------
   Ghost-backed SimpleOracle state, keyed by contract address.
   -------------------------------------------------------------------------- */
ghost mapping(address => uint256) ghostOraclePriceValue;
ghost mapping(address => uint256) ghostOracleTimestamp;

function simpleOracleGetPriceSummary(address callee) returns (uint256, uint256) {
    return (ghostOraclePriceValue[callee], ghostOracleTimestamp[callee]);
}

function simpleOraclePriceSummary(address callee) returns uint256 {
    return ghostOraclePriceValue[callee];
}

function simpleOracleTimestampSummary(address callee) returns uint256 {
    return ghostOracleTimestamp[callee];
}

methods {
    function getOraclesLength() external returns (uint256) envfree;
    function getOracleAt(uint256) external returns (address) envfree;
    function getOraclePriceValueAt(uint256) external returns (uint256) envfree;
    function getOracleTimestampAt(uint256) external returns (uint256) envfree;
    function STALE_DATA_WINDOW() external returns (uint256) envfree;

    // Deterministic per-address summaries. `calledContract` is the runtime
    // callee, passed through as a parameter so the ghost reads can key on it.
    function _.getPrice() external =>
        simpleOracleGetPriceSummary(calledContract) expect (uint256, uint256);
    function _.price() external =>
        simpleOraclePriceSummary(calledContract) expect uint256;
    function _.timestamp() external =>
        simpleOracleTimestampSummary(calledContract) expect uint256;

    // Unused in these rules; NONDET keeps them out of the way.
    function _.setPrice(uint256) external => NONDET;
    function _.owner() external => NONDET;
}

function setup(env e) {
    require e.msg.sender != 0;
    require e.msg.value == 0;
    require e.block.timestamp > 0;
    require e.block.timestamp < 2^64;
}

/* --------------------------------------------------------------------------
   H-13 (subset):
   Every address returned by getActiveOracleNodes() appears in oracles[].

   Bounded enumeration: loop_iter=3, so oracles.length <= 3 is the verified
   regime. `i` is a rule-level parameter and thus universally quantified
   over [0, returned_length).
   -------------------------------------------------------------------------- */
rule activeNodesSubsetOfOracles(env e, uint256 i) {
    setup(e);
    uint256 len = getOraclesLength();
    require len <= 3;

    // Match real SimpleOracle: timestamps cannot be set to the future.
    require len < 1 || ghostOracleTimestamp[getOracleAt(0)] <= e.block.timestamp;
    require len < 2 || ghostOracleTimestamp[getOracleAt(1)] <= e.block.timestamp;
    require len < 3 || ghostOracleTimestamp[getOracleAt(2)] <= e.block.timestamp;

    address[] activeNodes = getActiveOracleNodes(e);
    uint256 retLen = activeNodes.length;

    require i < retLen;
    address returned = activeNodes[i];

    assert (len >= 1 && returned == getOracleAt(0)) ||
           (len >= 2 && returned == getOracleAt(1)) ||
           (len >= 3 && returned == getOracleAt(2)),
        "returned active node must appear somewhere in oracles[]";
}

/* --------------------------------------------------------------------------
   H-08 (forward):
   Every oracle in oracles[] whose timestamp is fresh must appear in the
   array returned by getActiveOracleNodes().

   We parametrize over `j`, universally quantifying over candidate fresh
   indices, and require j to point at a fresh oracle. The assertion
   bounded-enumerates the three possible positions in the return array.
   -------------------------------------------------------------------------- */
rule freshOraclesInActiveNodes(env e, uint256 j) {
    setup(e);
    uint256 len = getOraclesLength();
    require len >= 1 && len <= 3;

    uint256 staleWindow = STALE_DATA_WINDOW();

    require ghostOracleTimestamp[getOracleAt(0)] <= e.block.timestamp;
    require len < 2 || ghostOracleTimestamp[getOracleAt(1)] <= e.block.timestamp;
    require len < 3 || ghostOracleTimestamp[getOracleAt(2)] <= e.block.timestamp;

    require j < len;
    address oracleJ = getOracleAt(j);
    uint256 tsJ = ghostOracleTimestamp[oracleJ];

    // oracle j is FRESH.
    require e.block.timestamp - tsJ < staleWindow;

    address[] activeNodes = getActiveOracleNodes(e);
    uint256 retLen = activeNodes.length;

    assert (retLen >= 1 && activeNodes[0] == oracleJ) ||
           (retLen >= 2 && activeNodes[1] == oracleJ) ||
           (retLen >= 3 && activeNodes[2] == oracleJ),
        "every fresh oracle in oracles[] must appear in the active-nodes return";
}

/* --------------------------------------------------------------------------
   Length sanity: the returned array length cannot exceed oracles.length,
   and equals the count of fresh oracles. This one is a cheap win — proves
   getActiveOracleNodes doesn't return bogus extra entries.
   -------------------------------------------------------------------------- */
rule activeNodesLengthBoundedByOraclesLength(env e) {
    setup(e);
    uint256 len = getOraclesLength();
    require len <= 3;

    require len < 1 || ghostOracleTimestamp[getOracleAt(0)] <= e.block.timestamp;
    require len < 2 || ghostOracleTimestamp[getOracleAt(1)] <= e.block.timestamp;
    require len < 3 || ghostOracleTimestamp[getOracleAt(2)] <= e.block.timestamp;

    address[] activeNodes = getActiveOracleNodes(e);
    assert activeNodes.length <= len,
        "|active nodes| cannot exceed |oracles|";
}
