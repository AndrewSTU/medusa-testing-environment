import os
from enum import Enum

from setup import results_dir, result_details_dir, has_key


class Result(Enum):
    """
    Enum used for easier test's results gradings.
    """
    FAILED = 0
    PASSED = 1
    IGNORED = 2

class Validator:
    """
    Handles validations of test results.
    """

    def __init__(self):
        """
        Initializes dictionary with overal results.
        """
        self.test_results = {"success": 0, "failed": 0, "partial": 0}

    def validate(self, test, out_std, out_constable, out_dmesg):
        """
        Main validation function.
        Verifies outputs with test's expected values.
        Verifies:
        - result code
        - Constable output
        - system log output

        @param test: test to validate .
        @param out_std: std output from command.
        @param out_constable: Constable output
        @param out_dmesg: system log output.
        """
        # Extract expected results
        expect = test["execution"]["results"]

        result = {
            "name": test["name"],
            "output": False,
            "constable": False,
            "dmesg": False
        }

        vc = 0
        # Validate stdout
        if has_key(expect, "return_code"):
            r = expect["return_code"] == out_std.returncode

            result["output"] = Result(int(r))
            vc += r
        else:
            result["output"] = Result.IGNORED
            vc += 1

        # Validate constable
        using_constable = True
        if has_key(test, "using_constable"):
            using_constable = test["using_constable"]

        if has_key(expect, "constable") and using_constable:
            r = expect["constable"] in str(out_constable)

            result["constable"] = Result(int(r))
            vc += r
        else:
            result["constable"] = Result.IGNORED
            vc += 1

        # Validate dmesg
        if has_key(expect, "dmesg"):
            r = expect["dmesg"] in str(out_dmesg)

            result["dmesg"] = Result(int(r))
            vc += r
        else:
            result["dmesg"] = Result.IGNORED
            vc += 1

        # Assign result group
        if vc == 0:
            self.test_results["failed"] += 1
        elif vc == 3:
            self.test_results["success"] += 1
        else:
            self.test_results["partial"] += 1

        # Append to global results
        self.__append_to_results(result)

        # Create details result file
        self.__append_to_details(test["name"], out_std, out_constable, out_dmesg)

    def failed(self, test, exception):
        """
        In case exception occurred during test execution, records error to results files.

        @param test: test during exception.
        @param exception: exception that occurred.
        """
        name = test["name"]
        self.test_results["failed"] += 1

        # Record failure to overal results
        with open(os.path.join(results_dir, "results"), "a") as f:
            f.write(f"{name}:{' ' * (32 - len(name))}Failed with error see details.\n")

        # Record failure to details result
        with open(os.path.join(results_dir, "details", test["name"]), "w") as f:
            f.write(f"{name} {'-' * (32 - len(name))}\n")
            f.write(f"\nerror:\n{str(exception)}\n")

    def __append_to_details(self, name, out_std, out_constable, out_dmesg):
        """
        Records outputs to test's result details report.

        @param name: test name.
        @param out_std: std output.
        @param out_constable: Constable output
        @param out_dmesg: sys log output.
        """
        with open(os.path.join(result_details_dir, name), "w") as f:
            f.write(f"{name} {'-' * (32 - len(name))}")
            f.write(f"\noutput:\n{out_std.stdout.decode('utf-8')+out_std.stderr.decode('utf-8')}")
            f.write(f"\nconstable:\n{str(out_constable)}")
            f.write(f"\ndmesg:\n{str(out_dmesg)}\n")
    def __append_to_results(self, results):
        """
        Appends results to overal results report.
        @param results:
        """
        name = results["name"]
        output = results["output"].name
        constable = results["constable"].name
        dmesg = results["dmesg"].name

        with open(os.path.join(results_dir, "results"), "a") as f:
            f.write(f"{name}:{' ' * (32 - len(name))}output: {output} \t constable: {constable} \t dmesg: {dmesg}\n")

    def dump_results(self):
        """
        Final function to append overal tests score to overal results file.
        """
        # Count number of tests in each category
        success_count = self.test_results["success"]
        failed_count = self.test_results["failed"]
        partial_count = self.test_results["partial"]

        # Write overall test results to file
        with open(os.path.join(results_dir, "results"), 'r+') as f:
            content = f.read()
            f.seek(0,0)
            f.write(
                f"Testing complete: {success_count} passed, {failed_count} failed, {partial_count} partial\n{content}"
            )


