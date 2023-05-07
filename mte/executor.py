import queue
import time

from mte.logger import Logger
from mte.vm_manager import VirtualBoxManager
from mte.test_manager import TestManager
from mte.config_manager import ConfigurationManager
from mte.ssh_manager import SSHManager

import threading as th


class TestExecutor:
    logger = Logger()

    connection_thread = None
    execution_thread = None
    check_thread = None
    check_queue = None

    connection = False

    def __init__(self, parent):
        self.__parent = parent

        self.logger.info("Loading configuration...")
        # Load configuration
        config = ConfigurationManager().get_config()
        self.client_config = config['target']
        self.environment_config = config['env']
        self.logger.info("Configuration loaded.")

        self.logger.info("Running setup...")
        # VB manager
        self.vb_manager = VirtualBoxManager(
            vm_name=self.client_config['name'],
            host=self.client_config['ip'],
            port=self.client_config['port'],
            username=self.client_config['username'],
            password=self.client_config['password'],
            using_vb=self.client_config.getboolean("using_vb")
        )

        # Create test manager
        self.test_manager = TestManager()

        # Create SSH manager
        self.ssh_manager = SSHManager(
            self.client_config["ip"],
            self.client_config["port"],
            self.client_config["username"],
            self.client_config["password"]
        )

        self.logger.info("Setup complete.")

    def get_tests(self):
        self.logger.info("Loading tests...")
        tests = self.test_manager.list_tests()
        self.logger.info("Tests have been loaded.")

        return tests

    def check_execution_status(self):
        # Check queue for freeze
        if not self.check_queue.empty():
            self.logger.info("Host has frozen. Canceling testing.")
            self.execution_thread = None
            return True

        # Check if execution finished
        if not self.execution_thread.is_alive():
            self.logger.debug("Execution thread finished.")

            self.logger.debug("Stopping checking thread...")
            self.check_queue.put(True)
            return True

        return False

    def check_connection_status(self):
        return not self.connection_thread.is_alive()

    def connect(self):
        self.connection_thread = th.Thread(target=self.__connection_thread)
        self.connection_thread.start()

    def execute(self, selected_tests):
        if not self.connection:
            return False

        self.execution_thread = th.Thread(target=self.__execute_thread, args=(selected_tests,))
        self.execution_thread.start()

        self.check_queue = queue.Queue()
        self.check_thread = th.Thread(target=self.__checking_thread)
        self.check_thread.start()

        return True

    def __connection_thread(self):
        self.logger.info("Establishing connection to remote...")
        self.vb_manager.connect()

        self.ssh_manager.connect()
        self.logger.info("Connection to remote was established.")

        self.connection = True
    def __checking_thread(self):
        self.logger.debug("Started checking thread.")

        while True:
            if not self.check_queue.empty():
                break
            self.logger.debug("Validating guest connection...")

            try:
                self.ssh_manager.exec("ls")
            except AttributeError:
                break
            except Exception as e:
                self.logger.error(e, "SSH failed. Host is frozen.")
                self.check_queue.put(True)
                break
            time.sleep(5)

        self.logger.debug("Checking thread has stopped.")

    def __execute_thread(self, selected_tests):
        self.logger.info("Preparing selected tests for transfer...")
        self.test_manager.prepare_tests(selected_tests, self.environment_config["environmentDir"])
        self.logger.info("Tests are ready for transfer.")

        self.logger.info("Preparing environment on remote...")
        include_git = any(t.get("type") for t in selected_tests)
        self.ssh_manager.prepare_environment(self.environment_config["environmentDir"], include_git)
        self.logger.info("Remote setup is done.")

        self.logger.info("Started testing...")

        try:
            print(self.ssh_manager.exec(f"{self.environment_config['environmentDir']}/executor.bash"))

            self.logger.info("Testing has finished.")

            print(self.ssh_manager.exec(f"sudo cat {self.environment_config['environmentDir']}/results"))

            print(self.ssh_manager.exec(f"sudo cat {self.environment_config['environmentDir']}/results_details"))
        except Exception as e:
            self.logger.error(e, "Test run failed. See log file for more information.")
        finally:
            self.ssh_manager.disconnect()


