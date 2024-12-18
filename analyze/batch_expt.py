# Thu Nov 21 10:50:03 AM EST 2024

# %%
import qiskit_ibm_runtime
from qiskit_ibm_runtime import QiskitRuntimeService, Batch
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.quantum_info import SparsePauliOp, PauliList
from qiskit_ibm_runtime import Batch, EstimatorV2, EstimatorOptions
from typing import List, Optional

import qexperiments.versions

# This is actually called `NoneType`.
# The fact that Python can use `None` for both a type and its single instance gives me vertigo.
NoneType = type(None)

class CircInput:
    def __init__(self, num_qubits: int, trotter_steps: int, backend_name: str,
                 seed_transpiler: Optional[int]=None):
        self.num_qubits = num_qubits
        self.trotter_steps = trotter_steps
        self.backend_name = backend_name
        if seed_transpiler is None:
            self.seed_transpiler = 1234

    def build(self, service):
        isa_circ = ISACirc(self)
        isa_circ.build(service)
        return isa_circ

# This is more than just the ISA circuit. Also observable and backend
class ISACirc:
    def __init__(self, circ_input):
        self.circ_input = circ_input
        # The following are built from inputs
        self.isa_circuit = None
        self.isa_observable = None
        self.backend = None

    def run_job(self, batch: Batch, options: EstimatorOptions):
        """Construct ``pub`` from ``self`` and run under ``batch``.

        Args:
           options: Options to the estimator.
        """
        estimator = EstimatorV2(mode=batch, options=options)
        pub = (self.isa_circuit, self.isa_observable)
        job_id = estimator.run([pub]).job_id
        return job_id

    def build(self, service):
        """Construct the isa_circuit.

        The function that creates the reference circuit is hardcoded here.
        The observable is hardcoded to measuring all Z-basis measurements.
        """
        num_qubits = self.circ_input.num_qubits
        trotter_steps = self.circ_input.trotter_steps
        seed_transpiler = self.circ_input.seed_transpiler
        backend = self.ensure_backend(service)

        _circuit = RefCircuit(num_qubits=num_qubits, trotter_steps=trotter_steps)
        print_2q_info(_circuit)

        _pass_manager = generate_preset_pass_manager(
            optimization_level=3, backend=backend, seed_transpiler=seed_transpiler
        )
        isa_circuit = _pass_manager.run(_circuit)
        _observable = SparsePauliOp('Z'*num_qubits)
        isa_observable = _observable.apply_layout(isa_circuit.layout)

        self.isa_circuit = isa_circuit
        self.isa_observable = isa_observable

    # If we expect the backend is already cached, then `service` can be `None`.
    def ensure_backend(self, service: Optional[QiskitRuntimeService] = None):
        """Return the backend. Fetch from `service` if not already cached."""
        if self.backend is None:
            if self.circ_input.backend_name is None:
                raise(ValueError("No backend_name set in expt: Expt"))
            if service is None:
                raise(ValueError("Can't create backend object without `service`"))
            backend = service.backend(self.circ_input.backend_name)
            self.backend = backend
        return self.backend


def RefCircuit(num_qubits, trotter_steps):
    qc = QuantumCircuit(num_qubits)
    for step in range(trotter_steps):
        for qubit in range(num_qubits):
            qc.x(qubit)
        for qubit in range(0, num_qubits - 1, 2):
            qc.cx(qubit, qubit + 1)
        for qubit in range(1, num_qubits - 1, 2):
            qc.cx(qubit, qubit + 1)
    return qc

# This only works if gates are `cx`
def print_2q_info(circuit):
    print('Depth of two-qubit gates: ', circuit.depth(lambda x: len(x.qubits) == 2))
    print('Number of two-qubit gates: ', circuit.count_ops()['cx'])

class RuntimeInput:
    """Input parameters controlling Qiskit runtime.

    Other parameters, for example those specifying the circuit are not included here.

    Args:
       tags: A list of job tags that will be merged with tags for each job.
    """
    def __init__(self,
                 tags: Optional[List] = None,
                 options_list: Optional[List] = None, default_shots = None, resilience_level = None,
                 ):
        if default_shots is None:
            default_shots = 10_000
        if resilience_level is None:
            resilience_level = 0
        if tags is None:
            tags = []

        self.options_list = options_list # list of dicts of options to EstimatorOptions
        self.default_shots = default_shots
        self.resilience_level = resilience_level
        self.tags = tags

    def set_estimator_options(self, opts_dict: dict, options: [NoneType, EstimatorOptions] = None):
        """Set or update backend estimator options.

        Args:
            opts_dict: A dictionary of options to ``EstimatorOptions``. For example
                 ``{'dynamical_decoupling': {'enable': True, 'sequence_type': "XpXm"},}``

            options: If ``None`` then instantiate a new ``EstimatorOptions`` and populate it
                 with ``opts_dict``. Otherwise, update ``options``. The resulting ``options`` is returned.
        """
        default_shots = self.default_shots
        resilience_level = self.resilience_level
        tags = self.tags
        if options is None:
            options = EstimatorOptions(default_shots=default_shots, resilience_level=resilience_level)
        # Update with tags particular to this job
        options.update(**opts_dict)
        # Merge "global" tags. Tags added to every job.
        _merge_job_tags(options, tags)

        return options

class ExptInput:
    """Input parameters and data for running experiment
    """
    def __init__(self, circ_input: CircInput, runtime_input: RuntimeInput):
        self.circ_input = circ_input
        self.runtime_input = runtime_input

class BatchExpt:
    def __init__(self, expt_inputs: List[ExptInput]):
        self.expt_inputs = expt_inputs

        self.versions = qexperiments.versions.Versions()
        # Following will be created later
        self.session_id = None
        self.batch_details = None
        self.job_ids = None
        self.expts = [Expt(inp) for inp in self.expt_inputs]
        self.backend = None # set in build_isa_objects

    def build_isa_objects(self, service):
        for expt in self.expts:
            expt.build_isa_objects(service)
        self.backend = self.expts[0].isa_objects.backend

    def run_batch(self, additive_options: bool = False, dry_run: bool = False):
        """Instantiate and run jobs in a `Batch`. Each element in the list
           ``self.expt_input.options_list`` is a of options for one job.

        Args:
          additive_options: if `True` then the options accumulate for each job.
            Otherwise, each job runs with only the options from its corresponding
            element in ``options_list``.

          dry_run: If `True`, everything is executed except ``self.run_job``. This is useful
            for validating the options in ``options_list`` without actually starting a job
            on the backend.

        """
        if self.job_ids is not None and len(self.job_ids) != 0:
            raise Exception(f"job_ids has already been filled, or is not `None`, length is {len(self.job_ids)}")
        backend = self.backend # self.ensure_backend()

        job_ids = []
        with Batch(backend=backend) as batch:
            for expt in self.expts:
                expt.batch_append(batch, additive_options, dry_run)
                job_ids.extend(expt.job_ids)

            self.job_ids = job_ids
            self.session_id = batch.session_id
            self.batch_details = batch.details()
            print("Batch info")
            print_batch_info(batch)

    def info(self):
        return BatchInfo(self.expt_inputs, self.session_id, self.batch_details, self.job_ids, self.versions)

class BatchInfo:
    def __init__(self, expt_inputs, session_id, batch_details, job_ids, versions):
        self.expt_inputs = expt_inputs
        self.session_id = session_id
        self.batch_details = batch_details
        self.job_ids = job_ids
        self.versions = versions

    # hmm. not a great name for this method
    def job_ids_by_expt(self):
        job_ids_list = []
        ind = 0
        for inp in self.expt_inputs:
            ind_offset = len(inp.runtime_input.options_list)
            job_ids_list.append(self.job_ids[ind:ind+ind_offset])
            ind += ind_offset
        return job_ids_list

class Expt:
    """Capture relevant data and metadata while preparing and running experiment.

    The input parameters and data is also stored in attribute `expt_input`.
    """

    def __init__(self, expt_input: ExptInput):
        self.expt_input = expt_input
        self.isa_objects = None
        self.job_ids = None

    def build_isa_objects(self, service):
        self.isa_objects = self.expt_input.circ_input.build(service)

    def batch_append(self, batch: Batch, additive_options: bool = False, dry_run: bool =False):
        """Append, or add jobs to `batch`. Each element in the list
           ``self.expt_input.options_list`` is a of options for one job.

        Args:
          additive_options: if `True` then the options accumulate for each job.
            Otherwise, each job runs with only the options from its corresponding
            element in ``options_list``.

          dry_run: If `True`, everything is executed except ``self.run_job``. This is useful
            for validating the options in ``options_list`` without actually starting a job
            on the backend.

        """
        options_list = self.expt_input.runtime_input.options_list
        if self.job_ids is not None and len(self.job_ids) != 0:
            raise Exception(f"job_ids has already been filled, or is not `None`, length is {len(self.job_ids)}")
        options = self.expt_input.runtime_input.set_estimator_options({})
        job_ids = []
        for opts_dict in options_list:
            print(f"Running job: options {opts_dict}")
            if  additive_options:
                options = self.expt_input.runtime_input.set_estimator_options(opts_dict, options)
            else:
                options = self.expt_input.runtime_input.set_estimator_options(opts_dict)
            if not dry_run:
                job_id = self.isa_objects.run_job(batch, options)
                # NOTE! We call the func: job_id()
                # This returns a string of the id hash
                # We don't want to save the function itself.
                # Among other reasons, it is not pickleable.
                job_ids.append(job_id())

        self.job_ids = job_ids

def print_batch_info(batch: Batch):
    print(f"Session ID: {batch.session_id}")
    print(f"Status: {batch.status()}")
    print(f"Details: {batch.details()}")

# Add the elements of list of tags `tags` to the
# list of tags in options.environment.job_tags
def _merge_job_tags(options, tags):
    if len(tags) == 0:
        return
    if options.environment.job_tags is None:
        options.environment.job_tags = tags.copy()
    else:
        options.environment.job_tags.extend(tags.copy())
