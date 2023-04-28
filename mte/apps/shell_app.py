from mte.executor import TestExecutor
from mte.apps.app import App


class ShellApp(App):
    def __init__(self):
        super().__init__()

    def load(self):
        self.executor = TestExecutor(self)

        self.select()

    def select(self):
        self.tests = self.executor.get_tests()

        self.execute()

    def execute(self):
        self.executor.execute(self.tests)

    def out(self, message):
        print(message)
