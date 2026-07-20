import random
from qiskit.circuit import QuantumRegister, QuantumCircuit, AncillaRegister, ClassicalRegister
from reqomp.ancilla_circuit import AncillaCircuit, AncillaGate
from RwUn.uncomp import *
from RwUn.uncomputability import is_clean_uncomputable
from time import *
import random
from dataclasses import dataclass
from typing import List
import os
import json
import matplotlib.pyplot as plt
import qiskit.qpy as qpy
from RwUn.dependencygraph import *

def quantum_to_ancilla_circuit(qc: QuantumCircuit) -> AncillaCircuit:
    regs = []
    for reg in qc.qregs + qc.cregs:
        regs.append(reg)
    ac = AncillaCircuit(*regs, name=qc.name)

    for instr, qargs, cargs in qc.data:
        ac.append(instr, qargs, cargs)

    return ac

def save_with_qpy(QC: List[QuantumCircuit], filename: str, n_data: int, n_ancilla: int):
    QC_ = []
    for qc in QC:
        qreg = QuantumRegister(n_data, "q")
        areg = QuantumRegister(n_ancilla, "anc")
        new_qc = QuantumCircuit(qreg, areg)

        mapping = {}
        for i in range(n_data):
            mapping[qc.qubits[i]] = qreg[i]
        for i in range(n_ancilla):
            mapping[qc.qubits[n_data + i]] = areg[i]

        for instr, qargs, cargs in qc.data:
            new_qc.append(instr, [mapping[q] for q in qargs], cargs)

        QC_.append(new_qc)

    with open(filename, "wb") as f:
        qpy.dump(QC_, f)

def load_with_registers(filename: str, n_data: int, n_ancilla: int) -> QuantumCircuit:
    with open(filename, "rb") as f:
        loaded_circuits = qpy.load(f)

    QC = []
    for qc in loaded_circuits:
        qreg = QuantumRegister(n_data, "q")
        areg = AncillaRegister(n_ancilla, "anc")
        new_qc = QuantumCircuit(qreg, areg)

        mapping = {qc.qubits[i]: (qreg[i] if i < n_data else areg[i - n_data])
                for i in range(n_data + n_ancilla)}

        for instr, qargs, cargs in qc.data:
            new_qc.append(instr, [mapping[q] for q in qargs], cargs)
        QC.append(new_qc)

    return QC

ALLOWED_QFREE = ["x", "cx", "ccx"]
ALLOWED_GATES = ["x", "cx", "ccx", "z", "h", "s", "t"]

def random_circuit(rng, n_qubits, n_ancillas, n_gates, qfree):
    n_bits = n_qubits + n_ancillas
    qreg = QuantumRegister(n_qubits, "q")
    areg = AncillaRegister(n_ancillas, "a")
    def target_at(index):
        return qreg[index] if index < n_qubits else areg[index - n_qubits]
    qc1 = QuantumCircuit(qreg, areg)
    qc2 = AncillaCircuit(qreg, areg)

    for _ in range(n_gates):
        if qfree:
            gate_type = rng.choice(list(ALLOWED_QFREE))
        else:
            gate_type = rng.choice(list(ALLOWED_GATES))

        if gate_type in {"x", "z", "h", "s", "t"}:
            if gate_type == "h":
                q = rng.randrange(n_qubits)
            else:
                q = rng.randrange(n_bits)
            if gate_type == "x":
                qc1.x(target_at(q))
                qc2.x(target_at(q))
            if gate_type == "z":
                qc1.z(target_at(q))
                qc2.z(target_at(q))
            if gate_type == "h":
                qc1.h(target_at(q))
                qc2.h(target_at(q))
            if gate_type == "s":
                qc1.s(target_at(q))
                qc2.s(target_at(q))
            if gate_type == "t":
                qc1.t(target_at(q))
                qc2.t(target_at(q))

        elif gate_type == "cx":
            control, target = rng.sample(range(n_bits), 2)
            qc1.cx(target_at(control), target_at(target))
            qc2.cx(target_at(control), target_at(target))

        elif gate_type == "ccx":
            controls = rng.sample(range(n_bits), 3)
            qc1.ccx(target_at(controls[0]), target_at(controls[1]), target_at(controls[2]))
            qc2.ccx(target_at(controls[0]), target_at(controls[1]), target_at(controls[2]))

    return qc1, qc2



@dataclass
class ExperimentConfig:
    seed: int
    n_qubits: int
    n_ancillas: int
    n_gates: int
    n_circuits: int
    folder: str

    def unpack(self):
        return (self.seed, self.n_qubits, self.n_ancillas, self.n_gates, self.n_circuits, self.folder)


def random_circuit_batch(config: ExperimentConfig, qfree, all_uncomputable=True):
    seed, n_qubs, n_ancs, n_gates, n_circs, _ = config.unpack()
    rng = random.Random(seed)

    folder = config.folder + "/examples_" + ("nonqfree" if not qfree else "qfree") + "/" + f"{seed}_{n_qubs}_{n_ancs}/"
    os.makedirs(folder, exist_ok=True)

    filename = os.path.join(folder, f"{seed}_{n_qubs}_{n_ancs}_{n_gates}_{n_circs}.qpy")

    if os.path.exists(filename):
        circuits = load_with_registers(filename, n_qubs, n_ancs)
        QC1 = circuits
        QC2 = [quantum_to_ancilla_circuit(C) for C in QC1]
        return QC1, QC2

    QC1, QC2 = [], []
    for i in range(n_circs):
        if all_uncomputable and qfree:
            while True:
                qc1, qc2 = random_circuit(rng, n_qubs, n_ancs, n_gates, qfree)
                if is_clean_uncomputable(qc1, qc1.qregs[1]):
                    break
        else:
            qc1, qc2 = random_circuit(rng, n_qubs, n_ancs, n_gates, qfree)
        QC1.append(qc1)
        QC2.append(qc2)

    save_with_qpy(QC1, filename, n_qubs, n_ancs)
    print('saved to:' + filename)

    return QC1, QC2



def random_test(config: ExperimentConfig, qfree, all_uncomputable=True):
    QC1, QC2 = random_circuit_batch(config, qfree, all_uncomputable)
    
    dependency = 0
    cycle = 0

    s_qc1 = 0
    s_qc2 = 0
    t_qc1 = 0
    t_qc2 = 0
    n_qc1_success = 0
    n_qc2_success = 0

    s_only_qc1 = 0
    s_only_qc2 = 0

    cnt_both_success = 0
    dep_both_success = 0
    dep_only_1_success = 0
    cyc_both_success = 0
    cyc_only_1_success = 0

    s_qc1_no_cyc = 0
    s_qc2_no_cyc = 0
    s_qc1_cyc = 0
    s_qc2_cyc = 0

    for i in range(len(QC1)):
        qc1_success, qc2_success = False, False
        qc1, qc2 = QC1[i], QC2[i]

        # Analyze dependencies
        dep_max, cyc = dep_cyc(qc1)
        dependency += dep_max
        cycle += cyc

        # test uncomputation
        s = time()
        try:
            if qfree:
                uncompAll(qc1, all=True)
            else:
                uncompAll0(qc1)
                
            e = time()
            t_qc1 += e - s
            n_qc1_success += 1
            qc1_success = True
        except Exception as e:
            pass
        e = time()
        t_qc1 += e - s

        s = time()
        try:
            qc2.uncompute(config.n_ancillas)
            e = time()
            t_qc2 += e - s
            n_qc2_success += 1
            qc2_success = True
        except Exception as e:
            pass
        e = time()
        t_qc2 += e - s

        if qc1_success and not qc2_success:
            s_only_qc1 += 1
            dep_only_1_success += dep_max
            cyc_only_1_success += cyc
        elif not qc1_success and qc2_success:
            s_only_qc2 += 1
        
        if qc1_success and qc2_success:
            cnt_both_success += 1
            dep_both_success += dep_max
            cyc_both_success += cyc
        
        if not cyc:
            if qc1_success:
                s_qc1_no_cyc += 1
            if qc2_success:
                s_qc2_no_cyc += 1
        
        if cyc:
            if qc1_success:
                s_qc1_cyc += 1
            if qc2_success:
                s_qc2_cyc += 1
    
    dependency_avg = 1.0 * dependency / len(QC1)
    cycle_avg = 1.0 * cycle / len(QC1)
    # cycle_avg = cycle

    s_qc1 = 1.0 * n_qc1_success / len(QC1)
    s_qc2 = 1.0 * n_qc2_success / len(QC2)
    t_qc1 = 1.0 * t_qc1 / n_qc1_success if n_qc1_success > 0 else 0
    t_qc2 = 1.0 * t_qc2 / n_qc2_success if n_qc2_success > 0 else 0

    dep_both_success = 1.0 * dep_both_success / cnt_both_success if cnt_both_success > 0 else 0
    dep_only_1_success = 1.0 * dep_only_1_success / s_only_qc1 if s_only_qc1 > 0 else 0
    cyc_both_success = 1.0 * cyc_both_success / cnt_both_success if cnt_both_success > 0 else 0
    cyc_only_1_success = 1.0 * cyc_only_1_success / s_only_qc1 if s_only_qc1 > 0 else 0

    s_qc1_no_cyc = 1.0 * s_qc1_no_cyc / (len(QC1) - cycle) if (len(QC1) - cycle) > 0 else 0
    s_qc2_no_cyc = 1.0 * s_qc2_no_cyc / (len(QC1) - cycle) if (len(QC1) - cycle) > 0 else 0
    s_qc1_cyc = 1.0 * s_qc1_cyc / cycle if cycle > 0 else 0
    s_qc2_cyc = 1.0 * s_qc2_cyc / cycle if cycle > 0 else 0



    return {
        "s1": s_qc1,
        "s2": s_qc2,
        "t1": t_qc1,
        "t2": t_qc2,
        "dep": dependency_avg,
        "cyc": cycle_avg,
        "s1_only": s_only_qc1,
        "s2_only": s_only_qc2,
        "dep_both_success": dep_both_success,
        "cyc_both_success": cyc_both_success,
        "dep_1_success": dep_only_1_success,
        "cyc_1_success": cyc_only_1_success,
        "s1_no_cyc": s_qc1_no_cyc,
        "s2_no_cyc": s_qc2_no_cyc,
        "s1_cyc": s_qc1_cyc,
        "s2_cyc": s_qc2_cyc
    }


def evaluate(qfree, mode=0, folder="evaluation", all_uncomputable=True, quick=False):
    n_circs = 100

    # 10 width and 5~60 gates
    if mode == 0:
        n_qubs, n_ancs = 5, 5
        begin, end, step = 5, 56, 5
        if quick:
            end = 50
    # 80 width and 50~200 gates
    elif mode == 1:
        n_qubs, n_ancs = 40, 40
        begin, end, step = 50, 141, 10
        if quick:
            end = 101
    # 400 width and 50~200 gates
    elif mode == 2:
        n_qubs, n_ancs = 200, 200
        begin, end, step = 50, 501, 50    
        if quick:
            end = 101
    else:
        pass

    
    for n_gates in range(begin, end, step):
        config = ExperimentConfig(42, n_qubs, n_ancs, n_gates, n_circs, folder)

        results = random_test(config, qfree, all_uncomputable)

        payload = {
            "config": config.__dict__,
            "results": results,
        }
        
        import json
        result_folder = config.folder + "/results_" + ("nonqfree" if not qfree else "qfree") + "/" + f"{config.seed}_{n_qubs}_{n_ancs}"
        os.makedirs(result_folder, exist_ok=True)
        result_filename = os.path.join(result_folder, f"{config.seed}_{n_qubs}_{n_ancs}_{n_gates}_{n_circs}")

        with open(result_filename, "w") as f:
            json.dump(payload, f, indent=2)


def plot_results(folder):
    gate_counts = []
    my_success_rates = []
    other_success_rates = []
    my_times = []
    other_times = []

    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if not os.path.isfile(filepath):
            continue
        
        with open(filepath, "r") as f:
            data = json.load(f)
            config = data["config"]
            results = data["results"]
            
            gate_counts.append(config["n_gates"])
            my_success_rates.append(results[0])
            other_success_rates.append(results[1])
            my_times.append(results[2])
            other_times.append(results[3])

    sorted_data = sorted(zip(gate_counts, my_success_rates, other_success_rates, my_times, other_times))

    gate_counts, my_success_rates, other_success_rates, my_times, other_times = zip(*sorted_data)

    plt.figure(figsize=(8, 5))
    plt.plot(gate_counts, my_success_rates, marker="o", label="My Success Rate")
    plt.plot(gate_counts, other_success_rates, marker="s", label="Other Success Rate")
    plt.xlabel("Gate Count")
    plt.ylabel("Success Rate")
    plt.title("Success Rate vs Gate Count")
    plt.legend()
    plt.grid(True)
    plt.show()

    plt.figure(figsize=(8, 5))
    plt.plot(gate_counts, my_times, marker="o", label="My Time")
    plt.plot(gate_counts, other_times, marker="s", label="Other Time")
    plt.xlabel("Gate Count")
    plt.ylabel("Time (s)")
    plt.title("Time vs Gate Count")
    plt.legend()
    plt.grid(True)
    plt.show()
            