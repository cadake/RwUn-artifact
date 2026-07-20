# Adapted from https://github.com/eth-sri/Reqomp/blob/master/reqomp/examples/grover.py

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, AncillaRegister
from qiskit.circuit.library import ZGate
from RwUn.examples.mcx import *

def makesOracle(i, n):
    # Creates the oracle finding exactly i on n qubits (+ 1 for target)(or its lowest n bits if i >= 2^n)
    # Could use some uncomputation...
    ctrls = QuantumRegister(n)
    target = QuantumRegister(1) 
    fcirc = QuantumCircuit(ctrls, target, name="oracle_" + str(i) + "_" + str(n))
    format_str = '{0:0' + str(n) + 'b}'
    binary_i = format_str.format(i)[::-1]
    for j in range(n):
        if binary_i[j] == '0':
            fcirc.x(ctrls[j])
    fcirc.mcx(ctrls[:], target[0])
    for j in range(n):
        if binary_i[j] == '0':
            fcirc.x(ctrls[j])
    return fcirc
    
def makesGroverCircuit(n, oracle = None, nb_sols = 1):
    assert n > 2
    # grover circuit on n qubits, without measurements as uncomp cannot deal with that yet
    nbIter = int(np.floor(np.pi / 4.0 * np.sqrt(pow(2, n))))

    working_qubits = QuantumRegister(n, name = 'r')
    phase_qubit = QuantumRegister(1, name = 'p')
    ancs = []
    for i in range(nbIter):
        ancs.append(AncillaRegister(n-2, name = f'a{i}'))
    circ = QuantumCircuit(working_qubits, phase_qubit)
    for i in range(nbIter):
        circ.add_register(ancs[i])
    circ.x(phase_qubit[0])
    circ.h(phase_qubit[0])

    circ.h(working_qubits)
        
    for i in range(nbIter):
        if oracle is not None:
            circ.append(oracle, [*working_qubits[:], phase_qubit[0]])
        else:
            circ.compose(makeMCX(n, False), qubits=list(working_qubits[:]) + list(phase_qubit[:]) + list(ancs[i][:]), inplace=True)
            # circ.mcx(working_qubits, phase_qubit)

        #Grover diffusion operator
        circ.h(working_qubits)
        circ.x(working_qubits)
        circ.h(working_qubits[-1])
        # --- create an MCX instruction and remove its .definition ---
        mcx_inst = MCXGate(n-1)   # MCXGate(n) has n controls and 1 target
        mcx_inst.definition = None
        # append the opaque MCX instruction (controls ... then target)
        circ.append(mcx_inst, [*working_qubits[:-1], working_qubits[-1]])
        # circ.mcx(working_qubits[:-1], working_qubits[-1])
        circ.h(working_qubits[-1])
        circ.x(working_qubits)
        
        circ.h(working_qubits)

    # bring the phase qubit back to 0, we can't uncompute it, as it went through cz, non qfree -> no need to uncomp it, Qiskit doesn't 
    #circ.h(phase_qubit[0])
    #circ.x(phase_qubit)
    return circ
