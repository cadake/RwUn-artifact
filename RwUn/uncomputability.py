from qiskit.circuit import QuantumCircuit, AncillaRegister, AncillaQubit
from RwUn.symbolic import *

def check_injective_when_bit_zero(state: dict, fixed_name: str) -> bool:
    solver = Solver()

    other_inputs = [name for name in state if name != fixed_name]

    inputs1 = {name: Bool(f"{name}_1") for name in other_inputs}
    inputs2 = {name: Bool(f"{name}_2") for name in other_inputs}

    outputs_equal = []

    for out_name, expr in state.items():
        if out_name == fixed_name:
            continue 

        subs1 = [(Bool(name), inputs1[name]) for name in other_inputs]
        subs1.append((Bool(fixed_name), BoolVal(False)))
        replaced1 = substitute(expr, subs1)

        subs2 = [(Bool(name), inputs2[name]) for name in other_inputs]
        subs2.append((Bool(fixed_name), BoolVal(False)))
        replaced2 = substitute(expr, subs2)

        outputs_equal.append(replaced1 == replaced2)

    solver.add(And(outputs_equal))

    input_diff = Or([inputs1[name] != inputs2[name] for name in other_inputs])
    solver.add(input_diff)

    res = solver.check() == unsat

    return solver.check() == unsat

def check_injective_when_bits_zero(state: dict, fixed_names: list[str]) -> bool:
    solver = Solver()

    other_inputs = [name for name in state if name not in fixed_names]

    inputs1 = {name: Bool(f"{name}_1") for name in other_inputs}
    inputs2 = {name: Bool(f"{name}_2") for name in other_inputs}

    outputs_equal = []

    for out_name, expr in state.items():
        if out_name in fixed_names:
            continue 
        subs1 = [(Bool(name), inputs1[name]) for name in other_inputs]
        subs1.extend([(Bool(fn), BoolVal(False)) for fn in fixed_names])
        replaced1 = substitute(expr, subs1)

        subs2 = [(Bool(name), inputs2[name]) for name in other_inputs]
        subs2.extend([(Bool(fn), BoolVal(False)) for fn in fixed_names])
        replaced2 = substitute(expr, subs2)

        outputs_equal.append(replaced1 == replaced2)

    solver.add(And(outputs_equal))

    input_diff = Or([inputs1[name] != inputs2[name] for name in other_inputs])
    solver.add(input_diff)

    res = solver.check() == unsat

    return solver.check() == unsat

def is_clean_uncomputable(C: QuantumCircuit, ancs: AncillaRegister) -> bool:
    state = compute_final_symbolic_state(C)
    names = [qubit_name(anc, C) for anc in ancs]
    return check_injective_when_bits_zero(state, names)

def is_independent_of(state: dict, fixed_name: str) -> bool:
    other_inputs = [name for name in state if name != fixed_name]

    for out_name, expr in state.items():
        if out_name == fixed_name:
            continue
        solver = Solver()

        x = {name: Bool(name) for name in other_inputs}

        subs0 = [(Bool(name), x[name]) for name in other_inputs]
        subs0.append((Bool(fixed_name), BoolVal(False)))
        expr0 = substitute(expr, subs0)

        subs1 = [(Bool(name), x[name]) for name in other_inputs]
        subs1.append((Bool(fixed_name), BoolVal(True)))
        expr1 = substitute(expr, subs1)

        solver.add(expr0 != expr1)

        if solver.check() == sat:
            model = solver.model()
            print(f"{out_name} depends on {fixed_name}：")
            for name in x:
                print(f"  {name} =", model.evaluate(x[name], model_completion=True))
            print(f"  {fixed_name} = 0/1 leads different outputs")
            print("  when fixed=0:", model.evaluate(expr0, model_completion=True))
            print("  when fixed=1:", model.evaluate(expr1, model_completion=True))
            return False

    return True

def is_dirty_uncomputable(C: QuantumCircuit, a: AncillaQubit) -> bool:
    state = compute_final_symbolic_state(C)
    name = qubit_name(a, C)
    return is_independent_of(state, name)