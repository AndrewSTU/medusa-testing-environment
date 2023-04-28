from mte.logger import Logger
from mte.vm_manager import VirtualBoxManager
from mte.test_manager import TestManager
from mte.configuration_manager import ConfigurationManager
from mte.ssh_manager import SSHManager


class TestExecutor:
    logger = Logger()

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

    def execute(self, selected_tests):
        self.logger.info("Preparing selected tests for transfer...")
        self.test_manager.prepare_tests(selected_tests, self.environment_config["environmentDir"])
        self.logger.info("Tests are ready for transfer.")

        self.logger.info("Establishing connection to remote...")
        self.vb_manager.connect()

        self.ssh_manager.connect()
        self.logger.info("Connection to remote was established.")

        self.logger.info("Preparing environment on remote...")
        self.ssh_manager.prepare_environment(self.environment_config["environmentDir"])
        self.logger.info("Remote setup is done.")

        self.logger.info("Started testing...")

        try:
            print(self.ssh_manager.exec(f"cd {self.environment_config['environmentDir']}; sudo python3 runner.py"))

            self.logger.info("Testing has finished.")

            return self.ssh_manager.exec(f"sudo cat {self.environment_config['environmentDir']}/results")
        except Exception as e:
            self.logger.error(e, "Test run failed. See log file for more information.")
        finally:
            self.ssh_manager.disconnect()


