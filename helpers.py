import os
import json
import hashlib
from flatten_dict import flatten



def hash_vals(data):
    keys = sorted([e for e in data])
    hash = hashlib.sha512()
    for key in keys:
        hash.update(str(data[key]).encode())
    digest = hash.hexdigest()
    return digest


def dump_data(data, path):
    with open(path, mode='w') as fl:
        json.dump(data, fl, indent=2, ensure_ascii=False)
        fl.close()


def load_data(path):
    try:
        with open(path, mode='r') as fl:
            data = json.load(fl)
            return data
    except:
        return {}


def compare(a, b):
    keys = set(a.keys()).union(set(b.keys()))
    diff = []
    for key in keys:
            if a.get(key) != b.get(key, 'null'):
                diff.append(key)
    return diff
