import threading as th
import time

from mte.config_manager import ConfigurationManager
from mte.logger import Logger
from mte.remote_manager import RemoteManager
from mte.ssh_manager import SSHManager
from mte.test_manager import TestManager


class TestExecutor:
    """
    Main execution node. Represents interface for execution process for application.
    """
    __logger = Logger()

    __connection_thread = None
    __execution_thread = None

    __connection_active = False

    def __init__(self):
        """
        Initializes TestExecutor.
        Reads config using ConfigManger and create RemoteManager, SSHManager and VMManager.
        """
        self.__logger.info("Loading configuration...")

        # Load configuration
        config = ConfigurationManager().get_config()
        self.__client_config = config['target']
        self.__environment_config = config['env']
        self.__logger.info("Configuration loaded.")

        self.__logger.info("Running setup...")
        # Create remote manager
        self.__remote_manager = RemoteManager(
            vm_name=self.__client_config['name'],
            host=self.__client_config['ip'],
            port=self.__client_config['port'],
            username=self.__client_config['username'],
            password=self.__client_config['password'],
            using_vb=self.__client_config.getboolean("using_vb")
        )

        # Create test manager
        self.__test_manager = TestManager()

        # Create SSH manager
        self.__ssh_manager = SSHManager(
            self.__client_config["ip"],
            self.__client_config["port"],
            self.__client_config["username"],
            self.__client_config["password"]
        )

        self.__logger.info("Setup complete.")

    def get_tests(self):
        """
        Loads test using TestManager.

        @return: all available tests.
        """
        self.__logger.info("Loading tests...")
        tests = self.__test_manager.list_tests()
        self.__logger.info("Tests have been loaded.")

        return tests

    def check_execution_status(self):
        """
        Returns information if execution thread is still running.

        @return: if execution thread is done.
        """
        return not self.__execution_thread.is_alive()

    def check_connection_status(self):
        """
        Returns information if connection thread is still running.

        @return: if connection is done.
        """
        return not self.__connection_thread.is_alive()

    def get_results(self):
        """
        Returns tests results from transferred results.

        @return: test resutls.
        """
        results = self.__test_manager.load_results()

        if results:
            self.__logger.info("Result details are present in 'results' folder.")
        return results
    def establish_connection(self):
        """
        Starts connection thread.
        """
        self.__connection_thread = th.Thread(target=self.__connection_thread_target)
        self.__connection_thread.start()

    def execute(self, selected_tests):
        """
        If connection is established, starts execution thread.

        @param selected_tests: tests to run.
        @return: if execution thread started.
        """
        if not self.__connection_active:
            return False

        self.__execution_thread = th.Thread(target=self.__execution_thread_target, args=(selected_tests,))
        self.__execution_thread.start()

        return True

    def __connection_thread_target(self):
        """
        Target function for connection thread.
        1. Checks connection with target.
        2. Creates ssh connection.
        """
        try:
            self.__logger.info("Establishing connection to target...")
            self.__remote_manager.connect()

            self.__ssh_manager.connect()
            self.__logger.info("Connection to target was established.")

            # Set flag to signalize that connection is ready.
            self.__connection_active = True
        except:
            quit(1)

    def __check_execution_status(self):
        """
        Helper function for execution.
        Runs pgrep for executor in while with 5s pauses.
        Call has timeout set for 10s, if it fails, it means that host is iresponsive -> frozen.
        If pgrep returns 1 -> executor has finished, then checks exit file on remote for execution result status.
        """
        env_dir = self.__environment_config["environmentDir"]

        self.__ssh_manager.disconnect()
        time.sleep(5)

        while True:
            self.__logger.info("Validating remote...")

            try:
                # Test connection
                self.__ssh_manager.connect()

                # Check if still runnning
                try:
                    self.__ssh_manager.exec("pgrep medusaTestsExec", timeout=True, log_error=False)
                except IOError:
                    # pgrep returned 1 = proces stopped
                    break

                self.__ssh_manager.disconnect()
            except:
                self.__ssh_manager.disconnect()
                self.__logger.error(OSError, "Remote is not responding, remote is most likely frozen.")

            time.sleep(5)

        result = self.__ssh_manager.exec(f"cat {env_dir}/exit")
        if result != "SUCCESS":
            self.__ssh_manager.download_results(env_dir, True)
            self.__logger.error(IOError("Test failed."), "Execution on remote resulted in error")

    def __execution_thread_target(self, selected_tests):
        """
        Execution thread target. Starts testing process:
        1. Prepares test and files for transfer.
        2. Prepares environment on remote.
        3. Runs test execution in background.
        4. Waits for execution process to stop.

        @param selected_tests: tests to prepare and run.
        """
        env_dir = self.__environment_config["environmentDir"]

        # Prepare tests
        self.__logger.info("Preparing selected tests for transfer...")
        self.__test_manager.prepare_tests(selected_tests, env_dir)
        self.__logger.info("Tests are ready for transfer.")

        # Prepare env
        self.__logger.info("Preparing environment on target...")
        include_git = any(t.get("type") == 'GIT' for t in selected_tests)
        self.__ssh_manager.prepare_environment(env_dir, include_git)
        self.__ssh_manager.exec(f"sudo chmod -R 777 {env_dir}")

        self.__logger.info("Remote setup is done.")

        try:
            # Execute tests
            self.__ssh_manager.exec_async(f"{env_dir}/medusaTestsExec.bash &")
            self.__logger.info("Started testing...")

            # Wait for testing to exit
            self.__check_execution_status()

            self.__logger.info("Testing has finished.")

            # Download results
            self.__logger.info("Fetching results...")
            self.__ssh_manager.download_results(env_dir)
            self.__logger.info("Results ready.")

            # Clean target
            self.__logger.info("Running cleanup...")
            self.__ssh_manager.clean_target(env_dir)
            self.__logger.info("Cleanup done.")
        except IOError:
            pass
        except Exception as e:
            self.__logger.error(e, "Test run failed. See log files for more information.")
        finally:
            self.__ssh_manager.disconnect()
            self.__connection_active = False


