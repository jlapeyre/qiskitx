import json
import pickle
from qiskit_ibm_runtime import RuntimeEncoder
from qiskit_ibm_runtime import RuntimeDecoder

def save_job_result(job, fname):
    with open(fname, "w") as file:
        json.dump(job.result(), file, cls=RuntimeEncoder)

def read_job_result(fname):
    with open(fname, "r") as file:
        result = json.load(file, cls=RuntimeDecoder)
        return result

def json_dump(thing, fname):
    with open(fname, "w") as file:
        json.dump(thing, file)

def json_load(fname):
    with open(fname, "r") as file:
        return json.load(file)

def pickle_dump(data, fname):
    with open(fname, "wb") as file:
        pickle.dump(data, file)

def pickle_load(fname):
    with open(fname, "rb") as file:
       data = pickle.load(file)
    return data

from typing import Any

# This is not bullet-proof. But works for what we have so far
def convert_to_serializable(obj: Any) -> Any:
    if hasattr(obj, "__dict__"):
        return dict([(k, convert_to_serializable(v)) for k, v in vars(obj).items()])
    if isinstance(obj, list):
        return [convert_to_serializable(el) for el in obj]
    return obj
