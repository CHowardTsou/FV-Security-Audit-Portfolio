# CrowdFund Certora Suite

This directory contains a small but fully working Certora suite for the crowdfunding protocol in [CrowdFund.sol](/Users/howard/speedrunethereum/challenge-crowdfunding/packages/hardhat/contracts/CrowdFund.sol).

The suite is split by behavior:

- `certora/specs/CrowdFundStateMachine.spec`
- `certora/specs/CrowdFundAccounting.spec`
- `certora/specs/CrowdFundMeta.spec`

It follows the 4-tier methodology:

1. valid state properties
2. variable transition properties
3. state transition properties
4. high-level user expectations

## Protocol model

Actors:

- contributors
- the funding recipient
- an arbitrary caller who may call `execute()`

Core storage:

- `balances[user]`
- `openToWithdraw`
- `deadline`
- `fundingRecipient.completed()`

Lifecycle:

1. Before `deadline`, users may contribute.
2. After `deadline`, `execute()` picks one branch:
   - success: all ETH is forwarded to `FundingRecipient` and `completed = true`
   - failure: `openToWithdraw = true`
3. In the failure branch, contributors may withdraw their recorded balances.

External-call boundaries:

- `withdraw()` sends ETH to `msg.sender`
- `execute()` sends ETH to `FundingRecipient.complete()`
- `receive()` forwards into `contribute()`

## File layout

- `certora/harness/CrowdFundHarness.sol`
- `certora/specs/CrowdFundStateMachine.spec`
- `certora/specs/CrowdFundAccounting.spec`
- `certora/specs/CrowdFundMeta.spec`
- `certora/conf/CrowdFundStateMachine.conf`
- `certora/conf/CrowdFundAccounting.conf`
- `certora/conf/CrowdFundMeta.conf`

## Harness notes

`CrowdFundHarness` exists to make proof-writing simpler, not to change protocol behavior.

It provides scalar getters for proof-relevant state:

- `contributionOf(address)`
- `contractBalance()`
- `recipientBalance()`
- `recipientCompleted()`
- `thresholdValue()`
- `receiveForwarderAddress()`

It also deploys:

- a fresh `FundingRecipient`
- a `ReceiveForwarder`, used to exercise the `receive()` path through a distinct sender contract

The configs link these storage fields to real contracts so Certora does not treat them as unresolved external calls:

- `fundingRecipient`
- `receiveForwarder`

## Green rules

### State machine

Current green rules in `CrowdFundStateMachine.spec`:

- `deadlineIsImmutable`
- `openToWithdrawIsSticky`
- `executeBeforeDeadlineReverts`
- `executeBelowThresholdOpensWithdraw`
- `executeAtOrAboveThresholdCompletesAndDrains`
- `failedExecuteKeepsWithdrawalsOpen`
- `contributeRevertsAfterCompletion`
- `withdrawRevertsAfterCompletion`
- `executeRevertsAfterCompletion`

These cover:

- immutable deployment-time deadline
- sticky failed branch state
- pre-deadline safety
- correct success/failure branch selection after deadline
- post-completion blocking through `notCompleted`

### Accounting

Current green rules in `CrowdFundAccounting.spec`:

- `contributeIncreasesCallerBalanceByMsgValue`
- `receiveIncreasesCallerBalanceByMsgValue`
- `successfulWithdrawZerosRecordedBalance`
- `withdrawCannotIncreaseRecordedBalance`
- `contributeDoesNotChangeOtherUserBalance`
- `withdrawDoesNotChangeOtherUserBalance`

These cover:

- caller accounting on `contribute()`
- receive-path accounting equivalence
- zeroing behavior on successful `withdraw()`
- monotonicity of recorded balances under `withdraw()`
- per-user balance isolation

### Ghost-backed accounting

The accounting spec also includes two green ghost-based properties:

- `shadowContribution`
- `trackedTotalContribution`

These are not separate rules by themselves; they are ghost models used inside the accounting rules.

`shadowContribution[user]` is a direct mirror ghost:

- it is updated on every `balances[user]` write
- it uses direct assignment:
  `shadowContribution[user] = newValue`
- it is useful when the ghost is meant to match one storage slot exactly

`trackedTotalContribution` is a derived aggregate ghost:

- it tracks the sum of observed `balances[user]` deltas
- it uses delta-update form:
  `trackedTotalContribution = trackedTotalContribution + newValue - oldValue`
- it is useful when the ghost represents an aggregate, not one slot

The suite currently checks that:

- after `contribute()`, the caller shadow matches the stored contribution
- after `receive()`, the forwarder shadow matches the stored contribution
- after `contribute()` and `receive()`, `trackedTotalContribution` increases by exactly `msg.value`

### Meta-rules applied to this protocol

Current green rules in `CrowdFundMeta.spec`:

- `contributeHasEffect`
- `withdrawHasEffect`
- `executeHasEffect`
- `nonViewFunctionCanSucceed`
- `viewFunctionDoesNotChangeStorage`
- `revertRollsBackStorage`

These cover:

- each main state-changing entrypoint has at least one path with local storage effect
- each main state-changing entrypoint has at least one successful path
- view-like methods do not mutate `CrowdFundHarness` storage
- reverting executions roll back local storage

## Commands

Compile/typecheck only:

```bash
certoraRun certora/conf/CrowdFundStateMachine.conf --solc /Users/howard/.svm/0.8.20/solc-0.8.20 --compilation_steps_only
certoraRun certora/conf/CrowdFundAccounting.conf --solc /Users/howard/.svm/0.8.20/solc-0.8.20 --compilation_steps_only
certoraRun certora/conf/CrowdFundMeta.conf --solc /Users/howard/.svm/0.8.20/solc-0.8.20 --compilation_steps_only
```

Run proofs:

```bash
certoraRun certora/conf/CrowdFundStateMachine.conf --solc /Users/howard/.svm/0.8.20/solc-0.8.20
certoraRun certora/conf/CrowdFundAccounting.conf --solc /Users/howard/.svm/0.8.20/solc-0.8.20
certoraRun certora/conf/CrowdFundMeta.conf --solc /Users/howard/.svm/0.8.20/solc-0.8.20
```

## Modeling decisions and constraints

The suite intentionally adds a few proof constraints to avoid false positives from symbolic EVM edge cases.

### Nonpayable calls

Rules that exercise nonpayable functions require:

```text
e.msg.value == 0
```

Without this, Certora may invent calls that would revert before protocol logic because Solidity rejects ETH sent to nonpayable functions.

### Linked external contracts

`FundingRecipient` and `ReceiveForwarder` are linked in the config so calls to:

- `fundingRecipient.completed()`
- `fundingRecipient.complete(...)`
- `receiveForwarder.send(...)`

are proven against real code instead of `AUTO summary` / `DEFAULT HAVOC`.

### Success-branch transfer overflow guard

The success-branch rule requires:

```text
recipientBalanceBefore <= max_uint256 - contractBalanceBefore
```

This excludes impossible EVM states where the recipient account balance would overflow during ETH transfer.

### Sender aliasing

Some rules exclude:

```text
e.msg.sender == currentContract
```

This avoids self-call traces that are legal symbolically but not meaningful for the user-facing property being proved.

### Receive-path scope

`receiveIncreasesCallerBalanceByMsgValue` proves the important accounting property:

- the direct sender through the `receive()` path gets credited by exactly `msg.value`

It does not currently prove a raw `address(this).balance` delta in the wrapper-based setup, because the harness entrypoint itself introduces self-transfer artifacts that make that balance assertion low-signal.

### Withdraw success scope

The suite proves conditional withdraw properties:

- if a withdraw succeeds, the caller's recorded balance is zeroed
- withdraw never increases a recorded balance
- withdraw does not mutate another user's recorded balance

It does not prove that `withdraw()` must always succeed for every symbolic caller, because arbitrary symbolic recipients may reject ETH.

This is also why ghost alignment is not currently asserted after `withdraw()`: the external call to `msg.sender` can trigger unresolved-call havoc for non-persistent ghosts.

### Meta-rule scoping

The first attempt at a universal no-op detector was intentionally too broad:

- it treated every non-view method in the linked system as if it should mutate `currentContract` storage

That produced low-signal counterexamples for:

- `FundingRecipient.complete()`
- `ReceiveForwarder.<receiveOrFallback>()`

Those traces were correct. They taught an important lesson:

- reusable meta-rules should usually be scoped to the verified contract's own entrypoints, not every linked helper contract

The final `CrowdFundMeta.spec` therefore scopes effect and revert meta-rules to the main `CrowdFundHarness` methods:

- `contribute`
- `withdraw`
- `execute`
- `sendEthToReceive` where appropriate

It also leaves `timeLeft()` non-`envfree`, because it depends on `block.timestamp`.

## How to extend the suite

Recommended next additions:

1. witness specs for intentionally broken variants of the protocol
2. stronger end-to-end failed-campaign withdrawal flow properties
3. a more ambitious ghost model over a tracked contributor set with explicit preserved invariants

## Reusable meta-rules

Besides protocol-specific rules, it is often worth adding a small library of protocol-agnostic sanity rules. These are useful for catching implementation mistakes like:

- writing to memory instead of storage
- broken modifiers
- dead code paths
- accidental state mutation in view functions
- state changes that survive reverting executions

These rules are not universally sound for every function family, so treat them as templates and scope them carefully.

For this repo, the most useful version was not the raw universal form. The useful version was:

- reusable rule shape
- scoped to the main protocol contract
- aware of linked helper contracts and env-dependent view functions

### 1. Non-view function has some effect

This is the pattern you surfaced. It is especially useful for setters, admin functions, and state-transition entrypoints.

```cvl
rule noOpFunctionDetection(env e, method f, calldataarg args)
    filtered { f -> !f.isView && !f.isPure }
{
    storage before = lastStorage;
    f(e, args);
    storage after = lastStorage;

    satisfy(before[currentContract] != after[currentContract]);
}
```

Meaning:

- for each non-view function, there exists at least one execution path where local storage changes

Good at catching:

- `memory` vs `storage` bugs in setters
- accidentally no-op admin functions
- functions that only emit events but never persist the intended update

### 2. Non-view function can succeed

Useful for catching dead entrypoints, impossible preconditions, or broken modifier wiring.

```cvl
rule nonViewFunctionCanSucceed(env e, method f, calldataarg args)
    filtered { f -> !f.isView && !f.isPure }
{
    f@withrevert(e, args);
    satisfy(!lastReverted);
}
```

Meaning:

- each non-view function should have at least one successful execution path

### 3. View or pure function does not mutate storage

Useful as a broad sanity check.

```cvl
rule viewFunctionDoesNotChangeStorage(env e, method f, calldataarg args)
    filtered { f -> f.isView || f.isPure }
{
    storage before = lastStorage;
    f(e, args);
    storage after = lastStorage;

    assert before[currentContract] == after[currentContract];
}
```

Meaning:

- view and pure functions should not mutate contract storage

### 4. Reverting path rolls back local storage

Useful for checking that partially executed failing paths do not leave unexpected local state behind.

```cvl
rule revertRollsBackStorage(env e, method f, calldataarg args)
    filtered { f -> !f.isView && !f.isPure }
{
    storage before = lastStorage;
    f@withrevert(e, args);

    assert lastReverted => before[currentContract] == lastStorage[currentContract];
}
```

Meaning:

- if a call reverts, local storage should match the pre-state

### 5. Repeated same-input call is eventually idempotent

This is best for admin/config setters, not for counters or accrual functions.

```cvl
rule repeatedCallEventuallyIdempotent(env e, method f, calldataarg args)
    filtered { f -> !f.isView && !f.isPure }
{
    f@withrevert(e, args);
    require !lastReverted;

    storage after1 = lastStorage;

    f@withrevert(e, args);
    require !lastReverted;

    storage after2 = lastStorage;

    satisfy(after1[currentContract] == after2[currentContract]);
}
```

Meaning:

- there exists at least one same-input path where the second call causes no additional storage change

### 6. Unauthorized caller should not successfully mutate protected state

This one is broad in spirit but usually needs scoping to known privileged methods or storage regions.

```cvl
rule unauthorizedCannotMutateProtectedFunction(env e, method f, calldataarg args, address admin)
    filtered { f -> !f.isView && !f.isPure }
{
    require e.msg.sender != admin;

    storage before = lastStorage;
    f@withrevert(e, args);

    assert !lastReverted => before[currentContract] != lastStorage[currentContract] => false;
}
```

In practice, use this only after narrowing:

- the protected methods
- the expected admin identity
- or the storage region that should remain unchanged

## When to use these

These meta-rules work best:

- early in a proving campaign
- on small and medium protocols
- when you want broad structural bug discovery before deep economic invariants

They are especially helpful for:

- setters
- governance/admin controls
- state-machine transitions
- upgrade/configuration plumbing

## When not to overuse them

Be careful with:

- accrual functions that may legitimately do nothing on some paths
- permissioned functions where success needs caller setup
- wrappers whose useful effect is external, not local storage
- functions whose main behavior is ETH or token transfer rather than storage mutation

Meta-rules are best used as bug-finders and smoke tests, not as replacements for protocol-specific correctness properties.

Keep the same workflow:

1. write the property in English first
2. decide which tier it belongs to
3. add the minimum harness support needed
4. run one spec file
5. classify the first red as bug, model gap, or over-strong rule
6. tighten only what the trace justifies

## Practical lessons from this suite

This protocol was a good example of the normal Certora workflow:

- first red traces came from unresolved external calls
- the next reds came from nonpayable-call modeling
- later reds came from symbolic aliasing and impossible EVM balances
- ghost assertions were clean on pure storage-write paths, but became low-signal across unresolved external calls
- only after those were constrained did the rules describe the protocol cleanly

That is expected. The main skill is not avoiding red traces. The main skill is learning which reds are meaningful.
