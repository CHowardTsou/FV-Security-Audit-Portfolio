# StakingOracle - Certora Formal Verification

Checkpoint 2 of the Speedrun Ethereum Oracles challenge. This folder
contains a Certora verification suite against `StakingOracle.sol`, the
staking-based oracle where nodes escrow ORA tokens, report prices by bucket,
claim rewards, exit after a waiting period, and can be slashed for outlier
reports.

The suite also includes the provided `OracleToken.sol` and `StatisticsUtils.sol`
dependencies, plus a verification-only ORA model and harness for exposing
internal oracle state.

- **solc:** 0.8.30
- **Loop unrolling:** `loop_iter=3` for bounded registry and bucket-array checks
- **Token model:** honest ERC20-like `CertoraORA` model, linked as `oracleToken`
- **Primary limitation:** slash accounting is proven for a staged finalized
  outlier bucket; a full production-only slash sequence is left as future work

## Layout

```
certora/
├── ACCOUNTING.md              # Accounting source map for stake, rewards, exit, slashing
├── HYPOTHESES.md              # Bug-hypothesis tracker and function coverage matrix
├── README.md
├── conf/                      # One .conf per spec family
│   ├── staking_accounting.conf
│   ├── staking_sanity.conf
│   ├── staking_state_machine.conf
│   ├── staking_valid_state.conf
│   └── staking_views.conf
├── harness/
│   ├── CertoraORA.sol         # Verification-only ORA token model
│   └── StakingOracleHarness.sol
└── specs/
    ├── setup/
    │   ├── methods.spec       # Method declarations and harness getters
    │   └── setup.spec         # Shared setup helpers and bounds
    ├── Accounting.spec
    ├── Sanity.spec
    ├── StateMachine.spec
    ├── ValidState.spec
    └── Views.spec
```

## Verification status

| Conf | Spec | Status | Rules | Link |
|------|------|--------|-------|------|
| `staking_sanity.conf` | `Sanity.spec` | GREEN | 3/3 | [run](https://prover.certora.com/output/6854102/6600e3dcc0b3418bb77d7b33a4e24902?anonymousKey=e3f208d858ebeae3300983ee0f5614ebedfdfd25) |
| `staking_valid_state.conf` | `ValidState.spec` | GREEN | 4/4 | [run](https://prover.certora.com/output/6854102/93ba9ce145f64976a05ca5cdc9bb8fd3?anonymousKey=efc88cb1c4e6f2cf5d863e955cb9472ffc7c85cf) |
| `staking_state_machine.conf` | `StateMachine.spec` | GREEN | 9/9 | [run](https://prover.certora.com/output/6854102/e39b401332574df6bfe58e42a692cbfa?anonymousKey=337657dad4b5c8a3ddf3149d3ba3b08158ca967a) |
| `staking_accounting.conf` | `Accounting.spec` | GREEN | 6/6 | [run](https://prover.certora.com/output/6854102/3a171217ee2a4129950e1731849a5171?anonymousKey=177e07728ec98151555ed20f5390b57d95778b9b) |
| `staking_views.conf` | `Views.spec` | GREEN | 15/15 | [run](https://prover.certora.com/output/6854102/54d6c47a9045446e894d4d86689986ff?anonymousKey=ca0fb0cc132cf0cc9e0c56391ea395f6c40f1d5c) |

## Bug-hypothesis coverage

| ID | Claim | Coverage | Spec | Notes |
|----|-------|----------|------|-------|
| H-01 | `nodeAddresses` stays consistent with `nodes[address].active` | Partial | ValidState | Bounded list-shape preservation plus direct registration append rule |
| H-02 | Bucket `reporters[]` and `prices[]` arrays cannot desync | Strong | ValidState | `bucketReportersAndPricesStayAligned` |
| H-03 | Inactive or unregistered nodes cannot report | Strong | StateMachine | `inactiveNodeCannotReport` |
| H-04 | Inactive nodes cannot add stake | Strong | StateMachine | `inactiveNodeCannotAddStake` |
| H-05 | A node cannot report twice in the same bucket | Strong | StateMachine | `registeredNodeReportsAtMostOncePerBucket` |
| H-06 | A node cannot report in a later bucket before its previous bucket median is recorded | Strong | StateMachine | `reportingInLaterBucketRequiresPriorMedian` |
| H-07 | Past-bucket median recording stores the sorted median | Strong | StateMachine | Three-price intentionally unsorted bucket setup |
| H-08 | Current or future buckets cannot be finalized | Strong | StateMachine | `recordBucketMedianRejectsCurrentAndFutureBuckets` |
| H-09 | Registration escrows exactly the stored stake | Partial | Accounting | Honest ORA model exact-delta rule |
| H-10 | `addStake` increases stake and escrow by the transferred amount | Partial | Accounting | Honest ORA model exact-delta rule |
| H-11 | Rewards mint exactly unclaimed reports times `REWARD_PER_REPORT` | Partial | Accounting | `claimRewardMintsUnclaimedReports` |
| H-12 | Early exit before waiting period reverts | Strong | Accounting | `exitBeforeWaitingPeriodReverts` |
| H-13 | Exit pays at most effective stake and deactivates the node | Partial | Accounting + StateMachine | Payout bound plus `exitDeactivatesNode` |
| H-14 | Slashing reduces stake by the penalty and pays the slasher 10% | Partial | Accounting + StateMachine | Proven for staged finalized outlier bucket |
| H-15 | Effective stake matches inactivity-penalty formula and floors at zero | Partial | Views | Bounded seeded-node assumptions |
| H-16 | `getPastPrice` and `getLatestPrice` require recorded medians | Strong | Views | Missing-median revert rules plus recorded-median return rules |
| H-17 | Exact 10% deviation is not slashable; greater than 10% is slashable | Strong | Views | Boundary rules around `MAX_DEVIATION_BPS` |
| H-18 | `getOutlierNodes` excludes non-deviated and already-slashed reporters | Partial | Views | Includes one-reporter and mixed three-reporter checks |

## What's NOT proven (residual risks)

1. **Adversarial ERC20 behavior** - ORA is modeled as an honest ERC20-like token.
   Fee-on-transfer, rebasing, callback, malicious-return, and fake-token behavior
   are out of scope.

2. **Unbounded dynamic-array reasoning** - node-list and bucket-array properties
   are proven with `loop_iter=3`. Raising the bound is a follow-up proof-strengthening
   step, not a source change.

3. **Production-only slash flow** - exact slash accounting is proven for a harness
   staged finalized outlier bucket. A future suite could prove the full multi-call
   sequence through only production entrypoints:
   `registerNode -> reportPrice -> recordBucketMedian -> slashNode`.

4. **Full `getOutlierNodes` loop progress** - the suite checks semantic filtering
   cases, including mixed reporters, but dynamic-array loop progress is still bounded
   by the configured loop strategy.
