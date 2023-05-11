from abc import ABC, abstractmethod

from mte.logger import Logger


class App(ABC):
    """
    Abstract class for any application class used as execution format.

    Used as interface between user and testing environment.
    All of the testing logic is in TestExecutor which needs to be loaded in Load function.
    """
    __logger = Logger()

    def __init__(self):
        self.tests = []

    @abstractmethod
    def load(self):
        """
        Execution starts here, logger is not registered before this, so any other execution will fail.
        Should contain:
        1. Initialization of TestExecutor.
        2. Loading of tests through TestExecutor.
        """
        pass

    @abstractmethod
    def out(self, message):
        """
        Method passed to Logger to be used as stdout for application messages.
        Should contain 'printing' logic.
        @param message: Message to be showed to user.
        """
        pass