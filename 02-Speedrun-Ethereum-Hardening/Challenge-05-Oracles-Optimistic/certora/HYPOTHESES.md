# OptimisticOracle Bug Hypotheses

## Canonical Bug Classes

| ID | Category | Hypothesis | Contract / field | Planned spec pattern | Status | Coverage tier |
|---|---|---|---|---|---|---|
| H-01 | State machine | Asserted assertion can bypass proposal and become settled. | lifecycle fields | `StateMachine` transition rules | Covered | Strong |
| H-02 | Terminal state | `claimed` or `winner` can be reversed after terminal state. | `claimed`, `winner` | terminal preservation rules + invariants | Covered | Strong |
| H-03 | Reentrancy | ETH recipient reenters `claimUndisputedReward`. | low-level call | modeled with `optimistic_fallback`, CEI documented | Modeling boundary | Weak |
| H-04 | Reentrancy | ETH recipient reenters `claimDisputedReward`. | low-level calls | modeled with `optimistic_fallback`, CEI documented | Modeling boundary | Weak |
| H-05 | Reentrancy | ETH recipient reenters `claimRefund`. | low-level call | modeled with `optimistic_fallback`, CEI documented | Modeling boundary | Weak |
| H-06 | Field authority | `proposer` can be overwritten or mutated by unrelated calls. | `proposer` | field-authority rule | Covered | Strong |
| H-07 | Field authority | `disputer` can be overwritten or mutated by unrelated calls. | `disputer` | field-authority rule | Covered | Strong |
| H-08 | Field authority | `winner` can be set before valid settlement/claim. | `winner` | state-machine + valid-state rules | Covered | Strong |
| H-09 | Access control | Non-decider can settle disputed assertion. | `settleAssertion` | access-control rule | Covered | Strong |
| H-10 | Access control | Non-owner can update decider. | `setDecider` | access-control rule | Covered | Strong |
| H-11 | Timing | Undisputed reward can be claimed before dispute window closes. | `endTime` | timing-window rule | Covered | Strong |
| H-12 | Timing | Outcome can be proposed outside assertion window. | `startTime`, `endTime` | timing-window rules | Covered | Strong |
| H-13 | Timing | Outcome can be disputed after dispute window. | `endTime` | timing-window rule | Covered | Strong |
| H-14 | Timing | Refund can be claimed before assertion expiry. | `endTime` | timing-window rule | Covered | Strong |
| H-15 | Financial correctness | Bond/reward arithmetic admits wrong amount or overflow edge. | `reward`, `bond` | accounting + valid-state rules | Covered | Partial |
| H-16 | Financial correctness | Any payout path can be claimed more than once. | `claimed` | accounting rules | Covered | Strong |
| H-17 | Winner determination | Disputed winner differs from proposed/resolved outcome comparison. | `winner`, outcomes | state-machine rule | Covered | Strong |
| H-18 | Undisputed settlement | Undisputed claim sets wrong winner or outcome. | `winner`, `resolvedOutcome` | accounting/state-machine rules | Covered | Strong |
| H-19 | Bond semantics | Bond is not exactly twice reward for created assertions. | `bond`, `reward` | valid-state invariant | Covered | Strong |
| H-20 | Assertion ID | `nextAssertionId` decreases or starts invalid. | `nextAssertionId` | sanity + invariant | Covered | Strong |
| H-21 | State atomicity | Proposal partially updates state, leaving inconsistent deadline/proposer. | `proposer`, `endTime` | timing/state-machine rules | Covered | Strong |
| H-22 | Claimed ordering | `claimed` can be true without winner where payout requires winner. | `claimed`, `winner` | accounting/state-machine rules | Covered | Strong |
| H-23 | Recipient correctness | Funds can be redirected to an unintended recipient. | payout recipients | state-machine/accounting rules | Covered | Partial |

## Trust Boundaries

| Function | Address boundary | Classification | Modeling |
|---|---|---|---|
| constructor | `_decider` | config-controlled | Harness constructor chooses symbolic decider; access-control rules constrain settlement authority. |
| `setDecider` | `_decider` | config-controlled | Owner-admin cascade covered by H-10 and decider authority checks. |
| claim functions | `asserter`, `proposer`, `disputer`, `winner`, `decider` as ETH recipients | storage-derived user/config addresses | Native transfer fallback modeled by `optimistic_fallback`; CEI residual in `MODELING_DEBT.md`. |
| all public functions | `msg.sender` | user-controlled | Modeled by Certora `env`; access restrictions checked explicitly where applicable. |
| all payable functions | `msg.value` | user-controlled | Exact-value and nonzero rules in Accounting/Timing. |

## Function Coverage Matrix

| Function | Access | Reverts | Conservation / value | Round-trip / lifecycle |
|---|---|---|---|---|
| `setDecider` | `AccessControl` | `AccessControl` | N/A: no value moved | state authority covered by H-10 |
| `assertEvent` | N/A: public payable | `Accounting`, `TimingWindow` | reward/bond initialization | assertion creation in `StateMachine` |
| `proposeOutcome` | N/A: public payable | `Accounting`, `TimingWindow` | exact bond required | proposal transition |
| `disputeOutcome` | N/A: public payable | `Accounting`, `TimingWindow` | exact bond required | dispute transition |
| `claimUndisputedReward` | N/A: public trigger | `Accounting`, `TimingWindow` | no double-claim, recipient selection | terminal claimed state |
| `claimDisputedReward` | N/A: public trigger | `Accounting`, `StateMachine` | no double-claim, winner/decider payout shape | terminal claimed state |
| `claimRefund` | N/A: public trigger | `Accounting`, `TimingWindow` | no double-claim, asserter refund | expired/refund terminal state |
| `settleAssertion` | `AccessControl` | `AccessControl`, `StateMachine` | N/A: no value moved | disputed to settled transition |

## Adversarial Sequence Matrix

| Sequence | Risk | Coverage |
|---|---|---|
| Assert -> no proposal -> refund | Early refund or wrong recipient | `TimingWindow` + `Accounting` |
| Assert -> propose -> undisputed claim | Early claim, double-claim, wrong winner | `TimingWindow` + `Accounting` + `StateMachine` |
| Assert -> propose -> dispute -> settle -> disputed claim | Non-decider settlement, wrong winner, double-claim | `AccessControl` + `StateMachine` + `Accounting` |
| Admin changes decider before settlement | Authority cascade | `AccessControl`; residual governance trust noted |
| Recipient fallback during claim | Reentrancy / storage havoc | C-class modeling debt with CEI justification |

## Coverage Summary

- Strong hypotheses: 18
- Partial hypotheses: 2
- Weak hypotheses: 3 reentrancy boundaries
- Status: all six proof families passed; mutation suite kills 5/5 unique mutants via Sanity and StateMachine.

## Mutation Testing Results

| Family | Result | Triage |
|---|---|---|
| ValidState | 0/5 killed | Safety-only invariant family; survivors expected and covered by liveness/state-machine families. |
| Sanity | 3/5 killed | Kills always-reverting claim/refund mutants through reachability/liveness. |
| StateMachine | 2/5 killed | Kills settlement/getState semantic mutants. |
| Accounting | 0/5 killed | Survivors already killed by Sanity/StateMachine or outside this family's liveness scope. |
| AccessControl | 0/5 killed | Revert-condition/access family; liveness mutants covered elsewhere. |
| TimingWindow | 0/5 killed | Deadline-enforcement family; liveness mutants covered elsewhere. |

Combined suite kill rate: 5/5 unique mutants (100%).
