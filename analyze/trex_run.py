from qiskit_ibm_runtime import QiskitRuntimeService

# Code for running and analyzing experiments
import trex
from qexperiments.runtime import backends

# BACKEND_NAME = 'ibm_cusco'
BACKEND_NAME = 'ibm_nazca'
# BACKEND_NAME = 'ibm_brisbane'
# BACKEND_NAME = 'ibm_kyiv'

# Options to EstimatorOptions
OPTIONS_LIST = [
    # Run job with no error mitigation
    {'environment': {'job_tags': ['No error mitigation']}},

    {'resilience': {'measure_mitigation': True}, 'dynamical_decoupling': {'enable': False},
     'environment': {'job_tags': ['TREX']}},
]

TAGS = ['GJL']

# Set the input parameters for the experiments.
# Set our input options list to the list defined above.
expt_input = trex.ExptInput(
    backend_name = BACKEND_NAME,
    num_qubits = 50,
    trotter_steps = 2,
    tags = TAGS.copy(), # tags merged in for each job
    options_list = OPTIONS_LIST,)

# Connect to the service
# Token and instance info is stored in local file or ENV variables
service = QiskitRuntimeService()

# Instantiate a class for organizing input and output.
expt = trex.Expt(service=service, expt_input=expt_input)

# Build and store the circuit, observable, etc.
expt.build_isa_circuit()

# Perform a dry run of experiments. Validates OPTIONS_LIST with backend
# expt.run_batch(additive_options = False, dry_run = True)
# expt.run_batch(additive_options = False, dry_run = False)
