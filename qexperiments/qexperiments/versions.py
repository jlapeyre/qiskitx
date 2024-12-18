import platform
import qiskit
import qiskit_ibm_runtime

# I think the runtime actually does some or all of this.
# So this may not be useful after all.
class Versions:
    """Fetch versions of relevant software components.

    Qiskit has something like this built in. But I can't find it.
    """

    def __init__(self):
        self.python_version = platform.python_version()
        self.qiskit_version = qiskit.version.__version__
        self.qiskit_ibm_runtime_version = qiskit_ibm_runtime.version.__version__

    def as_dict(self):
        return {'python': self.python_version, 'qiskit': self.qiskit_version,
                'qiskit_ibm_runtime': self.qiskit_ibm_runtime_version}
