# Includes code from https://github.com/eth-sri/Unqomp/blob/master/unqomp/dependencygraph.py https://github.com/eth-sri/Unqomp/blob/master/unqomp/converter.py

from qiskit.converters import circuit_to_dag
import networkx as nx
from qiskit.dagcircuit import DAGInNode, DAGOpNode, DAGOutNode
from qiskit.circuit import QuantumCircuit, Qubit, AncillaRegister
from qiskit.circuit.library import IGate
from qiskit.dagcircuit import DAGCircuit
from qiskit.converters import circuit_to_dag

class InitGate:
    def __init__(self):
        self.name = 'init'

class Edge:
    def __init__(self, node_from, node_to, edge_type):
        self.node_from = node_from
        self.node_to = node_to
        self.type = edge_type

    def __repr__(self):
        return "Edge: from({}), to({}), type({})".format(self.node_from, self.node_to, self.type)

class Node:
    def __init__(self, register, index, gate, value_id = 0, copy_id = 0):
        self.register = register
        self.index = index
        self.variable_name = Node.wireName(register, index)
        self.gate = gate
        self.value_id = value_id
        self.copy_id = copy_id
        self.ctrl_edges_in = []
        self.non_ctrl_edges_in = []
        self.edges_out = []
        self.consume_edge_in = None
        self.consume_edge_out = None

    def __repr__(self):
        return "Node: var({}), vId({}), cId({})".format(self.variable_name, self.value_id, self.copy_id)

    def __gt__(self, node2): #order does not matter so much, we just want to break ties when comparing ancillaRegisters
        if self.register.name == node2.register.name:
            return self.index > node2.index
        return self.register.name > node2.register.name

    def wireName(register, index):
        return "%s[%s]" % (register.name, index)

class DependencyGraph:
    def __init__(self, extra_qfree_gates = [], extra_non_qfree_gates = []):
        self.nodes = {} #for a variable name, contains a list (ordered by value_id) of list (ordered by copy_id) of nodes
        self.deallocate_nodes = [] # we don't want to pollute the graph to much
        self.extra_qfree_gates = extra_qfree_gates
        self.extra_non_qfree_gates = extra_non_qfree_gates

    def addNode(self, node):
        list_nodes = self.nodes.get(node.variable_name)
        if node.gate.name == 'deallocate':
            self.deallocate_nodes.append(node)
            return
        if list_nodes is not None:
            if len(list_nodes) > node.value_id:
                assert len(list_nodes[node.value_id]) == node.copy_id
                list_nodes[node.value_id].append(node)
            else:
                assert len(list_nodes) == node.value_id and node.copy_id == 0
                list_nodes.append([node])
        else:
            assert node.value_id == 0 and node.copy_id == 0
            self.nodes[node.variable_name] = [[node]]

    def addRootNode(self, node):
        self.addNode(node)        

    def connectConsumedNodes(self, node_from, node_to, return_new_edges = False):
        assert node_from.variable_name == node_to.variable_name
        assert node_from.value_id == node_to.value_id + 1 or node_from.value_id == node_to.value_id - 1 #computation or uncomputation
        assert node_to.consume_edge_in is None
        assert node_from.consume_edge_out is None
        # removed bc of deallocate nodes, without them holds
        #assert self.nodes[node_from.variable_name][node_from.value_id][node_from.copy_id] == node_from
        #assert self.nodes[node_to.variable_name][node_to.value_id][node_to.copy_id] == node_to
        e = Edge(node_from, node_to, 'c')
        node_from.consume_edge_out = e
        node_to.consume_edge_in = e
        added_avail_edges = self._updatesAvailabilityEdges(e, return_new_edges)
        if(return_new_edges):
            added_avail_edges.append(e)
            return added_avail_edges
    
    def connectDependencyNodes(self, node_from, node_to, return_new_edges = False):
        assert node_from.variable_name != node_to.variable_name
        assert self.nodes[node_from.variable_name][node_from.value_id][node_from.copy_id] == node_from
        assert self.nodes[node_to.variable_name][node_to.value_id][node_to.copy_id] == node_to
        e = Edge(node_from, node_to, 'd')
        node_from.edges_out.append(e)
        node_to.ctrl_edges_in.append(e)
        added_avail_edges = self._updatesAvailabilityEdges(e, return_new_edges)
        if(return_new_edges):
            added_avail_edges.append(e)
            return added_avail_edges

    def _connectAvailabilityNodes(self, node_from, node_to, return_new_edges = False):
        assert node_from.variable_name != node_to.variable_name
        # removed bc of deallocate gates, holds otherwise
        #assert self.nodes[node_from.variable_name][node_from.value_id][node_from.copy_id] == node_from
        #assert self.nodes[node_to.variable_name][node_to.value_id][node_to.copy_id] == node_to
        e = Edge(node_from, node_to, 'a')
        node_from.edges_out.append(e)
        node_to.non_ctrl_edges_in.append(e)
        if return_new_edges:
            return e

    def _updatesAvailabilityEdges(self, edge, return_new_edges = False):
        new_edges = []
        if edge.type == 'c':
            #edge is some x1 -> x2, for all dependency edges x1 -> y, we add the availability one y -> x2
            for edge_out in edge.node_from.edges_out:
                if edge_out.type == 'd':
                    e = self._connectAvailabilityNodes(edge_out.node_to, edge.node_to, return_new_edges)
                    if return_new_edges:
                        new_edges.append(e)
        elif edge.type == 'd':
            #edge is some x1 -> y, if there is some consume edge x1 -> x2, we add the availability one y -> x2
            if edge.node_from.consume_edge_out is not None:
                e = self._connectAvailabilityNodes(edge.node_to, edge.node_from.consume_edge_out.node_to, return_new_edges)
                if return_new_edges:
                        new_edges.append(e)
        
        if return_new_edges:
            return new_edges

    def _aux_topoligical_sort(self, sorted_nodes, seen_nodes, node):
        seen = seen_nodes.get(node)
        if seen is not None:
            if seen == 1:
                print("wow cycle from node")
                print(node)
                assert False
            else:
                return
        seen_nodes[node] = 1 #to detect cycle, changed to 2 when the node is not active anymore
        for e in node.edges_out:
            self._aux_topoligical_sort(sorted_nodes, seen_nodes, e.node_to)
        if node.consume_edge_out is not None:
            self._aux_topoligical_sort(sorted_nodes, seen_nodes, node.consume_edge_out.node_to)
        seen_nodes[node] = 2
        sorted_nodes.append(node)

    def nodesInTopologicalOrder(self):
        sorted_nodes = []
        seen_nodes = {}
        for variable_name in self.nodes:
            for list_copies in self.nodes[variable_name]:
                for node in list_copies:
                    self._aux_topoligical_sort(sorted_nodes, seen_nodes, node)
        sorted_nodes.reverse()
        return sorted_nodes

    def hasCycleWith(self, orig_node):
        #returns true if there is a cycle containing orig_node
        marked = {} # 1 if seen, 2 if active

        def hasCycle(node):
            t = marked.get(node)
            if t is not None:
                if t==2:
                    return True
                else:
                    return False
            marked[node] = 2
            if node.consume_edge_out and hasCycle(node.consume_edge_out.node_to):
                return True
            for e in node.edges_out:
                if hasCycle(e.node_to):
                    return True
            marked[node] = 1
            return False

        return hasCycle(orig_node)

    def to_networkx(self) -> nx.MultiDiGraph:
        G = nx.MultiDiGraph()

        def node_key(node: "Node"):
            return (node.variable_name, node.value_id, node.copy_id)

        for var_name, versions in self.nodes.items():
            for value_id, copies in enumerate(versions):
                for copy_id, node in enumerate(copies):
                    key = node_key(node)
                    if key in G:
                        continue
                    G.add_node(
                        key,
                        variable_name=node.variable_name,
                        value_id=node.value_id,
                        copy_id=node.copy_id,
                        gate_name=node.gate.name if node.gate is not None else None,
                        register_name=node.register.name if node.register is not None else None,
                        index=node.index,
                    )

        for node in self.deallocate_nodes:
            key = node_key(node)
            if key not in G:
                G.add_node(
                    key,
                    variable_name=node.variable_name,
                    value_id=node.value_id,
                    copy_id=node.copy_id,
                    gate_name=node.gate.name if node.gate is not None else None,
                    register_name=node.register.name if node.register is not None else None,
                    index=node.index,
                )

        for var_name, versions in self.nodes.items():
            for value_id, copies in enumerate(versions):
                for copy_id, node in enumerate(copies):
                    if node.consume_edge_out is not None:
                        e = node.consume_edge_out
                        u = node_key(e.node_from)
                        v = node_key(e.node_to)
                        G.add_edge(u, v, etype='c')

        for var_name, versions in self.nodes.items():
            for value_id, copies in enumerate(versions):
                for copy_id, node in enumerate(copies):
                    for e in node.edges_out:
                        u = node_key(e.node_from)
                        v = node_key(e.node_to)
                        G.add_edge(u, v, etype=e.type)

        return G
                        
class ConverterDependencyGraph:
    # maybe allow for extra custom gates (for which we'll need their inverse + ctrls/target + qfree or not), as arguments to ConverterDependencyGraph constructor
    known_qfree_gates = ['ccx', 'cnot', 'cx', 'i', 'id', 'iden', 'mct', 'mcx', 'mcx_gray', 'toffoli', 'x']
    known_non_qfree_gates = ['ch', 'crx', 'cry', 'crz', 'cu1', 'cu2', 'cu3', 'cy', 'cz', 'h', 'mcrx', 'mcry', 'mcrz', 'mcu1', 'r', 'rcccx', 'rccx', 'rx', 'ry', 'rz', 's', 'sdg', 't', 'tdg', 'u', 'u1', 'u2', 'u3', 'ucrx', 'ucry', 'ucrz', 'ucx', 'ucy', 'ucz', 'y', 'z']
    # left out on purpose: cswap, dcx, fredkin, iswap, mcmt, ms, rxx, ryy, rzx, rzz, swap, as those have two targets

    def __init__(self, extra_gates = []):
        # list of gates names to add to known_gates + bool if qfree (arguments have to be of the form (ctrl*, target))
        self.extra_qfree_gates = []
        self.extra_non_qfree_gates = []
        for (gate, is_qfree) in extra_gates:
            if is_qfree:
                self.extra_qfree_gates.append(gate.name)
            else:
                self.extra_non_qfree_gates.append(gate.name)
        pass
       

    def _isKnownInstruction(self, instruction):
        if instruction.name in self.extra_qfree_gates or instruction.name in self.extra_non_qfree_gates:
            return True
        if instruction.name in ConverterDependencyGraph.known_qfree_gates or instruction.name in ConverterDependencyGraph.known_non_qfree_gates:
            return True
        return False

    def _decomposeDAGToKnownGates(self, dag):
        unseen_gates = True
        while(unseen_gates):
            unseen_gates = False
            old_dag_nodes = dag.op_nodes()
            for node in old_dag_nodes:
                if not self._isKnownInstruction(node.op):
                    unseen_gates = True
                    if not self._decomposeNodeOnDAG(node, dag):
                        return None
        return dag

    def _simplUGates(self, dag):
        dag_nodes = dag.op_nodes()
        for node in dag_nodes:
            if node.op.name == 'u1' and node.op.params[0] == 0:
                node.op = IGate()
        for node in dag_nodes:
            if node.op.name == 'u' and node.op.params[0] == 0 and node.op.params[1] == 0 and node.op.params[2] == 0.0: #detects Id gates that have been implemented with u
                node.op = IGate()
        return dag

    def _decomposeNodeOnDAG(self, node, dag):
        # we cannot use qiskit.transpiler.passes.Decompose, since any custom gate is of type Instruction, and 
        # Decompose checks the type, so no way to decompose only those custom gates
        if not node.op.definition:
            print("could not deocmp " + str(node)+ " and op " + str(node.op.name))
            return False
        node_decomposition = DAGCircuit()
        qreg = set()
        creg = set()
        for instruction in node.op.definition:
            for qubit in instruction[1]:
                if not qubit.register in qreg:
                    node_decomposition.add_qreg(qubit.register)
                    qreg.add(qubit.register)
            for cbit in instruction[2]:
                 if not cbit.register in creg:
                    node_decomposition.add_creg(cbit.register)
                    creg.add(cbit.register)
        
        for instruction in node.op.definition:
            node_decomposition.apply_operation_back(*instruction)
        
        dag.substitute_node_with_dag(node, node_decomposition)
        return True

    def dagToDepGraph(self, dag):
        dag = self._decomposeDAGToKnownGates(dag)
        dag = self._simplUGates(dag)
        if dag is None:
            print("Could not decompose to known gates")
            return None

        dep_g = DependencyGraph(self.extra_qfree_gates, self.extra_non_qfree_gates)
        latest_node_on_wire = {}

        for dag_node in dag.topological_nodes():
            if isinstance(dag_node, DAGInNode):
                wire = dag_node.wire
                node = Node(wire.register,
                            wire.index,
                            InitGate(),
                            0, 0)
                latest_node_on_wire[node.variable_name] = node
                dep_g.addRootNode(node)

            elif isinstance(dag_node, DAGOpNode):
                modified_qubit = dag_node.qargs[-1]
                wire_name = Node.wireName(modified_qubit.register, modified_qubit.index)

                assert self._isKnownInstruction(dag_node.op)
                assert latest_node_on_wire.get(wire_name) is not None

                previous_node_on_wire = latest_node_on_wire[wire_name]
                node = Node(
                    modified_qubit.register,
                    modified_qubit.index,
                    dag_node.op,
                    previous_node_on_wire.value_id + 1,
                    0,
                )
                dep_g.addNode(node)
                dep_g.connectConsumedNodes(previous_node_on_wire, node)
                latest_node_on_wire[node.variable_name] = node

                for qarg in dag_node.qargs[:-1]:
                    wire_name_dep = Node.wireName(qarg.register, qarg.index)
                    ctrl_node = latest_node_on_wire[wire_name_dep]
                    dep_g.connectDependencyNodes(ctrl_node, node)

            elif isinstance(dag_node, DAGOutNode):
                continue

        return dep_g

    
    def circuit_to_nx_depgraph(self, circuit) -> nx.MultiDiGraph:
        dag = circuit_to_dag(circuit)
        dep_g = self.dagToDepGraph(dag)
        if dep_g is None:
            return None
        return dep_g.to_networkx()

    def _getQubit(self, node, ancilla_correspondance):
        if not isinstance(node.register, AncillaRegister):
            return Qubit(node.register, node.index)
        (reg, ind) = ancilla_correspondance[(node.register, node.index)]
        return Qubit(reg, ind)



def avg_ancilla_dependency(qc: QuantumCircuit) -> int:
    conv = ConverterDependencyGraph(extra_gates=[])
    G = conv.circuit_to_nx_depgraph(qc)
    if G is None:
        return 0

    ancilla_wires = sorted({
        (q.register.name, q.index)
        for q in qc.qubits
        if isinstance(q.register, AncillaRegister)
    })

    if not ancilla_wires:
        return 0

    nodes_by_wire: dict[tuple[str, int], list] = {}
    for n, data in G.nodes(data=True):
        w = (data["register_name"], data["index"])
        nodes_by_wire.setdefault(w, []).append(n)

    wire_scores: list[int] = []

    for w in ancilla_wires:
        nodes = nodes_by_wire.get(w, [])
        score = 0
        for n in nodes:
            data_n = G.nodes[n]
            gate_name = data_n.get("gate_name")

            for _, v, key, edata in G.out_edges(n, keys=True, data=True):
                et = edata.get("etype")
                if et == "a":
                    continue

                v_data = G.nodes[v]
                w_to = (v_data["register_name"], v_data["index"])

                if w_to != w:
                    score += 1

        wire_scores.append(score)

    if not wire_scores:
        return 0

    avg_score = 1.0 * sum(wire_scores) // len(ancilla_wires)
    return sum(wire_scores), avg_score, max(wire_scores)


def _score_from_control_node(G: nx.MultiDiGraph, start_node, level: int) -> int:
    if level <= 0:
        return 0

    total = 0
    frontier = {start_node}
    is_change_layer = True

    for cur_level in range(1, level + 1):
        if not frontier:
            break

        next_frontier = set()

        if is_change_layer:
            for u in frontier:
                current = u
                while True:
                    succs_c = [
                        v
                        for _, v, k, edata in G.out_edges(
                            current, keys=True, data=True
                        )
                        if edata.get("etype") == "c"
                    ]
                    if not succs_c:
                        break
                    for v in succs_c:
                        next_frontier.add(v)
                        current = v
        else:
            for u in frontier:
                u_data = G.nodes[u]
                u_wire = (u_data["register_name"], u_data["index"])

                for _, v, k, edata in G.out_edges(u, keys=True, data=True):
                    if edata.get("etype") != "d":
                        continue
                    v_data = G.nodes[v]
                    v_wire = (v_data["register_name"], v_data["index"])
                    if v_wire == u_wire:
                        continue
                    total += 1
                    next_frontier.add(v)

        frontier = next_frontier
        is_change_layer = not is_change_layer

    return total


def avg_ancilla_input_dependency(qc: QuantumCircuit, level: int) -> int:
    if level <= 0:
        return 0

    conv = ConverterDependencyGraph(extra_gates=[])
    G = conv.circuit_to_nx_depgraph(qc)
    if G is None:
        return 0

    ancilla_wires = sorted({
        (q.register.name, q.index)
        for q in qc.qubits
        if isinstance(q.register, AncillaRegister)
    })

    if not ancilla_wires:
        return 0

    nodes_by_wire: dict[tuple[str, int], list] = {}
    for n, data in G.nodes(data=True):
        w = (data["register_name"], data["index"])
        nodes_by_wire.setdefault(w, []).append(n)

    wire_scores: list[int] = []

    for w in ancilla_wires:
        nodes = nodes_by_wire.get(w, [])
        score = 0

        for n in nodes:
            data_n = G.nodes[n]
            gate_name = data_n.get("gate_name")

            if gate_name in ("init", "deallocate", None):
                continue
            

            for u, _, k, edata in G.in_edges(n, keys=True, data=True):
                if edata.get("etype") != "d":
                    continue
                control_node = u
                score += _score_from_control_node(G, control_node, level)

        wire_scores.append(score)

    if not wire_scores:
        return 0

    avg_score = 1.0 * sum(wire_scores) // len(ancilla_wires)
    return sum(wire_scores), avg_score, max(wire_scores)

def has_cross_ancilla_cycle(qc: QuantumCircuit) -> int:

    conv = ConverterDependencyGraph(extra_gates=[])
    G = conv.circuit_to_nx_depgraph(qc)
    if G is None:
        return 0

    # 1) ancilla wires
    ancilla_wires = sorted({
        (q.register.name, q.index)
        for q in qc.qubits
        if isinstance(q.register, AncillaRegister)
    })
    ancilla_wire_set = set(ancilla_wires)

    if not ancilla_wires:
        return 0
    
    # helper: node -> wire (if it is a wire node)
    def wire_of(n):
        data = G.nodes[n]
        rn = data.get("register_name")
        idx = data.get("index")
        if rn is None or idx is None:
            return None
        return (rn, idx)

    # 2) build H: ignore 'a'; make 'c' bidirectional; keep direction for others
    H = nx.DiGraph()
    for n, data in G.nodes(data=True):
        H.add_node(n, **data)

    for u, v, k, edata in G.edges(keys=True, data=True):
        et = edata.get("etype")
        if et == "a":
            continue
        if et == "c":
            H.add_edge(u, v)

            w = wire_of(u)  # = wire_of(v) for 'c' edges in your construction
            if w is not None and w not in ancilla_wire_set:
                H.add_edge(v, u)  # only working-wire target edges become bidirected
        else:
            H.add_edge(u, v)

    # 3) node -> wire
    wire_of_node = {
        n: (data["register_name"], data["index"])
        for n, data in H.nodes(data=True)
        if "register_name" in data and "index" in data
    }

    # 4) SCC scan: early exit
    for comp in nx.strongly_connected_components(H):
        if len(comp) <= 1:
            continue

        wires_in_comp = {wire_of_node[n] for n in comp if n in wire_of_node}
        if len(wires_in_comp) < 2:
            continue

        anc_in  = wires_in_comp & ancilla_wire_set
        work_in = wires_in_comp - ancilla_wire_set
        if anc_in and work_in:
            return 1

    return 0




def _compress_multidigraph_to_digraph(Gm: nx.MultiDiGraph) -> nx.DiGraph:
    H = nx.DiGraph()
    for n, data in Gm.nodes(data=True):
        H.add_node(n, **data)

    def add_etype(u, v, t):
        if H.has_edge(u, v):
            H[u][v]["etypes"].add(t)
        else:
            H.add_edge(u, v, etypes=set([t]))

    for u, v, _k, edata in Gm.edges(keys=True, data=True):
        t = edata.get("etype")
        if t is None or t == "a":
            continue
        add_etype(u, v, t)

    return H


def _remove_etype(H: nx.DiGraph, u, v, t: str):
    if not H.has_edge(u, v):
        return
    etypes = H[u][v].get("etypes", set())
    if t in etypes:
        etypes.remove(t)
    if not etypes:
        H.remove_edge(u, v)
    else:
        H[u][v]["etypes"] = etypes


def _add_etype(H: nx.DiGraph, u, v, t: str):
    if H.has_edge(u, v):
        H[u][v].setdefault("etypes", set()).add(t)
    else:
        H.add_edge(u, v, etypes=set([t]))


# --------- 2) Node attribute helpers ---------

def _node_wire(H: nx.DiGraph, n):
    d = H.nodes[n]
    return (d.get("register_name"), d.get("index"))

def _node_vid(H: nx.DiGraph, n):
    return H.nodes[n].get("value_id", None)

def _node_gate(H: nx.DiGraph, n):
    return H.nodes[n].get("gate_name", None)

def _ancilla_wires_from_qc(qc: QuantumCircuit):
    anc = set()
    for q in qc.qubits:
        if isinstance(q.register, AncillaRegister):
            anc.add((q.register.name, q.index))
    return sorted(anc)

def _nodes_by_wire(H: nx.DiGraph):
    mp = {}
    for n, data in H.nodes(data=True):
        w = (data.get("register_name"), data.get("index"))
        mp.setdefault(w, []).append(n)
    return mp


# --------- 3) Core: score(n) = #deps m such that (n,m) share a cycle in modified graph ---------

def _safe_copy_digraph_with_detached_etypes(H: nx.DiGraph) -> nx.DiGraph:
    H2 = nx.DiGraph()

    for n, data in H.nodes(data=True):
        H2.add_node(n, **data)

    for u, v, data in H.edges(data=True):
        new_data = dict(data)
        if "etypes" in new_data:
            new_data["etypes"] = set(new_data["etypes"])  # 关键：断开共享
        H2.add_edge(u, v, **new_data)

    return H2


def avg_ancilla_input_dependency_gated_by_cycle(qc: QuantumCircuit, level: int):
    if level <= 0:
        return 0, 0, 0

    conv = ConverterDependencyGraph(extra_gates=[])
    G_multi = conv.circuit_to_nx_depgraph(qc)
    if G_multi is None:
        return 0, 0, 0

    H0 = _compress_multidigraph_to_digraph(G_multi)

    # ancilla wires
    ancilla_wires = sorted({
        (q.register.name, q.index)
        for q in qc.qubits
        if isinstance(q.register, AncillaRegister)
    })
    if not ancilla_wires:
        return 0, 0, 0

    nodes_by_wire_multi: dict[tuple[str, int], list] = {}
    for n, data in G_multi.nodes(data=True):
        w = (data["register_name"], data["index"])
        nodes_by_wire_multi.setdefault(w, []).append(n)

    by_wire_H0 = _nodes_by_wire(H0)
    sorted_nodes_on_wire = {}
    for w, nodes in by_wire_H0.items():
        nodes2 = [n for n in nodes if isinstance(_node_vid(H0, n), int)]
        nodes2.sort(key=lambda x: _node_vid(H0, x))
        sorted_nodes_on_wire[w] = nodes2

    wire_scores: list[int] = []

    def deps_of_n_in_original_H0(n):
        deps = []
        for u, _, edata in H0.in_edges(n, data=True):
            if "d" in edata.get("etypes", set()):
                deps.append(u)
        return deps

    def build_scc_for_n(n, anc_wire):
        vid_n = _node_vid(H0, n)
        if not isinstance(vid_n, int):
            return None, None, None

        Hn = _safe_copy_digraph_with_detached_etypes(H0)

        in_edges = list(Hn.in_edges(n, data=True))
        out_edges = list(Hn.out_edges(n, data=True))

        for u, _, edata in in_edges:
            if "d" in edata.get("etypes", set()):
                _remove_etype(Hn, u, n, "d")
                _add_etype(Hn, n, u, "d")

        for _, v, edata in out_edges:
            if "d" in edata.get("etypes", set()):
                _remove_etype(Hn, n, v, "d")
                _add_etype(Hn, v, n, "d")

        seq = [x for x in sorted_nodes_on_wire.get(anc_wire, []) if _node_vid(Hn, x) >= vid_n]
        for a, b in zip(seq, seq[1:]):
            if Hn.has_edge(a, b) and ("c" in Hn[a][b].get("etypes", set())):
                _add_etype(Hn, b, a, "c")

        comps = list(nx.strongly_connected_components(Hn))
        comp_id = {}
        comp_size = {}
        for i, comp in enumerate(comps):
            comp_size[i] = len(comp)
            for x in comp:
                comp_id[x] = i

        cid_n = comp_id.get(n, None)
        return comp_id, comp_size, cid_n

    for w in ancilla_wires:
        nodes_multi = nodes_by_wire_multi.get(w, [])
        score_w = 0

        for n in nodes_multi:
            gate_name = G_multi.nodes[n].get("gate_name")
            if gate_name in ("init", "deallocate", None):
                continue

            deps = deps_of_n_in_original_H0(n)
            if not deps:
                continue

            comp_id, comp_size, cid_n = build_scc_for_n(n, w)
            if cid_n is None:
                continue
            if comp_size.get(cid_n, 1) <= 1:
                continue

            for m in deps:
                cid_m = comp_id.get(m, None)
                if cid_m is None or cid_m != cid_n:
                    continue
                score_w += _score_from_control_node(G_multi, m, level)

        wire_scores.append(score_w)

    if not wire_scores:
        return 0, 0, 0

    sum_score = sum(wire_scores)
    avg_score = sum_score // len(ancilla_wires)
    max_score = max(wire_scores)
    # print(f"{sum_score}, {avg_score}, {max_score}")
    return sum_score, avg_score, max_score

def dep_cyc(circ: QuantumCircuit):
    # _, _, max_dep = avg_ancilla_input_dependency(circ, 10)


    _, _, maxsocre = avg_ancilla_input_dependency_gated_by_cycle(circ, 10)


    cyc = has_cross_ancilla_cycle(circ)
    return maxsocre, cyc