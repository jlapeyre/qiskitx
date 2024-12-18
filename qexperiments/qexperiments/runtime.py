### Enhancements or utilities for qiskit_ibm_runtime

from typing import List

from qiskit_ibm_runtime.utils import (
    validate_isa_circuits,
    validate_job_tags,
    validate_estimator_pubs
)

# These are backends available for enablement
BACKEND_NAMES_CACHED = ['ibm_kyiv', 'ibm_cusco', 'ibm_brisbane', 'ibm_nazca', 'ibm_sherbrooke', 'ibm_torino']

# I was unable to find a way to filter out test backends using service.backends(...)
# (You can probably pass a lambda somewhere)
# If you ask for least_busy, you always get the test backend.
# This function addresses these problems.
def backends(service, bybusy=False, pending=False, names=False, **kwargs):
    """Return a list of all backends except test backends.

    Args:
       service: An instance of ``QiskitRuntimeService``

       bybusy: If ``True``, sort the list of backends in increasing order of number of pending
         jobs.

       pending: If ``True``, return a list of tuples: ``(backend, num pending jobs)`` sorted in
         increasing order of number of pending jobs. Sorting is performed regardless of the value
         of ``bybusy``.

       names: If ``True`` names of backends are returned as strings rather than backend instances.

       **kwargs: Any ``kwargs`` that can be passed to QiskitRuntimeService.backends().
    """
    bkends = [b for b in service.backends(**kwargs) if not b.name.startswith('test')]
    if names:
        bkends_out = [b.name for b in bkends]
    else:
        bkends_out = bkends
    if bybusy or pending:
        pairs = list(zip(bkends_out, pending_jobs(bkends))) # Tuples: (bkend, no. jobs)
        pairs.sort(key=lambda x: x[1]) # Least busy first
        if pending:
            return pairs  # Return tuples: (bkend, num pending_jobs)
        return [p[0] for p in pairs] # Only return backends, not pending_jobs
    return bkends_out # Faster, because we don't fetch number of pending jobs.

def pending_jobs(bkends: List):
    """Return a list of number of pending jobs corresponding to the list of backends ``bkends``.
    """
    return [b.status().pending_jobs for b in bkends]

# Backends available in enablement

# I looked around it slack channels. It seems that people have asked to add this to metadata
# in the backends. But there was resistance.
# CLOPS in thousands
# Thu Nov 21 11:55:28 PM EST 2024
CLOPS = {
    'ibm_nazca': 29,
    'ibm_sherbrooke': 30,
    'ibm_torino': 200,
    'ibm_kyiv': 30,
    'test_eagle_us-east': 0,
    'ibm_cusco': 5 ,
    'ibm_brisbane': 30,
}
"""CLOPS values for backends in thousands"""
