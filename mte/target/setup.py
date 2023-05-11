import os
import pickle
import shutil

env_root = os.path.dirname(__file__)
restricted_dir = os.path.join(env_root, "restricted")
allowed_dir = os.path.join(env_root, "allowed")
helper_dir = os.path.join(env_root, "helper")
results_dir = os.path.join(env_root, "results")
result_details_dir = os.path.join(results_dir, "details")

def clear_dir(path):
    """
    Removes whole node.

    @param path: node to remove.
    """
    shutil.rmtree(path, ignore_errors=True)

def setup_env():
    """
    Creates and clears required directory structure.
    """
    # Remove old results if present
    try:
        os.remove(os.path.join(env_root, "results"))
        os.remove(os.path.join(env_root, "results_details"))
    except:
        pass

    # Clear directories
    clear_dir(results_dir)
    clear_dir(result_details_dir)
    clear_dir(restricted_dir)
    clear_dir(allowed_dir)
    clear_dir(helper_dir)

    # Create results dir
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    # Create result details dir
    if not os.path.exists(result_details_dir):
        os.makedirs(result_details_dir)

    # Create restricted dir
    if not os.path.exists(restricted_dir):
        os.makedirs(restricted_dir)

    # Create allowed dir
    if not os.path.exists(allowed_dir):
        os.makedirs(allowed_dir)

    # Create allowed dir
    if not os.path.exists(helper_dir):
        os.makedirs(helper_dir)

def validate_env():
    """
    Validates environment.
    """
    if not os.path.exists(restricted_dir):
        raise FileNotFoundError("Missing restricted dir.")

    if not os.path.exists(helper_dir):
        raise FileNotFoundError("Missing helper dir.")

    if not os.path.exists(allowed_dir):
        raise FileNotFoundError("Missing allowed dir.")

    required_path = os.path.join(env_root, "medusa-template.conf")
    if not os.path.exists(required_path):
        raise FileNotFoundError("Missing configuration: medusa-template.conf")

    required_path = os.path.join(env_root, "constable.conf")
    if not os.path.exists(required_path):
        raise FileNotFoundError("Missing configuration: constable.conf")

def load_tests():
    """
    Loads tests from pickle file.

    @return: loaded tests.
    """
    file_path = os.path.join(env_root, "local.pickle")
    tests = None

    with open(file_path, "rb") as f:
        tests = pickle.load(f)

    return tests

def has_key(dictionary, key):
    """
    helper function to check if dictionary has valid key.

    @param dictionary: dict to check.
    @param key: key to validate.
    @return: if key exists and has valid value.
    """
    if not key in dictionary:
        return False

    item = dictionary[key]
    if item is None:
        return False

    if isinstance(item, list) and len(item) == 0:
        return False

    return True