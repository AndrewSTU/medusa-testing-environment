from setup import env_root, has_key
from enum import Enum

import os

class Result(Enum):
    FAILED = 0
    PASSED = 1
    IGNORED = 2

class Validator:

    def __init__(self):
        self.test_results = {"success": 0, "failed": 0, "partial": 0}

    def validate(self, test, out_std, out_constable, out_dmesg, using_constable):
        expect = test["execution"]["results"]

        result = {
            "name": test["name"],
            "output": False,
            "constable": False,
            "dmesg": False
        }

        vc = 0
        # validate stdout
        if has_key(expect, "return_code"):
            r = expect["return_code"] == out_std.returncode

            result["output"] = Result(int(r))
            vc += r
        else:
            result["output"] = Result.IGNORED
            vc += 1

        # validate constable
        if has_key(expect, "constable") and using_constable:
            r = expect["constable"] in str(out_constable)

            result["constable"] = Result(int(r))
            vc += r
        else:
            result["constable"] = Result.IGNORED
            vc += 1

        # validate dmesg
        if has_key(expect, "dmesg"):
            r = expect["dmesg"] in str(out_dmesg)

            result["dmesg"] = Result(int(r))
            vc += r
        else:
            result["dmesg"] = Result.IGNORED
            vc += 1

        # assign result group
        if vc == 0:
            self.test_results["failed"] += 1
        elif vc == 3:
            self.test_results["success"] += 1
        else:
            self.test_results["partial"] += 1

        self.__append_to_results(result)
        self.__append_to_details(test["name"], out_std, out_constable, out_dmesg)

    def failed(self, test, exception):
        name = test["name"]
        self.test_results["failed"] += 1

        with open(os.path.join(env_root, "results"), "a") as f:
            f.write(f"{name}:{' ' * (32 - len(name))}Failed with error see details.\n")

        with open(os.path.join(env_root, "results_details"), "a") as f:
            f.write(f"{name} {'-' * (32 - len(name))}\n")
            f.write(f"\nerror:\n{str(exception)}\n")

    def __append_to_details(self, name, out_std, out_constable, out_dmesg):
        with open(os.path.join(env_root, "results_details"), "a") as f:
            f.write(f"{name} {'-' * (32 - len(name))}")
            f.write(f"\noutput:\n{out_std.stdout.decode('utf-8')+out_std.stderr.decode('utf-8')}")
            f.write(f"\nconstable:\n{str(out_constable)}")
            f.write(f"\ndmesg:\n{str(out_dmesg)}\n")
    def __append_to_results(self, results):
        name = results["name"]
        output = results["output"].name
        constable = results["constable"].name
        dmesg = results["dmesg"].name

        with open(os.path.join(env_root, "results"), "a") as f:
            f.write(f"{name}:{' ' * (32 - len(name))}output: {output} \t constable: {constable} \t dmesg: {dmesg}\n")

    def prevalidate_dmesg(self, test, out_dmseg):
        expect = test["execution"]["results"]["dmesg"]

        return expect in out_dmseg

    def dump_results(self):
        # Count number of tests in each category
        success_count = self.test_results["success"]
        failed_count = self.test_results["failed"]
        partial_count = self.test_results["partial"]

        # Write overall test results to file
        with open(os.path.join(env_root, "results"), 'r+') as f:
            content = f.read()
            f.seek(0,0)
            f.write(
                f"Testing complete: {success_count} passed, {failed_count} failed, {partial_count} partial\n{content}"
            )


