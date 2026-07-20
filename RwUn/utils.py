from qiskit.quantum_info import SparsePauliOp, Operator, Statevector, DensityMatrix, partial_trace
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.primitives import Sampler
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, AncillaRegister
from RwUn.uncomp import *
from RwUn.examples.adder import *
from RwUn.examples.mcx import *
from RwUn.examples.incrementer import *
from RwUn.examples.intergercomparator import *
from RwUn.examples.deutschjozsa import *
from RwUn.examples.grover import *
from RwUn.examples.mcry import *
from RwUn.evaluation_utils import quantum_to_ancilla_circuit



# test whether the operator of qc1 can be written as U_n \otimes I_m
def test_dirty(qc1, n, m):
    U = Operator(qc1.reverse_bits()).data
    U = np.array(U)
    dim_u = 2 ** n
    dim_i = 2 ** m

    U_reshaped = U.reshape(dim_u, dim_i, dim_u, dim_i)
    I = np.eye(dim_i)

    is_tensor_product = True

    for i in range(dim_u):
        for j in range(dim_u):
            submatrix = U_reshaped[i, :, j, :]
            if not np.allclose(submatrix, U_reshaped[i, 0, j, 0] * I):
                is_tensor_product = False
                break
        if not is_tensor_product:
            print(f"❌ can not written into U_{n} ⊗ I_{m}")
            return

# test whether C[n, n, n] implements (a, b, anc) -> (a, b + a, anc)
def test_adder(C, n):
    compute_qubits = range(2*n)
    x_qubits = range(n)
    y_qubits = [i + n for i in range(n)]
    
    correct = True
    sampler = Sampler()

    for x in range(2 ** n):
        for y in range(2 ** n):
            test_qc = QuantumCircuit(3*n, 2*n)

            binary_x = f"{x:0{n}b}"[::-1]
            for i, qubit in enumerate(x_qubits):
                if binary_x[i] == '1':
                    test_qc.x(qubit)
            binary_y = f"{y:0{n}b}"[::-1]
            for i, qubit in enumerate(y_qubits):
                if binary_y[i] == '1':
                    test_qc.x(qubit)

            test_qc.compose(C, inplace=True)

            test_qc.measure(compute_qubits, range(2*n))

            job = sampler.run(test_qc)
            result = job.result()
            counts = result.quasi_dists[0]

            expected_y = (x + y) % (2 ** n)
            expected_binary = binary_x + f"{expected_y:0{n}b}"[::-1]

            found_correct = False
            for bitstring, probability in counts.items():
                bitstring_str = f"{bitstring:0{2*n}b}"[::-1]
                if probability > 0:
                    if bitstring_str == expected_binary:
                        found_correct = True

            if not found_correct:
                correct = False
                print(f"wrong！input {x} ({binary_x}) and {y} ({binary_y})，doesn't get expected: {expected_y} ({expected_binary})")
                return

    # if correct:
    #     print("correctly implements (a, b+a)")

# test whether C[n, n-1] implements (a, anc) -> (a', anc) where highest bit of a' is a + const
def test_highest_bit_adder(C, n, value):
    compute_qubits = range(n)
    x_qubits = range(n)
    dirty_qubits = [i + n for i in range(n-1)]
    
    correct = True
    sampler = Sampler()

    for x in range(2 ** n):
        test_qc = QuantumCircuit(n + n - 1, n)

        binary_x = f"{x:0{n}b}"[::-1]
        for i, qubit in enumerate(x_qubits):
            if binary_x[i] == '1':
                test_qc.x(qubit)
        binary_y = f"{value:0{n}b}"[::-1]

        test_qc.compose(C, inplace=True)

        test_qc.measure(x_qubits, range(n))

        job = sampler.run(test_qc)
        result = job.result()
        counts = result.quasi_dists[0]

        expected_result = (x + value) % (2 ** n)
        highest_bit = str((expected_result >> (n - 1)) & 1)
        expected_binary = binary_x[:-1] + highest_bit

        found_correct = False
        for bitstring, probability in counts.items():
            bitstring_str = f"{bitstring:0{n}b}"[::-1]
            if probability > 0:
                # print(f"input {x} ({binary_x}) and {value} ({binary_y}) -> actual ouput {bitstring_str}，prob：{probability}")

                if bitstring_str == expected_binary:
                    found_correct = True

        if not found_correct:
            correct = False
            print(f"wrong！input {x} ({binary_x}) and {value} ({binary_y}) ，doesn't get the expected ({expected_binary})")
            return

    # if correct:
    #     print("correctly implements (a, b+a)")

# test whether C:[n, 1, n] implements (x, c) -> (c, 1 if x >= value else 0)
def test_comparator(C, n, value, dirty=False):
    x_qubits = range(n)
    c_qubit = n
    sampler = Sampler()

    correct = True
    for x in range(2 ** n):
        if not dirty:
            test_qc = QuantumCircuit(n + 1 + (n - 1), 1)
        else:
            test_qc = QuantumCircuit(n + 1 + n, 1)

        binary_x = f"{x:0{n}b}"[::-1]
        for i, qubit in enumerate(x_qubits):
                if binary_x[i] == '1':
                    test_qc.x(qubit)
        test_qc.compose(C, inplace=True)
        test_qc.measure(c_qubit, 0)

        job = sampler.run(test_qc)
        result = job.result()
        counts = result.quasi_dists[0]
        
        expected_c = "1" if x >= value else "0"
        for bit, probability in counts.items():
                bit_str = f"{bit}"
                if probability > 0:
                    # print(f"input {x} ({binary_x}) and {y} ({binary_y}) -> actual {bitstring_str}，prob：{probability}")

                    if bit_str != expected_c:
                        correct = False
                        print(f"wrong! input {x} ({binary_x}) -> actual output {bit_str}, expected {expected_c}")
    
    if correct:
        pass
        # print("C correctly implements the comparator for value", value)


def test_mcx(C, n):
    control_qubits = range(n)
    target_qubit = n
    
    with_a = True if n > 2 else False
    correct = True

    for x in range(2 ** n):
        for y in range(2):
            if with_a:
                test_qc = QuantumCircuit(n + 1 + n - 2, 1)
            else:
                test_qc = QuantumCircuit(n + 1, 1)
            
            binary_x = f"{x:0{n}b}"[::-1]        
            for i, qubit in enumerate(control_qubits):
                if binary_x[i] == '1':
                    test_qc.x(qubit)
            if y == 1:
                test_qc.x(target_qubit)
            
            test_qc.compose(C, inplace=True)
            
            sv = Statevector.from_label("0" * test_qc.num_qubits)
            final_sv = sv.evolve(test_qc)
            probs = final_sv.probabilities_dict()
            
            if y == 0:
                expected_y = 1 if x == 2 ** n - 1 else 0
            else:
                expected_y = 0 if x == 2 ** n - 1 else 1

            for bitstring, prob in probs.items():
                if prob > 1e-12:
                    measured_y = int(bitstring[::-1][target_qubit])
                    if measured_y != expected_y:
                        correct = False
                        print(f"wrong! input x: {x} ({binary_x}) y: {y} -> "
                              f"actual output target={measured_y}, expected {expected_y}, prob: {prob}")

    # if correct:
    #     print("C correctly implements the mcx circuit for n =", n)


def test_inc(C, n):
    assert n > 0, "n must be greater than 0 for incrementer circuit"

    x_qubits = range(n)

    with_a = True if n > 2 else False
    sampler = Sampler()
    correct = True

    for x in range(2 ** n):
        if with_a:
            test_qc = QuantumCircuit(n + n - 2, n)
        else:
            test_qc = QuantumCircuit(n, n)
        binary_x = f"{x:0{n}b}"[::-1]        
        for i, qubit in enumerate(x_qubits):
            if binary_x[i] == '1':
                test_qc.x(qubit)
        test_qc.compose(C, inplace=True)
        test_qc.measure(x_qubits, range(n))

        job = sampler.run(test_qc)
        result = job.result()
        counts = result.quasi_dists[0]

        expected_x = (x + 1) % (2 ** n)
        expected_binary = f"{expected_x:0{n}b}"[::-1]
        correct = True
        for bits, probability in counts.items():
                bits_str = f"{bits:0{n}b}"[::-1]
                if probability > 0:
                    # print(f"input {x} ({binary_x}) and {y} ({binary_y}) -> actual {bitstring_str}，prob：{probability}")

                    if bits_str != expected_binary:
                        correct = False
                        print(f"wrong! input {x} ({binary_x}) -> actual output {bits_str}, expected {expected_binary}")
    
    if correct:
        print("C correctly implements the incrementer circuit for n =", n)

def test_adder_functionality(uncomputation=False, mode=0):
    for i in range(1, 5, 1):
        adder = makesAdder(i)
        if uncomputation:
            adder = uncompute(adder, mode)
            if mode == 3 or mode == 4:
                if i < 4:
                    test_dirty(adder, 2*i, i)
        test_adder(adder, i)



def test_dirtyadder_functionality(uncomputation=False, mode=0):
    for i in range(1, 5, 1):
        adder = makesDirtyAdder(i)
        if uncomputation:
            adder = uncompute(adder, mode)
            if mode == 3 or mode == 4:
                if i < 4:
                    test_dirty(adder, 2*i, i-1)
        test_adder(adder, i)



def test_hbadder_functionality(uncomputation=False, mode=0):
    for i in range(1, 6, 1):
        for v in range(2 ** i):
            adder = makesDirtyHighestBitConstAdder(i, v)
            if uncomputation:
                adder = uncompute(adder, mode)
                if 2 < i and i < 5:
                    test_dirty(adder, i, i-1)
            test_highest_bit_adder(adder, i, v)



def test_cleanmcx_functionality(uncomputation=False, mode=0):
    for i in range(1, 7, 1):
        C = makeMCX(i, dirty=False)
        if uncomputation:
            C = uncompute(C, mode)
            if mode == 3 or mode == 4:
                if i < 5 and i > 2:
                    test_dirty(C, i+1, i-2)
        test_mcx(C, i)

def test_dirtymcx_functionality(uncomputation=False, mode=0):
    for i in range(1, 7, 1):
        C = makeMCX(i, dirty=True)
        if uncomputation:
            C = uncompute(C, mode)
            if mode == 3 or mode == 4:
                if i < 5 and i > 2:
                    test_dirty(C, i+1, i-2)
        test_mcx(C, i)

def test_conditionalcleanmcx_functionality(uncomputation=False, mode=0):
    for i in range(6, 7, 1):
        C = makeConditionalMCX(i, dirty=False)
        if uncomputation:
            C = uncompute(C, mode)
            # if mode == 3 or mode == 4:
            #     if i < 5 and i > 2:
            #         test_dirty(C, i+1, i-2)
        test_mcx(C, i)

def test_conditionaldirtymcx_functionality(uncomputation=False, mode=0):
    for i in range(6, 7, 1):
        C = makeConditionalMCX(i, dirty=True)
        if uncomputation:
            C = uncompute(C, mode)
            # if mode == 3 or mode == 4:
            #     if i < 5 and i > 2:
            #         test_dirty(C, i+1, i-2)
        test_mcx(C, i)

def test_riseconditionalcleanmcx_functionality(uncomputation=False, mode=0):
    for i in range(6, 7, 1):
        C = makeRiseConditionalMCX(i, dirty=False)
        if uncomputation:
            C = uncompute(C, mode)
            # if mode == 3 or mode == 4:
            #     if i < 5 and i > 2:
            #         test_dirty(C, i+1, i-2)
        test_mcx(C, i)

def test_riseconditionaldirtymcx_functionality(uncomputation=False, mode=0):
    for i in range(6, 7, 1):
        C = makeRiseConditionalMCX(i, dirty=True)
        if uncomputation:
            C = uncompute(C, mode)
            # if mode == 3 or mode == 4:
            #     if i < 5 and i > 2:
            #         test_dirty(C, i+1, i-2)
        test_mcx(C, i)

def test_cleancomparator_functionality(uncomputation=False, mode=0):
    for n in range(2, 5):
        for v in range(-1, 2 ** n + 1):
            C = makeIntegerComparator(n, v, True, False)
            if uncomputation:
                C = uncompute(C, mode)
                # if mode == 3 or mode == 4:
                #     test_dirty(C, n + 1, n)
            test_comparator(C, n, v, False)
            
def test_dirtycomparator_functionality(uncomputation=False, mode=0):
    for n in range(2, 5):
        for v in range(-1, 2 ** n + 1):
            C = makeIntegerComparator(n, v, True, True)
            if uncomputation:
                C = uncompute(C, mode)
                if mode == 3 or mode == 4:
                    test_dirty(C, n + 1, n)
            test_comparator(C, n, v, True)
# ========================================================
def alt10(n: int) -> int:
    if n <= 0:
        return 0
    x = 0
    for i in range(n):
        x = (x << 1) | (1 if i % 2 == 1 else 0)
    return x


def _run_efficiency_test(builder, mode=0, begin=1, end=2, step=1, limit=30):
    print(f"test efficiency: mode = {mode}")

    max_n_in_30s = None
    time_for_n = None
    size = 0
    depth = 0
    star = ""
    try:
        for n in range(begin, end, step):
            C = builder(n)
            s = C.size()
            d = C.depth()
            if mode == 4:
                C = quantum_to_ancilla_circuit(C)
                ancs = C._nb_ancillas
            start_time = time()
            if mode == 4:
                C.uncompute(ancs)
            else:
                uncompute(C, mode)
            elapsed = time() - start_time

            print(f"n = {n} {elapsed}s")

            if elapsed > limit:
                break

            max_n_in_30s = n
            time_for_n = elapsed
            size = s
            depth = d
    except RecursionError as e:
        star = "*"
        print(e)
    except AssertionError as e:
        print(e)
    return f"{mode}, {max_n_in_30s}{star}, {time_for_n}, {size}, {depth}"


def test_adder_efficiency(mode=0, begin=1, end=2, step=1):
    return _run_efficiency_test(
        lambda n: makesAdder(n),
        mode=mode, begin=begin, end=end, step=step
    )


def test_dirtyadder_efficiency(mode=0, begin=1, end=2, step=1):
    return _run_efficiency_test(
        lambda n: makesDirtyAdder(n),
        mode=mode, begin=begin, end=end, step=step
    )


def test_hbadder_efficiency(mode=0, begin=1, end=2, step=1):
    return _run_efficiency_test(
        lambda n: makesDirtyHighestBitConstAdder(n, 2 ** n - 1),
        mode=mode, begin=begin, end=end, step=step
    )


def test_mcx_efficiency(mode=0, begin=1, end=2, step=1):
    return _run_efficiency_test(
        lambda n: makeMCX(n, False),
        mode=mode, begin=begin, end=end, step=step
    )


def test_dirtymcx_efficiency(mode=0, begin=1, end=2, step=1):
    return _run_efficiency_test(
        lambda n: makeMCX(n, True),
        mode=mode, begin=begin, end=end, step=step
    )


def test_conditionalcleanmcx_efficiency(mode=0, begin=1, end=2, step=1):
    return _run_efficiency_test(
        lambda n: makeConditionalMCX(n, False),
        mode=mode, begin=begin, end=end, step=step
    )


def test_conditionaldirtymcx_efficiency(mode=0, begin=1, end=2, step=1):
    return _run_efficiency_test(
        lambda n: makeConditionalMCX(n, True),
        mode=mode, begin=begin, end=end, step=step
    )


def test_riseconditionalcleanmcx_efficiency(mode=0, begin=1, end=2, step=1):
    return _run_efficiency_test(
        lambda n: makeRiseConditionalMCX(n, False),
        mode=mode, begin=begin, end=end, step=step
    )


def test_riseconditionaldirtymcx_efficiency(mode=0, begin=1, end=2, step=1):
    return _run_efficiency_test(
        lambda n: makeRiseConditionalMCX(n, True),
        mode=mode, begin=begin, end=end, step=step
    )


def test_cleancomparator_efficiency(mode=0, begin=1, end=1, step=1):
    return _run_efficiency_test(
        lambda n: makeIntegerComparator(n, alt10(n), True, False),
        mode=mode, begin=begin, end=end, step=step
    )


def test_dirtycomparator_efficiency(mode=0, begin=1, end=1, step=1):
    return _run_efficiency_test(
        lambda n: makeIntegerComparator(n, alt10(n), True, True),
        mode=mode, begin=begin, end=end, step=step
    )


def test_incrementer_efficiency(mode=0, begin=1, end=1, step=1):
    return _run_efficiency_test(
        lambda n: makesIncrementer(n, False),
        mode=mode, begin=begin, end=end, step=step
    )


def test_dirtyincrementer_efficiency(mode=0, begin=1, end=1, step=1):
    return _run_efficiency_test(
        lambda n: makesIncrementer(n, True),
        mode=mode, begin=begin, end=end, step=step
    )


def test_gidneydirtyincrementer_efficiency(mode=0, begin=1, end=1, step=1):
    return _run_efficiency_test(
        lambda n: makesDirtyIncrementer(n),
        mode=mode, begin=begin, end=end, step=step
    )


def test_DJ_efficiency(mode=0, begin=1, end=1, step=1):
    return _run_efficiency_test(
        lambda n: makesDJ(n),
        mode=mode, begin=begin, end=end, step=step
    )


def test_grover_efficiency(mode=0, begin=1, end=1, step=1):
    return _run_efficiency_test(
        lambda n: makesGroverCircuit(n),
        mode=mode, begin=begin, end=end, step=step
    )


def test_mcry_efficiency(mode=0, begin=1, end=1, step=1):
    return _run_efficiency_test(
        lambda n: makeMCRY(n),
        mode=mode, begin=begin, end=end, step=step
    )

def test_efficiency(test_f_efficiency):
    test_f_efficiency(0)
    test_f_efficiency(1)
    test_f_efficiency(2)
    test_f_efficiency(3)
    test_f_efficiency(4)


def test_functionality(test_f_functionality):
    # test without uncomputation functionality
    test_f_functionality(False)
    
    # uncomputation with clean version
    test_f_functionality(True, 0)
    test_f_functionality(True, 1)
    test_f_functionality(True, 2)

    # uncomputation with dirty version
    test_f_functionality(True, 3)
    test_f_functionality(True, 4)






