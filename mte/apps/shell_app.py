import re

from mte.apps.app import App
from mte.executor import TestExecutor


class ShellApp(App):
    """
    Simple command line execution application.
    Uses command line as user interface.
    """
    def __init__(self):
        super().__init__()

    def load(self):
        """
        Loads TestExecutor object, tests and starts execution.
        """
        try:
            self.executor = TestExecutor()
            self.tests = self.executor.get_tests()

            self.select()
        except:
            quit(1)

    def execute(self):
        """
        Starts testing, when done prints output.
        """
        try:
            self.executor.establish_connection()

            while True:
                if self.executor.check_connection_status():
                    break

            self.executor.execute([t for t in self.tests if t["selected"] is True])

            while True:
                if self.executor.check_execution_status():
                    break

            print(self.executor.get_results())
        except:
            quit(1)

    def out(self, message):
        """
        Implements standard print as stdout for Logger.

        @param message: string to print.
        """
        print(message)

    def select(self):
        """
        Test selection logic through input.
        After confirmation of test selection, starts test execution.
        """
        while True:
            print("Actual selection: '+' as selected, '-' as unselected")
            self.__print_selection()

            # Print options
            cmd = input("['s'/'u'/'d'] ['all'/test numbers separated by ',']\n")

            try:
                command, choice = self.__parse_input(cmd)

                if command == 'd':
                    break
                else:
                    if choice == 'all':
                        for t in self.tests:
                            t["selected"] = (command == 's')
                        continue

                    for i in choice:
                        if i < len(self.tests):
                            self.tests[i]["selected"] = (command == 's')
                        else:
                            raise ValueError(f"Invalid input: invalid index {i}")
            except ValueError:
                print("Invalid input.")

        self.execute()

    def __parse_input(self, cmd):
        """
        Input parsing handler for test selection.
        Accepts:
        - u for unselect, options: 'all' or list of numbers separated by ','
        - s for select, options: 'all' or list of numbers separated by ','
        - d for confirmation of selection

        @param cmd: user input.
        @return: command, affected item indexes.
        """
        # Define regex
        regex = r'^([sud])(\s+all|\s+(\d+)(,\s*\d+)*)?$'
        # match regex
        match = re.match(regex, cmd.strip())
        if not match:
            raise ValueError(f"Invalid input: {cmd}")

        command, items = match.group(1), match.group(2)

        if not items:
            if command != 'd':
                raise ValueError(f"Invalid input: {cmd}")
            items = None
        elif items.strip() == 'all':
            items = 'all'
        else:
            items = [int(i) for i in items.split(',')]
        return command, items

    def __print_selection(self):
        """
        Prints formated string of tests with specified selection.
        '+' -> selected.
        '-' -> unselected.
        """
        for i in range(len(self.tests)):
            test = self.tests[i]
            print(f"{'+' if test['selected'] else '-'} {i} [{test['type']}] src: {test['src']} | {test['name']}")