import argparse

from mte.logger import Logger
from mte.apps.shell_app import ShellApp
from mte.apps.gui_app import GuiApp


def main():
    # Create argument parser
    arg_parser = argparse.ArgumentParser(description='Main script to run MTE (Multilingual Text Editor).')

    # Define argument options
    arg_parser.add_argument('--mode', type=str, help='Run mode of application. Options: [shell, gui]. Default = shell')
    arg_parser.add_argument('--debug', action='store_const', const=True, help='Run in debug logging mode.')

    # Parse arguments
    args = arg_parser.parse_args()

    # Extract values from arguments
    run_mode = args.mode
    debug_mode = args.debug

    # Create logger instance
    logger = Logger()

    # Determine appropriate app instance
    app = ShellApp()  # default to ShellApp
    if run_mode == 'gui':
        app = GuiApp()

    # Enable debug logging if debug flag is set
    if debug_mode:
        logger.set_debug_mode()

    # Assign output handler to logger
    logger.set_stdout(app)

    # Load app
    try:
        app.load()
    except:
        quit()