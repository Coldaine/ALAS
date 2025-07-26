
import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import os
from datetime import datetime

# Import the original ALAS script's main class
from alas import AzurLaneAutoScript, AzurLaneConfig

class AlasGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ALAS Log Viewer")
        self.geometry("800x600")

        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled')
        self.log_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.pause_button = tk.Button(self, text="Pause", command=self.pause_bot)
        self.pause_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.resume_button = tk.Button(self, text="Resume", command=self.resume_bot, state='disabled')
        self.resume_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.exit_button = tk.Button(self, text="Exit", command=self.exit_bot)
        self.exit_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # --- Bot control events ---
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set() # Start in the "running" state

        # --- Bot thread ---
        self.bot_thread = threading.Thread(target=self.run_alas)
        self.bot_thread.daemon = True
        self.bot_thread.start()

        # --- Log reader ---
        self.log_file_path = "" # Will be set once the bot starts
        self.after(1000, self.update_log_area)

    def run_alas(self):
        """Runs the ALAS bot in a separate thread."""
        try:
            alas = AzurLaneAutoScript()
            alas.stop_event = self.stop_event
            # We need to inject the pause event into the bot's loop.
            # This will require a small modification to alas.py
            alas.pause_event = self.pause_event 
            
            # Determine log file path
            log_dir = "./log"
            config_name = alas.config_name
            date_str = datetime.now().strftime("%Y-%m-%d")
            self.log_file_path = os.path.join(log_dir, f"{date_str}_{config_name}.txt")

            alas.loop()
        except Exception as e:
            print(f"Error in ALAS thread: {e}")


    def update_log_area(self):
        """Periodically reads the log file and updates the text area."""
        if self.log_file_path and os.path.exists(self.log_file_path):
            try:
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    # Simple read and update, could be optimized for large files
                    content = f.read()
                    self.log_area.config(state='normal')
                    self.log_area.delete('1.0', tk.END)
                    self.log_area.insert(tk.END, content)
                    self.log_area.config(state='disabled')
                    self.log_area.yview(tk.END)
            except Exception as e:
                print(f"Error reading log file: {e}")
        
        self.after(1000, self.update_log_area)

    def pause_bot(self):
        self.pause_event.clear()
        self.pause_button.config(state='disabled')
        self.resume_button.config(state='normal')

    def resume_bot(self):
        self.pause_event.set()
        self.resume_button.config(state='disabled')
        self.pause_button.config(state='normal')

    def exit_bot(self):
        self.stop_event.set()
        # Give the bot a moment to shut down
        self.after(2000, self.destroy)

if __name__ == "__main__":
    app = AlasGui()
    app.mainloop()
