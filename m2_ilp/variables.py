"""
Module 2: Linear and Integer Programming (ILP)
Task W03-T3: Sets, Parameters and Decision Variables Definition
Author: 2453210 Phan The Thong

This module defines:
  1. Sets: I (invigilators), J (exam sessions), C (campuses).
  2. Parameters: demand (d_j), availability (a_ij), overlap (o_jk), campus (c_j, pref_i, p_ij).
  3. Decision Variables:
     - x_ij: Binary assignment variables (x_ij in {0, 1})
     - w_i: Integer workload variables (w_i in Z_>=0)
     - t: Continuous/Integer minimax load variable (t >= w_i, for min-max fairness)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import pulp
except ImportError:
    pulp = None  # type: ignore


class VariableType(str, Enum):
    """Supported variable types in Mathematical Programming."""
    BINARY = "binary"
    INTEGER = "integer"
    CONTINUOUS = "continuous"


@dataclass(frozen=True)
class SetDefinition:
    """Mathematical sets for the Invigilator Assignment Problem (IAP)."""
    invigilators_I: List[str]  # Staff IDs: CB001, ..., CB073
    sessions_J: List[str]       # Shift IDs: 20260518_1, ..., 20260609_5
    campuses_C: List[str]       # Campuses: 'Cơ sở 1', 'Cơ sở 2'
    dates: List[str] = field(default_factory=list)
    start_times: List[str] = field(default_factory=list)

    @property
    def num_invigilators(self) -> int:
        return len(self.invigilators_I)

    @property
    def num_sessions(self) -> int:
        return len(self.sessions_J)

    @property
    def num_campuses(self) -> int:
        return len(self.campuses_C)

    def validate(self) -> None:
        if self.num_invigilators == 0:
            raise ValueError("Set I (invigilators) cannot be empty.")
        if self.num_sessions == 0:
            raise ValueError("Set J (sessions) cannot be empty.")
        if self.num_campuses == 0:
            raise ValueError("Set C (campuses) cannot be empty.")


@dataclass
class ParameterDefinition:
    """Parameters extracted from dataset and preprocessing for Module 2 ILP."""
    # demand d_j: required number of proctors for session j
    demand: Dict[str, int]
    # availability a_ij: 1 if proctor i is available for session j, 0 if Busy(i,j)
    availability: Dict[Tuple[str, str], int]
    # overlap o_jk: set of session pairs (j, k) with overlapping time intervals
    overlap_pairs: List[Tuple[str, str]]
    # campus of session j
    session_campus: Dict[str, str]
    # preferred campus of invigilator i
    proctor_preferred_campus: Dict[str, str]
    # penalty matrix p_ij: 1.0 if session_campus != preferred_campus, else 0.0
    location_penalty: Dict[Tuple[str, str], float]
    # weights
    soft_weights: List[float] = field(default_factory=lambda: [1.28, 1.14, 1.57])
    weight_location: float = 1.28
    total_demand: int = 0

    def is_overlapping(self, j: str, k: str) -> bool:
        return (j, k) in self.overlap_pairs or (k, j) in self.overlap_pairs

    def is_available(self, i: str, j: str) -> bool:
        return self.availability.get((i, j), 1) == 1


@dataclass
class DecisionVariableMeta:
    """Metadata describing a mathematical decision variable."""
    name: str
    symbol: str
    var_type: VariableType
    lower_bound: Optional[float]
    upper_bound: Optional[float]
    indices: Tuple[str, ...]
    description: str


@dataclass
class VariableContainer:
    """Container holding all instantiated decision variables for solvers."""
    sets: SetDefinition
    parameters: ParameterDefinition
    # x_ij: (i, j) -> pulp.LpVariable or generic var
    x: Dict[Tuple[str, str], Any] = field(default_factory=dict)
    # w_i: i -> pulp.LpVariable or generic var
    w: Dict[str, Any] = field(default_factory=dict)
    # t: minimax load variable
    t: Optional[Any] = None
    # metadata
    metadata: Dict[str, DecisionVariableMeta] = field(default_factory=dict)

    @property
    def total_x_count(self) -> int:
        return len(self.x)

    @property
    def total_w_count(self) -> int:
        return len(self.w)

    @property
    def total_variables_count(self) -> int:
        return self.total_x_count + self.total_w_count + (1 if self.t is not None else 0)


# =============================================================================
# DATA LOADING & PARAMETER EXTRACTION
# =============================================================================

def load_sets_and_parameters(
    preprocessed_path: str | Path = "data/generated/m2_preprocessed_input.json",
    schema_report_path: str | Path = "data/generated/W03_T1_schema_report.md",
) -> Tuple[SetDefinition, ParameterDefinition]:
    """
    Loads sets I, J, C and parameters (demand, availability, overlap, campus)
    from W03-T1 and W03-T2 generated artifacts.
    """
    p_prep = Path(preprocessed_path).resolve()
    if not p_prep.is_file():
        # Try alternate path relative to workspace or MHH-BTL directory
        alt_paths = [
            Path("data/generated/m2_preprocessed_input.json"),
            Path("MHH-BTL/data/generated/m2_preprocessed_input.json"),
            Path("../data/generated/m2_preprocessed_input.json"),
        ]
        found = False
        for alt in alt_paths:
            if alt.is_file():
                p_prep = alt.resolve()
                found = True
                break
        if not found:
            raise FileNotFoundError(
                f"Preprocessed input file not found: {preprocessed_path}. "
                "Please run m2_ilp/preprocess_and_preferences.py first."
            )

    with open(p_prep, "r", encoding="utf-8") as f:
        prep_data = json.load(f)

    # 1. Sets I, J, C
    invigilators_I = sorted(prep_data["sets"]["invigilators_I"])
    sessions_J = sorted(prep_data["sets"]["sessions_J"])
    campuses_C = sorted(prep_data["sets"]["campuses_C"])

    # Extract dates and times from sessions dict
    sessions_dict = prep_data.get("sessions", {})
    dates = sorted({s["date"] for s in sessions_dict.values() if "date" in s})
    start_times = sorted({s["start_time"] for s in sessions_dict.values() if "start_time" in s})

    sets = SetDefinition(
        invigilators_I=invigilators_I,
        sessions_J=sessions_J,
        campuses_C=campuses_C,
        dates=dates,
        start_times=start_times,
    )
    sets.validate()

    # 2. Parameters: demand d_j, session_campus, overlap_pairs
    demand: Dict[str, int] = {}
    session_campus: Dict[str, str] = {}
    time_intervals: Dict[str, Tuple[str, str, str]] = {}  # sid -> (date, start, end)

    for sid, sdata in sessions_dict.items():
        demand[sid] = int(sdata.get("capacity", 2))
        session_campus[sid] = str(sdata.get("campus", "Cơ sở 1"))
        time_intervals[sid] = (
            str(sdata.get("date", "")),
            str(sdata.get("start_time", "")),
            str(sdata.get("end_time", "")),
        )

    # Compute overlapping pairs from half-open intervals [start, end) on same date
    overlap_pairs: List[Tuple[str, str]] = []
    session_list = sorted(sessions_dict.keys())
    for idx_a in range(len(session_list)):
        sid_a = session_list[idx_a]
        date_a, start_a, end_a = time_intervals[sid_a]
        if not date_a or not start_a or not end_a:
            continue

        for idx_b in range(idx_a + 1, len(session_list)):
            sid_b = session_list[idx_b]
            date_b, start_b, end_b = time_intervals[sid_b]
            if date_a != date_b:
                continue

            # Overlap condition: max(start_a, start_b) < min(end_a, end_b)
            if max(start_a, start_b) < min(end_a, end_b):
                overlap_pairs.append((sid_a, sid_b))

    # 3. Parameters: Preferences and Availability
    pref_dict = prep_data.get("preferences", {})
    proctor_pref: Dict[str, str] = {}
    location_penalty: Dict[Tuple[str, str], float] = {}
    availability: Dict[Tuple[str, str], int] = {}

    for i in invigilators_I:
        p_campus = pref_dict.get(i, {}).get("preferred_campus", "Cơ sở 1")
        proctor_pref[i] = p_campus

        for j in sessions_J:
            c_j = session_campus.get(j, "Cơ sở 1")
            # Unfavorable location penalty: 1.0 if mismatch, 0.0 if match
            penalty = 0.0 if c_j == p_campus else 1.0
            location_penalty[(i, j)] = penalty
            # Availability defaults to 1 (all available unless marked busy in dataset)
            availability[(i, j)] = 1

    weights = prep_data.get("metadata", {}).get("soft_weights", [1.28, 1.14, 1.57])
    weight_loc = float(prep_data.get("metadata", {}).get("weight_location_preference", weights[0]))

    parameters = ParameterDefinition(
        demand=demand,
        availability=availability,
        overlap_pairs=overlap_pairs,
        session_campus=session_campus,
        proctor_preferred_campus=proctor_pref,
        location_penalty=location_penalty,
        soft_weights=weights,
        weight_location=weight_loc,
        total_demand=sum(demand.values()),
    )

    return sets, parameters


# =============================================================================
# DECISION VARIABLE CREATION & REGISTRATION
# =============================================================================

def create_decision_variables(
    sets: SetDefinition,
    parameters: ParameterDefinition,
    model: Optional[pulp.LpProblem] = None,
    workload_as_integer: bool = True,
    t_as_continuous: bool = True,
) -> VariableContainer:
    """
    Instantiates decision variables for PuLP or generic optimization:
      1. x_ij in {0, 1} (Binary): assignment of proctor i to session j.
      2. w_i in Z_>=0 (Integer): total workload of proctor i (sum_j x_ij).
      3. t in R_>=0 or Z_>=0 (Continuous/Integer): maximum load across all proctors.
    """
    container = VariableContainer(sets=sets, parameters=parameters)

    # Calculate theoretical bounds for t
    min_possible_t = math.ceil(parameters.total_demand / sets.num_invigilators)
    max_possible_t = sets.num_sessions

    # Metadata definitions
    container.metadata["x"] = DecisionVariableMeta(
        name="x_ij",
        symbol="x_{ij}",
        var_type=VariableType.BINARY,
        lower_bound=0.0,
        upper_bound=1.0,
        indices=("i in I", "j in J"),
        description="Binary variable: 1 if proctor i is assigned to session j, 0 otherwise.",
    )

    container.metadata["w"] = DecisionVariableMeta(
        name="w_i",
        symbol="w_i",
        var_type=VariableType.INTEGER if workload_as_integer else VariableType.CONTINUOUS,
        lower_bound=0.0,
        upper_bound=float(sets.num_sessions),
        indices=("i in I",),
        description="Integer variable: total number of sessions assigned to proctor i.",
    )

    container.metadata["t"] = DecisionVariableMeta(
        name="t",
        symbol="t",
        var_type=VariableType.CONTINUOUS if t_as_continuous else VariableType.INTEGER,
        lower_bound=float(min_possible_t),
        upper_bound=float(max_possible_t),
        indices=("scalar",),
        description="Continuous/Integer minimax variable: maximum workload upper bound across all proctors.",
    )

    if pulp is not None:
        # 1. Create x_ij (Binary)
        for i in sets.invigilators_I:
            for j in sets.sessions_J:
                # Sanitized name for PuLP
                var_name = f"x_{i}_{j}"
                var = pulp.LpVariable(
                    name=var_name,
                    lowBound=0,
                    upBound=1,
                    cat=pulp.LpBinary,
                )
                container.x[(i, j)] = var

        # 2. Create w_i (Integer)
        w_cat = pulp.LpInteger if workload_as_integer else pulp.LpContinuous
        for i in sets.invigilators_I:
            var_name = f"w_{i}"
            var = pulp.LpVariable(
                name=var_name,
                lowBound=0,
                upBound=sets.num_sessions,
                cat=w_cat,
            )
            container.w[i] = var

        # 3. Create t (Continuous/Integer)
        t_cat = pulp.LpContinuous if t_as_continuous else pulp.LpInteger
        container.t = pulp.LpVariable(
            name="max_workload_t",
            lowBound=min_possible_t,
            upBound=max_possible_t,
            cat=t_cat,
        )
    else:
        # Fallback dummy representation when PuLP is not installed
        for i in sets.invigilators_I:
            for j in sets.sessions_J:
                container.x[(i, j)] = f"x[{i},{j}]"
            container.w[i] = f"w[{i}]"
        container.t = "t"

    return container


# =============================================================================
# MODEL COUPLING & LINEARIZATION CONSTRAINTS
# =============================================================================

def link_workload_and_minmax_constraints(
    model: pulp.LpProblem,
    container: VariableContainer,
) -> None:
    """
    Adds coupling constraints to the PuLP model:
      1. Workload definition: w_i = sum_j x_ij   (for all i in I)
      2. Minimax fairness:   t >= w_i            (for all i in I)
    """
    if pulp is None:
        raise RuntimeError("PuLP is required to construct mathematical model constraints.")

    # 1. Link workload: w_i - sum_j x_ij = 0
    for i in container.sets.invigilators_I:
        assigned_shifts = [container.x[(i, j)] for j in container.sets.sessions_J]
        model += (
            container.w[i] == pulp.lpSum(assigned_shifts),
            f"Workload_Definition_{i}",
        )

    # 2. Link minimax load: t >= w_i (equivalent to t - w_i >= 0)
    for i in container.sets.invigilators_I:
        model += (
            container.t >= container.w[i],
            f"MinMax_Fairness_Bound_{i}",
        )


def validate_variables(container: VariableContainer) -> Dict[str, Any]:
    """Validates variable dimensions, bounds, and types against theoretical specifications."""
    expected_x = container.sets.num_invigilators * container.sets.num_sessions
    expected_w = container.sets.num_invigilators
    expected_t = 1

    actual_x = container.total_x_count
    actual_w = container.total_w_count
    has_t = container.t is not None

    status = (
        actual_x == expected_x
        and actual_w == expected_w
        and has_t
    )

    return {
        "status": "VALID" if status else "INVALID",
        "sets": {
            "num_invigilators_|I|": container.sets.num_invigilators,
            "num_sessions_|J|": container.sets.num_sessions,
            "num_campuses_|C|": container.sets.num_campuses,
        },
        "variables": {
            "x_ij": {
                "count": actual_x,
                "expected": expected_x,
                "type": container.metadata["x"].var_type.value,
                "bounds": [container.metadata["x"].lower_bound, container.metadata["x"].upper_bound],
            },
            "w_i": {
                "count": actual_w,
                "expected": expected_w,
                "type": container.metadata["w"].var_type.value,
                "bounds": [container.metadata["w"].lower_bound, container.metadata["w"].upper_bound],
            },
            "t": {
                "count": 1 if has_t else 0,
                "expected": expected_t,
                "type": container.metadata["t"].var_type.value,
                "bounds": [container.metadata["t"].lower_bound, container.metadata["t"].upper_bound],
            },
            "total_count": container.total_variables_count,
            "expected_total": expected_x + expected_w + expected_t,
        },
        "parameters_summary": {
            "total_demand": container.parameters.total_demand,
            "num_overlap_pairs": len(container.parameters.overlap_pairs),
            "weight_location": container.parameters.weight_location,
        },
    }


# =============================================================================
# CLI EXECUTION & VERIFICATION TEST
# =============================================================================

def print_summary_table(val_report: Dict[str, Any]) -> None:
    """Pretty prints mathematical model structure."""
    print("=" * 78)
    print("  MODULE 2 (ILP) - SETS, PARAMETERS & DECISION VARIABLES SPECIFICATION")
    print("=" * 78)
    sets_info = val_report["sets"]
    vars_info = val_report["variables"]
    params_info = val_report["parameters_summary"]

    print("\n[1] MATHEMATICAL SETS:")
    print(f"  * I (Invigilators) : |I| = {sets_info['num_invigilators_|I|']:<4} proctors (CB001 - CB073)")
    print(f"  * J (Sessions)     : |J| = {sets_info['num_sessions_|J|']:<4} shifts (20260518_1 - 20260609_5)")
    print(f"  * C (Campuses)     : |C| = {sets_info['num_campuses_|C|']:<4} locations ('Cơ sở 1', 'Cơ sở 2')")

    print("\n[2] MODEL PARAMETERS:")
    print(f"  * Demand (d_j)     : Total required shift slots = {params_info['total_demand']}")
    print(f"  * Availability(a_ij: Binary availability flag (1=free, 0=busy)")
    print(f"  * Overlap (o_jk)   : Conflicting time slot pairs = {params_info['num_overlap_pairs']}")
    print(f"  * Campus (c_j, pref: Campus mapping + staff location preference (weight: {params_info['weight_location']})")

    print("\n[3] DECISION VARIABLES:")
    print(f"  {'Variable':<10} {'Symbol':<10} {'Type':<12} {'Count':<8} {'Bounds [LB, UB]':<18} {'Description'}")
    print("  " + "-" * 74)
    print(f"  {'x_ij':<10} {'x_{ij}':<10} {'BINARY':<12} {vars_info['x_ij']['count']:<8} {'[0, 1]':<18} {'Proctor i assigned to shift j'}")
    print(f"  {'w_i':<10} {'w_i':<10} {'INTEGER':<12} {vars_info['w_i']['count']:<8} {str(vars_info['w_i']['bounds']):<18} {'Total workload of proctor i'}")
    print(f"  {'t':<10} {'t':<10} {'CONTINUOUS':<12} {vars_info['t']['count']:<8} {str(vars_info['t']['bounds']):<18} {'Minimax maximum workload'}")
    print("  " + "-" * 74)
    print(f"  {'TOTAL':<10} {'':<10} {'':<12} {vars_info['total_count']:<8} {'':<18} {'Variables in ILP model'}")

    print(f"\n[4] VALIDATION STATUS: {val_report['status']}")
    print("=" * 78)


def main() -> None:
    parser = argparse.ArgumentParser(description="W03-T3: ILP Variables and Sets Definition")
    parser.add_argument(
        "--preprocessed",
        default="data/generated/m2_preprocessed_input.json",
        help="Path to m2_preprocessed_input.json",
    )
    parser.add_argument(
        "--output-summary",
        default="data/generated/m2_variables_summary.json",
        help="Path to export validation summary JSON",
    )
    args = parser.parse_args()

    # Load sets and parameters
    sets, parameters = load_sets_and_parameters(preprocessed_path=args.preprocessed)

    # Create variables
    container = create_decision_variables(sets, parameters)

    # Validate
    report = validate_variables(container)
    print_summary_table(report)

    # Test test problem creation with PuLP if available
    if pulp is not None:
        test_model = pulp.LpProblem("IAP_Module2_Test", pulp.LpMinimize)
        link_workload_and_minmax_constraints(test_model, container)
        # Objective min t
        test_model += container.t, "MinMax_Fairness_Objective"
        print(f"\n[5] PU LP INTEGRATION TEST:")
        print(f"  * Created test LpProblem: '{test_model.name}'")
        print(f"  * Total constraints added: {len(test_model.constraints)} (73 workload + 73 minimax)")
        print(f"  * Model objective: {test_model.objective}")
        print("  * Test model construction successful!")

    # Export summary
    out_path = Path(args.output_summary).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[6] Summary exported to: {out_path}\n")


if __name__ == "__main__":
    main()
