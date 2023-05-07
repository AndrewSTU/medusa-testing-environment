import os
import subprocess
import time

from asynchronous_reader import Reader
from setup import env_root, has_key, load_tests, validate_env, setup_env
from validator import Validator

def run_cmd(command):
    command = command.replace("allowed", env_root + "/allowed")
    command = command.replace("restricted", env_root + "/restricted")
    command = command.replace("warmup", env_root + "/warmup")

    return subprocess.run(command, shell=True, capture_output=True)

def read_dmesg():
    result = run_cmd("dmesg -ce")
    return result.stdout.decode('utf-8')

def setup(test):
    # Run setup commands
    for cmd in test["setup"]:
        result = run_cmd(cmd)

        if result.returncode != 0:
            raise RuntimeError(f"Setup failed: {result.stderr.decode('utf-8')}")

def cleanup(test):
    for cmd in test["cleanup"]:
        result = run_cmd(cmd)

        if result.returncode != 0:
            raise RuntimeError(f"Cleanup failed: {result.stderr.decode('utf-8')}")

def warmup():
    try:
        run_cmd("mkdir warmup/test")
        run_cmd("rmdir warmup/test")
    except:
        raise RuntimeError("Warmup failed.")
def pre_execute(test):
    for pe in test["pre-execution"]:
        result = run_cmd(pe)

        if result.returncode != 0:
            raise RuntimeError(f"Pre-execution failed: {result.stderr.decode('utf-8')}")

def execute(test, constable):
    # Clear constable and dmesg output
    read_dmesg()
    if constable:
        constable.read()

    # Trigger warmup rule for logging
    # Run execution
    execution = test["execution"]
    out_std = run_cmd(execution["command"])

    warmup()
    # Wait for outputs
    #time.sleep(4)
    out_constable = constable.read() if constable else ""
    out_dmesg = read_dmesg()

    return out_std, out_constable, out_dmesg

def post_execute(test):
    for pe in test["post-execution"]:
        result = run_cmd(pe)

        if result.returncode != 0:
            raise RuntimeError(f"Post-execution failed: {result.stderr.decode('utf-8')}")

def cleanup(test):
    # Run cleanup commands
    for cmd in test["cleanup"]:
        result = run_cmd(cmd)

        if result.returncode != 0:
            raise RuntimeError(f"Setup for: {test['name']} failed: {result.stderr.decode('utf-8')}")

def create_constable():
    src_path = os.path.join(env_root, "medusa-template.conf")
    dest_path = os.path.join(env_root, "medusa.conf")

    content = ""
    with open(src_path, "r") as f:
        content = f.read()

    with open(dest_path, "w") as f:
        f.write(content)

def add_to_constable(config):
    with open(os.path.join(env_root, "medusa.conf"), "a") as f:
        f.write(config)

def run_test(test, validator):
    constable = None
    try:
        # Run setup
        if has_key(test, "setup"):
            setup(test)

        # Create constable
        using_constable = not has_key(test, "use_constable") or test["use_constable"]
        if using_constable:
            create_constable()

            if has_key(test, "constable"):
                add_to_constable(test["constable"])

            # constable.start()
            constable = Reader(f"sudo constable {env_root}/constable.conf")
            time.sleep(.5)

        # Run pre-execution
        if has_key(test, "pre-execution"):
            pre_execute(test)

        # Run execution
        out_std, out_constable, out_dmesg = execute(test, constable if using_constable else None)

        # Validate results
        validator.validate(test, out_std, out_constable, out_dmesg, using_constable)

        # Run post execution
        if has_key(test, "post-execution"):
            post_execute(test)

        if constable:
            constable.terminate()

        # Run cleanup
        if has_key(test, "cleanup"):
            cleanup(test)
    except Exception as e:
        print(e)
        validator.failed(test, e)
        if constable:
            constable.terminate()

def run_local_tests(tests, validator):
    for test in tests:
        run_test(test, validator)

def run_git_tests(tests, validator):
    # Navigate to git dir
    os.chdir(os.path.join(env_root, "medusa-tests"))

    for test in tests:
        run_test(test, validator)

    # Navigate back to env
    os.chdir(env_root)

if __name__ == "__main__":
    try:
        # Setup environment
        setup_env()
        validate_env()

        # load tests
        loaded_tests = load_tests()
        validator = Validator()

        # Clear dmesg
        run_cmd("dmesg -ce")

        # Initialize async readers
        # dmesg = Reader("dmesg -w")

        # Execute tests
        run_local_tests([t for t in loaded_tests if t["type"] == "LOCAL"], validator)

        # Execute git tests
        run_git_tests([t for t in loaded_tests if t["type"] == "GIT"], validator)
    except Exception as e:
        print(str(e))