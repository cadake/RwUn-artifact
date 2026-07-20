# Includes code from https://github.com/eth-sri/Reqomp/blob/master/reqomp/examples/adder.py

from qiskit.circuit import QuantumRegister, QuantumCircuit, AncillaRegister

def makesAdder(num_qubits):
    #[a, b]: b = a + b, a and b made of num_qubits each
    # returns an AncillaCircuit, without uncomputation
    def neg_mct_gate():
        neg_mct = QuantumCircuit(4)
        neg_mct.cx(1, 2)
        neg_mct.ccx(0, 2, 3)
        neg_mct.cx(1, 2)
        return neg_mct

    def carry_gate():
        carry_circ = QuantumCircuit(4)
        (c0, a, b, c1) = (carry_circ.qubits[0], carry_circ.qubits[1], carry_circ.qubits[2], carry_circ.qubits[3])
        carry_circ.ccx(a, b, c1)
        carry_circ.append(neg_mct_gate(), [c0, a, b, c1])
        return carry_circ

    def sum_gate():
        sum_circ = QuantumCircuit(3)
        (c0, a, b) = (sum_circ.qubits[0], sum_circ.qubits[1], sum_circ.qubits[2])
        sum_circ.cx(a, b)
        sum_circ.cx(c0, b)
        return sum_circ

    a = QuantumRegister(num_qubits, name = "a")
    b = QuantumRegister(num_qubits, name = "b")
    c = AncillaRegister(num_qubits, name = "c")

    circuit = QuantumCircuit(a, b, c)

    for i in range(num_qubits-1):
        circuit.append(carry_gate(), [c[i], a[i], b[i], c[i+1]])
        circuit.append(sum_gate(), [c[i], a[i], b[i]])
    circuit.append(sum_gate(), [c[num_qubits-1], a[num_qubits-1], b[num_qubits-1]])

    return circuit

def to_nbit_list(n: int, val: int) -> list[int]:
    return [(val >> i) & 1 for i in range(n)]

def makesDirtyHighestBitConstAdder(num_qubits, value):
    assert num_qubits > 0
    x = QuantumRegister(num_qubits, name = 'x')
    bits = to_nbit_list(num_qubits, value)
    if num_qubits == 1:
        adder = QuantumCircuit(x)
        if bits[0] == 1:
            adder.x(x[0])
        return adder
    
    a = AncillaRegister(num_qubits-1, name = 'a')
    adder = QuantumCircuit(x, a)
    adder.cx(a[num_qubits-2], x[num_qubits-1])
    for i in range(num_qubits-2, 0, -1):
        if bits[i]:
            adder.cx(x[i], a[i])
            adder.x(x[i])
        adder.ccx(a[i-1], x[i], a[i])
    if bits[0]:
        adder.cx(x[0], a[0])
    for i in range(1, num_qubits-1):
        adder.ccx(a[i-1], x[i], a[i])
        if bits[i]:
            adder.x(x[i])
    adder.cx(a[num_qubits-2], x[num_qubits-1])
    if bits[num_qubits-1]:
        adder.x(x[num_qubits - 1])
    return adder

def makesDirtyAdder(num_qubits):
    x = QuantumRegister(num_qubits, name = 'x')
    y = QuantumRegister(num_qubits, name = 'y')
    
    if num_qubits == 1:
        circuit = QuantumCircuit(x, y)
        circuit.cx(x[0], y[0])
        return circuit

    a = AncillaRegister(num_qubits - 1, name = 'a')

    circuit = QuantumCircuit(x, y, a)

    for n in range(num_qubits - 1, 0, -1):
        circuit.cx(a[n - 1], y[n])
        for i in range(n-1, 0, -1):
            circuit.ccx(x[i], y[i], a[i])
            circuit.cx(x[i], y[i])
            circuit.ccx(a[i - 1], y[i], a[i])
        circuit.ccx(x[0], y[0], a[0])
        for i in range(n - 1):
            circuit.ccx(a[i], y[i + 1], a[i + 1])
            circuit.cx(x[i + 1], y[i + 1])
        circuit.cx(a[n - 1], y[n])
        circuit.cx(x[n], y[n])
    circuit.cx(x[0], y[0])
    return circuit



