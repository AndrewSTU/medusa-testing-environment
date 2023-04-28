import queue
import threading
import pexpect


class Reader:
    def __init__(self, cmd):
        """
        Creates a virtual terminal for a command which can be read in realtime using the read method.
        Output is stored in a queue which is filled in a separate thread.
        @param cmd: Command to be started and read
        @return: Reader object with running process
        """
        self.cmd = cmd
        self.process = None
        self.queue = queue.Queue()
        self.process = pexpect.spawnu(cmd)
        self.thread = threading.Thread(name=cmd, target=self.__start)
        self.thread.start()

    def __start(self):
        """
        Function to be started in a separate thread for reading output of the command in real-time
        """
        for line in iter(self.process.readline, ''):
            self.queue.put(line)

    def read(self):
        """
        Reads queue that was filled by standard output of the process
        @return: Unread output by the running process
        """
        output = ''
        while not self.queue.empty():
            output += self.queue.get_nowait()
        return output

    def terminate(self):
        """
        Terminates the running process
        """
        self.process.terminate()