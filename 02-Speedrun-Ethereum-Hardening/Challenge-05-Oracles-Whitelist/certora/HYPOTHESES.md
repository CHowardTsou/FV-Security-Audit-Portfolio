# Bug Hypotheses — WhitelistOracle Formal Verification

Scope: `WhitelistOracle.sol` (Checkpoint 1 of the Speedrun Ethereum Oracles
challenge). Companion contracts: `SimpleOracle.sol` (provided),
`StatisticsUtils.sol` (provided library).

## Tracker

| ID    | Claim                                                                                                                                    | Component                                           | Spec pattern                                                                                                                                           | Status    | Conf(s)                                                                                                   |
|-------|------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|-----------|-----------------------------------------------------------------------------------------------------------|
| H-01  | `removeOracle(i)` may corrupt `oracles[]` if swap-and-pop mishandled (wrong element moved, length not decremented, etc.)                | `WhitelistOracle.removeOracle`, `oracles[]`         | State-transition rule: len decreases by 1; surviving elements all distinct                                                                             | Covered   | `WhitelistOracle_transitions.conf`                                                                        |
| H-02  | `removeOracle(index)` must revert `IndexOutOfBounds` when `index >= oracles.length`                                                     | `WhitelistOracle.removeOracle`                      | State-transition rule (revert condition)                                                                                                               | Covered   | `WhitelistOracle_transitions.conf`                                                                        |
| H-03  | Parametric field-write authority: `oracles[]` only mutated by `addOracle`/`removeOracle`; no other function can change length or entries | `WhitelistOracle.oracles[]`                         | Field-monotonicity parametric rule                                                                                                                     | Covered   | `WhitelistOracle_transitions.conf`                                                                        |
| H-04  | Staleness boundary: the filter uses strict `currentTime - time < STALE_DATA_WINDOW`; delta == window is treated as STALE                 | `WhitelistOracle.getPrice`, `getActiveOracleNodes`  | Compliance rule: witness + verification of chosen boundary semantics                                                                                   | Covered   | `WhitelistOracle_readpath.conf`                                                                           |
| H-05  | Underflow in staleness calc: if `time > currentTime`, `currentTime - time` reverts                                                      | `WhitelistOracle.getPrice`, `getActiveOracleNodes`  | Rule: getPrice reverts when any `oracles[i].timestamp > block.timestamp`                                                                               | Covered   | `WhitelistOracle_readpath.conf`                                                                           |
| H-06  | Error propagation: when zero fresh oracles exist, `getPrice` must revert `NoOraclesAvailable`                                           | `WhitelistOracle.getPrice`                          | State-transition rule: zero-fresh case yields `NoOraclesAvailable` revert                                                                              | Covered   | `WhitelistOracle_readpath.conf`                                                                           |
| H-07  | Empty-oracle-set: `getPrice()` with `oracles.length == 0` must revert `NoOraclesAvailable`                                              | `WhitelistOracle.getPrice`                          | State-transition rule (explicit length-0 revert)                                                                                                       | Covered   | `WhitelistOracle_transitions.conf`                                                                        |
| H-08  | `getActiveOracleNodes` return set equals the set of fresh oracles in `oracles[]`                                                        | `WhitelistOracle.getActiveOracleNodes`              | Quantified rule: every fresh oracle appears in the return (bounded enumeration, ghost-backed summary)                                                  | Covered   | `WhitelistOracle_active_set.conf` (`freshOraclesInActiveNodes`)                                           |
| H-09  | Event emission: `OracleAdded` on add, `OracleRemoved` on remove; no silent state changes                                                | `WhitelistOracle.addOracle`, `removeOracle`         | Event rule: event iff state change                                                                                                                     | Partial   | `WhitelistOracle_transitions.conf` (state-change proxy)                                                   |
| H-10  | No reentrancy path: view functions call external `SimpleOracle.getPrice` but cannot trigger state writes in caller                       | `WhitelistOracle.getPrice`, `getActiveOracleNodes`  | Assert: oracles.length unchanged across getPrice / getActiveOracleNodes                                                                                | Covered   | `WhitelistOracle_readpath.conf` (view-purity rules, contract_recursion_limit=1)                           |
| H-11  | `getPrice` median = `StatisticsUtils.getMedian(sorted fresh prices)` — library delegated correctly                                      | `WhitelistOracle.getPrice`                          | Rule: return value matches `StatisticsUtils.getMedian` on the sorted fresh-prices array                                                                | Uncovered | — (residual — library delegation trusted)                                                                 |
| H-12  | Access control disabled intentionally: `addOracle`/`removeOracle` callable by any address                                               | `WhitelistOracle.addOracle`, `removeOracle`         | Witness rule (`satisfy`) + documented deviation                                                                                                        | Covered   | `WhitelistOracle_transitions.conf`                                                                        |
| H-13  | Fresh-oracle membership: every address in `getActiveOracleNodes()` appears in `oracles[]`                                               | `WhitelistOracle.getActiveOracleNodes`              | Quantified rule: returned ⊆ oracles[] (bounded enumeration, ghost-backed summary)                                                                      | Covered   | `WhitelistOracle_active_set.conf` (`activeNodesSubsetOfOracles`, `activeNodesLengthBoundedByOraclesLength`) |
| H-14  | `addOracle` strictly increments length by 1 and the new entry is a freshly-deployed, non-zero SimpleOracle                              | `WhitelistOracle.addOracle`                         | State-transition rule: length += 1; new entry != address(0); uniqueness via `addOracleUnique` harness wrapper (EVM CREATE guarantee as post-call `require`) | Covered   | `WhitelistOracle_transitions.conf` (length + non-zero); `WhitelistOracle_valid_state.conf` (V-02 `oraclesPairwiseDistinct`) |

## Coverage plan

**Valid-state invariants:**
- V-01: `forall i in [0, oracles.length), oracles[i] != address(0)`
- V-02: `forall i in [0, oracles.length), forall j in [0, i), oracles[i] != oracles[j]` (uniqueness)
- V-03 (timing): `forall i, oracles[i].timestamp() <= block.timestamp`

**State-transition rules:**
- `addOracle` grows length by 1
- `removeOracle` shrinks length by 1 when `index < len`; reverts otherwise
- Parametric: only `addOracle` and `removeOracle` mutate `oracles[]`

**Sanity rules:**
- Each non-view function can succeed
- `getPrice()` can succeed when at least one oracle is fresh
- `getPrice()` reverts when no oracles
- `removeOracle` reverts with bad index

**Access-control witness rules:**
- `satisfy`: non-owner calls `addOracle` successfully (documents disabled modifier)
