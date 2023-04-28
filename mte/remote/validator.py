from setup import env_root
import os

class Validator:

    def __init__(self):
        self.test_results = {"success": [], "failed": [], "partial":[]}

    def validate_local_test(self, test, out_std, out_constable, out_dmesg):
        expect = test["execution"]["results"]

        result = {
            "name": test["name"],
            "output": False,
            "constable": False,
            "dmesg": False
        }

        vc = 0
        # validate stdout
        if expect["return_code"] == out_std.returncode:
            result["output"] = True
            vc += 1
        else:
            # TODO: log stderr
            pass

        # validate constable
        if "constable" not in expect or expect["constable"] is None or expect["constable"] in out_constable:
            result["constable"] = True
            vc += 1
        else:
            # TODO: log constable
            pass

        # validate dmesg
        if expect["dmesg"] in str(out_dmesg):
            result["dmesg"] = True
            vc += 1
        else:
            # TODO: log dmesg
            pass

        # assign result group
        if vc == 0:
            self.test_results["failed"].append(result)
        elif vc == 3:
            self.test_results["success"].append(result)
        else:
            self.test_results["partial"].append(result)

    def prevalidate_dmesg(self, test, out_dmseg):
        expect = test["execution"]["results"]["dmesg"]

        return expect in out_dmseg

    def dump_results(self):
        # Count number of tests in each category
        success_count = len(self.test_results["success"])
        failed_count = len(self.test_results["failed"])
        partial_count = len(self.test_results["partial"])

        # Write overall test results to file
        with open(os.path.join(env_root, "results"), 'w') as f:
            f.write(f"Testing complete: {success_count} passed, {failed_count} failed, {partial_count} partial\n")

            # Write results for each test to file
            for test in self.test_results["success"] + self.test_results["failed"] + self.test_results["partial"]:
                name = test["name"]
                output = "passed" if test["output"] else "failed"
                constable = "passed" if test["constable"] else "failed"
                dmesg = "passed" if test["dmesg"] else "failed"

                f.write(f"{name}: \t output: {output} \t constable: {constable} \t dmesg: {dmesg}\n")


