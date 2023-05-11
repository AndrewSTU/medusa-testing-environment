import os
import shutil
import socket

import paramiko as p

from mte.logger import Logger


class SSHManager:
    """
    Manages and handles SSH operations as commands execution and file transfers.
    """
    __logger = Logger()

    __skip_nodes = [".idea", ".git", ".gitignore"]

    def __init__(self, host: str, port: int, username: str, password: str):
        """
        Initializes SSHManager.

        @param host: remote IP address or hostname.
        @param port: remote SSH port.
        @param username: remote SSH username.
        @param password: remote SSH password
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self.ssh = p.SSHClient()
        self.ssh.set_missing_host_key_policy(p.AutoAddPolicy)

    def connect(self):
        """
        Tries to establish connection to remote target.
        """
        try:
            # Try to connect to ssh
            self.ssh.connect(hostname=self.host, port=self.port, username=self.username, password=self.password)
        except Exception as e:
            self.__logger.error(e, "Failed to connect to SSH server")

    def exec(self, command, timeout=False, log_error=True):
        """
        Execute command through ssh and wait for response.
        If timeout is set, waits for response for 10 seconds, then throws exception.

        @param log_error: flag for silent error.
        @param command: shell command to execute.
        @param timeout: timeout flag limiting wait time for command execution.
        @return: shell command response.
        """
        timeout_val = 10 if timeout else None
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command, timeout=timeout_val)
        except socket.timeout:
            raise TimeoutError("Command took to long.")

        # Wait for command until finishes
        exit_status = stdout.channel.recv_exit_status()

        # Read response
        output = stdout.read().decode().strip('\n')
        error = stderr.read().decode().strip('\n')

        # Check if resulted in error
        if exit_status != 0:
            e = IOError(f"SSH command: {command} failed: \n{error}")
            if log_error:
                self.__logger.error(IOError(e, "Error while executing ssh command."))
            else:
                raise IOError(e)

        return output

    def exec_async(self, command):
        """
        Executes command without waiting for result.
        @param command: shell command to execute.
        """
        self.ssh.exec_command(command)

    def prepare_environment(self, env_path, include_git):
        """
        Creates and transfers required directories on remote target
        @param env_path:
        @param include_git:
        """
        self.__logger.debug("Preparing environment directory on target...")

        transfer_dir = os.path.join(os.path.dirname(__file__), "target")

        # Transfer target dir
        self.transfer(transfer_dir, env_path, True)

        if include_git:
            # Transfer git tests repository
            git_dir = os.path.join(os.path.dirname(__file__), "tests", "medusa-tests")

            if not os.path.exists(git_dir):
                e = "Git tests repo missing in tests folder."
                self.__logger.error(FileNotFoundError(e), e)

            self.transfer(git_dir, env_path, False)

        self.__logger.debug("Remote environment is ready.")


    def transfer(self, src_path, dest_path, just_content=True):
        """
        Transfers files or whole directories.

        @param src_path: source node to transfer.
        @param dest_path: remote target path for transfer.
        @param just_content: if ture, transfers only src files.
        """
        # Obtain SFTP connection
        sftp = None
        try:
            sftp = self.ssh.open_sftp()
        except Exception as e:
            self.__logger.error(e, "Failed to open SFTP connection.")

        # Check if file/dir exists
        if not os.path.exists(src_path):
            self.__logger.error(FileNotFoundError(f"File for transfer on {src_path} doesnt exist."), "Error while file transfer.")

        # Create target dir
        try:
            sftp.stat(dest_path)
        except FileNotFoundError:
            sftp.mkdir(dest_path)

        if just_content and os.path.isdir(src_path):
            # Leave out main folder
            for node in os.listdir(src_path):
                self.__transfer_recursive(
                    sftp,
                    os.path.join(src_path, node),
                    dest_path
                )
        else:
            self.__transfer_recursive(sftp, src_path, dest_path)

        # Close sftp
        sftp.close()

    def download_results(self, env_path, just_log=False):
        """
        Downloads results folder and log file from target.
        if just_log is True, downlaods only log file.

        @param env_path: target path containing results and log.
        @param just_log: flag, if just log is needed.
        """
        # Create results dir, if doesn't exist
        self.__logger.debug("Transfering results...")

        # Build paths
        local_path = os.path.join(os.path.dirname(__file__), "results")
        remote_path = f"{env_path}/results"

        # Clear local results
        if os.path.exists(local_path):
            self.__logger.debug("Clearing previous results...")
            shutil.rmtree(local_path)

        # Create results directories
        os.makedirs(local_path, mode=0o777, exist_ok=True)
        os.makedirs(os.path.join(local_path, "details"), mode=0o777, exist_ok=True)
        try:
            sftp = self.ssh.open_sftp()
            # Transfer log
            sftp.get(f"{env_path}/log", os.path.join(local_path, "log"))

            # End if just transferring log
            if just_log:
                return

            # Transfer overal results
            sftp.get(f"{remote_path}/results", os.path.join(local_path, "results.txt"))

            # Transfer details
            sftp.chdir(f"{remote_path}/details")
            for file in sftp.listdir():
                sftp.get(f"{remote_path}/details/{file}", f"{os.path.join(local_path, 'details', file)}")

            sftp.close()
            self.__logger.debug("Results transfer complete.")
        except Exception as e:
            self.__logger.error(e, "Failed to transfer results. See log file.")

    def clean_target(self, env_path):
        """
        Clears all dependencies from target and if the directory remains empty, removes whole directory.

        @param env_path: remote testing dir.
        """
        self.__logger.debug("Clearing target environment...")

        # Register all transferred files
        files = os.listdir(os.path.join(os.path.dirname(__file__), "target"))
        files.append("medusa.conf")
        files.append("exit")

        # Register all dirs created by environment
        dirs = ["medusa-tests", "allowed", "restricted", "results", "log", "helper", "__pycache__"]

        # Clear files
        for f in files:
            try:
                self.exec(f"sudo rm {env_path}/{f}", log_error=False)
            except OSError:
                pass

        # Clear dirs
        for d in dirs:
            try:
                self.exec(f"sudo rm -r {env_path}/{d}", log_error=False)
            except OSError as e:
                if d != 'medusa-tests':
                    raise e

        # Remove parent if empty:
        try:
            self.exec(f"rmdir {env_path}")
        except:
            pass

    def __transfer_recursive(self, sftp, src_path, dest_path):
        """
        Helper function for recursive transfer for directories.

        @param sftp: sftp session.
        @param src_path: source to transfer.
        @param dest_path: remote target, where to transfer.
        """
        node_name = os.path.basename(src_path)
        new_dest = os.path.normpath(os.path.join(dest_path, node_name)).replace("\\", "/")

        if node_name in self.__skip_nodes:
            return

        if os.path.isdir(src_path):
            # Ger target dir path
            # Create dir
            try:
                sftp.stat(new_dest)
            except FileNotFoundError:
                sftp.mkdir(new_dest)

            # Iterate content
            for f in os.listdir(src_path):
                self.__transfer_recursive(
                    sftp,
                    os.path.join(src_path, f),
                    new_dest
                )
        else:
            # File
            try:
                sftp.put(src_path, new_dest)
            except Exception as e:
                self.__logger.error(e, f"File transfer failed for {node_name}")

    def disconnect(self):
        """
        Closes SSH session.
        """
        self.__logger.debug("Disconnecting SSH client...")
        self.ssh.close()
        self.__logger.debug("SSH client disconnected.")

    def __del__(self):
        """
        Calls @disconnect method on destruction, if still open.
        """
        try:
            self.disconnect()
        except:
            pass
