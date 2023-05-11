import tkinter as tk

from mte.apps.app import App
from mte.executor import TestExecutor


class GuiApp(App):
    """
    GUI execution application.
    Uses tkinter window graphics for user interface.
    """
    def __init__(self):
        super().__init__()

        # Define root
        self.root = tk.Tk()
        self.root.title("Medusa testing environment")
        self.root.geometry("800x500")

        # Create a frame for the buttons
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(side="top", fill="x")

        # Select buttons
        self.select_all_button = tk.Button(self.buttons_frame, text="Select all", state="disabled", command=lambda: self.toggle_all(True))
        self.select_all_button.pack(side="left", padx=5, pady=5)

        self.unselect_all_button = tk.Button(self.buttons_frame, text="Unselect all", state="disabled", command=lambda: self.toggle_all(False))
        self.unselect_all_button.pack(side="left", padx=5, pady=5)

        # Start button
        self.start_button = tk.Button(self.buttons_frame, text="Start", state="disabled", command=self.start)
        self.start_button.pack(side="right", padx=5, pady=5)

        # Reload button
        self.reload_button = tk.Button(self.buttons_frame, text="Reload", state="disabled", command=self.reload)
        self.reload_button.pack(side="right", padx=5, pady=5)

        # create a frame for the list of element
        self.elements_frame = tk.Frame(self.root, relief="groove", bd=2, bg="white")
        self.elements_frame.pack(side="top", fill="both", expand=True)

        # Create a canvas and scrollbar for tests
        self.canvas = tk.Canvas(self.elements_frame, bg="white")
        self.scrollbar = tk.Scrollbar(self.elements_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind_all("<MouseWheel>", self.scroll_wheel)

        # Create a frame to hold the checkboxes
        self.checkboxes_frame = tk.Frame(self.canvas, bg="white")
        self.canvas.create_window((0,0), window=self.checkboxes_frame, anchor="nw")

        # Create a frame for the log output
        self.log_frame = tk.Frame(self.root, relief="groove", bd=2)
        self.log_frame.pack(side="bottom", fill="both", expand=True)

        # Create a text widget for the log output
        self.log_text = tk.Text(self.log_frame, bg="white", state="disabled")
        self.log_text.pack(side="left", fill="both", expand=True)

    def scroll_wheel(self, event):
        """
        Handler for scroll event in test selection frame.

        @param event: scroll event.
        """
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def set_state(self, state):
        """
        Disables/enables buttons according to application state.

        @param state: current application state.
        """
        if state == "ERROR":
            self.reload_button["state"] = "normal"
            self.select_all_button["state"] = "disabled"
            self.unselect_all_button["state"] = "disabled"
            self.start_button["state"] = "disabled"

        if state == "READY":
            self.reload_button["state"] = "normal"
            self.select_all_button["state"] = "normal"
            self.unselect_all_button["state"] = "normal"
            self.start_button["state"] = "normal"

        if state == "RUNNING":
            self.reload_button["state"] = "disabled"
            self.select_all_button["state"] = "disabled"
            self.unselect_all_button["state"] = "disabled"
            self.start_button["state"] = "disabled"

        if state == "DONE":
            self.reload_button["state"] = "normal"
            self.select_all_button["state"] = "disabled"
            self.unselect_all_button["state"] = "disabled"
            self.start_button["state"] = "disabled"

    def __update_test_list(self, tests):
        """
        used for updating and redering of tests selection.

        @param tests: loaded tests.
        """
        self.tests = list(map(lambda x: {**x, 'selected': tk.BooleanVar(value=x['selected'])}, tests))
        # Clear the frame
        for widget in self.checkboxes_frame.winfo_children():
            widget.destroy()

        # Create new checkboxes
        for test in self.tests:
            text = f"[{test['type']}] src: {test['src']} | {test['name']}"
            checkbox = tk.Checkbutton(self.checkboxes_frame, text=text, bg="white",pady=2, variable=test["selected"])
            checkbox.pack(anchor=tk.W)

        # Update the scrollbar
        self.checkboxes_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def toggle_all(self, new_value):
        """
        Sets selection value for all tests.

        @param new_value: new selected value.
        """
        for t in self.tests:
            t["selected"].set(new_value)

    def show_results(self, results):
        """
        Opens new window and prints results.

        @param results: results to print.
        """
        if not results:
            return
        # Create a new window
        new_window = tk.Toplevel()
        new_window.geometry("750x300")
        new_window.title("Results")

        # Create a Text widget and a Scrollbar
        text_widget = tk.Text(new_window, wrap=tk.WORD)
        scrollbar = tk.Scrollbar(new_window, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        # Add some text to the Text widget
        text_widget.insert(tk.END, results)

        # Pack the Text widget and Scrollbar
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def out(self, message):
        """
        Implements stdout for logger, by appending to log_text frame.

        @param message: message to append.
        """
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.root.update_idletasks()

    def start(self):
        """
        Triggers execution process.
        """
        self.set_state("RUNNING")

        self.executor.establish_connection()
        self.root.after(100, self.check_connection)

    def execute(self):
        """
        Starts tests execution.
        """
        self.set_state("RUNNING")
        started = self.executor.execute(
            [t for t in self.tests if t["selected"].get() is True]
        )
        if started:
            self.root.after(1000, self.check_execution)
        else:
            self.set_state("DONE")

    def check_connection(self):
        """
        Checks if connection setup is still running.
        Prevents window freeze.
        """
        if not self.executor.check_connection_status():
            self.root.after(100, self.check_connection)
        else:
            self.set_state("DONE")
            self.execute()

    def check_execution(self):
        """
        Checks if tests execution is running.
        Prevents window freeze.
        """
        if not self.executor.check_execution_status():
            self.root.after(1000, self.check_execution)
        else:
            self.set_state("DONE")
            self.show_results(self.executor.get_results())

    def reload(self):
        """
        Reloads execution.
        """
        self.load()
        self.__logger.info("Reloaded environment.")
        self.set_state("READY")


    def load(self):
        """
        Loads TestExecutor object and tests.
        """
        try:
            self.executor = TestExecutor()

            self.__update_test_list(self.executor.get_tests())
        except:
            # Disable buttons
            self.set_state("ERROR")

        # Enable start button
        self.set_state("READY")
        self.root.mainloop()