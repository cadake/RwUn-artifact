# Adapted from Reqomp's reqomp/examples/adder.py.
from qiskit.circuit import QuantumCircuit, QuantumRegister, AncillaRegister
from .adder import makesAdder
from ._ancillas import append_with_ancillas


def makesMult(num_qubits):
    """Compute b += x*y modulo 2**num_qubits, without uncomputation."""
    b = QuantumRegister(num_qubits, 'b')
    y = QuantumRegister(num_qubits, 'y')
    x = QuantumRegister(num_qubits, 'x')
    circuit = QuantumCircuit(b, y, x)
    for i, x_i in enumerate(x):
        a = AncillaRegister(num_qubits, 'a_m' + str(i))
        circuit.add_register(a)
        for a_qubit, y_qubit in zip(a[i:], y[:num_qubits-i]):
            circuit.ccx(x_i, y_qubit, a_qubit)
        append_with_ancillas(circuit, makesAdder(num_qubits), [*a, *b])
    return circuit
