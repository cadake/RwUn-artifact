# Adapt from https://github.com/eth-sri/Reqomp/blob/master/reqomp/examples/mcx.py
from qiskit.circuit import QuantumRegister, QuantumCircuit
from qiskit.circuit.library.standard_gates.x import RCCXGate, CCXGate, MCXGate
from qiskit.circuit.quantumregister import AncillaRegister


def makeMCRY(n):
    q_controls = QuantumRegister(n, name='ctrls')
    q_target = QuantumRegister(1, name='target')
    q_ancilla = AncillaRegister(1, name='anc')

    circuit = QuantumCircuit(q_controls, q_target, q_ancilla)
    # --- create an MCX instruction and remove its .definition ---
    mcx_inst = MCXGate(n)   # MCXGate(n) has n controls and 1 target
    mcx_inst.definition = None               

    # append the opaque MCX instruction (controls ... then target)
    circuit.append(mcx_inst, [*q_controls[:], q_ancilla[0]])
    
    circuit.h(q_target)
    circuit.cx(q_ancilla, q_target)
    circuit.tdg(q_target)
    circuit.cx(q_ancilla, q_target)    
    circuit.h(q_target)
    
    return circuit

