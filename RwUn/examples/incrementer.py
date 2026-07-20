from qiskit.circuit import QuantumRegister, QuantumCircuit, AncillaRegister

def makesIncrementer(num_qubits, dirty=False):
    x = QuantumRegister(num_qubits, 'x')
    assert num_qubits > 0, "Number of qubits must be greater than 0"
    if num_qubits <= 2:
        circuit = QuantumCircuit(x)
        if num_qubits == 1:
            circuit.x(0)
        elif num_qubits == 2:
            circuit.cx(0, 1)
            circuit.x(0)
        return circuit
    a = AncillaRegister(num_qubits - 2, 'a')
    circuit = QuantumCircuit(x, a)
    if not dirty:
        for i in range(num_qubits - 2):
            circuit.ccx(x[i], x[i+1], a[i])
        for i in range(num_qubits - 3, -1, -1):
            circuit.cx(a[i], x[i+2])
        circuit.cx(x[0], x[1])
        circuit.x(x[0])
        # circuit.ccx(x[0], x[1], a[0])
        # circuit.cx(x[0], x[1])
        # circuit.x(x[0])
        # for i in range(1, num_qubits - 2):
        #     circuit.ccx(a[i - 1], x[i + 1], a[i])
        #     circuit.cx(a[i - 1], x[i + 1])
        # circuit.cx(a[num_qubits - 3], x[num_qubits - 1])
    else:
        for n in range(num_qubits, 2, -1):
            circuit.cx(a[n - 3], x[n - 1])
            for i in range(n - 3, 0, -1):
                circuit.ccx(x[i+1], a[i - 1], a[i])
            circuit.ccx(x[0], x[1], a[0])
            for i in range(1, n - 2):
                circuit.ccx(x[i+1], a[i - 1], a[i])
            circuit.cx(a[n - 3], x[n - 1])
        circuit.cx(x[0], x[1])
        circuit.x(x[0])
        
    return circuit

# gidney's dirty inc
def makesDirtyIncrementer(num_qubits):
    assert num_qubits > 0, "Number of qubits must be greater than 0"
    g = AncillaRegister(num_qubits, 'g')
    v = QuantumRegister(num_qubits, 'v')

    C = QuantumCircuit(g, v)
    for i in range(num_qubits):
        C.cx(g[0], v[i])
    for i in range(1, num_qubits):
        C.x(g[i])
    C.x(v[num_qubits - 1])

    for i in range(1, num_qubits):
        C.cx(g[i-1], v[i-1])
        C.cx(g[i], g[i-1])
        C.ccx(g[i-1], v[i-1], g[i])
    
    C.cx(g[num_qubits - 1], v[num_qubits - 1])

    for i in range(num_qubits - 1, 0, -1):
        C.ccx(g[i-1], v[i-1], g[i])
        C.cx(g[i], g[i-1])
        C.cx(g[i], v[i-1])
    
        
    return C
 