from qiskit.circuit import QuantumRegister, QuantumCircuit, AncillaRegister, Instruction, AncillaQubit, Qubit
from qiskit.circuit.library.standard_gates import HGate, XGate, ZGate, SGate, SdgGate, TGate, TdgGate
from qiskit.circuit.library import MCXGate
from .uncomputability import *
from .optimizer import *
from llist import dllist, dllistnode
from time import *
import heapq
from collections import defaultdict

ALLOWED_GATES = ["x", "h", "z", "s", "sdg", "t", "tdg", "cx", "ccx", "mcx"]
ALLOWED_ANCILLA = ["x", "z", "s", "sdg", "t", "tdg", "cx", "ccx", "mcx"]
ALLOWED_QFREE = ["x", "cx", "ccx", "mcx"]
ALLOWED_PHASE = ["z", "s", "sdg", "t", "tdg"]

def is_allowed_instruction(g : Instruction) -> bool:
    if g.name in ALLOWED_GATES:
        return True
    elif g.definition is not None:
        return all(is_allowed_instruction(op[0]) for op in g.definition.data)
    else:
        assert False, f"not allowed gate: {g.name}"

def flatten_instruction(instr: Instruction, qargs, clargs):
    if instr.name in ALLOWED_GATES:
        return [(instr, qargs, clargs)]
    elif instr.definition is not None:
        flat_ops = []
        for sub_instr, sub_qargs, sub_clargs in instr.definition.data:
            mapped_qargs = [qargs[q.index] for q in sub_qargs]
            mapped_clargs = [clargs[c.index] for c in sub_clargs]
            flat_ops.extend(flatten_instruction(sub_instr, mapped_qargs, mapped_clargs))
        return flat_ops
    else:
        raise ValueError(f"Unsupported instruction: {instr.name}")

def flatten_if_allowed(circuit: QuantumCircuit) -> QuantumCircuit:
    if not all(is_allowed_instruction(op[0]) for op in circuit.data):
        raise ValueError("Circuit is not qfree.")

    flat_circuit = QuantumCircuit(*circuit.qregs, *circuit.cregs, name=circuit.name + "_flat")

    for instr, qargs, clargs in circuit.data:
        ops = flatten_instruction(instr, qargs, clargs)
        for g, q, c in ops:
            flat_circuit.append(g, q, c)

    return flat_circuit

def is_qfree_circuit(circuit: QuantumCircuit) -> bool:
    def is_allowed_qfree(g : Instruction) -> bool:
        if g.name in ALLOWED_QFREE:
            return True
        elif g.definition is not None:
            return all(is_allowed_qfree(op[0]) for op in g.definition.data)
    return all(is_allowed_qfree(op[0]) for op in circuit.data)
        


target_index = {"x": 0, "h" : 0, "z" : 0,  "s" : 0, "sdg": 0, "t" : 0, "tdg":0, "cx": 1, "ccx": 2, "mcx": -1}

def get_target(gate, args) -> Qubit:
    return args[target_index[gate.name]]

def target_at(instr, ancs) -> bool:
    gate, args, _ = instr
    target = get_target(gate, args)
    return target in ancs

def inverse_CUns(E: QuantumCircuit, data_list: dllist, ancs) -> QuantumCircuit:
    for gate, qargs, cargs in reversed(data_list):
        target = get_target(gate, qargs)
        if target in ancs:
            assert gate.name in ALLOWED_ANCILLA
            if gate.name in ALLOWED_QFREE:
                E.append(gate, qargs, cargs)
        else:
            break
    return E

def swap_insert(instr1, instr2, ancs):
    gate1, args1, _ = instr1
    gate2, args2, _ = instr2
    target1 = get_target(gate1, args1)
    target2 = get_target(gate2, args2)

    CUn_ACUn = False
    if target1 in ancs and target2 not in ancs:
        CUn_ACUn = True
    
    insert_instr = None
    if CUn_ACUn:
        a_in_gate2 = target1 in args2
        b_in_gate1 = target2 in args1

        all_qubits = list(set(args1 + args2))
        controls = [q for q in all_qubits if q != target1 and q != target2]

        if gate1.name == "h":
            raise ValueError(
                f"H acts on ancilla"
            )
        
        if a_in_gate2 and not b_in_gate1:    
            if gate1.name in ALLOWED_PHASE:
                pass
            elif len(controls) != 0:
                mcx = MCXGate(num_ctrl_qubits=len(controls))
                insert_instr = (mcx, controls + [target2], [])
            else:
                insert_instr = (XGate(), [target2], [])
        elif not a_in_gate2 and b_in_gate1:
            if gate2.name == "h":
                raise ValueError(
                    f"H acts on qubit"
                )
            elif gate2.name in ALLOWED_PHASE:
                pass
            elif len(controls) != 0:
                mcx = MCXGate(num_ctrl_qubits=len(controls))
                insert_instr = (mcx, controls + [target1], [])
            else:
                insert_instr = (XGate(), [target1], [])
        elif a_in_gate2 and b_in_gate1:
            raise ValueError(
                f"Conflict: Qubit a is in gate2 and target2 is in gate1 at index {i}"
            )
        else:
            pass
    
    return CUn_ACUn, insert_instr


def update_head(head, ancs):
    while head:
        if not target_at(head.value, ancs):
            if head.next:
                head = head.next
            else:
                break
        else:
            head = head.prev
            break
    return head

def update_j(j, ancs):
    while j is not None:
        if target_at(j.value, ancs):
            j = j.next
        else:
            break
    return j

def uncomp(C: 'QuantumCircuit', ancs : list[Qubit], clean=True) -> 'QuantumCircuit':
    D = flatten_if_allowed(C.copy())
    
    D = k_local_commute_optimize1(D)
    
    data_list = dllist(D.data)

    # head is the last ACUn of the ACUns in the front, these ACUns will not be used
    head = update_head(data_list.first, ancs)

    # ACUns, head, CUns, j(the first ACUn after CUns, which will be swapped until head), ...
    j = head.next if head else data_list.first
    j = update_j(j, ancs)

    while j is not None:
        # k is the CUn before j, while j is the first ACUn after CUns
        k = j.prev
        assert k is not None, "k should not be None"
        CUn_ACUn, insert_instr =  swap_insert(k.value, j.value, ancs)
        assert CUn_ACUn, "k should be CUn, j should be ACUn"
        k.value, j.value = j.value, k.value
        if insert_instr:
            data_list.insertafter(insert_instr, k)
            if target_at(insert_instr, ancs):
                now = j.prev
            else:
                now = j
        else:
            now = j
        

        
        next_ = now.next
        l = dllist()
        for i in range(5):
            if not now:
                break
            l.append(now.value)
            next_ = now.next
            data_list.remove(now)
            now = next_
        k_local_commute_optimize2(l)
        for val in l:
            data_list.insert(val, next_)

        # head
        head = head.next if head else data_list.first
        head = update_head(head, ancs)
        
        j = head.next if head else data_list.first
        j = update_j(j, ancs)
        
        if j is None:
            break
    
    E = QuantumCircuit(*D.qregs, *D.cregs)
    return inverse_CUns(E, data_list, ancs)

# This uncomputation will return a clean version by:
# 1. reverse all gates targets at ancillas in the last
def uncompAll(C: 'QuantumCircuit', all=False, clean=True, reverse=True) -> 'QuantumCircuit':
    ancilla_regs = [reg for reg in C.qregs if isinstance(reg, AncillaRegister)]
    ancs = [q for reg in ancilla_regs for q in reg]

    if ancs is None:
        return C.copy()

    D = flatten_if_allowed(C.copy())
    if all:
        D = D.compose(uncomp(D, ancs, clean=clean))
        D = k_local_commute_optimize1(D)
    else:
        for qubit in (reversed(ancs) if reverse else ancs):
            D = D.compose(uncomp(D, [qubit], clean=clean))
            D = k_local_commute_optimize1(D)

    return D

def get_shortest_lft(data_list: dllist, ancs):
    lft_heap = []
    lifetimes = defaultdict(lambda: [None, None])
    idx = 0
    head = data_list.first

    while head:
        _, qargs, _ = head.value
        for q in qargs:
            flag = q in ancs
            if flag:
                if lifetimes[q][0] is None:
                    lifetimes[q][0] = head
                    lifetimes[q].append(idx)
                lifetimes[q][1] = head
                if len(lifetimes[q]) == 3:
                    lifetimes[q].append(idx)  # tail index
                else:
                    lifetimes[q][3] = idx
        head = head.next
        idx += 1
    for q, (head, tail, head_idx, tail_idx) in lifetimes.items():
        lifetime = tail_idx - head_idx + 1
        heapq.heappush(lft_heap, (lifetime, q.register.name + "_" + str(q.index), q, head, tail))
    if len(lft_heap) == 0:
        return None, None, None
    lft, qdex, qubit, head, tail = heapq.heappop(lft_heap)
    return qubit, head, tail

def to_circuit(data_list: dllist, D: QuantumCircuit) -> QuantumCircuit:
    E = QuantumCircuit(*D.qregs, *D.cregs)
    for gate, qargs, cargs in data_list:
        E.append(gate, qargs, cargs)
    return E


def uncomp0(data_list: dllist, ancs : list[Qubit], qfree: bool):
    if data_list == None or data_list.first == None:
        return data_list

    assert data_list.first.prev == None
    assert data_list.last.next == None

    k_local_commute_optimize2(data_list)

    # head is the last ACUn of the ACUns in the front, these ACUns will not be used
    head = update_head(data_list.first, ancs)

    # ACUns, head, CUns, j(the first ACUn after CUns, which will be swapped until head), ...
    j = head.next if head else data_list.first
    j = update_j(j, ancs)
    while j is not None:
        # k is the CUn before j, while j is the first ACUn after CUns
        k = j.prev
        assert k is not None, "k should not be None"
        CUn_ACUn, insert_instr =  swap_insert(k.value, j.value, ancs)
        assert CUn_ACUn, "k should be CUn, j should be ACUn"
        k.value, j.value = j.value, k.value
        if insert_instr:
            data_list.insertafter(insert_instr, k)
            if target_at(insert_instr, ancs):
                now = j.prev
            else:
                now = j
        else:
            now = j
            


        # optimize
        next_ = now.next
        l = dllist()
        for i in range(3):
            if not now:
                break
            l.append(now.value)
            next_ = now.next
            data_list.remove(now)
            now = next_
        k_local_commute_optimize2(l)
        for val in l:
            data_list.insert(val, next_)


        # head
        head = head.next if head else data_list.first
        head = update_head(head, ancs)
        
        j = head.next if head else data_list.first
        j = update_j(j, ancs)


        
        if j is None:
            break
    

    if qfree:   # dirty uncomputation
        k_local_commute_optimize2(data_list)
        # append qfree (remove actually)
        tail = data_list.last
        while tail:
            gate, qargs, cargs = tail.value
            target = get_target(gate, qargs)
            if target in ancs:
                data_list.remove(tail)
                tail = data_list.last
            else:
                break

        # remove qfree
        now = data_list.first
        while now:
            next_ = now.next
            gate, qargs, cargs = now.value
            if get_target(gate, qargs) not in ancs:
                if set(ancs) & set(qargs):
                    data_list.remove(now)
            else:
                break
            now = next_
        k_local_commute_optimize2(data_list)
    else:   # clean uncomputation(todo: dirty uncomputation for non-qfree)
        # append qfree
        k_local_commute_optimize2(data_list)
        for gate, qargs, cargs in reversed(data_list):
            target = get_target(gate, qargs)
            if target in ancs:
                assert gate.name in ALLOWED_ANCILLA
                if gate.name in ALLOWED_QFREE:
                    data_list.append((gate, qargs, cargs))
            else:
                break

        # remove qfree
        now = data_list.first
        while now:
            next_ = now.next
            gate, qargs, cargs = now.value
            if get_target(gate, qargs) not in ancs:
                if set(ancs) & set(qargs):
                    data_list.remove(now)
            else:
                break
            now = next_
        k_local_commute_optimize2(data_list)
        
    return data_list

# This uncomputation will return a dirty version by:
# 1. reverse all gates targets at ancillas in the last
# 2. cancel all gates using ancilla as control
def uncompAll0(C: 'QuantumCircuit', all=False) -> 'QuantumCircuit':
    ancilla_regs = [reg for reg in C.qregs if isinstance(reg, AncillaRegister)]
    ancs = [q for reg in ancilla_regs for q in reg]
    ancs = set(ancs)

    if ancs is None:
        return C.copy()

    D = flatten_if_allowed(C.copy())
    qfree = is_qfree_circuit(D)
    D = k_local_commute_optimize1(D)
    data_list = dllist(D.data)

    if all:
        data_list = uncomp0(data_list, list(ancs), qfree)
    else:
        while ancs:
            anc, head, tail = get_shortest_lft(data_list, ancs)
            if anc == None:
                break
            
            last = tail.next

            now = head
            next_ = now.next
            l = dllist()
            while now and now != last:
                next_ = now.next
                l.append(now.value)
                data_list.remove(now)
                now = next_
            l = uncomp0(l, [anc], qfree)

            head = l.first
            while head:
                data_list.insert(head, last)
                head = head.next
            ancs.remove(anc)


        
    D = QuantumCircuit(*D.qregs, *D.cregs)
    for gate, qargs, cargs in data_list:
        D.append(gate, qargs, cargs)
        
    return D

def uncompute(C: 'QuantumCircuit', mode=0):
    # return clean version
    if mode == 0:
        # seq
        return uncompAll(C, False, True, False)
    elif mode == 1:
        # reverse
        return uncompAll(C, False, True, True)
    elif mode == 2:
        # all
        return uncompAll(C, True, True, False)
    # return dirty version for qfree and clean version for non-qfree
    elif mode == 3:
        # lifetime
        return uncompAll0(C, False)
    # elif mode == 4:
    #     # all
    #     return uncompAll0(C, True)
    else:
        assert False 
