import time

import paramiko
import virtualbox as vb
from virtualbox.library import MachineState, SessionState

from mte.logger import Logger


class RemoteManager:
    """
        Manages a VirtualBox VM and its connection using SSH.
    """
    __logger = Logger()

    def __init__(self, vm_name: str | None, host: str, port: int, username: str, password: str, using_vb: bool):
        """
        Initialization of RemoteManager.
        In case of usign virtual box, validates VM.

        @param vm_name: name of VM.
        @param host: remote IP.
        @param port: remote SSH port.
        @param username: remote username for SSH.
        @param password: remote password for SSH.
        @param using_vb: determines if using Virtual Box API.
        """
        self.__host = host
        self.__port = port
        self.__username = username
        self.__password = password
        self.__using_vb = using_vb
        self.__vm_name = vm_name

        if self.__using_vb:
            if not vm_name:
                self.__logger.error(ValueError("Missing VM name."), "Missing VM name.")
            self.__validate_vm(vm_name)

    def connect(self):
        """
        Connects to the VM using SSH and waits until the SSH port is available.
        """
        try:
            if self.__using_vb:
                self.__start_vm()
            else:
                self.__validate_connection(True)
            self.__logger.info("Guest is ready.")
        except Exception as e:
            self.__logger.error(e, "Failed to connect to guest.")

    def __validate_connection(self, time_out: bool):
        """
        Validates if connection to the remote can be established. In case of time_out doesnt limit validation time
        and in case of virtual box, if time_out is False, waits for 30 seconds for boot-up of VM.

        @param time_out (bool): determines if to limit validation time.
        """
        # Wait until ssh port is available
        tries_count = 0
        while True:
            tries_count += 1
            self.__logger.debug("Validating SSH connection...")

            if self.__check_ssh():
                # SSH connection is ready

                if self.__using_vb and not time_out:
                    # This block is intended for freshly started VM to wait for complete boot run.
                    # Sleep value is set high. Depends on target system.
                    time.sleep(90)
                break

            time.sleep(2)
            if tries_count >= 3 and time_out:
                # Reached limited tries for connection.
                raise ConnectionError("SSH connection timeout.")

    def __validate_vm(self, vm_name: str):
        """
        Validates VM instance in local Virtual Box.

        @param vm_name: VM name.
        """
        self.__logger.debug("Validating virtual machine...")

        # Establish connection with Virtual Box
        try:
            self.vbox = vb.VirtualBox()
        except Exception as e:
            self.__logger.error(e, "Failed to establish connection with Virtual Box. See logs for more info.")

        self.__logger.debug(f"Running virtual box version: {self.vbox.version}")

        # Find desired virtual machine
        try:
            self.machine = self.vbox.find_machine(vm_name)
        except Exception as e:
            # Machine doesnt exist
            self.__logger.error(e, f"VM: {vm_name} does not exist on host system.")

        self.__logger.debug(f"Virtual machine {vm_name} found.")

    def __start_vm(self):
        """
        Starts the VM in VirtualBox and waits until it is running.
        """
        try:
            self.__logger.debug("Checking virtual machine...")
            session = vb.Session()

            if self.machine.state == MachineState.running or self.machine.state == MachineState.paused:
                # Virtual machine is already running
                self.__validate_connection(True)
                self.__logger.info("Virtual machine is running.")
                return

            # Start virtual machine
            self.__logger.debug("Starting virtual machine...")

            progress = self.machine.launch_vm_process(session, "gui", [])
            progress.wait_for_completion(-1)
            self.__logger.debug("Virtual machine has started.")

            self.__validate_connection(False)
        except Exception as e:
            self.__logger.error(e, "Failed to start VM. See log file for details.")
        finally:
            if session.state == SessionState.locked:
                session.unlock_machine()
            # vb._cleanup_managers()

    def __check_ssh(self) -> bool:
        """
        Check if SSH connection can be established with the virtual machine.

        @return: True if ssh connection was successful, False otherwise.
        """
        try:
            # Establish SSH connection with the virtual machine
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            ssh.connect(hostname=self.__host, port=self.__port, username=self.__username, password=self.__password, timeout=5)

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



