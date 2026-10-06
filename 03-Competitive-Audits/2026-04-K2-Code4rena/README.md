# Code4rena — K2 (April 2026)

**K2** is an Aave-style lending protocol on **Stellar / Soroban**, written in Rust. It has a router, aTokens and debt tokens, a price oracle with a TTL cache, interest-rate strategies, a liquidation engine, flash liquidations, incentives, and swap adapters (Aquarius, Soroswap).

- **Official report:** https://code4rena.com/reports/2026-04-k2 (published 2026-08-20)
- **Contest repo:** https://github.com/code-423n4/2026-04-k2
- **Warden handle:** `cht1206`

## Results

| ID | Title | Severity | Bug class | Found with | Submission |
|:--|:--|:--|:--|:--|:--|
| [M-25](findings/M-25-oracle-vector-cache-serves-disabled-asset.md) | Disabled oracle assets remain usable through the batch-price TTL cache | Medium | Cache invalidation / check ordering | Sunbeam reduced-model rules (GAP-39/47) + host PoC | [S-1781](https://code4rena.com/audits/2026-04-k2/submissions/S-1781) |
| [M-42](findings/M-42-atoken-transfer-from-exceeds-allowance.md) | Approved spender exceed nominal allowance by splitting aToken transfers into dust chunks | Medium | Unit mismatch: nominal allowance vs. rounded-up scaled debit | Sunbeam bounded symbolic rules (GAP-96) + host PoC | [S-2190](https://code4rena.com/audits/2026-04-k2/submissions/S-2190) |

## Methodology: Certora Sunbeam campaign

I ran the audit as a formal-verification campaign with **Certora Sunbeam** (`certoraSorobanProver`), the Certora Prover for Soroban WASM. Rules are written in Rust with CVLR (`#[rule]`, `cvlr_assume!`, `cvlr_assert!`, `cvlr_satisfy!`).

```
 protocol analysis ──► spec families ──► hypotheses (GAP-xx)
                                              │
                                              ▼
                               expected-red rule on contest code
                                              │  Prover violation = bug witness
                                              ▼
                          host PoC on real compiled WASM (confirm impact)
                                              │
                                              ▼
                        source fix  ──►  closure rule (SFC-xx) must pass
```

**Scale of the campaign:**

| | |
|:--|:--|
| Spec families | 8: router core, router liquidation/flash, token ledgers, oracle & interest, incentives & treasury, config/admin/upgrade, swap adapters, thin helpers |
| Target contracts | 14 |
| `#[rule]`s written | ~1,950 |
| Prover jobs | ~760 |

**Techniques used:**

| Technique | Where |
|:--|:--|
| **Expected-red → fix → closure workflow.** Each hypothesis gets a rule that should fail on the contest code and a matching rule that must pass on the fix. | M-25 (GAP-39/47 → SFC-02) |
| **Reduced-model rules.** Branch or arithmetic logic restated as pure functions, so the Prover reasons about the decision itself without host-environment noise. | M-25 (cache/config decision), M-42 (share arithmetic + allowance guard) |
| **Bounded symbolic inputs** (`cvlr_assume!` ranges on u64 → u128) to keep RAY-scale arithmetic tractable. | M-42 |
| **Guarded invariants.** Assume the guard *accepted* the call, then assert the safety bound, so any counterexample is an accepted exploit input. | M-42 (`…_exact_allowance_cannot_transfer_more_than_approved`) |
| **Symbolic + concrete rule pairs**, so the counterexample is easy to read and matches the PoC. | M-42 (`…_one_unit_allowance_moves_two_indexed_units`) |
| **Linked host PoCs** (Soroban `#[test]` with mock router / price source) to confirm Prover findings against real WASM. | Both findings |

## Contents

```
findings/   write-ups for each judged finding
certora/
  specs/    rule excerpts (expected-red, plus closure where it exists) for each finding
  confs/    certoraSorobanProver .conf files used for the runs
poc/        Soroban host PoC tests (drop into the contest's tests/c4 template)
```

## Prover runs

| Finding | Expected-red (bug) | Closure (fixed) |
|:--|:--|:--|
| M-25 | [gap39-47 ❌ 2/2 violated](https://prover.certora.com/output/6854102/f7fd2fe09c7a4a8b8e571b2f9ec1a5e2?anonymousKey=010f81181f8cef998467df588cb5b3d46a624a4b) | [sfc02 ✅ 4/4](https://prover.certora.com/output/6854102/a0a6402285254d97bcbcc3617ad4e912?anonymousKey=b3ba369e7e3c189ca8ce5935d8084ede40bbfc67) |
| M-42 | [gap96 ❌ 3/3 violated](https://prover.certora.com/output/6854102/f4687e97891c426bb9ef2ca10af2654f?anonymousKey=40f43b7c6f76a18e3303faea31e21ba42868c9e5) | — (no closure rule) |

Prover versions: 8.13.0 (M-25), 8.13.1 (M-42 refreshed run).

## Honest scope notes

- The rules here are **reduced models**. They prove properties of the logic restated as pure functions, not of the deployed entrypoints end to end. The host PoCs bridge that gap by showing the same behavior on the real compiled contracts.
- M-42 has expected-red evidence and a host PoC, but no closure rule for a patched version.
- M-25 was submitted as High and downgraded to Medium by the judge. Both findings were shared with other wardens.
