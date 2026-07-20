# Adapted from https://github.com/eth-sri/Reqomp/blob/master/reqomp/examples/intergercomparator.py
import numpy as np

from qiskit.circuit import QuantumRegister, QuantumCircuit, AncillaRegister
from qiskit.circuit.exceptions import CircuitError
from qiskit.circuit.library.boolean_logic import OR


      
def _get_twos_complement(n, val):
    """Returns the 2's complement of ``self.value`` as array.

    Returns:
         The 2's complement of ``self.value``.
    """
    twos_complement = pow(2, n) - int(np.ceil(val))
    twos_complement = '{0:b}'.format(twos_complement).rjust(n, '0')
    twos_complement = \
        [1 if twos_complement[i] == '1' else 0 for i in reversed(range(len(twos_complement)))]
    return twos_complement

def makeIntegerComparator(num_state_qubits, value, geq  = True, dirty = False):
    """Build the comparator circuit."""
    or_gate = OR(2).to_gate()
    qr_state = QuantumRegister(num_state_qubits, name='state')
    q_compare = QuantumRegister(1, name='compare')
    circuit = QuantumCircuit(qr_state, q_compare)
    if not dirty:
        if num_state_qubits > 1:
            qr_ancilla = AncillaRegister(num_state_qubits - 1)
            circuit.add_register(qr_ancilla)
    else:
        if num_state_qubits > 1:
            qr_ancilla = AncillaRegister(num_state_qubits)
            circuit.add_register(qr_ancilla)

    if value <= 0:  # condition always satisfied for non-positive values
        if geq:  # otherwise the condition is never satisfied
            circuit.x(q_compare)
    # condition never satisfied for values larger than or equal to 2^n
    elif value < pow(2, num_state_qubits):

        if num_state_qubits > 1:
            twos = _get_twos_complement(num_state_qubits, value)
            if not dirty:
                for i in range(num_state_qubits):
                    if i == 0:
                        if twos[i] == 1:
                            circuit.cx(qr_state[i], qr_ancilla[i])
                    elif i < num_state_qubits - 1:
                        if twos[i] == 1:
                            circuit.append(or_gate, [qr_state[i], qr_ancilla[i - 1], qr_ancilla[i]])
                        else:
                            circuit.ccx(qr_state[i], qr_ancilla[i - 1], qr_ancilla[i])
                    else:
                        if twos[i] == 1:
                            circuit.append(or_gate, [qr_state[i], qr_ancilla[i - 1], q_compare])
                        else:
                            circuit.ccx(qr_state[i], qr_ancilla[i - 1], q_compare)
            else:
                circuit.cx(qr_ancilla[num_state_qubits - 1], q_compare)
                for i in range(num_state_qubits-1, 0, -1):
                    if twos[i] == 1:
                        circuit.cx(qr_state[i], qr_ancilla[i])
                        circuit.x(qr_state[i])
                    circuit.ccx(qr_ancilla[i-1], qr_state[i], qr_ancilla[i])
                if twos[0] == 1:
                    circuit.cx(qr_state[0], qr_ancilla[0])
                for i in range(num_state_qubits - 1):
                    circuit.ccx(qr_ancilla[i], qr_state[i+1], qr_ancilla[i+1])
                    if twos[i+1] == 1:
                        circuit.x(qr_state[i+1])
                circuit.cx(qr_ancilla[num_state_qubits - 1], q_compare)
                

            # flip result bit if geq flag is false
            if not geq:
                circuit.x(q_compare)

        else:

            # num_state_qubits == 1 and value == 1:
            circuit.cx(qr_state[0], q_compare)

            # flip result bit if geq flag is false
            if not geq:
                circuit.x(q_compare)

    else:
        if not geq:  # otherwise the condition is never satisfied
            circuit.x(q_compare)

    return circuit