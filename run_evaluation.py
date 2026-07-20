from RwUn.evaluation_utils import evaluate
from RwUn.utils import *
from multiprocessing import Process
from RwUn.evaluation_plot import plot_gatecount_two_curves_panels
from RwUn.examples.mcx import *
from RwUn.examples.adder import *
from RwUn.examples.mcry import *
from RwUn.examples.grover import *
from RwUn.examples.incrementer import *
from RwUn.examples.deutschjozsa import *
from RwUn.examples.intergercomparator import *
from RwUn.dependencygraph import dep_cyc
import os

evaluation_folder = "evaluation"

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

    lines.append("conditionalclean mcs:")
    lines.append(test_conditionalcleanmcs_efficiency(0, 1000, 1001, 10))
    lines.append(test_conditionalcleanmcs_efficiency(1, 1000, 1001, 10))
    lines.append(test_conditionalcleanmcs_efficiency(2, 1000, 1001, 10))
    lines.append(test_conditionalcleanmcs_efficiency(3, 1000, 1001, 10))
    lines.append(test_conditionalcleanmcs_efficiency(4, 10, 41, 10))


    lines.append("conditionaldirty mcs:")
    lines.append(test_conditionaldirtymcs_efficiency(0, 1000, 1001, 10))
    lines.append(test_conditionaldirtymcs_efficiency(1, 1000, 1001, 10))
    lines.append(test_conditionaldirtymcs_efficiency(2, 1000, 1001, 10))
    lines.append(test_conditionaldirtymcs_efficiency(3, 1000, 1001, 10))
    lines.append(test_conditionaldirtymcs_efficiency(4, 10, 41, 10))


    lines.append("riseconditionalclean mcs:")
    lines.append(test_riseconditionalcleanmcs_efficiency(0, 10, 14, 1))
    lines.append(test_riseconditionalcleanmcs_efficiency(1, 10, 14, 1))
    lines.append(test_riseconditionalcleanmcs_efficiency(2, 10, 14, 1))
    lines.append(test_riseconditionalcleanmcs_efficiency(3, 8, 12, 1))
    lines.append(test_riseconditionalcleanmcs_efficiency(4, 900, 970, 10))


    lines.append("riseconditionaldirty mcs:")
    lines.append(test_riseconditionaldirtymcs_efficiency(0, 11, 12, 1))
    lines.append(test_riseconditionaldirtymcs_efficiency(1, 11, 12, 1))
    lines.append(test_riseconditionaldirtymcs_efficiency(2, 11, 12, 1))
    lines.append(test_riseconditionaldirtymcs_efficiency(3, 11, 12, 1))
    lines.append(test_riseconditionaldirtymcs_efficiency(4, 740, 940, 20))


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
    lines.append(test_dirtyadder_efficiency(0, 6, 7, 1))
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





    

def run_random_qfree_quick():
    def run(i: int):
        evaluate(True, i, evaluation_folder, True, quick=True)

    ps = [Process(target=run, args=(i,)) for i in (0, 1, 2)]
    for p in ps: p.start()
    for p in ps: p.join()

def run_random_qfree():
    def run(i: int):
        evaluate(True, i, evaluation_folder, True, quick=False)

    ps = [Process(target=run, args=(i,)) for i in (0, 1, 2)]
    for p in ps: p.start()
    for p in ps: p.join()

def plot_random_qfree():
    folders = [
        evaluation_folder + "/results_qfree/42_5_5",
        evaluation_folder + "/results_qfree/42_40_40",
        evaluation_folder + "/results_qfree/42_200_200",
    ]

    y_builder = lambda d: (d.get("s1", []), d.get("s2", []))
    plot_gatecount_two_curves_panels(
        folders = folders,
        width_labels = ['small', 'medium', 'large'],
        tool_labels = ("RwUn", "Reqomp"),
        out_path = evaluation_folder +"/success_qfree.pdf",
        y_builder = y_builder,
        y_label = "Success Rate"
    )

    
    def y_builder(d, alpha=0.3):
        dep_1 = d.get("dep_1_success", [])
        dep_both = d.get("dep_both_success", [])
        
        y1 = dep_1
        y2 = dep_both
        
        return y1, y2
    plot_gatecount_two_curves_panels(
        folders = folders,
        width_labels = ['small', 'medium', 'large'],
        tool_labels = ("RwUn-only", "Both"),
        out_path = evaluation_folder +"/dep_qfree.pdf",
        y_builder = y_builder,
        y_label = "Aw-Dep",
        share_y=False
    )

    
    def y_builder(d, alpha=0.3):
        s1_cyc = d.get("s1_cyc", [])
        s2_cyc = d.get("s2_cyc", [])

        y1 = s1_cyc
        y2 = s2_cyc
        return y1, y2
    plot_gatecount_two_curves_panels(
        folders = folders,
        width_labels = ['small', 'medium', 'large'],
        tool_labels = ("RwUn", "Reqomp"),
        out_path = evaluation_folder +"/success_cyc_qfree.pdf",
        y_builder = y_builder,
        y_label = "Success Rate (Aw-Cyc)",
        share_y=False
    )

    def y_builder(d, alpha=0.3):
        s1_cyc = d.get("s1_no_cyc", [])
        s2_cyc = d.get("s2_no_cyc", [])

        y1 = s1_cyc
        y2 = s2_cyc
        return y1, y2
    plot_gatecount_two_curves_panels(
        folders = folders,
        width_labels = ['small', 'medium', 'large'],
        tool_labels = ("RwUn", "Reqomp"),
        out_path = evaluation_folder +"/success_no_cyc_qfree.pdf",
        y_builder = y_builder,
        y_label = "Success Rate (No Aw-Cyc)",
        share_y=False
    )

def run_random_nonqfree():
    def run(i: int):
        evaluate(False , i, evaluation_folder)

    ps = [Process(target=run, args=(i,)) for i in (0, 1, 2)]
    for p in ps: p.start()
    for p in ps: p.join()

def plot_random_nonqfree():
    folders = [
        evaluation_folder + "/results_nonqfree/42_5_5",
        evaluation_folder + "/results_nonqfree/42_40_40",
        evaluation_folder + "/results_nonqfree/42_200_200",
    ]
    
    y_builder = lambda d: (d.get("s1", []), d.get("s2", []))
    plot_gatecount_two_curves_panels(
        folders = folders,
        width_labels = ['small', 'medium', 'large'],
        tool_labels = ("RwUn", "Reqomp"),
        out_path = evaluation_folder +"/success_quan.pdf",
        y_builder = y_builder,
        y_label = "Success Rate"
    )

if __name__ == "__main__":
    arg = 0
    if arg == 0:
        run_table1_dependency_complexity()
        run_table1()
        run_random_qfree(quick=True)
        plot_random_qfree()
        run_random_nonqfree(quick=True)
        plot_random_nonqfree()
    elif arg == 2:
        run_table1_dependency_complexity()
        run_table1()
        run_random_qfree(quick=False)
        plot_random_qfree()
        run_random_nonqfree(quick=False)
        plot_random_nonqfree()
    elif arg == 3:
        run_table1_dependency_complexity()
    elif arg == 4:
        run_table1()
    elif arg == 5:
        run_random_qfree(quick=True)
        plot_random_qfree()
        run_random_nonqfree(quick=True)
        plot_random_nonqfree()