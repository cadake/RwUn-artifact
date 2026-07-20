from z3 import Bool, Solver, And, Or, Not, Xor, unsat, substitute, BoolVal, sat
from qiskit import QuantumCircuit, QuantumRegister, AncillaRegister

def qubit_name(qubit, C):
    for reg in C.qregs:
        if qubit in reg:
            return f"{reg.name}_{reg.index(qubit)}"
    raise ValueError("Qubit not found in any register")

def create_symbolic_state(circuit):
    state = {}
    for qubit in circuit.qubits:
        name = qubit_name(qubit, circuit)
        state[name] = Bool(name)
    return state

def apply_gate_to_state(gate_name, qubits, state):
    if gate_name == "id":
        pass
    elif gate_name == "x":
        state[qubits[0]] = Not(state[qubits[0]]) 
    elif gate_name == "cx":
        control, target = qubits
        state[target] = Xor(state[target], state[control])
    elif gate_name == "ccx":
        control1, control2, target = qubits
        state[target] = Xor(state[target], And(state[control1], state[control2]))
    elif gate_name == "mcx":
        *controls, target = qubits
        cond = And([state[q] for q in controls])
        state[target] = Xor(state[target], cond)
    else:
        raise ValueError(f"Unsupported gate: {gate_name}")
    
def compute_final_symbolic_state(circuit: QuantumCircuit):
    state = create_symbolic_state(circuit)
    
    for gate, qubits, _ in circuit.data:
        qubit_names = [qubit_name(q, circuit) for q in qubits]
        apply_gate_to_state(gate.name, qubit_names, state)

    return state

    
