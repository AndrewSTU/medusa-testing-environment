import os
import pickle

import git
import subprocess
import yaml
import shutil

from mte.logger import Logger


class TestManager:
    logger = Logger()
    __git_allowed_dirs = ["ipc"]

    def __init__(self):
        # Obtain tests directory
        file_dir = os.path.dirname(os.path.abspath(__file__))
        self.__tests_dir = os.path.join(file_dir, "tests")
        self.__git_dir = os.path.join(self.__tests_dir, "medusa-tests")
        self.__transport_dir = os.path.join(file_dir, "remote")

        self.__update_git_tests()

    def list_tests(self):
        return self.__list_git_tests() + self.__list_local_tests()

    def prepare_tests(self, tests, test_env):
        self.logger.info("Preparing tests for transfer...")

        self.__prepare_configs(test_env)

        self.__prepare_local_test(
            [t for t in tests if t["type"] == "LOCAL"]
        )

        self.__prepare_git_tests(
            [t for t in tests if t["type"] == "GIT"]
        )

        self.logger.info("Tests are ready for transfer.")

    def __prepare_configs(self, tests_env):
        # Prepare constable config
        with open(os.path.join(self.__tests_dir, "constable.conf"), "r") as f:
            constable_content = f.read()

        new_content = constable_content.replace("{@TEST_ENV}", tests_env)

        with open(os.path.join(self.__transport_dir, "constable.conf"), "w") as f:
            f.write(new_content)

        # Prepare medusa.conf
        with open(os.path.join(self.__tests_dir, "medusa.conf"), "r") as f:
            constable_content = f.read()

        new_content = constable_content.replace("{@TEST_ENV}", tests_env)

        with open(os.path.join(self.__transport_dir, "medusa.conf"), "w") as f:
            f.write(new_content)

    def __prepare_local_test(self, tests):
        if not os.path.exists(self.__transport_dir):
            os.makedirs(self.__transport_dir)

        file = os.path.join(self.__transport_dir, "local.pickle")

        for t in tests:
            del t["selected"]

        with open(file, "wb") as f:
            pickle.dump(tests, f)

    def __prepare_git_tests(self, tests):
        """
        Complile required files into transfer dir.

        Copy runners.
        """
        pass

    def cleanup(self):
        self.logger.debug("Running test cleanup...")

        transport_dir = os.path.join(self.__tests_dir, "/transfer")
        if os.path.exists(transport_dir):
            shutil.rmtree(transport_dir)

        self.logger.debug("Test cleanup complete.")

    def __list_local_tests(self):
        self.logger.debug("Listing local tests...")
        tests = []

        for subdir, dirs, files in os.walk(self.__tests_dir):
            if "medusa-tests" in dirs:
                dirs.remove("medusa-tests")

            for file in files:
                if file.endswith(".yaml"):
                    test_file_path = os.path.join(subdir, file)
                    test_relative_path = os.path.relpath(test_file_path, self.__tests_dir)

                    with open(os.path.join(subdir, file), "r") as f:
                        data = yaml.safe_load(f)

                        if data:
                            tests.extend(
                                [
                                    self.__transform_test(d, "LOCAL", d["name"], file, test_relative_path) for d in data
                                ]
                            )
        self.logger.debug("Listing local tests complete.")
        return tests

    def __list_git_tests(self):
        self.logger.debug("Listing git tests...")
        tests = []

        for subdir, dirs, files in os.walk(self.__git_dir):
            dirs[:] = [d for d in dirs if d in self.__git_allowed_dirs]

            for file in files:
                if file.endswith(".c"):
                    subdir = os.path.split(subdir)[-1]
                    tests.append(
                        self.__transform_test({}, "GIT", file, file, subdir)
                    )

        self.logger.debug("Listing git tests complete.")
        return tests

    def __transform_test(self, test, type, name, suit, src):
        test["type"] = type
        test["name"] = name
        test["suit"] = suit
        test["src"] = src
        test["selected"] = True

        return test

    def __update_git_tests(self):
        try:
            if os.path.exists(self.__git_dir):
                self.logger.debug("Git tests are present, checking for updates...")
                result = subprocess.run(["git", "pull"], cwd=self.__git_dir, capture_output=True, text=True)

                if result.returncode == 0:
                    self.logger.debug("Updated git tests.")
                else:
                    self.logger.error(RuntimeError("Git pull failed for unknown reason. Check your internet connection and git installation"))
            else:
                self.logger.debug("Missing git tests. Downloading repo...")
                git.Repo.clone_from("https://github.com/Medusa-Team/medusa-tests", self.__git_dir)
                self.logger.debug("Downloaded git tests.")
        except Exception as e:
            self.logger.error(e, "Updating git tests failed. See log file.")



