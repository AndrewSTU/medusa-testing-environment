from mte.logger import Logger
import paramiko as p
import os

class SSHManager:
    logger = Logger()

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

    def exec(self, command):
        stdin, stdout, stderr = self.ssh.exec_command(command)
        output = stdout.read().decode().strip('\n')
        error = stderr.read().decode().strip('\n')
        exit_status = stdout.channel.recv_exit_status()

        # Wait for command execution
        while not stdout.channel.exit_status_ready():
            # Wait for the command to complete
            pass

        # Check if resulted in error
        if exit_status != 0:
            self.logger.error(IOError(f"SSH command: {command} failed: \n{error}"), "Error while executing ssh command.")

        return output

    def prepare_environment(self, env_path):
        self.logger.debug("Preparing environment directory on remote...")

        src_dir = os.path.join(os.path.dirname(__file__), "remote")

        self.transfer(src_dir, env_path, True)

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

        if os.path.isdir(src_path):
            # Dir transfer
            if not just_content:
                dir_name = os.path.basename(src_path)
                dest_path = os.path.join(dest_path, dir_name)

            # Create dir on remote
            try:
                sftp.stat(dest_path)
            except FileNotFoundError:
                sftp.mkdir(dest_path)

            # Transfer dir contents
            for f in os.listdir(src_path):
                final_path = dest_path + '/' + f
                try:
                    sftp.remove(final_path)
                except FileNotFoundError:
                    pass

                try:
                    sftp.put(os.path.join(src_path, f), final_path)
                except Exception as e:
                    self.logger.error(e, f"File transfer failed for {f}")
        else:
            # File transfer
            base_name = os.path.basename(src_path)
            try:
                sftp.put(src_path, os.path.join(dest_path, base_name))
            except Exception as e:
                self.logger.error(e, f"File transfer failed for {base_name}")

        # Close sftp
        sftp.close()

    def disconnect(self):
        self.logger.debug("Disconnecting SSH client...")
        self.ssh.close()
        self.logger.debug("SSH client disconnected.")

    def __del__(self):
        try:
            self.disconnect()
        except:
            pass
