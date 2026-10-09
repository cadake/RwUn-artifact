"""Compose computation-only examples while preserving clean ancilla registers."""
from qiskit.circuit import AncillaRegister


def append_with_ancillas(circuit, subcircuit, data_qubits):
    """Append a subcircuit whose data qubits precede all its ancillas."""
    qubits = list(data_qubits)
    if subcircuit.num_ancillas:
        ancillas = AncillaRegister(subcircuit.num_ancillas)
        circuit.add_register(ancillas)
        qubits.extend(ancillas)
    circuit.append(subcircuit.to_instruction(), qubits)
