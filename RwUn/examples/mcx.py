# Includes code from https://github.com/eth-sri/Reqomp/blob/master/reqomp/examples/mcx.py

from qiskit.circuit import QuantumRegister, QuantumCircuit
from qiskit.circuit.library.standard_gates.x import RCCXGate, CCXGate
from qiskit.circuit.quantumregister import AncillaRegister
from qiskit.circuit.library import MCXGate

def makeMCX(n, dirty=False):
    assert n >= 1, "n must be at least 1"

    q_controls = QuantumRegister(n, name='ctrls')
    q_target = QuantumRegister(1, name='target')
    circuit = QuantumCircuit(q_controls, q_target)

    if n <=2:
        if n==1:
            circuit.cx(q_controls[0], q_target)
        else:
            circuit.ccx(q_controls[0], q_controls[1], q_target)
        return circuit

    q_ancillas = AncillaRegister(n-2, name= 'anc')
    circuit.add_register(q_ancillas)

    circuit.ccx(q_controls[0], q_controls[1], q_ancillas[0])

    idx_list= []
    i = 0
    for j in range(2, n - 1):
        circuit.ccx(q_controls[j], q_ancillas[i], q_ancillas[i + 1])
        if dirty:
            idx_list.append((j, i))
        i += 1
    circuit.ccx(q_controls[-1], q_ancillas[i], q_target)
    
    if dirty:
        prepend_circuit = QuantumCircuit(q_controls, q_target, q_ancillas)
        prepend_circuit.ccx(q_controls[-1], q_ancillas[i], q_target)
        for j, i in reversed(idx_list):
            prepend_circuit.ccx(q_controls[j], q_ancillas[i], q_ancillas[i+1])
        circuit = prepend_circuit.compose(circuit)
        
    return circuit


# log(n) depth MCX from Nie's et al. where we don't care about the recursive decompostion
def makeConditionalMCS(n, dirty=False):
    assert n >= 6, "n must be at least 6"

    q = QuantumRegister(n, name='ctrls')
    t = QuantumRegister(1, name='target')
    a = AncillaRegister(2, name='anc')
    circuit = QuantumCircuit(q, t, a)

    if dirty:
        # part 2
        circuit.x(q[0])
        circuit.x(q[1])
        circuit.x(q[2])
        circuit.x(q[3])
        circuit.append(MCXGate(int((n-4)//2)), [*(q[i] for i in range(4, int(4+(n-4)//2))), q[0]])
        circuit.append(MCXGate(int(n - (4+(n-4)//2))), [*(q[i] for i in range(int(4+(n-4)//2), n)), q[2]])

        # part 3
        circuit.append(MCXGate(3), [q[0], q[2], a[0], a[1]])

        # part 4
        circuit.append(MCXGate(int(n - (4+(n-4)//2))), [*(q[i] for i in range(int(4+(n-4)//2), n)), q[2]])
        circuit.append(MCXGate(int((n-4)//2)), [*(q[i] for i in range(4, int(4+(n-4)//2))), q[0]])
        circuit.x(q[0])
        circuit.x(q[1])
        circuit.x(q[2])
        circuit.x(q[3])


    # part 1
    circuit.append(MCXGate(4), [q[0], q[1], q[2], q[3], a[0]])

    # part 2
    circuit.x(q[0])
    circuit.x(q[1])
    circuit.x(q[2])
    circuit.x(q[3])
    circuit.append(MCXGate(int((n-4)//2)), [*(q[i] for i in range(4, int(4+(n-4)//2))), q[0]])
    circuit.append(MCXGate(int(n - (4+(n-4)//2))), [*(q[i] for i in range(int(4+(n-4)//2), n)), q[2]])

    # part 3
    circuit.append(MCXGate(3), [q[0], q[2], a[0], a[1]])

    # part 4
    circuit.append(MCXGate(int(n - (4+(n-4)//2))), [*(q[i] for i in range(int(4+(n-4)//2), n)), q[2]])
    circuit.append(MCXGate(int((n-4)//2)), [*(q[i] for i in range(4, int(4+(n-4)//2))), q[0]])
    circuit.x(q[0])
    circuit.x(q[1])
    circuit.x(q[2])
    circuit.x(q[3])

    # part 6
    circuit.t(a[1])
    circuit.t(t[0])
    circuit.cx(a[1], t[0])
    circuit.tdg(t[0])
    circuit.cx(a[1], t[0])


    return circuit


# MCX from Khattar et al also using conditional clean ancilla. where we don't care about the recursive decompostion
def makeRiseConditionalMCS(n, dirty=False):
    assert n >= 6, "n must be at least 6"

    q = QuantumRegister(n, name='ctrls')
    t = QuantumRegister(1, name='target')
    a = AncillaRegister(2, name='anc')
    circuit = QuantumCircuit(q, t, a)

    if dirty:
        # part 2
        last = 3
        for i in range(3, n, 2):
            circuit.ccx(q[i], q[i-1], q[i-2])
            last = i
        for i in range(last-1):
            circuit.x(q[i])
        if last == n - 1:
            circuit.cx(q[last-2], q[last-3])
        else:
            circuit.ccx(q[last+1], q[last-2], q[last-3])
        for i in range(last-5, -1, -2):
            circuit.ccx(q[i+1], q[i+2], q[i])

        # part 3
        circuit.ccx(q[0], a[0], a[1])

        # part 4
        for i in range(0, last-4, 2):
            circuit.ccx(q[i+1], q[i+2], q[i])
        if last == n - 1:
            circuit.cx(q[last-2], q[last-3])
        else:
            circuit.ccx(q[last+1], q[last-2], q[last-3])
        for i in range(last-1):
            circuit.x(q[i])
        for i in range(last, 2, -2):
            circuit.ccx(q[i], q[i-1], q[i-2])


    # part 1
    circuit.ccx(q[0], q[1], a[0])
    
    # part 2
    last = 3
    for i in range(3, n, 2):
        circuit.ccx(q[i], q[i-1], q[i-2])
        last = i
    for i in range(last-1):
        circuit.x(q[i])
    if last == n - 1:
        circuit.cx(q[last-2], q[last-3])
    else:
        circuit.ccx(q[last+1], q[last-2], q[last-3])
    for i in range(last-5, -1, -2):
        circuit.ccx(q[i+1], q[i+2], q[i])

    # part 3
    circuit.ccx(q[0], a[0], a[1])

    # part 4
    for i in range(0, last-4, 2):
        circuit.ccx(q[i+1], q[i+2], q[i])
    if last == n - 1:
        circuit.cx(q[last-2], q[last-3])
    else:
        circuit.ccx(q[last+1], q[last-2], q[last-3])
    for i in range(last-1):
        circuit.x(q[i])
    for i in range(last, 2, -2):
        circuit.ccx(q[i], q[i-1], q[i-2])

    # part 6
    circuit.t(a[1])
    circuit.t(t[0])
    circuit.cx(a[1], t[0])
    circuit.tdg(t[0])
    circuit.cx(a[1], t[0])

    return circuit