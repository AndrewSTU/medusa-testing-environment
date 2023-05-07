import time

from mte.logger import Logger
import paramiko as p
import os

class SSHManager:
    logger = Logger()

    skip_nodes = [".idea", ".git", ".gitignore"]

    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssh = None

    def connect(self):
        try:
            self.ssh = p.SSHClient()
            self.ssh.set_missing_host_key_policy(p.AutoAddPolicy)
            self.ssh.connect(hostname=self.host, port=self.port, username=self.username, password=self.password)
        except Exception as e:
            self.logger.error(e, "Failed to connect to SSH server")

    def exec(self, command, timeout=False):
        stdin, stdout, stderr = self.ssh.exec_command(command)
        output = stdout.read().decode().strip('\n')
        error = stderr.read().decode().strip('\n')
        exit_status = stdout.channel.recv_exit_status()

        if timeout:
            timer = time.time()
            while not stdout.channel.recv_ready():
                if (time.time() - timer) > 10:
                    raise TimeoutError("Command took too long.")
                time.sleep(0.1)

        # Wait for command execution
        while not stdout.channel.exit_status_ready():
            # Wait for the command to complete
            pass

        # Check if resulted in error
        if exit_status != 0:
            self.logger.error(IOError(f"SSH command: {command} failed: \n{error}"), "Error while executing ssh command.")

        return output

    def prepare_environment(self, env_path, include_git):
        self.logger.debug("Preparing environment directory on remote...")

        transfer_dir = os.path.join(os.path.dirname(__file__), "remote")

        self.transfer(transfer_dir, env_path, True)

        if include_git:
            git_dir = os.path.join(os.path.dirname(__file__), "tests", "medusa-tests")

            if not os.path.exists(git_dir):
                e = "Git tests repo missing in tests folder."
                self.logger.error(FileNotFoundError(e), e)

            self.transfer(git_dir, env_path, False)

        self.logger.debug("Remote environment is ready.")


    def transfer(self, src_path, dest_path, just_content=True):
        # Obtain SFTP connection
        sftp = None
        try:
            sftp = self.ssh.open_sftp()
        except Exception as e:
            self.logger.error(e, "Failed to open SFTP connection.")

        # Check if file/dir exists
        if not os.path.exists(src_path):
            self.logger.error(FileNotFoundError(f"File for transfer on {src_path} doesnt exist."), "Error while file transfer.")

        # Create remote dir
        try:
            sftp.stat(dest_path)
        except FileNotFoundError:
            sftp.mkdir(dest_path)

        # Get node name
        base_name = os.path.basename(src_path)

        if just_content and os.path.isdir(src_path):
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

    def __transfer_recursive(self, sftp, src_path, dest_path):
        node_name = os.path.basename(src_path)
        new_dest = os.path.normpath(os.path.join(dest_path, node_name)).replace("\\", "/")

        if node_name in self.skip_nodes:
            return

        if os.path.isdir(src_path):
            # Ger remote dir path
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
                self.logger.error(e, f"File transfer failed for {node_name}")

    def disconnect(self):
        self.logger.debug("Disconnecting SSH client...")
        self.ssh.close()
        self.logger.debug("SSH client disconnected.")

    def __del__(self):
        try:
            self.disconnect()
        except:
            pass
