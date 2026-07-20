# Adapted from https://github.com/eth-sri/Reqomp/blob/master/reqomp/examples/deutschjozsa.py


import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, AncillaRegister
from RwUn.examples.mcx import *

def makesDJ(num_qubits, oracle_gate = None):
    assert num_qubits > 2
    #Builds the Deutsch Jozsa circuit for n + 1 qubits, finding the value 111...111
    var_reg = QuantumRegister(num_qubits, name = 'vals')
    out_reg = QuantumRegister(1, name = 'out')
    anc_reg = AncillaRegister(num_qubits-2, name="anc")
    

    circ = QuantumCircuit(var_reg, out_reg, anc_reg)

    circ.h(var_reg)
    circ.x(out_reg)
    circ.h(out_reg)

    if oracle_gate:
        circ.append(oracle_gate, [*var_reg, out_reg[0]])
    else:
        circ.compose(makeMCX(num_qubits, False), qubits=list(var_reg[:]) + list(out_reg[:]) + list(anc_reg[:]), inplace=True)

    circ.h(var_reg)

    return circ
