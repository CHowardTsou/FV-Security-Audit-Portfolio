# Hypotheses

## Trust Boundaries

| id | boundary | classification | modeling | status |
|---|---|---|---|---|
| TB-01 | constructor `oraTokenAddress` / `oracleToken` | config-controlled | linked to `CertoraORA` mock in each verification conf | Partial |
| TB-02 | `nodeToSlash` in `slashNode` | user-controlled address | checked against bucket reporter and node-address indexes | Partial |
| TB-03 | `msg.sender` node identity | user-controlled caller | direct CVL `env` caller modeling | Partial |

## Bug Hypotheses

| id | scope | class | planned / implemented coverage | status |
|---|---|---|---|---|
| H-01 | `nodeAddresses` vs `nodes` mapping | array/mapping desync | `ValidState.successfulCallsPreserveBoundedNodeAddressShape` plus registration append rule | Implemented |
| H-02 | bucket reporters/prices | array desync | `ValidState.bucketReportersAndPricesStayAligned` | Implemented |
| H-03 | duplicate bucket reports | state-machine bypass | `StateMachine.registeredNodeReportsAtMostOncePerBucket` | Implemented |
| H-04 | reporting before prior median finalized | multi-step bypass | `StateMachine.reportingInLaterBucketRequiresPriorMedian` | Implemented |
| H-05 | stake escrow mismatch | accounting | `Accounting.registerEscrowsExactStake`, `addStakeIncreasesStoredStakeAndEscrow` | Implemented |
| H-06 | reward over/under mint | accounting | `Accounting.claimRewardMintsUnclaimedReports` | Implemented |
| H-07 | exit overpayment | accounting | `Accounting.exitPaysAtMostEffectiveStake` | Implemented |
| H-08 | slash amount and slasher reward mismatch | accounting | `Accounting.slashNodeReducesStakeAndPaysReward` | Implemented |
| H-09 | deviation threshold off by one | oracle edge output | `Views.exactTenPercentDeviationIsNotSlashable`, `greaterThanTenPercentDeviationIsSlashable` | Implemented |
| H-10 | effective stake formula drift | view formula | `Views.effectiveStakeMatchesMissedBucketFormula` | Implemented |

## Function Coverage Matrix

| function | Access | Reverts | Conservation | Round-trip |
|---|---|---|---|---|
| `registerNode(uint256)` | N/A: open registration | sanity + minimum stake via production checks; duplicate registration rule | `registerEscrowsExactStake` | `registerCreatesActiveListedNode` |
| `reportPrice(uint256)` | `inactiveNodeCannotReport` | duplicate/later-bucket rules | report count delta rule | N/A: report is append-only |
| `claimReward()` | N/A: rewards keyed by caller | no-reward revert is production behavior; exact mint rule covers successful claim | `claimRewardMintsUnclaimedReports` | N/A: mint is one-way |
| `addStake(uint256)` | `inactiveNodeCannotAddStake` | zero-amount revert is production behavior; escrow delta rule covers successful add | `addStakeIncreasesStoredStakeAndEscrow` | N/A: paired with exit |
| `recordBucketMedian(uint256)` | N/A: public finalizer | current/future bucket rejection and successful sorted median recording | `recordBucketMedianRecordsSortedMedian` | N/A |
| `slashNode(address,uint256,uint256,uint256)` | reporter/index behavior covered by staged slash rules | current/unrecorded/nondeviated production checks are partially covered by staged setup and view threshold rules | `slashNodeReducesStakeAndPaysReward`, `slashMarksOffenseAndReducesStake` | N/A: penalty is one-way |
| `exitNode(uint256)` | only active node through production modifier | `exitBeforeWaitingPeriodReverts`, index behavior through `_removeNode` shape preservation | `exitPaysAtMostEffectiveStake` | `exitDeactivatesNode` |

## Adversarial Sequence Matrix

| sequence | risk | coverage |
|---|---|---|
| register -> miss buckets -> report | inactivity penalty can block reporting | full effective-stake formula rule |
| report -> skip median -> report next bucket | unfinalized bucket bypass | `reportingInLaterBucketRequiresPriorMedian` |
| report outlier -> record median -> slash | slash amount/reward correctness | staged slash accounting and state-machine slash rules |
| register -> wait -> exit | exit overpayment after penalties | `exitPaysAtMostEffectiveStake` |
