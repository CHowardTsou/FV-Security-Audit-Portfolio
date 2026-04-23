# WhitelistOracle — Certora Formal Verification

Checkpoint 1 of the Speedrun Ethereum Oracles challenge. This folder
contains a complete Certora verification suite against `WhitelistOracle.sol`
(the learner-implemented median aggregator) and its dependency
`SimpleOracle.sol`.

- **solc:** 0.8.20
- **Loop unrolling:** `loop_iter=3` (production deploy uses 10 oracles; see residual risks below)
- **Recursion budget:** `optimistic_summary_recursion=true, summary_recursion_limit=1` — covers the single-nesting `WhitelistOracle.getPrice → SimpleOracle.getPrice` call

## Layout

```
certora/
├── HYPOTHESES.md              # Bug-hypothesis tracker (H-01..H-14)
├── MUTATION_REPORT.md         # Per-family Gambit run triage
├── conf/                      # One .conf per spec family
├── harness/
│   └── WhitelistOracleHarness.sol
└── specs/
    ├── setup/setup.spec       # Shared methods{}, setup(e), setupValidState(e)
    ├── Sanity.spec
    ├── StateTransitions.spec
    ├── ValidState.spec
    ├── ReadPathProperties.spec
    └── ActiveSetMembership.spec
```

## Verification status

| Conf                                 | Spec                      | Status  | Rules     | Link |
|--------------------------------------|---------------------------|---------|-----------|------|
| `WhitelistOracle_sanity.conf`        | `Sanity.spec`             | GREEN   | 5/5       | [run](https://prover.certora.com/output/6854102/a1d2d274821444e2af9dc5a8090d583c?anonymousKey=8e8fd1abf61d185f13ab508d66da7d07e53c6912) |
| `WhitelistOracle_transitions.conf`   | `StateTransitions.spec`   | GREEN   | 10/10     | [run](https://prover.certora.com/output/6854102/3859b94e066340ceb30689b1383671ea?anonymousKey=8ead3862b3dc90f92f2d006e9e2a9f040414f718) |
| `WhitelistOracle_valid_state.conf`   | `ValidState.spec`         | GREEN   | 3/3 inv   | [run](https://prover.certora.com/output/6854102/f0010e1cef4e4d699fed3e3235c8aff0) |
| `WhitelistOracle_readpath.conf`      | `ReadPathProperties.spec` | GREEN   | 7/7       | [run](https://prover.certora.com/output/6854102/4be5dc6209184b13bb2a8a57242923f6) |
| `WhitelistOracle_active_set.conf`    | `ActiveSetMembership.spec`| GREEN   | 3/3       | [run](https://prover.certora.com/output/6854102/7d198f2a10e1454cbca582bb229ff38e) |

## Bug-hypothesis coverage

| ID   | Claim                                                          | Coverage | Spec                      | Notes                                                                               |
|------|----------------------------------------------------------------|----------|---------------------------|-------------------------------------------------------------------------------------|
| H-01 | swap-and-pop correctness                                       | Strong   | StateTransitions          | `removeOracleSwapAndPopCorrect` + ghost hooks                                       |
| H-02 | `removeOracle` reverts `IndexOutOfBounds`                      | Strong   | StateTransitions          | explicit revert-condition rule                                                      |
| H-03 | Only `add/removeOracle` mutate `oracles[]`                     | Strong   | StateTransitions          | parametric, filtered `!f.isView`                                                    |
| H-04 | Staleness boundary — delta == window is STALE (uses `<`)       | Strong   | ReadPathProperties        | `staleBoundaryIsStale`                                                              |
| H-05 | Future-timestamp underflow reverts                             | Strong   | ReadPathProperties        | `getPriceRevertsOnFutureTimestamp`                                                  |
| H-06 | Zero-fresh → `NoOraclesAvailable`                              | Strong   | ReadPathProperties        | `getPriceRevertsWhenAllStale`                                                       |
| H-07 | Empty `oracles[]` → `NoOraclesAvailable`                       | Strong   | StateTransitions          | `getPriceRevertsOnEmpty`                                                            |
| H-08 | Active-set fresh-subset equality                               | Strong   | ActiveSetMembership       | `freshOraclesInActiveNodes` (ghost-backed per-callee summary)                       |
| H-09 | Event emission on add/remove                                   | Partial  | StateTransitions          | `addOracleProducesVisibleEffect` (state-change proxy)                               |
| H-10 | No reentrancy / view-function purity                           | Strong   | ReadPathProperties        | `getPriceDoesNotChangeOraclesLength`, `getActiveOracleNodesDoesNotChangeState`      |
| H-11 | Median == `StatisticsUtils.getMedian(sorted fresh)`            | None     | —                         | Residual — trusts library delegation                                                |
| H-12 | Access-control disabled — any caller can add/remove            | Strong   | StateTransitions          | `anyCallerCanAddOracle` + sanity                                                    |
| H-13 | `getActiveOracleNodes ⊆ oracles[]`                             | Strong   | ActiveSetMembership       | `activeNodesSubsetOfOracles` + `activeNodesLengthBoundedByOraclesLength`            |
| H-14 | `addOracle` grows length by 1, appends non-zero, tail distinct | Strong   | StateTransitions + ValidState | Length/non-zero in StateTransitions; V-02 `oraclesPairwiseDistinct` via `addOracleUnique` harness wrapper |

## What's NOT proven (residual risks)

1. **Median correctness** (H-11) — delegation to `StatisticsUtils` is trusted. A
   follow-up would re-prove `sort` + `getMedian` as a standalone library harness.

2. **Loop bound** — `loop_iter=3`. Production deploys 10 oracles. Raising the bound
   is a mechanical re-run; properties use bounded length preconditions consistently.
   The `ActiveSetMembership` rules enumerate up to 3 positions in the return array
   and would need the assertions expanded if `loop_iter` is raised.

3. **V-02 pairwise-distinctness** of `oracles[]` is proven, but the inductive step
   routes the `addOracle` case through a harness wrapper (`addOracleUnique`) that
   encodes the EVM CREATE uniqueness guarantee as a `require`. Certora's native
   symbolic CREATE does not model this, so the wrapper is a justified modeling step —
   not a residual risk, but worth noting for readers.

## Mutation testing

**Cross-family union kill rate: 9/10 (90%).** See [MUTATION_REPORT.md](MUTATION_REPORT.md) for per-mutant triage.

| Spec family                   | Kill rate          | Notes                                                                                |
|-------------------------------|--------------------|--------------------------------------------------------------------------------------|
| Sanity                        | Not run            | Low-signal by design (witness rules)                                                 |
| StateTransitions              | 1/10               | Kills #1 (`removeOracle` swap-source mutation). 9 survivors all on read path — off-surface for this family |
| ReadPath (satisfy-only)       | 4/10               | Exposed satisfy-style weakness in `getActiveOracleNodesAlwaysSucceeds`               |
| ReadPath (strengthened)       | 8/10               | Added assert-style `getActiveOracleNodesNeverRevertsOnValidTimestamps`. Kills #2, #3, #5–10 |
| ValidState                    | 0/10 (by design)   | Invariants cover storage shape; Gambit batch had no shape-violating mutations        |

Run 2 showed four mutants slipping past `getActiveOracleNodesAlwaysSucceeds`
because `satisfy !lastReverted` accepts the trivial `len==0` witness. The
assert-style fix raised ReadPath's kill rate from 4/10 to 8/10.

Residual survivor: mutant #4 (`priceArray[validCount] = 1`) requires closing
H-11 (median-correctness rule).
