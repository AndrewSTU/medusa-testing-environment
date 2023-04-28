import os
import subprocess
import time

from asynchronous_reader import Reader
from setup import env_root, load_tests, validate_env, setup_env
from validator import Validator

def run_cmd(command):
    command = command.replace("allowed", env_root + "/allowed")
    command = command.replace("restricted", env_root + "/restricted")

    return subprocess.run(command, shell=True, capture_output=True)

def read_dmesg():
    result = run_cmd("dmesg -ce")

    if result.returncode != 0:
        raise RuntimeError(f"Failed to access dmesg: {result.stderr}")

    return str(result.stdout)

def prepare_local_tests(tests):
    for test in tests:
        # Add to constable configuration
        if test["constable"]:
            with open(os.path.join(env_root, "medusa.conf"), "a") as f:
                f.write(test['constable'])

        # Run setup commands
        if "setup" in test:
            for cmd in test["setup"]:
                result = run_cmd(cmd)

                if result.returncode != 0:
                    raise RuntimeError(f"Setup for: {test['name']} failed: {result.stderr.decode('utf-8')}")

def run_local_tests(tests, constable, validator):
    for test in tests:
        execution = test["execution"]

        if "pre_execution" in execution:
            for pe in execution["pre-execution"]:
                run_cmd(pe["command"])

        # clear constable buffer
        constable.read()
        read_dmesg()

        out_std = run_cmd(execution["command"])

        time.sleep(3)

        out_constable = constable.read()
        out_dmesg = read_dmesg()

        validator.validate_local_test(test, out_std, out_constable, out_dmesg)

        if "post_execution" in execution:
            for pe in execution["post_execution"]:
                run_cmd(pe["command"])

if __name__ == "__main__":
    # setup env
    try:
        setup_env()
        validate_env()

        # load tests
        tests = load_tests()
        tests_local = [t for t in tests if t["type"] == "LOCAL"]
        prepare_local_tests(tests_local)

        # start constable
        constable = Reader(f"sudo constable {env_root}/constable.conf")
        time.sleep(5)

        validator = Validator()

        # run local tests
        run_local_tests(tests_local, constable, validator)

        constable.terminate()
        validator.dump_results()
    except Exception as e:
        print(e)
        if constable:
            constable.terminate()


    # run cleanup
