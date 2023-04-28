import os
import shutil
import pickle


env_root = os.path.dirname(__file__)
restricted_path = os.path.join(env_root, "restricted")
allowed_path = os.path.join(env_root, "allowed")

def clear_dir(path):
    # Get a list of all the files in the folder
    shutil.rmtree(path, ignore_errors=True)

def setup_env():
    # create restricted
    clear_dir(restricted_path)
    clear_dir(allowed_path)

    if not os.path.exists(restricted_path):
        os.makedirs(restricted_path)
    else:
        clear_dir(restricted_path)

    # create allowed
    if not os.path.exists(allowed_path):
        os.makedirs(allowed_path)
    else:
        clear_dir(allowed_path)

def validate_env():
    if not os.path.exists(restricted_path):
        raise FileNotFoundError("Missing restricted dir.")

    if not os.path.exists(allowed_path):
        raise FileNotFoundError("Missing allowed dir.")

    required_path = os.path.join(env_root, "medusa.conf")
    if not os.path.exists(required_path):
        raise FileNotFoundError("Missing configuration: medusa.conf")

    required_path = os.path.join(env_root, "constable.conf")
    if not os.path.exists(required_path):
        raise FileNotFoundError("Missing configuration: constable.conf")

    # required_path = os.path.join(env_root, "tests.pickle")
    # if os.path.exists(required_path):
    #     raise FileNotFoundError("Missing tests.")

def load_tests():
    file_path = os.path.join(env_root, "local.pickle")
    tests = None

    with open(file_path, "rb") as f:
        tests = pickle.load(f)

    return tests