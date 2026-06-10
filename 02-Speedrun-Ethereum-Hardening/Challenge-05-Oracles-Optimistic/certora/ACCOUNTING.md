# Accounting Source Map

## Quantities

| id | contract / field / function | unit | decimals | rounding | source of truth | authorized writers | external mutation vector | coverage | notes |
|---|---|---|---|---|---|---|---|---|---|
| Q-01 | `assertions[id].reward` | wei | 18 | none | storage | `assertEvent` | direct/forced ETH can change raw balance but not storage | Strong | Reward is escrow principal for proposer or refund path. |
| Q-02 | `assertions[id].bond` | wei | 18 | multiplication by 2 | storage derived from `msg.value` | `assertEvent` | overflow if `msg.value * 2` exceeds uint256 | Partial | Solidity 0.8 checked arithmetic reverts on overflow; no separate upper-bound invariant. |
| Q-03 | `msg.value` in `assertEvent` | wei | 18 | none | call value | external caller | arbitrary positive value | Strong | Nonzero value and reward/bond initialization are covered. |
| Q-04 | `msg.value` in `proposeOutcome` / `disputeOutcome` | wei | 18 | none | call value | external caller | arbitrary value | Strong | Exact bond requirement covered. |
| Q-05 | `address(this).balance` | wei | 18 | none | raw native balance | payable functions plus forced ETH | force-send / recipient fallback interactions | Partial | Exact global balance conservation is limited by native ETH donation behavior. |
| Q-06 | `claimUndisputedReward` payout | wei | 18 | addition | storage-derived claimable amount | `claimUndisputedReward` | recipient fallback / reentrancy | Partial | CEI and no-double-claim covered; exact recipient balance delta not modeled. |
| Q-07 | `claimDisputedReward` winner payout | wei | 18 | addition | storage-derived claimable amount | `claimDisputedReward` | winner fallback / reentrancy | Partial | Winner selection covered; exact native balance delta not modeled. |
| Q-08 | `claimDisputedReward` decider fee | wei | 18 | none | storage-derived bond | `claimDisputedReward` | decider fallback / reentrancy | Partial | Decider address is owner-configurable. |
| Q-09 | `claimRefund` payout | wei | 18 | none | storage-derived reward | `claimRefund` | asserter fallback / reentrancy | Partial | Refund timing and no-double-claim covered; exact native balance delta not modeled. |
| Q-10 | `assertions[id].claimed` | boolean | n/a | none | storage | claim functions | none except contract calls | Strong | Prevents double-claim across all payout paths. |
| Q-11 | `assertions[id].winner` | address | n/a | none | storage | `claimUndisputedReward`, `settleAssertion` | none except contract calls | Strong | Determines disputed and undisputed payout recipient. |

## Source Buckets

| bucket | definition | examples | required proof shape |
|---|---|---|---|
| reserved | Escrowed ETH locked for a live assertion | assertion reward, proposer bond, disputer bond | state-machine and exact-value preconditions |
| claimable | ETH owed after lifecycle condition is satisfied | proposer undisputed payout, disputed winner payout, asserter refund | no double-claim and recipient-selection rules |
| fee | ETH owed to decider after disputed settlement | one bond in disputed claim path | access-control and payout-shape rules |
| donated | Unsolicited native ETH not assigned to an assertion | forced ETH | documented raw-balance residual |
| terminal | Value already claimed or assertion already settled | `claimed == true`, `winner != 0` | terminal-state preservation |

## Open Accounting Questions

| id | question | impact | owner / next step |
|---|---|---|---|
| AQ-01 | Should the campaign model recipient fallback reentrancy directly rather than using `optimistic_fallback`? | Would strengthen H-03/H-04/H-05 from Weak to Strong. | Optional follow-up; no related failure found in this campaign. |
| AQ-02 | Should exact native balance conservation exclude force-sent ETH with a provenance ghost? | Would upgrade raw `address(this).balance` coverage from Partial to Strong. | Optional follow-up; current challenge logic does not read raw balance for state decisions. |
