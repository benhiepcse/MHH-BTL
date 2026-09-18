# CO2011 SEM261 — Invigilator Assignment Problem (team repository)

Created from the course template with **"Use this template"** (not a fork). Keep this repo **private**
and add your class's instructor as a collaborator.

## First 15 minutes (Day 1)
1. Rename this repo to your **team ID**: `CO2011-261-<group>-<smallest student ID>`
   (`group ∈ {L, CC, A01, TN01}`), e.g. `CO2011-261-L-2252107`. Use it exactly everywhere.
2. Each member sets their git identity:
   `git config user.name "2252345 Nguyen Van A"` and `git config user.email "2252345@hcmut.edu.vn"`.
3. Generate your seed: `python tools/make_seed.py CO2011-261-L-2252107 > data/seed.txt`.
4. Read the assignment brief (on the LMS / course page); fill `MEETINGS.md` after your first meeting.

## Layout
```
run_all.py          # THE entry point: python run_all.py --seed $(cat data/seed.txt)
requirements.txt    # pin your versions
tools/make_seed.py  # seed + soft-weights from your team ID (do not edit)
data/               # dataset + seed.txt
m1_logic/  m2_ilp/  m3_automata/  m4_dynamics/  app/  report/
CHECKPOINTS.md  CONTRIBUTIONS.md  DECISIONS.md  MEETINGS.md
```

## Every week
Push a tagged commit `week-01 … week-14` with a `CHECKPOINTS.md` entry; tag milestones `m1 … m5`, then `submission`.
`python run_all.py --seed $(cat data/seed.txt)` must reproduce every number in your report from a clean clone.

Declare any AI-tool use in this README. Full rules, rubric (Appendix B), and the red **CRITICAL** items are in the brief.

## AI-use declaration

2453210 Phan Thế Thông used OpenAI Codex as an AI assistant while implementing
W02–T3 / Requirement 1.2. Assistance covered drafting and reviewing the CNF
encoder, verifier, and local test commands for the toy and real data slices.

2452347 Le Vo Nghia Hiep used OpenAI ChatGPT as an AI assistant while
implementing W02-T4 / Requirement 1.2. Assistance covered reviewing and
debugging the SAT/SMT solver and minimal UNSAT-core verifier, suggesting
additional validation steps and improvements, troubleshooting execution and
Git commands, verifying the generated results, and drafting the related
documentation. The implementation was authored, reviewed, tested, and
integrated by the student, who remains responsible for understanding and
explaining the submitted work.

2453196 Nguyen Ngoc Thien used Google Antigravity as an AI assistant while
implementing W02-T2 / Requirement 1.2. Assistance covered reviewing the JSON
data schema, designing lightweight Excel parsing using Python's standard
library, structuring the deterministic sampling logic with the team seed,
creating the SAT and UNSAT instance generators, troubleshooting Git workflows,
and drafting technical documentation. All modeling logic, constraint decisions,
and generated data slices were authored, verified, and validated by the student,
who remains responsible for explaining and defending the work.

#### Cardinality / Counting Rules (Req 1.3)
- **Exact Capacity Constraint**: Shift $j$ requires exactly $k$ invigilators.
  - **In LP**: Represented as a single linear equality $\sum_{i} x_{ij} = k$.
  - **In CNF**: Requires breaking into *At-least-k* and *At-most-k*. The naive binomial encoding for *At-most-k* generates $\binom{n}{k+1}$ clauses, leading to clause explosion on large instances.
- **At-most-k Constraint**: $\sum_{i} x_{ij} \le k$.
