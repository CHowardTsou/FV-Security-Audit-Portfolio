# Accounting Source Map

Accounting map for the `StakingOracle` Certora suite.

## Quantities

| id | contract / field / function | unit | decimals | rounding | source of truth | authorized writers | external mutation vector | coverage | notes |
|---|---|---:|---:|---|---|---|---|---|---|
| Q-01 | `nodes[node].stakedAmount` | ORA | 18 | exact | StakingOracle storage | `registerNode`, `addStake`, `slashNode`, `exitNode` | none, storage only | Partial | Exact delta rules cover register/add/exit and staged slash. |
| Q-02 | ORA escrow balance of StakingOracle | ORA | 18 | exact | `CertoraORA.balanceOf(oracle)` | ORA `transfer`, `transferFrom`, `mint`, harness seed helper | modeled token only | Partial | Modeled ORA token models transfer return and balance deltas; no fee-on-transfer/rebase class. |
| Q-03 | node ORA balance | ORA | 18 | exact | `CertoraORA.balanceOf(node)` | ORA model and StakingOracle flows | modeled token only | Partial | Used for reward and exit payout rules. |
| Q-04 | `nodes[node].reportCount` | reports | 0 | exact | StakingOracle storage | `reportPrice` | none | Partial | State-machine rule checks successful report increment. |
| Q-05 | `nodes[node].claimedReportCount` | reports | 0 | exact | StakingOracle storage | `claimReward` | none | Partial | Reward claim rule checks synchronization to report count. |
| Q-06 | `blockBuckets[bucket].medianPrice` | price | feed-defined | integer division for even median | StakingOracle storage | `recordBucketMedian` | reporter prices | Partial | View and state-machine rules depend on recorded/nonzero median. |
| Q-07 | slasher reward | ORA | 18 | down | `actualPenalty * 10 / 100` | `slashNode` | modeled token only | Partial | Verified for staged finalized outlier bucket with stake above `MISREPORT_PENALTY`. |
| Q-08 | effective stake | ORA | 18 | floor at zero | derived view | `getEffectiveStake` | block number and node storage | Partial | Formula verified under bounded seeded-node assumptions. |

## Source Buckets

| bucket | definition | examples | required proof shape |
|---|---|---|---|
| settled | stake held in oracle storage and token escrow | registered stake, added stake | exact delta / escrow conservation |
| claimable | ORA owed for reports | `reportCount - claimedReportCount` rewards | no double-claim / exact mint |
| penalty | slashable stake for outlier reports | `MISREPORT_PENALTY` capped by stored stake | exact slash delta and slasher reward |
| derived | views computed from state and block number | effective stake, current bucket | formula and boundary rules |

## Open Accounting Questions

| id | question | impact | owner / next step |
|---|---|---|---|
| AQ-01 | Should token verification include non-standard ERC20 behavior? | Current mock is honest ERC20-like, so fee/rebase/fake-token behavior is out of scope. | Documented as an honest-token modeling limitation. |
| AQ-02 | Can `slashNode` be fully proven through a production-only multi-call path without staged storage setup? | Current slash accounting is Partial because it uses a staged finalized outlier bucket. | Future work: add a multi-env production flow wrapper for register/report/finalize/slash. |
