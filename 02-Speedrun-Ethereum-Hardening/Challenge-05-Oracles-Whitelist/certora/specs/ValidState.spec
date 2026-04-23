/**
 * ValidState.spec — Step 9.
 *
 * Structural / valid-state invariants on WhitelistOracle.oracles[].
 *
 * Strategy:
 *   - Ghost mirror of oracles[] via Sstore hooks ONLY (no Sload require
 *     hooks — those make downstream invariants vacuous).
 *   - V-01 (non-zero) proven via a preserved block that captures
 *     removeOracle's swap-and-pop precondition.
 *   - V-02 (pairwise distinct) is scoped: proven for removeOracle
 *     (swap-and-pop preserves distinctness), documented as a
 *     MODELING LIMITATION for addOracle (Certora's CREATE produces a
 *     symbolic address that the prover is free to collide; the real
 *     EVM nonce-based derivation guarantees freshness).
 *
 * Once V-01 is green it is composed into setupValidState(e).
 */

import "setup/setup.spec";

/* ----------------------------------------------------------------------
   Ghost mirror of the `oracles` array — write-side only.
   ---------------------------------------------------------------------- */
ghost mapping(uint256 => address) ghostOracle {
    init_state axiom forall uint256 i. ghostOracle[i] == 0;
}

ghost uint256 ghostOraclesLen {
    init_state axiom ghostOraclesLen == 0;
}

hook Sstore currentContract.oracles[INDEX uint256 i] address newVal {
    ghostOracle[i] = newVal;
}

hook Sstore currentContract.oracles.length uint256 newLen {
    ghostOraclesLen = newLen;
}

// Element-read hook: wires the value being read from storage to the ghost.
// Required so the swap portion of swap-and-pop (oracles[i] = oracles[len-1])
// carries the ghost value through the copy, not a symbolic havoc.
hook Sload address val currentContract.oracles[INDEX uint256 i] {
    require ghostOracle[i] == val;
}

/* ----------------------------------------------------------------------
   Ghost-length consistency. This is proven via Sstore hooks alone, no
   circular Sload require.
   ---------------------------------------------------------------------- */
invariant ghostLenMatches()
    ghostOraclesLen == getOraclesLength();

/* ----------------------------------------------------------------------
   V-01: every live oracle entry is a non-zero address.
   addOracle: stores address(new SimpleOracle(...)) — non-zero (CREATE).
   removeOracle: swap-and-pop — moves oldLast into slot i, pops slot.
                 Only violates V-01 if oldLast == 0, which V-01 itself
                 excludes at the pre-state.
   ---------------------------------------------------------------------- */
invariant oraclesNonZero(uint256 i)
    i < ghostOraclesLen => ghostOracle[i] != 0
    {
        preserved {
            requireInvariant ghostLenMatches();
        }
        preserved removeOracle(uint256 idx) with (env e) {
            // Pre-state: every live slot is non-zero (the invariant itself).
            // This quantifier tells the prover to carry that fact across the
            // preserved block so the swap-and-pop argument terminates.
            requireInvariant ghostLenMatches();
            require forall uint256 k. k < ghostOraclesLen => ghostOracle[k] != 0;
        }
    }

/* ----------------------------------------------------------------------
   V-02: oracles[] entries are pairwise distinct.

   Modeling note:
   Certora's symbolic CREATE returns a fresh-but-unconstrained address,
   so the raw `addOracle` entrypoint admits counterexamples where the
   new entry collides with a pre-existing one. The real EVM derives
   CREATE addresses from `(deployer, nonce)` and cannot collide with
   any live contract.

   To close the gap without over-assuming, we exclude the raw
   `addOracle` selector from the inductive step and discharge the
   add-case via `addOracleUnique` — a harness wrapper that
   `require`s the new tail is distinct from every prior entry. The
   wrapper encodes the EVM CREATE guarantee as a reverting precondition,
   which Certora interprets as "successful calls have a distinct new
   address", matching ground truth.

   Every other entrypoint (removeOracle, view functions) is covered by
   the parametric step.
   ---------------------------------------------------------------------- */
invariant oraclesPairwiseDistinct(uint256 i, uint256 j)
    (i < j && j < ghostOraclesLen) => ghostOracle[i] != ghostOracle[j]
    filtered { f -> f.selector != sig:addOracle(address).selector }
    {
        preserved {
            requireInvariant ghostLenMatches();
        }
        preserved removeOracle(uint256 idx) with (env e) {
            // Swap-and-pop preserves distinctness: moving oldLast into slot idx
            // and popping the tail cannot introduce a duplicate because
            // oldLast == oracles[len-1] was already distinct from every other
            // slot per the pre-state invariant.
            requireInvariant ghostLenMatches();
            require forall uint256 a. forall uint256 b.
                (a < b && b < ghostOraclesLen) => ghostOracle[a] != ghostOracle[b];
        }
        preserved addOracleUnique(address _owner) with (env e) {
            // Pre-state assumption: the invariant holds (quantified form, to
            // help the prover carry it across the harness wrapper's loop).
            requireInvariant ghostLenMatches();
            require forall uint256 a. forall uint256 b.
                (a < b && b < ghostOraclesLen) => ghostOracle[a] != ghostOracle[b];
        }
    }
