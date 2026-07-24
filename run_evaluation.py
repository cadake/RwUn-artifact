from RwUn.evaluation_utils import evaluate, quantum_to_ancilla_circuit
from RwUn.utils import *
from RwUn.uncomp import uncompute
from multiprocessing import Process
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from RwUn.evaluation_plot import plot_gatecount_two_curves_pages, plot_gatecount_two_curves_panels
from RwUn.examples.mcx import *
from RwUn.examples.adder import *
from RwUn.examples.mcry import *
from RwUn.examples.grover import *
from RwUn.examples.incrementer import *
from RwUn.examples.deutschjozsa import *
from RwUn.examples.intergercomparator import *
from RwUn.dependencygraph import dep_cyc
import argparse
import ast
import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

evaluation_folder = "evaluation"

TABLE1_ROW_SPECS = (
    ("clean integercomparator", "Clean IntegerComparator", "controls", "IntegerComparator(200, dirty=False)"),
    ("clean mcx", "Clean MCX", "controls", "MCX(201, dirty=False)"),
    ("mcry(pi/2)", "MCRY(pi/2)", "controls", "MCRY(10)"),
    ("clean incrementer", "Clean Incrementer", "operand", "Incrementer(101, dirty=False)"),
    ("dj", "Deutsch-Jozsa", "controls", "DJ(66)"),
    ("grover", "Grover's algorithm", "controls", "GroverCircuit(6)"),
    ("dirty mcx", "Dirty MCX", "controls", "MCX(101, dirty=True)"),
    ("clean adder", "Clean Adder", "per operand", "Adder(100)"),
    ("dirty intercomparator", "Dirty IntegerComparator", "controls", "IntegerComparator(58, dirty=True)"),
    ("highestbitconstadder", "HighestBitConstAdder", "operand", "DirtyHighestBitConstAdder(41)"),
    ("riseconditionalclean mcs", "RiseConditionalCleanMCS", "controls", "RiseConditionalMCS(51, dirty=False)"),
    ("conditionalclean mcs", "ConditionalCleanMCS", "controls", "ConditionalMCS(52, dirty=False)"),
    ("riseconditionaldirty mcs", "RiseConditionalDirtyMCS", "controls", "RiseConditionalMCS(27, dirty=True)"),
    ("conditionaldirty mcs", "ConditionalDirtyMCS", "controls", "ConditionalMCS(52, dirty=True)"),
    ("gidney's incrementer", "Gidney's Incrementer", "operand", "DirtyIncrementer(25)"),
    ("dirty adder", "Dirty Adder", "per operand", "DirtyAdder(9)"),
    ("dirty incrementer", "Dirty Incrementer", "operand", "Incrementer(15, dirty=True)"),
)


def _read_table1_efficiency_results(path):
    results = {}
    current_circuit = None

    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row:
                continue

            first = row[0].strip()
            if len(row) == 1 and first.endswith(":"):
                current_circuit = first[:-1].strip()
                results[current_circuit] = {}
                continue

            if current_circuit is None or len(row) < 2:
                continue

            try:
                mode = int(first)
            except ValueError:
                continue
            results[current_circuit][mode] = row[1].strip()

    return results


def _read_table1_dependency_results(path):
    with open(path, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines or lines[0] != "size, depth, dependency, cycle":
        raise ValueError(f"Unexpected dependency result format: {path}")

    records = lines[1:]
    if len(records) % 3 != 0:
        raise ValueError(f"Incomplete dependency result: {path}")

    results = {}
    for i in range(0, len(records), 3):
        circuit_name, _, dependency_text = records[i:i + 3]
        dependency, cycle = ast.literal_eval(dependency_text)
        results[circuit_name] = (int(dependency), int(cycle))
    return results


def _format_scale(raw_value):
    if raw_value is None or raw_value.startswith("None"):
        return "X", None

    recursion_limited = raw_value.endswith("*")
    scale = int(raw_value.rstrip("*"))
    text = "1000+" if scale >= 1000 else str(scale)
    if recursion_limited:
        text += r"\*"
    return text, scale


def merge_table1_results(table1_path, dependency_path, output_path=None):
    efficiency = _read_table1_efficiency_results(table1_path)
    dependencies = _read_table1_dependency_results(dependency_path)
    output_path = Path(output_path or Path(table1_path).with_name("table1_merged.md"))

    rows = []
    for section, circuit, parameter, dependency_key in TABLE1_ROW_SPECS:
        if section not in efficiency:
            raise ValueError(f"Missing efficiency results for {section}")
        if dependency_key not in dependencies:
            raise ValueError(f"Missing dependency results for {dependency_key}")

        formatted_scales = [_format_scale(efficiency[section].get(mode)) for mode in range(5)]
        numeric_scales = [scale for _, scale in formatted_scales if scale is not None]
        best_scale = max(numeric_scales, default=None)
        scale_cells = [
            f"**{text}**" if scale is not None and scale == best_scale else text
            for text, scale in formatted_scales
        ]

        dependency, cycle = dependencies[dependency_key]
        dependency_cell = f"{dependency} (cycle)" if cycle else str(dependency)
        rows.append((dependency, [circuit, parameter, dependency_cell, *scale_cells]))

    rows.sort(key=lambda item: item[0])
    lines = [
        "# Table 1",
        "",
        "Largest scale parameter (n) uncomputed within 30 seconds, sorted by Aw-Dep.",
        "",
        "| Circuit | Param (n) | Aw-Dep | RwUn Sequential | RwUn Reverse | RwUn Jointly | RwUn Lifetime | Reqomp |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for _, row in rows)
    lines.extend([
        "",
        "Notes:",
        "",
        "- Bold values are the largest successful scale in each row.",
        "- `1000+` means scaling stopped at n = 1000.",
        "- `n*` means Reqomp hit the recursion-depth limit.",
        "- `X` means that the method failed for the tested range.",
        "- `(cycle)` marks an aw-cycle in the dependency graph.",
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved: {output_path}")
    return str(output_path)

def alt10(n: int) -> int:
    if n <= 0:
        return 0
    x = 0
    for i in range(n):
        x = (x << 1) | (1 if i % 2 == 1 else 0)
    return x

def run_table1_dependency_complexity():
    lines = []
    lines.append("size, depth, dependency, cycle")

    def record(circ_type: str, circ, label=None):
        if label is not None:
            lines.append(str(label))
        lines.append(f"{circ_type}")
        lines.append(f"$\\SD{{{circ.size()}}}{{{circ.depth()}}}$")
        lines.append(str(dep_cyc(circ)))
        lines.append("")

    v = alt10(200)
    inc = makeIntegerComparator(200, v, dirty=False)
    record("IntegerComparator(200, dirty=False)", inc)

    inc = makeMCX(201, dirty=False)
    record("MCX(201, dirty=False)", inc)

    inc = makeMCRY(10)
    record("MCRY(10)", inc)

    inc = makesIncrementer(101, dirty=False)
    record("Incrementer(101, dirty=False)", inc)

    inc = makesDJ(66)
    record("DJ(66)", inc)

    inc = makesGroverCircuit(6)
    record("GroverCircuit(6)", inc)

    inc = makeMCX(101, dirty=True)
    record("MCX(101, dirty=True)", inc)

    inc = makesAdder(100)
    record("Adder(100)", inc)

    inc = makeConditionalMCS(52, dirty=False)
    record("ConditionalMCS(52, dirty=False)", inc)

    inc = makeConditionalMCS(52, dirty=True)
    record("ConditionalMCS(52, dirty=True)", inc)

    inc = makeRiseConditionalMCS(51, dirty=False)
    record("RiseConditionalMCS(51, dirty=False)", inc)

    inc = makeRiseConditionalMCS(27, dirty=True)
    record("RiseConditionalMCS(27, dirty=True)", inc)

    v = alt10(58)
    inc = makeIntegerComparator(58, v, dirty=True)
    record("IntegerComparator(58, dirty=True)", inc)

    v = 2 ** 41 - 1
    inc = makesDirtyHighestBitConstAdder(41, v)
    record("DirtyHighestBitConstAdder(41)", inc)

    inc = makesDirtyIncrementer(25)
    record("DirtyIncrementer(25)", inc)

    inc = makesDirtyAdder(9)
    record("DirtyAdder(9)", inc)

    inc = makesIncrementer(15, dirty=True)
    record("Incrementer(15, dirty=True)", inc)

    os.makedirs(evaluation_folder, exist_ok=True)
    output_path = os.path.join(evaluation_folder, "dependency_result")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path

def run_table1():
    lines = []
    lines.append("sequential(0), reverse(1), jointly(2), lifetime(3), reqomp(4)")
    lines.append("mode, n, time, size, depth")
    lines.append("")

    lines.append("clean integercomparator:")
    lines.append(test_cleancomparator_efficiency(0, 10, 20, 10))
    lines.append(test_cleancomparator_efficiency(1, 80, 110, 10))
    lines.append(test_cleancomparator_efficiency(2, 20, 30, 10))
    lines.append(test_cleancomparator_efficiency(3, 20, 30, 10))
    lines.append(test_cleancomparator_efficiency(4, 140, 190, 10))

    lines.append("clean mcx:")
    lines.append(test_mcx_efficiency(0, 30, 40, 10))
    lines.append(test_mcx_efficiency(1, 420, 470, 10))
    lines.append(test_mcx_efficiency(2, 180, 230, 10))
    lines.append(test_mcx_efficiency(3, 1000, 1100, 50))
    lines.append(test_mcx_efficiency(4, 140, 200, 10))

    lines.append("mcry(pi/2):")
    lines.append(test_mcry_efficiency(0, 1000, 1001, 50))
    lines.append(test_mcry_efficiency(1, 1000, 1001, 50))
    lines.append(test_mcry_efficiency(2, 1000, 1001, 50))
    lines.append(test_mcry_efficiency(3, 1000, 1001, 50))
    lines.append(test_mcry_efficiency(4, 10, 18, 1))


    lines.append("clean incrementer:")
    lines.append(test_incrementer_efficiency(0, 7, 8, 1))
    lines.append(test_incrementer_efficiency(1, 60, 110, 10))
    lines.append(test_incrementer_efficiency(2, 16, 17, 1))
    lines.append(test_incrementer_efficiency(3, 700, 800, 50))
    lines.append(test_incrementer_efficiency(4, 140, 200, 10))


    lines.append("dj:")
    lines.append(test_DJ_efficiency(3, 1000, 1001, 50))
    lines.append(test_DJ_efficiency(4, 120, 200, 10))

    lines.append("grover:")
    lines.append(test_grover_efficiency(3, 15, 16, 1))
    lines.append(test_grover_efficiency(4, 10, 14, 1))

    lines.append("dirty mcx:")
    lines.append(test_dirtymcx_efficiency(0, 40, 90, 10))
    lines.append(test_dirtymcx_efficiency(1, 40, 90, 10))
    lines.append(test_dirtymcx_efficiency(2, 60, 120, 10))
    lines.append(test_dirtymcx_efficiency(3, 1000, 1100, 50))
    lines.append(test_dirtymcx_efficiency(4, 10, 70, 10))

    lines.append("clean adder:")
    lines.append(test_adder_efficiency(0, 6, 7, 1))
    lines.append(test_adder_efficiency(1, 70, 80, 10))
    lines.append(test_adder_efficiency(2, 9, 10, 1))
    lines.append(test_adder_efficiency(3, 4, 7, 1))
    lines.append(test_adder_efficiency(4, 130, 200, 10))

    lines.append("riseconditionalclean mcs:")
    lines.append(test_riseconditionalcleanmcx_efficiency(0, 8, 14, 1))
    lines.append(test_riseconditionalcleanmcx_efficiency(1, 6, 12, 1))
    lines.append(test_riseconditionalcleanmcx_efficiency(2, 6, 12, 1))
    lines.append(test_riseconditionalcleanmcx_efficiency(3, 6, 12, 1))
    lines.append(test_riseconditionalcleanmcx_efficiency(4, 10, 11, 1))

    lines.append("conditionalclean mcs:")
    lines.append(test_conditionalcleanmcx_efficiency(0, 1000, 1001, 10))
    lines.append(test_conditionalcleanmcx_efficiency(1, 1000, 1001, 10))
    lines.append(test_conditionalcleanmcx_efficiency(2, 1000, 1001, 10))
    lines.append(test_conditionalcleanmcx_efficiency(3, 1000, 1001, 10))
    lines.append(test_conditionalcleanmcx_efficiency(4, 10, 11, 1))


    lines.append("riseconditionaldirty mcs:")
    lines.append(test_riseconditionaldirtymcx_efficiency(0, 7, 8, 1))
    lines.append(test_riseconditionaldirtymcx_efficiency(1, 7, 8, 1))
    lines.append(test_riseconditionaldirtymcx_efficiency(2, 7, 8, 1))
    lines.append(test_riseconditionaldirtymcx_efficiency(3, 7, 8, 1))
    lines.append(test_riseconditionaldirtymcx_efficiency(4, 10, 11, 1))


    lines.append("conditionaldirty mcs:")
    lines.append(test_conditionaldirtymcx_efficiency(0, 1000, 1001, 10))
    lines.append(test_conditionaldirtymcx_efficiency(1, 1000, 1001, 10))
    lines.append(test_conditionaldirtymcx_efficiency(2, 1000, 1001, 10))
    lines.append(test_conditionaldirtymcx_efficiency(3, 1000, 1001, 10))
    lines.append(test_conditionaldirtymcx_efficiency(4, 10, 11, 1))


    


    


    lines.append("dirty intercomparator:")
    lines.append(test_dirtycomparator_efficiency(0, 13, 14, 1))
    lines.append(test_dirtycomparator_efficiency(1, 13, 14, 1))
    lines.append(test_dirtycomparator_efficiency(2, 19, 20, 1))
    lines.append(test_dirtycomparator_efficiency(3, 15, 16, 1))
    lines.append(test_dirtycomparator_efficiency(4, 10, 60, 10))


    lines.append("highestbitconstadder:")
    lines.append(test_hbadder_efficiency(0, 6, 10, 1))
    lines.append(test_hbadder_efficiency(1, 6, 10, 1))
    lines.append(test_hbadder_efficiency(2, 7, 13, 1))
    lines.append(test_hbadder_efficiency(3, 7, 11, 1))
    lines.append(test_hbadder_efficiency(4, 10, 70, 10))


    lines.append("gidney's incrementer:")
    lines.append(test_gidneydirtyincrementer_efficiency(2, 35, 41, 1))
    lines.append(test_gidneydirtyincrementer_efficiency(4, 4, 10, 1))


    lines.append("dirty adder:")
    lines.append(test_dirtyadder_efficiency(0, 5, 7, 1))
    lines.append(test_dirtyadder_efficiency(1, 5, 6, 1))
    lines.append(test_dirtyadder_efficiency(2, 5, 6, 1))
    lines.append(test_dirtyadder_efficiency(3, 9, 10, 1))
    lines.append(test_dirtyadder_efficiency(4, 4, 10, 1))


    lines.append("dirty incrementer:")
    lines.append(test_dirtyincrementer_efficiency(0, 9, 10, 1))
    lines.append(test_dirtyincrementer_efficiency(1, 9, 10, 1))
    lines.append(test_dirtyincrementer_efficiency(2, 9, 10, 1))
    lines.append(test_dirtyincrementer_efficiency(3, 50, 60, 10))
    lines.append(test_dirtyincrementer_efficiency(4, 10, 60, 10))


    os.makedirs(evaluation_folder, exist_ok=True)
    output_path = os.path.join(evaluation_folder, "table1_result")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path





    

def run_random(qfree, quick=False, output_folder=None):
    output_folder = str(output_folder or evaluation_folder)

    def run(i: int):
        evaluate(qfree, i, output_folder, True, quick=quick)

    ps = [Process(target=run, args=(i,)) for i in (0, 1, 2)]
    for p in ps: p.start()
    for p in ps: p.join()
    if any(p.exitcode != 0 for p in ps):
        kind = "Q-free" if qfree else "non-Q-free"
        raise RuntimeError(f"{kind} evaluation failed in a worker process")

def plot_random_qfree(source_folder=None, output_folder=None):
    source_folder = Path(source_folder or evaluation_folder)
    output_folder = Path(output_folder or source_folder)
    folders = [
        source_folder / "results_qfree/42_5_5",
        source_folder / "results_qfree/42_40_40",
        source_folder / "results_qfree/42_200_200",
    ]
    page_specs = [
        {
            "tool_labels": ("RwUn", "Reqomp"),
            "y_builder": lambda d: (d.get("s1", []), d.get("s2", [])),
            "y_label": "Success Rate",
        },
        {
            "tool_labels": ("RwUn-only", "Both"),
            "y_builder": lambda d: (d.get("dep_1_success", []), d.get("dep_both_success", [])),
            "y_label": "Aw-Dep",
            "share_y": False,
        },
        {
            "tool_labels": ("RwUn", "Reqomp"),
            "y_builder": lambda d: (d.get("s1_no_cyc", []), d.get("s2_no_cyc", [])),
            "y_label": "Success Rate (No Aw-Cyc)",
            "share_y": False,
        },
        {
            "tool_labels": ("RwUn", "Reqomp"),
            "y_builder": lambda d: (d.get("s1_cyc", []), d.get("s2_cyc", [])),
            "y_label": "Success Rate (Aw-Cyc)",
            "share_y": False,
        },
    ]
    plot_gatecount_two_curves_pages(
        folders=folders,
        width_labels=["small", "medium", "large"],
        page_specs=page_specs,
        out_path=output_folder / "qfree_metrics.pdf",
    )

def plot_random_nonqfree(source_folder=None, output_folder=None):
    source_folder = Path(source_folder or evaluation_folder)
    output_folder = Path(output_folder or source_folder)
    folders = [
        source_folder / "results_nonqfree/42_5_5",
        source_folder / "results_nonqfree/42_40_40",
        source_folder / "results_nonqfree/42_200_200",
    ]

    y_builder = lambda d: (d.get("s1", []), d.get("s2", []))
    plot_gatecount_two_curves_panels(
        folders = folders,
        width_labels = ['small', 'medium', 'large'],
        tool_labels = ("RwUn", "Reqomp"),
        out_path = output_folder / "success_quan.pdf",
        y_builder = y_builder,
        y_label = "Success Rate"
    )


class ArtifactSmokeTests(unittest.TestCase):
    def test_rwun_and_reqomp_clean_mcx_ancillas(self):
        source = makeMCX(4, dirty=False)
        circuits = {
            "RwUn": uncompute(source, mode=2),
            "Reqomp": quantum_to_ancilla_circuit(source).uncompute(2),
        }

        for tool, circuit in circuits.items():
            controls = circuit.qregs[0]
            target = circuit.qregs[1][0]
            ancillas = circuit.qregs[2]

            for bits in range(16):
                probe = QuantumCircuit(*circuit.qregs)
                for index, qubit in enumerate(controls):
                    if bits & (1 << index):
                        probe.x(qubit)
                probe.compose(circuit, inplace=True)
                state = Statevector.from_instruction(probe)

                for ancilla in ancillas:
                    index = probe.find_bit(ancilla).index
                    self.assertLess(
                        state.probabilities([index])[1],
                        1e-10,
                        f"{tool} did not clean {ancilla} for input {bits}",
                    )

                target_index = probe.find_bit(target).index
                expected = 1.0 if bits == 15 else 0.0
                actual = state.probabilities([target_index])[1]
                self.assertAlmostEqual(actual, expected, places=10)

    def test_dependency_analysis_smoke(self):
        dependency, cycle = dep_cyc(makeMCX(4, dirty=False))
        self.assertIsInstance(dependency, int)
        self.assertIn(cycle, (0, 1))


class EvaluationConfigurationTests(unittest.TestCase):
    def test_quick_profile_uses_small_deterministic_samples(self):
        with tempfile.TemporaryDirectory() as directory, patch(
            "RwUn.evaluation_utils.random_test", return_value={"s1": 1.0}
        ) as random_test:
            evaluate(qfree=True, mode=2, folder=directory, quick=True)

        configs = [item.args[0] for item in random_test.call_args_list]
        self.assertEqual([config.n_gates for config in configs], [50, 100, 150, 200])
        self.assertTrue(all(config.n_circuits == 10 for config in configs))

    def test_quick_and_full_outputs_are_isolated(self):
        module = sys.modules[__name__]
        with patch.object(module, "run_random") as run_random, patch.object(
            module, "plot_random_qfree"
        ) as plot_qfree, patch.object(
            module, "plot_random_nonqfree"
        ) as plot_nonqfree:
            run_random_evaluation(quick=True)

        output = Path("evaluation/quick")
        self.assertEqual(
            run_random.call_args_list,
            [
                call(qfree=True, quick=True, output_folder=output),
                call(qfree=False, quick=True, output_folder=output),
            ],
        )
        plot_qfree.assert_called_once_with(
            source_folder=output, output_folder=output
        )
        plot_nonqfree.assert_called_once_with(
            source_folder=output, output_folder=output
        )


def run_reviewer_check():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ArtifactSmokeTests)
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
        raise SystemExit(1)


def generate_table1():
    dependency_path = run_table1_dependency_complexity()
    table1_path = run_table1()
    merge_table1_results(table1_path, dependency_path)


def run_random_evaluation(quick=False):
    output_folder = Path(evaluation_folder) / ("quick" if quick else "full")
    run_random(qfree=True, quick=quick, output_folder=output_folder)
    plot_random_qfree(source_folder=output_folder, output_folder=output_folder)
    run_random(qfree=False, quick=quick, output_folder=output_folder)
    plot_random_nonqfree(source_folder=output_folder, output_folder=output_folder)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the RwUn evaluation")
    parser.add_argument(
        "mode",
        type=int,
        choices=(0, 1, 2, 3),
        help="0: reviewer check; 1: Table 1; 2: quick run; 3: full run",
    )
    args = parser.parse_args(argv)

    if args.mode == 0:
        run_reviewer_check()
    elif args.mode == 1:
        generate_table1()
    else:
        run_random_evaluation(quick=args.mode == 2)


if __name__ == "__main__":
    main()
