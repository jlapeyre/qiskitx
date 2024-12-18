from qiskit_ibm_runtime import QiskitRuntimeService

# Code for running and analyzing experiments
import batch_expt
from qexperiments.runtime import backends
from jobs_io import pickle_dump, pickle_load

# BACKEND_NAME = 'ibm_cusco'
# BACKEND_NAME = 'ibm_nazca'
# BACKEND_NAME = 'ibm_brisbane'
BACKEND_NAME = 'ibm_sherbrooke'
# BACKEND_NAME = 'ibm_kyiv'

TREX_OPTIONS =  {'resilience': {'measure_mitigation': True}, 'dynamical_decoupling': {'enable': False},
     'environment': {'job_tags': ['TREX']}}

# Options to EstimatorOptions
OPTIONS_LIST = [
    TREX_OPTIONS for _ in range(30)
]

TAGS = ['GJL']

# Connect to the service if not already done.
# `service` is global.
# Token and instance info is stored in local file or ENV variables, so we can
# simply call QiskitRuntimeService()
try:
    isinstance(service, QiskitRuntimeService)
except:
    service = QiskitRuntimeService()

def make_expt_inputs():
    expt_inputs = []
    for trotter_steps in [4,]:
        for num_qubits in [50,]:
            circ_input = batch_expt.CircInput(
                backend_name = BACKEND_NAME,
                num_qubits = num_qubits,
                trotter_steps = trotter_steps,
            )
            runtime_input = batch_expt.RuntimeInput(
                tags=TAGS.copy(),
                options_list = OPTIONS_LIST,
            )
            expt_input = batch_expt.ExptInput(circ_input, runtime_input)
            expt_inputs.append(expt_input)

    return expt_inputs

expt_inputs_6 = make_expt_inputs()
expt_6 = batch_expt.BatchExpt(expt_inputs_6)

expt_6.build_isa_objects(service)
expt_6.run_batch(dry_run=True)
expt_6.run_batch(dry_run=False)
expt_6_info = expt_6.info()
pickle_dump(expt_6_info, "expt_6_info.p")
