# OptimisticOracle Modeling Debt

## Debt Table

| ID | Class | Location | Assumption / approximation | Impact | Strengthening path |
|---|---|---|---|---|---|
| MD-C-01 | C-class | `claimUndisputedReward`, `claimDisputedReward`, `claimRefund` | Certora confs that touch ETH transfer paths use `optimistic_fallback` so recipient fallback calls do not havoc oracle storage. | Reentrancy witness coverage is Weak, but double-claim properties remain meaningful because production code sets `claimed = true` before external calls. | Add explicit receiver harness/reentrancy witness rules or add `nonReentrant` in production if a real issue is found. |
| MD-C-02 | C-class | Native ETH balance | Raw `address(this).balance` can be force-sent and is not provenance-modeled. | Global native balance conservation is Partial. Assertion storage does not read raw balance for lifecycle decisions. | Add a provenance ghost separating assertion-reserved ETH from donated ETH. |
| MD-C-03 | C-class | `assertEvent(string,...)` | CVL rules use `calldataarg` for string-bearing calls. | Description content is not semantically verified. | Add a harness getter or restrict to metadata-only coverage if needed. |

## Reentrancy Surface

| Function | Guard present | Production pattern | Risk |
|---|---|---|---|
| `claimUndisputedReward` | No `nonReentrant` | Checks-effects-interactions: `claimed = true` before transfer | Low residual under MD-C-01 |
| `claimDisputedReward` | No `nonReentrant` | Checks-effects-interactions: `claimed = true` before decider/winner transfers | Low residual under MD-C-01 |
| `claimRefund` | No `nonReentrant` | Checks-effects-interactions: `claimed = true` before transfer | Low residual under MD-C-01 |

## Bounded Assumptions

| Location | Bound | Rationale |
|---|---|---|
| Conf `loop_iter` | 4 | Existing OptimisticOracle specs do not rely on unbounded production loops; bound is retained for prover defaults. |
| `setup(e)` | `0 < e.block.timestamp < max_uint256` and `e.msg.value < max_uint256` | Prevents symbolic timestamp/value overflow artifacts. |
