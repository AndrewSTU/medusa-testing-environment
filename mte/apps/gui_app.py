from mte.apps.app import App
from mte.executor import TestExecutor
import tkinter as tk

class GuiApp(App):
    def __init__(self):
        super().__init__()

        self.root = tk.Tk()
        self.root.title("Medusa testing environment")
        self.root.geometry("800x500")

        self.actions_disabled = tk.BooleanVar(value=False)

        # create a frame for the buttons
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(side="top", fill="x")

        # select buttons
        self.reload_button = tk.Button(self.buttons_frame, text="Select all",  command=lambda: self.toggle_all(True))
        self.reload_button.pack(side="left", padx=5, pady=5)

        self.reload_button = tk.Button(self.buttons_frame, text="Unselect all", command=lambda: self.toggle_all(False))
        self.reload_button.pack(side="left", padx=5, pady=5)

        # create a start button
        self.start_button = tk.Button(self.buttons_frame, text="Start", command=self.start)
        self.start_button.pack(side="right", padx=5, pady=5)

        # create a reload button
        self.reload_button = tk.Button(self.buttons_frame, text="Reload", command=self.reload)
        self.reload_button.pack(side="right", padx=5, pady=5)

        # create a frame for the list of element
        self.elements_frame = tk.Frame(self.root, relief="groove", bd=2, bg="white")
        self.elements_frame.pack(side="top", fill="both", expand=True)

        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self.elements_frame, bg="white")
        self.scrollbar = tk.Scrollbar(self.elements_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind_all("<MouseWheel>", self.scroll_wheel)

        # Create a frame to hold the checkboxes
        self.checkboxes_frame = tk.Frame(self.canvas, bg="white")
        self.canvas.create_window((0,0), window=self.checkboxes_frame, anchor="nw")

        # add some example elements to the listbox
        self.all_tests = []


        # create a frame for the log output
        self.log_frame = tk.Frame(self.root, relief="groove", bd=2)
        self.log_frame.pack(side="bottom", fill="both", expand=True)

        # create a text widget for the log output
        self.log_text = tk.Text(self.log_frame, bg="white", state="disabled")
        self.log_text.pack(side="left", fill="both", expand=True)

    def scroll_wheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def __update_test_list(self, tests):
        self.all_tests = list(map(lambda x: {**x, 'selected': tk.BooleanVar(value=x['selected'])}, tests))
        # Clear the frame
        for widget in self.checkboxes_frame.winfo_children():
            widget.destroy()

        # Create new checkboxes
        for test in self.all_tests:
            text = f"[{test['type']}] src: {test['src']} | {test['name']}"
            checkbox = tk.Checkbutton(self.checkboxes_frame, text=text, bg="white",pady=2, variable=test["selected"])
            checkbox.pack(anchor=tk.W)

        # Update the scrollbar
        self.checkboxes_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def toggle_all(self, new_value):
        for t in self.all_tests:
            t["selected"].set(new_value)

    def show_results(self, results):
        # Create a new window
        new_window = tk.Toplevel()
        new_window.geometry("600x300")
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
        """Append a message to the log output"""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.root.update_idletasks()

    def start(self):
        self.executor.connect()
        self.root.after(100, self.check_connection)

    def execute(self):
        started = self.executor.execute(
            [t for t in self.all_tests if t["selected"].get() is True]
        )
        if started:
            self.root.after(1000, self.check_execution)

    def check_connection(self):
        if not self.executor.check_connection_status():
            self.root.after(100, self.check_connection)
        else:
            self.execute()

    def check_execution(self):
        if not self.executor.check_execution_status():
            self.root.after(1000, self.check_execution)

    def reload(self):
        self.__update_test_list(self.executor.get_tests())
        self.logger.info("Reloaded tests.")


    def load(self):
        self.executor = TestExecutor(self)

        self.__update_test_list(self.executor.get_tests())

        self.root.mainloop()