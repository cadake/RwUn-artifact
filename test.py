from RwUn.uncomp import uncompute
from qiskit.circuit import QuantumRegister, QuantumCircuit, AncillaRegister

if __name__ == "__main__":
    q = QuantumRegister(3)
    t = QuantumRegister(1)
    a = AncillaRegister(1)
    C = QuantumCircuit(q,t,a)
    C.ccx(q[0],q[1],a[0])
    C.ccx(a[0],q[2],t[0])
    print(C)
    D = uncompute(C, 0)
    print(D)
    E = uncompute(C, 3)
    print(E)
