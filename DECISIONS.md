# Design decisions (your own words)
Record, per module, WHY you chose each objective, constraint, DFA, and dynamical direction, and what you rejected.


## Module 1 — W02-T4 SAT Solver and Minimal UNSAT Core

**Requirement:** 1.2
**Decision owner:** 2452347 Le Vo Nghia Hiep

### Use Z3 with named CNF constraints

I used Z3 because W02-T4 requires both SAT model generation and named UNSAT
core extraction. Each CNF constraint is tracked by its original name so that
an UNSAT core can be reported in a readable form and traced back to the input
instance.

I rejected returning only an SAT/UNSAT status because it would not satisfy the
requirements for readable assignments, named UNSAT cores, or verification
evidence.

### Independently validate SAT assignments

After Z3 returns SAT, the Boolean model is decoded into readable
invigilator-shift assignments. The decoded assignment is then checked against
every CNF clause independently of the solver result.

This additional validation was chosen to detect errors in model decoding or
result serialization. I rejected relying only on Z3's SAT status because that
would not verify that the exported assignment still satisfies every
constraint.

### Use deletion-based UNSAT core minimization

The initial named UNSAT core returned by Z3 is minimized deterministically.
Each constraint is removed in turn, and the remaining constraints are checked
again. A constraint is permanently removed when the remaining subset is still
UNSAT.

I chose this method because it is straightforward, reproducible, and suitable
for the provided toy and real-data slices. I rejected claiming a globally
minimum-cardinality core because deletion-based minimization guarantees only
subset-minimality.

### Verify subset-minimality separately

The verification script checks that the complete candidate core is UNSAT and
that removing any single constraint makes the remaining subset SAT. It also
checks that every reported constraint name exists in the original CNF input.

I kept verification separate from core generation so that the generated result
can be independently checked instead of trusting the solver pipeline alone.

### Treat UNKNOWN as a failed verification

Any UNKNOWN result is recorded and causes the complete-suite validation or
UNSAT-core verification to fail.

I chose this conservative behavior because UNKNOWN does not prove either SAT
or UNSAT and therefore cannot support a correctness claim.

### Store reproducible evidence in JSON

The final results are stored in `data/generated/m1_results.json`, including
instance metadata, SAT assignments, assignment validation, named UNSAT cores,
minimality checks, seed, team ID, and summary counts.

JSON was selected because it is machine-readable, deterministic, and suitable
for later integration with the Module 1 runner and report.
