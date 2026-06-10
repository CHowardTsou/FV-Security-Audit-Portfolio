# OptimisticOracle Formal Verification

Certora formal verification suite for `contracts/OptimisticOracle.sol`.

## Verification Status

| Family | Conf | Status | Mutation |
|---|---|---|---|
| Sanity | `conf/optimistic_sanity.conf` | PASS | 3/5 killed |
| ValidState | `conf/optimistic_valid_state.conf` | PASS | 0/5 killed |
| StateMachine | `conf/optimistic_state_machine.conf` | PASS | 2/5 killed |
| Accounting | `conf/optimistic_accounting.conf` | PASS | 0/5 killed |
| AccessControl | `conf/optimistic_access_control.conf` | PASS | 0/5 killed |
| TimingWindow | `conf/optimistic_timing.conf` | PASS | 0/5 killed |

All six proof runs passed on 2026-05-21. Combined mutation kill rate: 5/5 unique mutants.

## Proof Run Links

| Family | Report |
|---|---|
| Sanity | https://prover.certora.com/output/6854102/848f8c3c94074c0caafc0e94b24a9037?anonymousKey=108585a4deb29330f1062c271aeaa1b3815ec90f |
| ValidState | https://prover.certora.com/output/6854102/98fc0a643a184b84beb0380ee8dad352?anonymousKey=41376053eb17b413c1769ddb24c45119c2066a58 |
| StateMachine | https://prover.certora.com/output/6854102/5bb420d92829435585fd55e07ee2d0e7?anonymousKey=47a5b225c6a86d8c529717bf12a532c4532705e8 |
| Accounting | https://prover.certora.com/output/6854102/15d8800501074a95bd9fe74728cb3a82?anonymousKey=c15fb75b792a329263209039055fab8cb98a5f5c |
| AccessControl | https://prover.certora.com/output/6854102/04daf462805f456f97a04d2fa15c4574?anonymousKey=ccfd69f50f57d3b437cd1d955e1b18ebe8099853 |
| TimingWindow | https://prover.certora.com/output/6854102/be83999d95874b1b808cd3f3d2fd5893?anonymousKey=27e83dc5414c74ce546cf44de55c982b62cbe9ec |

## Mutation Triage

| Family | Kill rate | Triage |
|---|---|---|
| Sanity | 3/5 | Kills always-reverting claim and refund mutants via liveness rules. |
| ValidState | 0/5 | Safety-only invariant family; liveness mutants covered by Sanity and StateMachine. |
| StateMachine | 2/5 | Kills always-reverting settlement mutant and broken `getState` return value mutant. |
| Accounting | 0/5 | Survivors killed by Sanity/StateMachine or outside this family's liveness scope. |
| AccessControl | 0/5 | Revert-condition family; liveness mutants covered elsewhere. |
| TimingWindow | 0/5 | Deadline-enforcement family; liveness mutants covered elsewhere. |

## Layout

```text
Challenge-05-Oracles-Optimistic/
  certora/
    conf/
    harness/
      OptimisticOracleHarness.sol
    specs/
      setup/
        protocol/
          methods.spec
          storage_hooks.spec
        helper.spec
        setup.spec
      AccessControl.spec
      Accounting.spec
      Sanity.spec
      StateMachine.spec
      TimingWindow.spec
      ValidState.spec
    ACCOUNTING.md
    FINDINGS.md
    HYPOTHESES.md
    MODELING_DEBT.md
    README.md
  contracts/
    Decider.sol
    OptimisticOracle.sol
```

## Running

```bash
certoraRun certora/conf/optimistic_sanity.conf
certoraRun certora/conf/optimistic_valid_state.conf
certoraRun certora/conf/optimistic_state_machine.conf
certoraRun certora/conf/optimistic_accounting.conf
certoraRun certora/conf/optimistic_access_control.conf
certoraRun certora/conf/optimistic_timing.conf
```

Add `--compilation_steps_only` to typecheck locally without submitting a cloud job.

## Modeling Notes

- ETH recipient fallbacks are modeled with `optimistic_fallback` where needed.
- The reentrancy residual is documented in `MODELING_DEBT.md`; production claim functions use checks-effects-interactions by setting `claimed = true` before transfers.
- Raw native balance conservation is Partial because force-sent ETH is not provenance-modeled.
