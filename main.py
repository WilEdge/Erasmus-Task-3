import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
from backup import BackupManager

class BackupApp(tk.Tk):
    """
    Tkinter GUI Application for the file backup program.
    Manages the user interface, configuration, and interaction with the BackupManager.
    """
    def __init__(self):
        super().__init__()
        self.title("File Backup Logger")
        self.geometry("600x400") # Initial window size
        self.resizable(False, False) # Prevent resizing

        self.backup_manager = BackupManager() # Initialize the backup manager
        self.config_path = "config.json"
        self.config = self._load_config()

        self._create_widgets()
        self._load_preferences_to_gui()

    def _load_config(self):
        """Loads the configuration from the JSON file or creates a default one."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                messagebox.showerror("Configuration Error", "The config.json file is corrupted. Creating a new one.")
                return self._create_default_config()
        else:
            return self._create_default_config()

    def _create_default_config(self):
        """Creates and returns a default configuration."""
        default_config = {
            "source_folder": "",
            "destination_folder": "",
            "compress_backup": False,
            "backup_interval_days": 7 # Not used in this manual version, but for future reference
        }
        self._save_config(default_config)
        return default_config

    def _save_config(self, config_data):
        """Saves the current configuration to the JSON file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save configuration: {e}")

    def _load_preferences_to_gui(self):
        """Loads preferences from the configuration into the GUI fields."""
        self.source_path_var.set(self.config.get("source_folder", ""))
        self.destination_path_var.set(self.config.get("destination_folder", ""))
        self.compress_var.set(self.config.get("compress_backup", False))

    def _save_preferences_from_gui(self):
        """Saves preferences from the GUI fields into the configuration."""
        self.config["source_folder"] = self.source_path_var.get()
        self.config["destination_folder"] = self.destination_path_var.get()
        self.config["compress_backup"] = self.compress_var.get()
        self._save_config(self.config)

    def _create_widgets(self):
        """Creates all GUI elements."""
        # Main frame for padding
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Variables for paths and compression
        self.source_path_var = tk.StringVar()
        self.destination_path_var = tk.StringVar()
        self.compress_var = tk.BooleanVar()

        # --- Source Folder Section ---
        tk.Label(main_frame, text="Source Folder :", font=("Inter", 10, "bold")).pack(anchor="w", pady=(10, 0))
        source_frame = tk.Frame(main_frame)
        source_frame.pack(fill=tk.X, pady=5)
        tk.Entry(source_frame, textvariable=self.source_path_var, width=60, bd=2, relief="groove", font=("Inter", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(source_frame, text="Browse", command=self._browse_source_folder, font=("Inter", 9), bd=2, relief="raised").pack(side=tk.RIGHT, padx=5)

        # --- Destination Folder Section ---
        tk.Label(main_frame, text="Destination Folder :", font=("Inter", 10, "bold")).pack(anchor="w", pady=(10, 0))
        dest_frame = tk.Frame(main_frame)
        dest_frame.pack(fill=tk.X, pady=5)
        tk.Entry(dest_frame, textvariable=self.destination_path_var, width=60, bd=2, relief="groove", font=("Inter", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(dest_frame, text="Browse", command=self._browse_destination_folder, font=("Inter", 9), bd=2, relief="raised").pack(side=tk.RIGHT, padx=5)

        # --- Compression Option ---
        tk.Checkbutton(main_frame, text="Compress Backup (ZIP)", variable=self.compress_var, font=("Inter", 10)).pack(anchor="w", pady=10)

        # --- Backup Button ---
        tk.Button(main_frame, text="Start Backup", command=self._start_backup,
                  font=("Inter", 12, "bold"), bg="#4CAF50", fg="white",
                  activebackground="#45a049", activeforeground="white",
                  bd=3, relief="raised", padx=20, pady=10).pack(pady=20)

        # --- Status Message ---
        self.status_message = tk.StringVar()
        self.status_label = tk.Label(main_frame, textvariable=self.status_message, font=("Inter", 10, "italic"), fg="blue")
        self.status_label.pack(pady=5)

    def _browse_source_folder(self):
        """Opens a dialog to select the source folder."""
        folder_selected = filedialog.askdirectory(title="Select Source Folder")
        if folder_selected:
            self.source_path_var.set(folder_selected)
            self._save_preferences_from_gui() # Save preference immediately

    def _browse_destination_folder(self):
        """Opens a dialog to select the destination folder."""
        folder_selected = filedialog.askdirectory(title="Select Destination Folder")
        if folder_selected:
            self.destination_path_var.set(folder_selected)
            self._save_preferences_from_gui() # Save preference immediately

    def _start_backup(self):
        """Initiates the backup process."""
        source_folder = self.source_path_var.get()
        destination_folder = self.destination_path_var.get()
        compress = self.compress_var.get()

        if not source_folder:
            messagebox.showwarning("Missing Source Folder", "Please select a source folder.")
            return
        if not destination_folder:
            messagebox.showwarning("Missing Destination Folder", "Please select a destination folder.")
            return

        # Save preferences before starting the backup
        self._save_preferences_from_gui()

        self.status_message.set("Backup in progress, please wait...")
        self.update_idletasks() # Update the GUI to show the message

        success = self.backup_manager.perform_backup(source_folder, destination_folder, compress)

        if success:
            self.status_message.set("Backup completed successfully!")
            messagebox.showinfo("Backup Successful", "The backup has been performed successfully.")
        else:
            self.status_message.set("Backup failed. See logs for more details.")
            messagebox.showerror("Backup Failed", "An error occurred during backup. Please check the 'logs/backup.log' file for more details.")

if __name__ == "__main__":
    app = BackupApp()
    app.mainloop()