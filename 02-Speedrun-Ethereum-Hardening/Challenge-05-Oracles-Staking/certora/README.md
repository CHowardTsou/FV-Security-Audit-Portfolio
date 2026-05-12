# StakingOracle Certora Suite

This suite verifies the core lifecycle, accounting, and view properties of the Speedrun Ethereum `StakingOracle` challenge.

## Scope

| item | status |
|---|---|
| Target | `packages/hardhat/contracts/01_Staking/StakingOracle.sol` |
| Supporting contracts | `OracleToken.sol`, `StatisticsUtils.sol` |
| Mode | Verification harness with modeled ORA token |
| Campaign status | Closed with documented modeling debt |

## Verification Families

| family | conf | cloud status | purpose |
|---|---|---|---|
| Sanity | `conf/staking_sanity.conf` | verified | reachability witnesses for registration, reporting, reward claim |
| Valid state | `conf/staking_valid_state.conf` | verified v7 | registration/listing rules, bounded node-address list shape preservation, and bucket array structural invariant |
| State machine | `conf/staking_state_machine.conf` | verified v5 | active-node gates, duplicate report prevention, prior-median requirement, median recording, slash state transition, exit deactivation |
| Accounting | `conf/staking_accounting.conf` | verified v7 | stake escrow, add-stake escrow, reward mint, exit payout bound, early-exit revert, slash reward/delta |
| Views | `conf/staking_views.conf` | verified v8 | current bucket formula, full effective-stake formula including reports-greater-than-expected, recorded median views, one-reporter and mixed multi-reporter outlier checks, deviation threshold edges |

## Current Coverage

| area | coverage | notes |
|---|---|---|
| Node registry structure | Partial | valid-state v7 verified with bounded node-address shape preservation; bounded by `loop_iter = 3` |
| Bucket reporter/price alignment | Partial | structural invariant |
| Report state machine | Partial | duplicate and previous-median gates covered |
| Stake escrow | Partial | accounting v7 verified; modeled ORA transfer deltas covered |
| Rewards | Partial | one-report reward mint covered |
| Slashing | Partial | exact penalty/reward rule verified for a staged finalized outlier bucket |
| Effective stake | Partial | full formula rule verified under bounded seeded-node assumptions |

## Limitations

The suite uses an honest ORA token model, bounded loop reasoning for dynamic arrays, and a staged finalized outlier bucket for slash accounting. A full production-only multi-call slash flow is left as future strengthening work.
