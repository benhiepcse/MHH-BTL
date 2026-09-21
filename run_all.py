#!/usr/bin/env python3
"""
run_all.py - THE single entry point for the CO2011 SEM261 assignment.
Grading command: python run_all.py --seed $(cat data/seed.txt)
"""
import argparse
import os
import subprocess
import sys

def run_m1(seed: int):
    print("\n" + "=" * 60)
    print("   RUNNING MODULE 1: LOGIC SPECIFICATION & SAT")
    print(f"   Team Seed: {seed}")
    print("=" * 60 + "\n")

    python_bin = sys.executable

    # 1. Predicate Validator (Req 1.1)
    print("[1/5] Validating Predicates (Req 1.1)...")
    subprocess.run([python_bin, "m1_logic/predicate_validator.py"], check=True)

    # 2. Data Preparation (Req 1.2)
    print("\n[2/5] Preparing Logic Data Slices (Req 1.2)...")
    subprocess.run([python_bin, "m1_logic/prepare_logic_data.py"], check=True)

    # 3. CNF Verification (Req 1.2)
    print("\n[3/5] Verifying CNF Encoding (Req 1.2)...")
    subprocess.run([
        python_bin, "m1_logic/verify_cnf.py",
        "--input", "data/generated/toy_sat_cnf.json"
    ], check=True)

    # 4. SAT Solver & UNSAT Core (Req 1.2)
    print("\n[4/5] Solving SAT Instances & UNSAT Core (Req 1.2)...")
    subprocess.run([
        python_bin, "m1_logic/sat_solver.py",
        "--input",
        "data/generated/toy_sat_cnf.json",
        "data/generated/m1_sat_slice_cnf.json",
        "data/generated/m1_unsat_slice_cnf.json",
        "--output", "data/generated/m1_results.json"
    ], check=True)

    subprocess.run([
        python_bin, "m1_logic/verify_unsat_core.py",
        "--input", "data/generated/m1_unsat_slice_cnf.json",
        "--results", "data/generated/m1_results.json"
    ], check=True)

    # 5. Logic to LP Bridge (Req 1.3)
    print("\n[5/5] Generating Logic-to-LP Bridge Constraints (Req 1.3)...")
    subprocess.run([python_bin, "m1_logic/logic_to_lp.py"], check=True)

    print("\n>>> [SUCCESS] Entire Module 1 pipeline executed cleanly.\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True, help="from data/seed.txt")
    ap.add_argument(
        "--stage",
        default="all",
        choices=["all", "m1", "m2", "m3", "m4", "m5"]
    )
    a = ap.parse_args()

    if a.stage in ("all", "m1"):
        run_m1(a.seed)

    if a.stage in ("all", "m2"):
        pass  # TODO: m2_ilp
    if a.stage in ("all", "m3"):
        pass  # TODO: m3_automata
    if a.stage in ("all", "m4"):
        pass  # TODO: m4_dynamics
    if a.stage in ("all", "m5"):
        pass  # TODO: m5_app

    print(f"[run_all] Finished stage: {a.stage}")

if __name__ == "__main__":
    main()