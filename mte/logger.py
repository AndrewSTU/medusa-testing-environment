import logging


class Logger:
    """
    Logger class using the singleton architecture.
    Manages logging of messages and exceptions.

    Attributes:
        - __instance: represents instances of logger in the whole application
        - __logger: interface for logging into the log file
        - __stdout: represents an output handler for application messages
    """
    __instance = None
    __logger = logging.getLogger()

    def __new__(cls):
        """
        Checks instances and prevents multiple instances.
        """
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        """
        Assigns output handler.
        """
        # Set up logging
        logging.basicConfig(
            filename="log",
            filemode="w",
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s]: %(message)s"
        )

        self.__stdout = None
        self.__debug = False

    def set_stdout(self, output_handler):
        self.__stdout = output_handler

    def set_debug_mode(self):
        self.__debug = True

    def info(self, message):
        """
        Prints message through output handler and logs it into the log file.
        """
        self.__stdout.out(message)
        self.__logger.info(message)

    def debug(self, message):
        """
        Prints message through output handler, if logger is in debug mode and logs it into the log file.
        """
        if self.__debug:
            self.__stdout.out(message)
        self.__logger.debug(message)

    def error(self, exception, message=None):
        """
        If message is present, prints it or prints a generic message.
        Logs the exception into the log file and raises a generic runtime exception.
        """
        if message:
            self.__stdout.out(message)
            self.__logger.error(f"{message}:\n{exception}")
        else:
            self.__stdout.out("Runtime error occurred. See log file for more information.")
            self.__logger.error(f"{exception.__class__.__name__}:\n{exception}")

        raise exception