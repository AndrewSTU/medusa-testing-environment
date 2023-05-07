import os
import shutil
import pickle


env_root = os.path.dirname(__file__)
restricted_dir = os.path.join(env_root, "restricted")
allowed_dir = os.path.join(env_root, "allowed")
warmup_dir = os.path.join(env_root, "warmup")

def clear_dir(path):
    # Get a list of all the files in the folder
    shutil.rmtree(path, ignore_errors=True)

def setup_env():
    os.chdir(env_root)

    # Remove old results if present
    try:
        os.remove(os.path.join(env_root, "results"))
        os.remove(os.path.join(env_root, "results_details"))
    except:
        pass

    # Clear directories
    clear_dir(restricted_dir)
    clear_dir(allowed_dir)
    clear_dir(warmup_dir)

    # Create restricted dir
    if not os.path.exists(restricted_dir):
        os.makedirs(restricted_dir)

    # Create allowed dir
    if not os.path.exists(allowed_dir):
        os.makedirs(allowed_dir)

    # Create allowed dir
    if not os.path.exists(warmup_dir):
        os.makedirs(warmup_dir)

def validate_env():
    if not os.path.exists(restricted_dir):
        raise FileNotFoundError("Missing restricted dir.")

    if not os.path.exists(allowed_dir):
        raise FileNotFoundError("Missing allowed dir.")

    required_path = os.path.join(env_root, "medusa-template.conf")
    if not os.path.exists(required_path):
        raise FileNotFoundError("Missing configuration: medusa-template.conf")

    required_path = os.path.join(env_root, "constable.conf")
    if not os.path.exists(required_path):
        raise FileNotFoundError("Missing configuration: constable.conf")

def load_tests():
    file_path = os.path.join(env_root, "local.pickle")
    tests = None

    with open(file_path, "rb") as f:
        tests = pickle.load(f)

    return tests

def has_key(dictionary, key):
    if not key in dictionary:
        return False

    item = dictionary[key]
    if item is None:
        return False

    if isinstance(item, list) and len(item) == 0:
        return False

    return True