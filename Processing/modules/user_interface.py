import tkinter as tk
from modules.connection_manager import ConnectionManager
from modules.processor import PacketProcessor
from modules.rotator import Rotator

class UserInterface(tk.Frame):
    def __init__(self, parent, connection_manager, processor, rotator, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent = parent
        self.connection_manager = connection_manager
        self.processor = processor
        self.rotator = rotator
        # Create the rest of your GUI here
        self.label = tk.Label(self, text="Hello from ThreadManager!")
        self.label.pack()

    def create_gui(self):
        root = tk.Tk()
        UserInterface(root).pack(side="top", fill="both", expand=True)
        root.mainloop()
