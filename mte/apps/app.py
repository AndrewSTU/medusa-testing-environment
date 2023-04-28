from mte.configuration_manager import ConfigurationManager
from mte.logger import Logger
from abc import ABC, abstractmethod

class App(ABC):
    logger = Logger()

    def __init__(self):
        self.client_config = None
        self.environment_config = None
        self.testing_config = None

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def out(self, message):
        pass