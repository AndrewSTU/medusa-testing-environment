import os
import pickle
import subprocess

import yaml

from mte.logger import Logger


class TestManager:
    """
    Class that manages tests and results.
    """
    __logger = Logger()

    def __init__(self):
        """
        Initializes Test manager.
        Loads all necessary paths needed for execution.
        """
        # Obtain tests directory
        file_dir = os.path.dirname(os.path.abspath(__file__))
        self.__tests_dir = os.path.join(file_dir, "tests")
        self.__git_dir = os.path.join(self.__tests_dir, "medusa-tests")
        self.__transport_dir = os.path.join(file_dir, "target")
        self.__results_dir = os.path.join(file_dir, "results")

        self.__update_git()

    def list_tests(self):
        """
        Lists and registers all tests in YAML files present in test directory.
        @return: List of available tests.
        """
        self.__logger.debug("Listing local tests...")
        tests = []

        # List through tests dir
        for subdir, dirs, files in os.walk(self.__tests_dir):
            # Exclude medusa tests
            if "medusa-tests" in dirs:
                dirs.remove("medusa-tests")

            for file in files:
                if file.endswith(".yaml"):
                    test_file_path = os.path.join(subdir, file)
                    test_relative_path = os.path.relpath(test_file_path, self.__tests_dir)

                    with open(os.path.join(subdir, file), "r") as f:
                        data = yaml.safe_load(f)

                        if data:
                            # Extend test with location information
                            tests.extend(
                                [
                                    self.__transform_test(d, d["name"], file, test_relative_path) for d in data
                                ]
                            )

        self.__logger.debug("Listing local tests complete.")
        return tests

    def prepare_tests(self, tests, test_env):
        """
        Wrapper method for preparing tests.

        @param tests:
        @param test_env:
        """
        self.__logger.info("Preparing tests for transfer...")

        self.__prepare_configs(test_env)

        self.__prepare_tests(tests)

        self.__logger.info("Tests are ready for transfer.")

    def load_results(self):
        """
        Loads test results from results.txt if present.
        @return: Test results string.
        """

        results = None
        try:
            # Try to open results file
            with open(os.path.join(self.__results_dir, "results.txt"), "r") as f:
                results = f.read()
                f.close()
        except Exception as e:
            self.__logger.debug("Results do not exist")
        return results

    def __prepare_configs(self, tests_env):
        """
        Prepares configuration files Constable and Medusa configuration.
        Formats files to contain path to testing environment, where the configurations will be transferred.

        @param tests_env: remote testing location.
        """
        # Prepare constable config
        with open(os.path.join(self.__tests_dir, "constable.conf"), "r") as f:
            # Load
            constable_content = f.read()

        # Replace
        new_content = constable_content.replace("{@TEST_ENV}", tests_env)

        with open(os.path.join(self.__transport_dir, "constable.conf"), "w") as f:
            # Save
            f.write(new_content)

        # Prepare medusa-template.conf
        with open(os.path.join(self.__tests_dir, "medusa-template.conf"), "r") as f:
            # Load
            constable_content = f.read()

        # Replace
        new_content = constable_content.replace("{@TEST_ENV}", tests_env)

        with open(os.path.join(self.__transport_dir, "medusa-template.conf"), "w") as f:
            # Save
            f.write(new_content)

    def __prepare_tests(self, tests):
        """
        Saves tests into transport_dir in .pickle format.

        @param tests: selected tests for transfer.
        """
        if not os.path.exists(self.__transport_dir):
            os.makedirs(self.__transport_dir)

        file = os.path.join(self.__transport_dir, "local.pickle")

        # Remove selected attribute
        for t in tests:
            del t["selected"]

        # Dump to file
        with open(file, "wb") as f:
            pickle.dump(tests, f)

    def __transform_test(self, test, name, suit, src):
        """
        Helper for transformation of test when loaded from test file.

        @param test: test dictionary
        @param name: name.
        @param suit: suit name.
        @param src: source.
        @return: transformed complete test
        """
        # Add required keys
        test["name"] = name
        test["suit"] = suit
        test["src"] = src
        test["selected"] = True

        return test

    def __update_git(self):
        """
        Updates git tests submodule - Medusa Tests.
        """
        try:
            # Run git update
            self.__logger.debug("Updating git tests, checking for updates...")
            result = subprocess.run(["git", "submodule", "update"], cwd=self.__git_dir, capture_output=True, text=True)

            # Check result
            if result.returncode == 0:
                self.__logger.debug("Git tests up to date.")
            else:
                raise RuntimeError(result.stderr)
        except Exception as e:
            self.__logger.error(e, "Updating git tests failed. See log file.")



