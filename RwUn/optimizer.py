# from qiskit.circuit import QuantumCircuit, Instruction
# from uncomputability import *

# def is_same_gate(op1, op2):
#     g1, q1, _ = op1
#     g2, q2, _ = op2
#     return g1.name == g2.name and q1 == q2

# def get_control_and_target(op):
#     gate, qargs, _ = op
#     if gate.name == "x" or gate.name == "id":
#         return set(), qargs[0]
#     elif gate.name == "cx":
#         return {qargs[0]}, qargs[1]
#     elif gate.name == "ccx":
#         return {qargs[0], qargs[1]}, qargs[2]
#     elif gate.name == "mcx":
#         return set(qargs[:-1]), qargs[-1]
#     else:
#         raise ValueError(f"Unsupported gate: {gate.name}")

# def can_commute(op1, op2):
#     ctrl1, tgt1 = get_control_and_target(op1)
#     ctrl2, tgt2 = get_control_and_target(op2)
#     return tgt1 not in ctrl2 and tgt2 not in ctrl1


# def k_local_commute_optimize1(C: QuantumCircuit) -> QuantumCircuit:
#     canceled = [0] * len(C.data)
#     for i in range(len(C.data)):
#         for j in range(i-1, -1, -1):
#             if canceled[j]:
#                 continue
#             if not can_commute(C.data[i], C.data[j]):
#                 break
#             if is_same_gate(C.data[i], C.data[j]):
#                 canceled[i], canceled[j] = 1, 1
#                 break

#     new_circuit = QuantumCircuit(*C.qregs, *C.cregs)
#     i = 0
#     for gate, qargs, cargs in C.data:
#         if not canceled[i]:
#             new_circuit.append(gate, qargs, cargs)
#         i += 1
#     return new_circuit

# def k_local_commute_optimize2(data_list: list):
#     canceled = [0] * len(data_list)
#     now = data_list.first
#     for i in range(len(data_list)):
#         prev = now.prev
#         for j in range(i-1, -1, -1):
#             if canceled[j]:
#                 pass
#             elif not can_commute(now.value, prev.value):
#                 break
#             elif is_same_gate(now.value, prev.value):
#                 canceled[i], canceled[j] = 1, 1
#                 break
#             prev = prev.prev
#         now = now.next

#     head = data_list.first
#     for i in range(len(canceled)):
#         next_ = head.next
#         if canceled[i]:
#             data_list.remove(head)
#         head = next_


from qiskit.circuit import QuantumCircuit, Instruction
from .uncomputability import *

X_FAMILY = {"x", "cx", "ccx", "mcx"}
PHASE_FAMILY = {"z", "s", "sdg", "t", "tdg"}
H_FAMILY = {"h"}
ALLOWED_GATES = X_FAMILY | PHASE_FAMILY | H_FAMILY


def cancel_each_other(op1, op2):
    g1, q1, _ = op1
    g2, q2, _ = op2

    if q1 != q2:
        return False

    if g1.name in ['x', 'cx', 'ccx', 'mcx', 'h', 'z'] and g2.name in ['x', 'cx', 'ccx', 'mcx', 'h', 'z']:
        return g1.name == g2.name

    return (
        (g1.name == 's' and g2.name == 'sdg') or
        (g1.name == 'sdg' and g2.name == 's') or
        (g1.name == 't' and g2.name == 'tdg') or
        (g1.name == 'tdg' and g2.name == 't')
    )


def get_control_and_target(op):
    gate, qargs, _ = op

    if gate.name not in ALLOWED_GATES:
        raise ValueError(f"Unsupported gate: {gate.name}")

    if gate.name in {"x", "h", "z", "s", "sdg", "t", "tdg"}:
        return set(), qargs[0]

    return set(qargs[:-1]), qargs[-1]


def can_commute(op1, op2):
    """
    Conservative commutation checker.
    Return True only when we are sure op1 and op2 commute.
    """
    gate1, qargs1, _ = op1
    gate2, qargs2, _ = op2

    g1 = gate1.name
    g2 = gate2.name

    if g1 not in ALLOWED_GATES:
        raise ValueError(f"Unsupported gate in op1: {g1}")
    if g2 not in ALLOWED_GATES:
        raise ValueError(f"Unsupported gate in op2: {g2}")

    qs1 = set(qargs1)
    qs2 = set(qargs2)

    # 1. disjoint support => always commute
    if qs1.isdisjoint(qs2):
        return True

    c1, t1 = get_control_and_target(op1)
    c2, t2 = get_control_and_target(op2)

    # 2. both phase gates => always commute
    if g1 in PHASE_FAMILY and g2 in PHASE_FAMILY:
        return True

    # 3. both X-family gates
    if g1 in X_FAMILY and g2 in X_FAMILY:
        return (t1 not in c2) and (t2 not in c1)

    # 4. phase vs X-family
    if g1 in PHASE_FAMILY and g2 in X_FAMILY:
        # phase gate acts on its target t1 only
        return t1 in c2

    if g1 in X_FAMILY and g2 in PHASE_FAMILY:
        return t2 in c1

    # 5. H cases: only handle the obviously safe ones
    if g1 == "h" and g2 == "h":
        # same qubit or disjoint; disjoint case already handled above
        return t1 == t2

    # H with anything else on overlapping qubits: conservatively say no
    return False

def k_local_commute_optimize1(C: QuantumCircuit) -> QuantumCircuit:
    canceled = [0] * len(C.data)
    for i in range(len(C.data)):
        if canceled[i]:
            continue
        op_i = C.data[i]
        for j in range(i - 1, -1, -1):
            if canceled[j]:
                continue
            op_j = C.data[j]

            if not can_commute(op_i, op_j):
                break
            if cancel_each_other(op_i, op_j):
                canceled[i] = 1
                canceled[j] = 1
                break

    new_circuit = QuantumCircuit(*C.qregs, *C.cregs)
    for i, (gate, qargs, cargs) in enumerate(C.data):
        if not canceled[i]:
            new_circuit.append(gate, qargs, cargs)

    return new_circuit

def k_local_commute_optimize2(data_list):
    n = len(data_list)
    canceled = [False] * n

    now = data_list.first
    for i in range(n):
        if canceled[i]:
            now = now.next
            continue

        op_i = now.value
        prev = now.prev

        for j in range(i - 1, -1, -1):
            if prev is None:
                break

            op_j = prev.value

            if not canceled[j]:
                if not can_commute(op_i, op_j):
                    break

                if cancel_each_other(op_i, op_j):
                    canceled[i] = True
                    canceled[j] = True
                    break

            prev = prev.prev

        now = now.next

    head = data_list.first
    for i in range(n):
        next_ = head.next
        if canceled[i]:
            data_list.remove(head)
        head = next_
