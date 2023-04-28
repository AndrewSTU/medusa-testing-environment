import os
import time
import paramiko
import platform

from mte.logger import Logger
import virtualbox as vb
from virtualbox.library import MachineState, SessionState


class VirtualBoxManager:
    """
        Manages a VirtualBox VM and its connection using SSH.
        """
    logger = Logger()

    def __init__(self, vm_name, host, port, username, password, using_vb):
        """
        Initializes the VirtualBoxManager instance.

        Args:
        vm_name (str): The name of the VM to manage.
        host (str): The hostname or IP address of the VM.
        port (int): The SSH port to connect to on the VM.
        username (str): The username to authenticate with on the VM.
        password (str): The password to authenticate with on the VM.
        using_vb (bool): Flag to indicate whether the VM is running in VirtualBox.
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.using_vb = using_vb

        if self.using_vb:
            self.__validate_vm(vm_name)

    def connect(self):
        """
        Connects to the VM using SSH and waits until the SSH port is available.
        """
        try:
            if self.using_vb:
                self.__start_vm()

            # Wait until ssh port is available
            self.logger.debug("Validating SSH connection...")
            while True:
                if self.__check_ssh():
                    break
                time.sleep(10)
                # TODO: Runtime error if takes too long?
            self.logger.info("Guest is ready.")
        except Exception as e:
            self.logger.error(e, "Failed to connect to guest.")

    def __validate_vm(self, vm_name):
        """
        Validates that the VM with the given name exists in VirtualBox.

        Args:
        vm_name (str): The name of the VM to validate.
        """
        self.logger.debug("Validating virtual machine...")

        # Establish connection with Virtual Box
        try:
            self.vbox = vb.VirtualBox()
        except Exception as e:
            self.logger.error(e, "Failed to establish connection with Virtual Box. See logs for more info.")

        self.logger.debug(f"Running virtual box version: {self.vbox.version}")

        # Find desired virtual machine
        try:
            self.machine = self.vbox.find_machine(vm_name)
        except Exception as e:
            self.logger.error(e, f"VM: {vm_name} does not exist on host system.")

        self.logger.debug(f"Virtual machine {vm_name} found.")

    def __start_vm(self):
        """
        Starts the VM in VirtualBox and waits until it is running.
        """
        try:
            self.logger.debug("Checking virtual machine...")
            session = vb.Session()

            if self.machine.state == MachineState.running or self.machine.state == MachineState.paused:
                # Virtual machine is already running
                self.logger.info("Virtual machine is running.")
                return

            # Start virtual machine
            self.logger.debug("Starting virtual machine...")

            progress = self.machine.launch_vm_process(session, "gui", [])
            progress.wait_for_completion()
            self.logger.debug("Virtual machine has started.")
        except Exception as e:
            self.logger.error(e, "Failed to start VM. See log file for details.")
        finally:
            if session.state == SessionState.locked:
                session.unlock_machine()

    def __check_ssh(self) -> bool:
        """
        Check if SSH connection can be established with the virtual machine.

        Returns:
            bool: True if SSH connection was successful, False otherwise.
        """
        try:
            # Establish SSH connection with the virtual machine
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            ssh.connect(hostname=self.host, port=self.port, username=self.username, password=self.password)

            # Execute "ls" command to check if the connection was successful
            stdin, stdout, stderr = ssh.exec_command("ls")
            exit_status = stdout.channel.recv_exit_status()

            # If the exit status is not 0, raise OSError
            if exit_status != 0:
                raise OSError()

            return True
        except Exception:
            # If an exception is raised, return False
            return False
        finally:
            # Close the SSH connection
            if ssh:
                ssh.close()



