import configparser as cp
import os
from mte.logger import Logger


class ConfigurationManager:
    """
    Class to manage configuration from 'config.ini' file.
    """

    logger = Logger()

    def __init__(self):
        """
        Load configuration from 'config.ini' file.
        """
        self.logger.debug("Loading configuration from config.ini...")

        self.__config = cp.ConfigParser()
        self.__load_configuration()

        self.logger.debug("Configuration loading complete.")

    def get_config(self, section=None):
        """
        Returns the configuration for a specific section or all the configuration.

        :param section: Optional section to retrieve configuration for.
        :type section: str or None
        :raises KeyError: If specified section is not found in configuration.
        :return: Configuration for specified section or all the configuration.
        :rtype: configparser.ConfigParser or configparser.SectionProxy
        """
        if section is None or section == "":
            return self.__config

        if section not in self.__config.sections():
            e = f"Section {section} not found in configuration."
            self.logger.error(KeyError(e), e)
            raise KeyError(e)

        return self.__config[section]

    def __load_configuration(self):
        """
        Load configuration from 'config.ini' file.
        """
        # Get absolute path to script
        file_dir = os.path.dirname(os.path.abspath(__file__))
        # Get absolute path to config file
        config_path = os.path.join(file_dir, "config.ini")

        # Check if config file exists
        if not os.path.exists(config_path):
            e = "Missing 'config.ini' file in root directory."
            self.logger.error(FileNotFoundError(e), e)
            raise FileNotFoundError(e)

        try:
            # Read config file
            self.__config.read(config_path)
        except Exception as e:
            # Unexpected exception
            self.logger.error(e, "Error reading configuration file. See log for more details.")
            raise e

        # TODO: Validate config parameters