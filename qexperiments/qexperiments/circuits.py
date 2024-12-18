from qiskit.quantum_info import Operator
from qiskit.converters import circuit_to_dag, dag_to_circuit
from collections import OrderedDict

def trace_of_circuit(circuit):
    """
    Compute trace by converting circuit to unitary.
    If circuit is not unitary some kind of error will be thrown.
    """
    op = Operator.from_circuit(circuit)
    opmat = op.to_matrix()
    dsum = sum(opmat.diagonal())
    return dsum

def remove_idle_qwires(circ):
    """Remove idle qubits from circuit"""
    dag = circuit_to_dag(circ)

    idle_wires = list(dag.idle_wires())
    for w in idle_wires:
        dag._remove_idle_wire(w)
        dag.qubits.remove(w)

    dag.qregs = OrderedDict()

    return dag_to_circuit(dag)
