import logging
import os
import subprocess
import time

from asynchronous_reader import Reader
from setup import env_root, has_key, load_tests, validate_env, setup_env
from validator import Validator


def run_cmd(command):
    """
    Runs shell command.
    Replaces relative folder paths with full paths.

    @param command: shell command to execute.
    @return: std out.
    """
    command = command.replace("allowed", env_root + "/allowed")
    command = command.replace("restricted", env_root + "/restricted")
    command = command.replace("helper", env_root + "/helper")

    return subprocess.run(command, shell=True, capture_output=True)

def execute_handlers(test, key):
    """
    Runs list of commands from selected execution block.

    @param test: test.
    @param key: block identifier.
    """
    # Run list of commands
    for cmd in test["setup"]:
        result = run_cmd(cmd)

        if result.returncode != 0:
            raise RuntimeError(f"Execution of '{key}' failed: {result.stderr.decode('utf-8')}")

def read_dmesg():
    """
    Reads and clears sys log.

    @return: sys logs.
    """
    result = run_cmd("dmesg -ce")
    return result.stdout.decode('utf-8')

def helper():
    """
    Helper execution to trigger Constable init.
    """
    logger.debug("Running helper")
    try:
        run_cmd("mkdir helper/test")
        run_cmd("rmdir helper/test")
    except:
        raise RuntimeError("Helper failed.")

def create_constable():
    """
    Creates medusa.conf from template.
    """
    src_path = os.path.join(env_root, "medusa-template.conf")
    dest_path = os.path.join(env_root, "medusa.conf")

    content = ""
    with open(src_path, "r") as f:
        content = f.read()

    with open(dest_path, "w") as f:
        f.write(content)

def add_to_constable(config):
    """
    Adds configuration to medusa.conf.

    @param config: configuration string to add.
    """
    with open(os.path.join(env_root, "medusa.conf"), "a") as f:
        f.write(config)
        f.close()
def execute(test, constable):
    """
    Execution helper for main test execution.

    1. Runs helper to trigger Constable init.
    2. Runs test.
    3. Reads outputs.

    @param test: test to execute.
    @param constable: async reader hooked to Constable
    @return: std, constable, sys log outputs.
    """
    # Clear constable and dmesg output
    read_dmesg()
    if constable:
        constable.read()

    helper()

    # Run execution
    execution = test["execution"]
    out_std = run_cmd(execution["command"])

    helper()
    # Wait for outputs
    time.sleep(0.5)
    out_constable = constable.read() if constable else ""
    out_dmesg = read_dmesg()

    return out_std, out_constable, out_dmesg

def run_single_test(test, validator):
    """
    Main execution function for test.

    @param test: test to execute.
    @param validator: validator object.
    """
    constable = None
    try:
        # Run setup
        if has_key(test, "setup"):
            logger.info(f"{test['name']}: running setup.")
            execute_handlers(test, "setup")

        # Create constable
        using_constable = not has_key(test, "use_constable") or test["use_constable"]
        if using_constable:
            logger.info(f"{test['name']}: creating constable.")
            create_constable()

            if has_key(test, "constable"):
                add_to_constable(test["constable"])

            # constable.start()
            constable = Reader(f"sudo constable {env_root}/constable.conf")
            time.sleep(.5)

        # Run pre-execution
        if has_key(test, "pre-execution"):
            logger.info(f"{test['name']}: running pre-execution.")
            execute_handlers(test, "pre-execution")

        # Run execution
        logger.info(f"{test['name']}: executing.")
        out_std, out_constable, out_dmesg = execute(test, constable if using_constable else None)

        # Validate results
        validator.validate(test, out_std, out_constable, out_dmesg)

        # Run post execution
        if has_key(test, "post-execution"):
            logger.info(f"{test['name']}: running post-execution.")
            execute_handlers(test, "post-execution")

        # Stop Constable
        if constable:
            constable.terminate()
            logger.info(f"{test['name']}: terminated Constable.")

        # Run cleanup
        if has_key(test, "cleanup"):
            logger.info(f"{test['name']}: running cleanup.")
            execute_handlers(test, "cleanup")
    except Exception as e:
        logger.error(f"{test['name']} failed. \n{str(e)}")

        # Assign error result
        validator.failed(test, e)

        # Stop Constable if running
        if constable:
            constable.terminate()

def run_multiple(tests, validator):
    logger.info(f"Creating constable.")
    create_constable()

    # Setup block
    for test in tests:
        try:
            # Run setup for each test
            if has_key(test, "setup"):
                logger.info(f"{test['name']}: running setup.")
                execute_handlers(test, "setup")

            # Add configuration to constable for each test
            if has_key(test, "constable"):
                add_to_constable(test["constable"])
        except Exception as e:
            logger.error(e)

    # Start Constable
    constable = Reader(f"sudo constable {env_root}/constable.conf")
    time.sleep(.5)

    # Execution block
    for test in tests:
        try:
            # Run pre-execution
            if has_key(test, "pre-execution"):
                logger.info(f"{test['name']}: running pre-execution.")
                execute_handlers(test, "pre-execution")

            # Run execution
            logger.info(f"{test['name']}: executing.")
            out_std, out_constable, out_dmesg = execute(test, constable)

            # Validate results
            validator.validate(test, out_std, out_constable, out_dmesg)

            # Run post execution
            if has_key(test, "post-execution"):
                logger.info(f"{test['name']}: running post-execution.")
                execute_handlers(test, "post-execution")
        except Exception as e:
            validator.failed(test, e)

    # Stop Constable
    if constable:
        constable.terminate()
        logger.info(f"Terminated Constable.")

    # Cleanup block
    for test in tests:
        try:
            if has_key(test, "cleanup"):
                logger.info(f"{test['name']}: running cleanup.")
                execute_handlers(test, "cleanup")
        except Exception as e:
            logger.error(e)


def run_local_tests(tests, validator):
    """
    Runs and handles LOCAL tests.

    @param tests: LOCAL tests
    @param validator: test validator instance.
    """
    # Group by source file
    grouped_tests = {}

    logger.debug("Grouping suites.")
    for t in tests:
        src = t['src']
        if src not in grouped_tests:
            grouped_tests[src] = []
        grouped_tests[src].append(t)

    for k in grouped_tests.keys():
        logger.info(f"Running tests for suite: {src}")

        run_multiple(grouped_tests[k], validator)
        time.sleep(3)

def run_git_tests(tests, validator):
    """
    Changes dir to git repository and runs GIT tests.

    @param tests: GIT tests
    @param validator: test validator instance.
    """
    if not tests or len(tests) == 0:
        return

    # Navigate to git dir
    os.chdir(os.path.join(env_root, "medusa-tests"))

    # Execute tests
    for test in tests:
        logger.info(f"Running git test: {test['name']}")
        run_single_test(test, validator)
        time.sleep(3)

    # Navigate back to env
    os.chdir(env_root)

def record_execution_result(result):
    """
    Records test run final state to exit file.

    @param result: test run result.
    """
    with open(os.path.join(env_root, "exit"), "w") as f:
        f.write(result)
        f.close()

if __name__ == "__main__":
    # Setup logger
    logging.basicConfig(
        filename=f"{env_root}/log",
        filemode="w",
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s]: %(message)s"
    )
    logger = logging.getLogger()

    try:
        # Setup environment
        logger.info("Running setup... ")
        setup_env()
        validate_env()
        logger.info("Setup finished. ")

        # load tests
        loaded_tests = load_tests()
        logger.info("Tests loaded.")

        validator = Validator()
        logger.info("Validator ready.")

        # Clear dmesg
        run_cmd("dmesg -ce")
        logger.info("Cleared system log.")

        # Execute git tests
        run_git_tests([t for t in loaded_tests if t["type"] == "GIT"], validator)

        # Execute tests
        run_local_tests([t for t in loaded_tests if t["type"] == "LOCAL"], validator)

        # Dump test summary
        validator.dump_results()

        # Mark as successful test run
        record_execution_result("SUCCESS")
    except Exception as e:
        logger.error(str(e))
        record_execution_result("ERROR")
        quit()